import argparse
import sys
import os
import json
import time
import socket
import logging
import threading
import subprocess
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from collections import OrderedDict
from contextlib import contextmanager
from typing import Optional, Dict, Any, Tuple

import requests
from requests.adapters import HTTPAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("translate_server")

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

_global_session = None

def get_global_session() -> requests.Session:
    global _global_session
    if _global_session is None:
        _global_session = requests.Session()
        _global_session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=3)
        _global_session.mount("https://", adapter)
        _global_session.mount("http://", adapter)
    return _global_session


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def setup_local_fork(config: dict):
    fork_path = config.get('local_deep_translator_fork_path')
    if fork_path:
        full_fork_path = os.path.abspath(os.path.join(os.path.dirname(__file__), fork_path))
        if full_fork_path not in sys.path:
            sys.path.insert(0, full_fork_path)


class ProviderRateLimiter:
    """
    Thread-safe concurrency and request pacing manager per provider.
    Enforces concurrency gating via semaphores and pacing delays.
    """
    def __init__(self, google_concurrency: int = 1, google_delay: float = 0.35,
                 deepl_concurrency: int = 5, argos_concurrency: int = 2):
        self.google_concurrency = max(1, int(google_concurrency))
        self.google_delay = max(0.0, float(google_delay))
        self.deepl_concurrency = max(1, int(deepl_concurrency))
        self.argos_concurrency = max(1, int(argos_concurrency))

        self._semaphores = {
            'google': threading.BoundedSemaphore(self.google_concurrency),
            'deepl': threading.BoundedSemaphore(self.deepl_concurrency),
            'argos': threading.BoundedSemaphore(self.argos_concurrency)
        }
        self._last_request_time = {
            'google': 0.0,
            'deepl': 0.0,
            'argos': 0.0
        }
        self._pacing_lock = threading.Lock()

    def acquire(self, provider: str):
        sem = self._semaphores.get(provider)
        if sem:
            sem.acquire()
        if provider == 'google' and self.google_delay > 0:
            with self._pacing_lock:
                now = time.time()
                elapsed = now - self._last_request_time['google']
                wait_time = self.google_delay - elapsed
                if wait_time > 0:
                    time.sleep(wait_time)
                self._last_request_time['google'] = time.time()

    def release(self, provider: str):
        try:
            if provider == 'google':
                with self._pacing_lock:
                    self._last_request_time['google'] = time.time()
        finally:
            sem = self._semaphores.get(provider)
            if sem:
                sem.release()

    @contextmanager
    def limit(self, provider: str):
        self.acquire(provider)
        try:
            yield
        finally:
            self.release(provider)

    def stats(self) -> dict:
        return {
            "google_concurrency": self.google_concurrency,
            "google_delay": self.google_delay,
            "deepl_concurrency": self.deepl_concurrency,
            "argos_concurrency": self.argos_concurrency
        }


class TranslationCache:
    """
    Thread-safe in-memory LRU cache storing translations keyed by (source, target, provider, text).
    """
    def __init__(self, max_size: int = 10000, enabled: bool = True):
        self.max_size = max(0, int(max_size))
        self.enabled = bool(enabled)
        self._cache = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def _make_key(self, source: str, target: str, provider: str, text: str) -> tuple:
        return (source, target, provider.lower(), text)

    def get(self, source: str, target: str, provider: str, text: str) -> Optional[str]:
        if not self.enabled or self.max_size <= 0:
            return None
        key = self._make_key(source, target, provider, text)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self.hits += 1
                return self._cache[key]
            self.misses += 1
            return None

    def set(self, source: str, target: str, provider: str, text: str, translation: str):
        if not self.enabled or self.max_size <= 0 or translation is None:
            return
        key = self._make_key(source, target, provider, text)
        with self._lock:
            self._cache[key] = translation
            self._cache.move_to_end(key)
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def stats(self) -> dict:
        with self._lock:
            return {
                "enabled": self.enabled,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses
            }

    def clear(self):
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0


_default_rate_limiter = ProviderRateLimiter()
_default_cache = TranslationCache()


class TranslationHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False
    disable_nagle_algorithm = True

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, config=None,
                 google_delay: float = 0.35, google_concurrency: int = 1,
                 deepl_concurrency: int = 5, argos_concurrency: int = 2,
                 cache_size: int = 10000, enable_cache: bool = True,
                 auto_failover: bool = False):
        self.seq_lock = threading.Lock()
        self.seq_counter = 0
        self.config = config or {}
        self.rate_limiter = ProviderRateLimiter(
            google_concurrency=google_concurrency,
            google_delay=google_delay,
            deepl_concurrency=deepl_concurrency,
            argos_concurrency=argos_concurrency
        )
        self.cache = TranslationCache(
            max_size=cache_size,
            enabled=enable_cache
        )
        self.auto_failover = auto_failover
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)


_argos_models: Dict[Tuple[str, str], Any] = {}
_argos_lock = threading.RLock()
_argos_warmup_status = "available"


def get_argos_warmup_status() -> str:
    with _argos_lock:
        if _argos_models:
            return "warm"
        return _argos_warmup_status


def setup_argostranslate_path():
    """Ensure argostranslate site-packages from neighboring workspace is accessible if needed."""
    try:
        import argostranslate.translate
        return
    except ImportError:
        pass
    base_dir = Path(__file__).resolve().parent.parent
    site_packages = base_dir / "20241121100211-argotranslate" / "venv" / "Lib" / "site-packages"
    if site_packages.exists() and str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))


def get_argos_translation_model(source: str, target: str):
    """Retrieve or initialize and cache an in-memory Argos translation model instance."""
    setup_argostranslate_path()
    key = (source.lower(), target.lower())
    with _argos_lock:
        if key in _argos_models:
            return _argos_models[key]
        try:
            import argostranslate.translate
            model = argostranslate.translate.get_translation_from_codes(source, target)
            if model:
                _argos_models[key] = model
                return model
        except Exception as e:
            logger.debug(f"In-memory Argos model loading failed for {source}->{target}: {e}")
    return None


def warmup_argos_models_async(language_pairs=None):
    """Spawn low-priority daemon thread to pre-warm installed Argos translation models into RAM."""
    global _argos_warmup_status
    _argos_warmup_status = "warming"
    pairs = language_pairs or [("en", "de"), ("de", "ru"), ("en", "ru"), ("de", "en")]

    def _worker():
        global _argos_warmup_status
        try:
            logger.info("Pre-warming Argos translation models in background...")
            for src, tgt in pairs:
                get_argos_translation_model(src, tgt)
            with _argos_lock:
                if _argos_models:
                    _argos_warmup_status = "warm"
                else:
                    _argos_warmup_status = "available"
            logger.info(f"Argos translation models pre-warmed. Status: {_argos_warmup_status}")
        except Exception as e:
            logger.debug(f"Argos model pre-warming worker exception: {e}")
            with _argos_lock:
                _argos_warmup_status = "warm" if _argos_models else "available"

    t = threading.Thread(target=_worker, daemon=True, name="argos-warmup")
    t.start()
    return t


class TranslationRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def setup(self):
        super().setup()
        # Enforce strict 5-second socket timeout to prevent orphan hangs
        self.connection.settimeout(5.0)

    def address_string(self):
        # Override to bypass reverse DNS lookups (<1ms vs multi-second delay)
        return self.client_address[0]

    def log_message(self, format_str, *args):
        # Suppress logging for health checks to keep logs clean
        if self.path and '/health' in self.path:
            return
        logger.info("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format_str % args))

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-ZID, X-Trace-ID')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.send_header('Connection', 'close')
        self.end_headers()

    def _send_json(self, status_code: int, data_obj: dict):
        body = json.dumps(data_obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status_code: int, code: str, message: str, provider: Optional[str] = None,
                         details: Optional[dict] = None, zid: Optional[str] = None, trace_id: Optional[str] = None):
        payload = {
            "status": "error",
            "zid": zid,
            "trace_id": trace_id,
            "code": code,
            "message": message,
            "provider": provider,
            "details": details or {}
        }
        self._send_json(status_code, payload)

    def do_GET(self):
        parsed_path = self.path.split('?')[0]
        if parsed_path in ('/health', '/api/v1/health'):
            providers = {
                "google": "available",
                "deepl": "available",
                "argos": get_argos_warmup_status()
            }
            rate_limiter = getattr(self.server, 'rate_limiter', _default_rate_limiter)
            cache = getattr(self.server, 'cache', _default_cache)
            auto_failover = getattr(self.server, 'auto_failover', False)
            resp = {
                "status": "healthy",
                "service": "translation_server",
                "port": self.server.server_address[1],
                "providers": providers,
                "rate_limiter": rate_limiter.stats(),
                "cache": cache.stats(),
                "auto_failover": auto_failover,
                "active_threads": threading.active_count()
            }
            self._send_json(200, resp)
            return

        self._send_error_json(404, "ERR_NOT_FOUND", f"Endpoint '{self.path}' not found")

    def do_POST(self):
        parsed_path = self.path.split('?')[0]

        if parsed_path in ('/shutdown', '/api/v1/shutdown'):
            self._send_json(200, {"status": "shutting_down", "message": "Server is shutting down..."})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return

        if parsed_path in ('/cache/clear', '/api/v1/cache/clear'):
            cache = getattr(self.server, 'cache', _default_cache)
            cache.clear()
            self._send_json(200, {"status": "success", "message": "Cache cleared"})
            return

        if parsed_path in ('/translate', '/api/v1/translate'):
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0:
                self._send_error_json(400, "ERR_INVALID_REQUEST", "Empty request body")
                return

            try:
                post_data = self.rfile.read(content_length)
                req = json.loads(post_data.decode('utf-8'))
            except Exception as e:
                self._send_error_json(400, "ERR_INVALID_JSON", f"Failed to parse JSON body: {e}")
                return

            zid = req.get('zid') or self.headers.get('X-ZID')
            trace_id = req.get('trace_id') or self.headers.get('X-Trace-ID')
            text = req.get('text')
            source = req.get('source')
            target = req.get('target')
            provider = (req.get('provider') or 'google').lower()
            chain = req.get('chain')
            strategy = req.get('strategy') or req.get('failover_strategy')
            deepl_api_key = req.get('deepl_api_key')
            req_failover = req.get('auto_failover')

            if text is None:
                self._send_error_json(400, "MISSING_FIELD", "Missing required field: 'text'", provider=provider, zid=zid, trace_id=trace_id)
                return
            if not source:
                self._send_error_json(400, "MISSING_FIELD", "Missing required field: 'source'", provider=provider, zid=zid, trace_id=trace_id)
                return
            if not target:
                self._send_error_json(400, "MISSING_FIELD", "Missing required field: 'target'", provider=provider, zid=zid, trace_id=trace_id)
                return

            if text == "":
                self._send_json(200, {
                    "status": "success",
                    "zid": zid,
                    "trace_id": trace_id,
                    "translated_text": "",
                    "provider": provider,
                    "provider_requested": provider,
                    "provider_resolved": provider,
                    "is_fallback": False,
                    "cached": False,
                    "duration_ms": 0.0
                })
                return

            cache = getattr(self.server, 'cache', _default_cache)
            rate_limiter = getattr(self.server, 'rate_limiter', _default_rate_limiter)
            auto_failover = req_failover if req_failover is not None else getattr(self.server, 'auto_failover', False)

            t0 = time.perf_counter()

            # 1. Fast path: check in-memory cache
            cached_text = cache.get(source, target, provider, text)
            if cached_text is not None:
                duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                logger.info(f"[{zid or 'NO_ZID'}] [{trace_id or 'NO_TRACE'}] cache_hit provider={provider} chars={len(text)} duration_ms={duration_ms}")
                self._send_json(200, {
                    "status": "success",
                    "zid": zid,
                    "trace_id": trace_id,
                    "translated_text": cached_text,
                    "provider": provider,
                    "provider_requested": provider,
                    "provider_resolved": provider,
                    "is_fallback": False,
                    "cached": True,
                    "duration_ms": duration_ms
                })
                return

            # 2. Execute translation with rate limiting, adaptive backoff, and failover
            try:
                translated_text, requested_provider, final_provider, is_fallback = self._translate_with_retry_and_failover(
                    text=text,
                    source=source,
                    target=target,
                    provider=provider,
                    deepl_api_key=deepl_api_key,
                    rate_limiter=rate_limiter,
                    auto_failover=auto_failover,
                    chain=chain,
                    strategy=strategy
                )
                duration_ms = round((time.perf_counter() - t0) * 1000, 2)

                # Store in cache under requested provider and final provider
                cache.set(source, target, requested_provider, text, translated_text)
                if is_fallback:
                    cache.set(source, target, final_provider, text, translated_text)

                logger.info(f"[{zid or 'NO_ZID'}] [{trace_id or 'NO_TRACE'}] provider={final_provider}{' (failover from ' + requested_provider + ')' if is_fallback else ''} chars={len(text)} duration_ms={duration_ms}")

                resp_payload = {
                    "status": "success",
                    "zid": zid,
                    "trace_id": trace_id,
                    "translated_text": translated_text,
                    "provider": final_provider,
                    "provider_requested": requested_provider,
                    "provider_resolved": final_provider,
                    "is_fallback": is_fallback,
                    "cached": False,
                    "duration_ms": duration_ms
                }
                if is_fallback:
                    resp_payload["failover_from"] = requested_provider
                    resp_payload["failed_over"] = True

                self._send_json(200, resp_payload)
            except TranslationServerException as tse:
                duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                logger.warning(f"[{zid or 'NO_ZID'}] [{trace_id or 'NO_TRACE'}] provider={provider} failed: {tse.code} ({tse.message}) in {duration_ms}ms")
                self._send_error_json(
                    status_code=tse.status_code,
                    code=tse.code,
                    message=tse.message,
                    provider=provider,
                    details=tse.details,
                    zid=zid,
                    trace_id=trace_id
                )
            except Exception as ex:
                duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                logger.error(f"[{zid or 'NO_ZID'}] [{trace_id or 'NO_TRACE'}] provider={provider} unhandled error: {ex} in {duration_ms}ms")
                self._send_error_json(
                    status_code=500,
                    code="ERR_TRANSLATION_FAILED",
                    message=f"Translation failed: {ex}",
                    provider=provider,
                    details={"raw_error": str(ex)},
                    zid=zid,
                    trace_id=trace_id
                )
            return

        self._send_error_json(404, "ERR_NOT_FOUND", f"Endpoint '{self.path}' not found")

    def _translate_with_retry_and_failover(self, text: str, source: str, target: str, provider: str,
                                          deepl_api_key: Optional[str], rate_limiter: ProviderRateLimiter,
                                          auto_failover: bool,
                                          chain: Optional[Any] = None,
                                          strategy: Optional[str] = None) -> Tuple[str, str, str, bool]:
        if chain:
            if isinstance(chain, list):
                providers_to_try = [p.strip().lower() for p in chain if isinstance(p, str) and p.strip()]
            elif isinstance(chain, str):
                providers_to_try = [p.strip().lower() for p in chain.split(',') if p.strip()]
            else:
                providers_to_try = []
        elif provider and ',' in provider:
            providers_to_try = [p.strip().lower() for p in provider.split(',') if p.strip()]
        else:
            primary = (provider or 'google').strip().lower()
            providers_to_try = [primary]

        if not providers_to_try:
            providers_to_try = ['google']

        requested_provider = providers_to_try[0]

        valid_providers = ('google', 'deepl', 'argos', 'mock')
        for p in providers_to_try:
            if p not in valid_providers:
                raise TranslationServerException(
                    status_code=400,
                    code="ERR_UNSUPPORTED_PROVIDER",
                    message=f"Unsupported translation provider: '{p}'"
                )

        eff_strategy = (strategy or "").strip().lower()
        if not eff_strategy:
            eff_strategy = 'chain' if auto_failover else 'strict' if (len(providers_to_try) == 1 and not auto_failover) else 'chain'

        if eff_strategy == 'strict':
            providers_to_try = [providers_to_try[0]]
        elif eff_strategy == 'chain' or auto_failover:
            if len(providers_to_try) == 1 and auto_failover:
                primary = providers_to_try[0]
                if primary == 'google':
                    has_deepl = bool(deepl_api_key or os.environ.get("DEEPL_API_KEY"))
                    if has_deepl:
                        providers_to_try.append('deepl')
                    providers_to_try.append('argos')
                elif primary == 'deepl':
                    providers_to_try.append('google')
                    providers_to_try.append('argos')

        last_exception = None
        for current_provider in providers_to_try:
            # If auto_failover or chain is enabled, perform retries with backoff on Google rate limit/transient
            max_attempts = 3 if ((eff_strategy == 'chain' or auto_failover) and current_provider == 'google') else 1
            for attempt in range(max_attempts):
                try:
                    with rate_limiter.limit(current_provider):
                        translated = self._execute_translation(text, source, target, current_provider, deepl_api_key)
                        is_fallback = (current_provider != requested_provider)
                        return translated, requested_provider, current_provider, is_fallback
                except TranslationServerException as tse:
                    last_exception = tse
                    # Auth or bad request errors should not failover or retry
                    if tse.code in ("ERR_DEEPL_AUTH", "ERR_UNSUPPORTED_PROVIDER", "MISSING_FIELD"):
                        raise tse
                    if current_provider == 'google' and tse.code in ("ERR_GOOGLE_RATE_LIMIT", "ERR_NETWORK_UNREACHABLE") and attempt < max_attempts - 1:
                        backoff_delay = 0.5 * (2 ** attempt)
                        logger.warning(f"Google translate encountered {tse.code}, retrying in {backoff_delay}s (attempt {attempt + 1}/{max_attempts})...")
                        time.sleep(backoff_delay)
                        continue
                    break
                except Exception as e:
                    last_exception = e
                    break

        if last_exception:
            if isinstance(last_exception, TranslationServerException):
                raise last_exception
            raise TranslationServerException(
                status_code=500,
                code="ERR_TRANSLATION_FAILED",
                message=f"Translation failed: {last_exception}",
                details={"raw_error": str(last_exception)}
            )

        raise TranslationServerException(
            status_code=500,
            code="ERR_TRANSLATION_FAILED",
            message="Translation failed across all candidate providers"
        )

    def _execute_translation(self, text: str, source: str, target: str, provider: str, deepl_api_key: Optional[str] = None) -> str:
        session = get_global_session()

        if provider == 'google':
            return self._translate_google(text, source, target, session)
        elif provider == 'deepl':
            return self._translate_deepl(text, source, target, deepl_api_key, session)
        elif provider == 'argos':
            return self._translate_argos(text, source, target)
        elif provider == 'mock':
            time.sleep(0.001)
            return f"[MOCK] {text}"
        else:
            raise TranslationServerException(
                status_code=400,
                code="ERR_UNSUPPORTED_PROVIDER",
                message=f"Unsupported translation provider: '{provider}'"
            )

    def _translate_google(self, text: str, source: str, target: str, session: requests.Session) -> str:
        try:
            from deep_translator import GoogleTranslator
            try:
                translator = GoogleTranslator(source=source, target=target, session=session, timeout=10.0)
            except TypeError:
                translator = GoogleTranslator(source=source, target=target)
            return translator.translate(text)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "too many requests" in err_str.lower() or "rate limit" in err_str.lower():
                raise TranslationServerException(
                    status_code=429,
                    code="ERR_GOOGLE_RATE_LIMIT",
                    message="Google Translate rate limit exceeded",
                    details={"http_code": 429, "raw_error": err_str}
                )
            elif any(term in err_str.lower() for term in ["timeout", "timed out", "connection", "unreachable", "name resolution", "dns"]):
                raise TranslationServerException(
                    status_code=503,
                    code="ERR_NETWORK_UNREACHABLE",
                    message=f"Google Translate network unreachable: {err_str}",
                    details={"raw_error": err_str}
                )
            else:
                raise TranslationServerException(
                    status_code=500,
                    code="ERR_TRANSLATION_FAILED",
                    message=f"Google translation failed: {err_str}",
                    details={"raw_error": err_str}
                )

    def _translate_deepl(self, text: str, source: str, target: str, api_key: Optional[str], session: requests.Session) -> str:
        key = api_key or os.environ.get("DEEPL_API_KEY")
        if not key:
            raise TranslationServerException(
                status_code=403,
                code="ERR_DEEPL_AUTH",
                message="DeepL API key not provided or configured",
                details={}
            )
        try:
            from deep_translator import DeeplTranslator
            try:
                translator = DeeplTranslator(api_key=key, source=source, target=target, session=session, timeout=10.0)
            except TypeError:
                translator = DeeplTranslator(api_key=key, source=source, target=target)
            return translator.translate(text)
        except Exception as e:
            err_str = str(e)
            if "456" in err_str or "quota" in err_str.lower():
                raise TranslationServerException(
                    status_code=429,
                    code="ERR_DEEPL_QUOTA",
                    message="DeepL API translation quota exceeded",
                    details={"http_code": 456, "raw_error": err_str}
                )
            elif "403" in err_str or "forbidden" in err_str.lower() or "authorization" in err_str.lower() or "invalid key" in err_str.lower():
                raise TranslationServerException(
                    status_code=403,
                    code="ERR_DEEPL_AUTH",
                    message="DeepL authentication failed / invalid API key",
                    details={"http_code": 403, "raw_error": err_str}
                )
            elif any(term in err_str.lower() for term in ["timeout", "timed out", "connection", "unreachable", "name resolution", "dns"]):
                raise TranslationServerException(
                    status_code=503,
                    code="ERR_NETWORK_UNREACHABLE",
                    message=f"DeepL network unreachable: {err_str}",
                    details={"raw_error": err_str}
                )
            else:
                raise TranslationServerException(
                    status_code=500,
                    code="ERR_TRANSLATION_FAILED",
                    message=f"DeepL translation failed: {err_str}",
                    details={"raw_error": err_str}
                )

    def _translate_argos(self, text: str, source: str, target: str) -> str:
        # 1. Fast in-memory cached model execution
        try:
            model = get_argos_translation_model(source, target)
            if model is not None:
                return model.translate(text)
        except Exception as e:
            logger.warning(f"In-memory Argos translation failed for {source}->{target}: {e}")

        # 2. Try direct argostranslate.translate
        try:
            import argostranslate.translate
            return argostranslate.translate.translate(text, source, target)
        except Exception:
            pass

        # 3. Try invoking argos CLI in neighboring workspace if present
        candidate_exes = [
            Path(__file__).resolve().parent.parent / "20241121100211-argotranslate" / "venv" / "Scripts" / "argos-translate.exe",
            Path(__file__).resolve().parent.parent / "20241121100211-argotranslate" / "venv" / "Scripts" / "argos-translate",
        ]
        exe_path = None
        for cand in candidate_exes:
            if cand.exists():
                exe_path = cand
                break

        if exe_path:
            if sys.platform == "win32" and not exe_path.name.lower().endswith(".exe"):
                python_exe = exe_path.parent / "python.exe"
                if not python_exe.exists():
                    python_exe = Path(sys.executable)
                cmd = [str(python_exe), str(exe_path), "-f", source, "-t", target]
            else:
                cmd = [str(exe_path), "-f", source, "-t", target]
            try:
                res = subprocess.run(cmd, input=text, capture_output=True, text=True, encoding='utf-8', timeout=60)
                if res.returncode == 0:
                    return res.stdout.strip()
                raise TranslationServerException(
                    status_code=500,
                    code="ERR_TRANSLATION_FAILED",
                    message=f"Argos translation failed (code {res.returncode}): {res.stderr.strip()}",
                    details={"stderr": res.stderr.strip(), "returncode": res.returncode}
                )
            except subprocess.TimeoutExpired:
                raise TranslationServerException(
                    status_code=504,
                    code="ERR_TIMEOUT",
                    message="Argos translation timed out",
                    details={"timeout": 60}
                )
            except Exception as e:
                raise TranslationServerException(
                    status_code=500,
                    code="ERR_TRANSLATION_FAILED",
                    message=f"Argos execution error: {e}",
                    details={"raw_error": str(e)}
                )

        raise TranslationServerException(
            status_code=500,
            code="ERR_DEPENDENCY_MISSING",
            message="Argos translate package/executable not found",
            details={}
        )


class TranslationServerException(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


def run_server(host: str = "127.0.0.1", port: int = 8082,
               google_delay: float = 0.35, google_concurrency: int = 1,
               deepl_concurrency: int = 5, argos_concurrency: int = 2,
               cache_size: int = 10000, enable_cache: bool = True,
               auto_failover: bool = False, warmup_argos: bool = True):
    config = load_config()
    setup_local_fork(config)

    server_address = (host, port)
    server = TranslationHTTPServer(
        server_address,
        TranslationRequestHandler,
        config=config,
        google_delay=google_delay,
        google_concurrency=google_concurrency,
        deepl_concurrency=deepl_concurrency,
        argos_concurrency=argos_concurrency,
        cache_size=cache_size,
        enable_cache=enable_cache,
        auto_failover=auto_failover
    )
    if warmup_argos:
        warmup_argos_models_async()

    logger.info(f"Starting Translation HTTP Server on http://{host}:{port} (google_delay={google_delay}s, google_concurrency={google_concurrency}, cache_size={cache_size}, auto_failover={auto_failover})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down server...")
    finally:
        server.server_close()
        logger.info("Server terminated.")


def main():
    parser = argparse.ArgumentParser(description="Translation HTTP Microservice Server")
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind server (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8082, help='Port to bind server (default: 8082)')
    parser.add_argument('--google-delay', type=float, default=0.35, help='Pacing delay between consecutive Google requests in seconds (default: 0.35)')
    parser.add_argument('--google-concurrency', type=int, default=1, help='Max concurrent Google requests (default: 1)')
    parser.add_argument('--deepl-concurrency', type=int, default=5, help='Max concurrent DeepL requests (default: 5)')
    parser.add_argument('--argos-concurrency', type=int, default=2, help='Max concurrent Argos requests (default: 2)')
    parser.add_argument('--cache-size', type=int, default=10000, help='Max in-memory LRU cache entries (default: 10000)')
    parser.add_argument('--no-cache', dest='enable_cache', action='store_false', help='Disable translation caching')
    parser.add_argument('--auto-failover', dest='auto_failover', action='store_true', help='Enable automatic provider failover')
    parser.set_defaults(enable_cache=True, auto_failover=False)
    args = parser.parse_args()

    run_server(
        host=args.host,
        port=args.port,
        google_delay=args.google_delay,
        google_concurrency=args.google_concurrency,
        deepl_concurrency=args.deepl_concurrency,
        argos_concurrency=args.argos_concurrency,
        cache_size=args.cache_size,
        enable_cache=args.enable_cache,
        auto_failover=args.auto_failover
    )


if __name__ == "__main__":
    main()

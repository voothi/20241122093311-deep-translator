import json
import time
import threading
import urllib.request
import urllib.error
import pytest
from unittest.mock import patch, MagicMock

import translate_server
from translate_server import (
    TranslationHTTPServer,
    TranslationRequestHandler,
    ProviderRateLimiter,
    TranslationCache,
    get_global_session
)


@pytest.fixture(scope="module")
def server_url():
    # Start test server on an ephemeral port
    server = TranslationHTTPServer(("127.0.0.1", 0), TranslationRequestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    server.shutdown()
    server.server_close()


@pytest.fixture(autouse=True)
def clear_server_cache(server_url):
    # Clear cache before each test to ensure test isolation
    req = urllib.request.Request(
        f"{server_url}/cache/clear",
        data=b"{}",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200


def test_health_endpoint(server_url):
    req = urllib.request.Request(f"{server_url}/health")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode('utf-8'))
        assert data["status"] == "healthy"
        assert data["service"] == "translation_server"
        assert "google" in data["providers"]
        assert "deepl" in data["providers"]
        assert "argos" in data["providers"]
        assert "rate_limiter" in data
        assert "cache" in data
        assert "auto_failover" in data


def test_translate_mock_provider(server_url):
    payload = {
        "text": "Hallo Welt",
        "source": "de",
        "target": "en",
        "provider": "mock",
        "zid": "20260819020400",
        "trace_id": "trace-test-123"
    }
    req = urllib.request.Request(
        f"{server_url}/translate",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode('utf-8'))
        assert data["status"] == "success"
        assert data["translated_text"] == "[MOCK] Hallo Welt"
        assert data["zid"] == "20260819020400"
        assert data["trace_id"] == "trace-test-123"
        assert data["provider"] == "mock"
        assert data["cached"] is False
        assert "duration_ms" in data


def test_translate_empty_text(server_url):
    payload = {
        "text": "",
        "source": "de",
        "target": "en",
        "provider": "mock",
        "zid": "20260819020400",
        "trace_id": "trace-empty"
    }
    req = urllib.request.Request(
        f"{server_url}/translate",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode('utf-8'))
        assert data["status"] == "success"
        assert data["translated_text"] == ""


def test_translate_missing_field(server_url):
    payload = {
        "text": "Hello",
        "source": "en"
        # missing target
    }
    req = urllib.request.Request(
        f"{server_url}/translate",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 400
    err = json.loads(exc_info.value.read().decode('utf-8'))
    assert err["status"] == "error"
    assert err["code"] == "MISSING_FIELD"


def test_translate_unsupported_provider(server_url):
    payload = {
        "text": "Hello",
        "source": "en",
        "target": "de",
        "provider": "unknown_ai"
    }
    req = urllib.request.Request(
        f"{server_url}/translate",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 400
    err = json.loads(exc_info.value.read().decode('utf-8'))
    assert err["status"] == "error"
    assert err["code"] == "ERR_UNSUPPORTED_PROVIDER"


def test_translate_deepl_missing_key(server_url):
    payload = {
        "text": "Hello",
        "source": "en",
        "target": "de",
        "provider": "deepl"
    }
    req = urllib.request.Request(
        f"{server_url}/translate",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 403
    err = json.loads(exc_info.value.read().decode('utf-8'))
    assert err["status"] == "error"
    assert err["code"] == "ERR_DEEPL_AUTH"


def test_translate_google_success(server_url):
    with patch("deep_translator.GoogleTranslator.translate", return_value="The tree is tall."):
        payload = {
            "text": "Der Baum ist hoch.",
            "source": "de",
            "target": "en",
            "provider": "google",
            "zid": "20260819002900",
            "trace_id": "20260819002900:translate:sentence_0"
        }
        req = urllib.request.Request(
            f"{server_url}/translate",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode('utf-8'))
            assert data["status"] == "success"
            assert data["translated_text"] == "The tree is tall."
            assert data["provider"] == "google"
            assert data["cached"] is False
            assert data["zid"] == "20260819002900"


def test_translate_deepl_quota_exceeded_mapping(server_url):
    with patch("deep_translator.DeeplTranslator.translate", side_effect=Exception("DeepL API HTTP 456 Quota Exceeded")):
        payload = {
            "text": "Der Baum ist hoch.",
            "source": "de",
            "target": "en",
            "provider": "deepl",
            "deepl_api_key": "dummy_key",
            "trace_id": "trace-quota-test"
        }
        req = urllib.request.Request(
            f"{server_url}/translate",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)
        assert exc_info.value.code == 429
        err = json.loads(exc_info.value.read().decode('utf-8'))
        assert err["status"] == "error"
        assert err["code"] == "ERR_DEEPL_QUOTA"
        assert err["trace_id"] == "trace-quota-test"


def test_translate_google_rate_limit_mapping(server_url):
    with patch("deep_translator.GoogleTranslator.translate", side_effect=Exception("HTTP 429 Too Many Requests")):
        payload = {
            "text": "Der Baum ist hoch.",
            "source": "de",
            "target": "en",
            "provider": "google"
        }
        req = urllib.request.Request(
            f"{server_url}/translate",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)
        assert exc_info.value.code == 429
        err = json.loads(exc_info.value.read().decode('utf-8'))
        assert err["status"] == "error"
        assert err["code"] == "ERR_GOOGLE_RATE_LIMIT"


def test_translate_network_unreachable_mapping(server_url):
    with patch("deep_translator.GoogleTranslator.translate", side_effect=Exception("Connection timed out")):
        payload = {
            "text": "Der Baum ist hoch.",
            "source": "de",
            "target": "en",
            "provider": "google"
        }
        req = urllib.request.Request(
            f"{server_url}/translate",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)
        assert exc_info.value.code == 503
        err = json.loads(exc_info.value.read().decode('utf-8'))
        assert err["status"] == "error"
        assert err["code"] == "ERR_NETWORK_UNREACHABLE"


def test_persistent_session_singleton():
    session1 = get_global_session()
    session2 = get_global_session()
    assert session1 is session2
    assert "https://" in session1.adapters


def test_lru_cache_hit_and_miss(server_url):
    with patch("deep_translator.GoogleTranslator.translate", return_value="The blue sky."):
        payload = {
            "text": "Der blaue Himmel.",
            "source": "de",
            "target": "en",
            "provider": "google"
        }
        req = urllib.request.Request(
            f"{server_url}/translate",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        # 1st call: Cache Miss
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            assert data["status"] == "success"
            assert data["translated_text"] == "The blue sky."
            assert data["cached"] is False

    # 2nd call: Cache Hit (even if GoogleTranslator is NOT mocked or fails, cache returns result)
    req2 = urllib.request.Request(
        f"{server_url}/translate",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req2) as resp2:
        data2 = json.loads(resp2.read().decode('utf-8'))
        assert data2["status"] == "success"
        assert data2["translated_text"] == "The blue sky."
        assert data2["cached"] is True


def test_provider_rate_limiter_pacing_delay():
    limiter = ProviderRateLimiter(google_concurrency=1, google_delay=0.15)
    t0 = time.perf_counter()
    with limiter.limit('google'):
        pass
    with limiter.limit('google'):
        pass
    elapsed = time.perf_counter() - t0
    assert elapsed >= 0.14


def test_auto_failover_google_to_argos(server_url):
    with patch("deep_translator.GoogleTranslator.translate", side_effect=Exception("HTTP 429 Too Many Requests")):
        with patch.object(TranslationRequestHandler, "_translate_argos", return_value="The house."):
            payload = {
                "text": "Das Haus.",
                "source": "de",
                "target": "en",
                "provider": "google",
                "auto_failover": True
            }
            req = urllib.request.Request(
                f"{server_url}/translate",
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as resp:
                assert resp.status == 200
                data = json.loads(resp.read().decode('utf-8'))
                assert data["status"] == "success"
                assert data["translated_text"] == "The house."
                assert data["provider"] == "argos"
                assert data["failover_from"] == "google"
                assert data["failed_over"] is True


def test_auto_failover_google_to_deepl(server_url):
    with patch("deep_translator.GoogleTranslator.translate", side_effect=Exception("HTTP 429 Too Many Requests")):
        with patch("deep_translator.DeeplTranslator.translate", return_value="The car."):
            payload = {
                "text": "Das Auto.",
                "source": "de",
                "target": "en",
                "provider": "google",
                "deepl_api_key": "valid_mock_key",
                "auto_failover": True
            }
            req = urllib.request.Request(
                f"{server_url}/translate",
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as resp:
                assert resp.status == 200
                data = json.loads(resp.read().decode('utf-8'))
                assert data["status"] == "success"
                assert data["translated_text"] == "The car."
                assert data["provider"] == "deepl"
                assert data["failover_from"] == "google"
                assert data["failed_over"] is True


def test_argos_warmup_and_health_reporting():
    mock_model = MagicMock()
    mock_model.translate.side_effect = lambda t: f"Warm: {t}"

    with patch.dict(translate_server._argos_models, {}, clear=True):
        with patch("translate_server.get_argos_translation_model", return_value=mock_model):
            t = translate_server.warmup_argos_models_async([("en", "de")])
            t.join(timeout=2.0)
            translate_server._argos_models[("en", "de")] = mock_model
            assert translate_server.get_argos_warmup_status() == "warm"

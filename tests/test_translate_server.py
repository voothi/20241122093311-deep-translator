import json
import time
import threading
import urllib.request
import urllib.error
import pytest
from unittest.mock import patch, MagicMock

import translate_server
from translate_server import TranslationHTTPServer, TranslationRequestHandler, get_global_session


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

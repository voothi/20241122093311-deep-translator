import sys
import runpy
import pytest
import json
from unittest.mock import patch, MagicMock, mock_open

@patch("deep_translator.GoogleTranslator")
def test_wrapper_config_defaults(mock_translator_cls):
    test_argv = [
        "translate_google.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "hola"
    mock_translator_cls.return_value = mock_instance

    with patch("os.path.exists", return_value=False):
        with patch.object(sys, "argv", test_argv):
            runpy.run_path("translate_google.py", run_name="__main__")

    kwargs = mock_translator_cls.call_args[1]
    assert kwargs["timeout"] == 5.0
    assert kwargs["max_retries"] == 2
    assert kwargs["retry_backoff"] == 1.0
    assert kwargs["max_total_time"] is None

@patch("deep_translator.GoogleTranslator")
def test_wrapper_config_precedence(mock_translator_cls):
    test_argv = [
        "translate_google.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es",
        "--timeout", "8"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "hola"
    mock_translator_cls.return_value = mock_instance

    config_data = {
        "netTimeout": 20,
        "maxRetries": 5,
        "retryBackoff": 3.0,
        "maxTotalTime": 120
    }
    
    import io
    real_open = open
    def mock_open_side_effect(file, *args, **kwargs):
        if "config.json" in str(file):
            return io.StringIO(json.dumps(config_data))
        return real_open(file, *args, **kwargs)
    
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", side_effect=mock_open_side_effect):
            with patch.object(sys, "argv", test_argv):
                runpy.run_path("translate_google.py", run_name="__main__")

    kwargs = mock_translator_cls.call_args[1]
    assert kwargs["timeout"] == 8.0
    assert kwargs["max_retries"] == 5
    assert kwargs["retry_backoff"] == 3.0
    assert kwargs["max_total_time"] == 120.0

def test_wrapper_config_bad_values():
    test_argv = [
        "translate_google.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es",
        "--timeout", "-10"
    ]
    with patch.object(sys, "argv", test_argv):
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path("translate_google.py", run_name="__main__")
        assert excinfo.value.code == 1

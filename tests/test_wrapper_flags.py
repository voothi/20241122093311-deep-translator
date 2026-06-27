import sys
import runpy
import pytest
from unittest.mock import patch, MagicMock

@patch("deep_translator.GoogleTranslator")
def test_google_flags(mock_translator_cls):
    test_argv = [
        "translate_google.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es",
        "--use-local-fork",
        "--timeout", "12",
        "--retries", "4",
        "--retry-backoff", "2.5",
        "--max-total-time", "60",
        "--quiet",
        "--plain"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "hola"
    mock_translator_cls.return_value = mock_instance

    with patch.object(sys, "argv", test_argv):
        runpy.run_path("translate_google.py", run_name="__main__")

    mock_translator_cls.assert_called_once()
    kwargs = mock_translator_cls.call_args[1]
    assert kwargs["timeout"] == 12.0
    assert kwargs["max_retries"] == 4
    assert kwargs["retry_backoff"] == 2.5
    assert kwargs["max_total_time"] == 60.0

@patch("deep_translator.DeeplTranslator")
def test_deepl_flags(mock_translator_cls):
    test_argv = [
        "translate_deepl.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es",
        "--deepl-api-key", "mykey",
        "--use-local-fork",
        "--timeout", "15",
        "--retries", "3",
        "--retry-backoff", "2.0",
        "--max-total-time", "30",
        "--quiet",
        "--plain"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "hola"
    mock_translator_cls.return_value = mock_instance

    with patch.object(sys, "argv", test_argv):
        runpy.run_path("translate_deepl.py", run_name="__main__")

    mock_translator_cls.assert_called_once()
    kwargs = mock_translator_cls.call_args[1]
    assert kwargs["timeout"] == 15.0
    assert kwargs["max_retries"] == 3
    assert kwargs["retry_backoff"] == 2.0
    assert kwargs["max_total_time"] == 30.0

@patch("deep_translator.MyMemoryTranslator")
def test_mymemory_flags(mock_translator_cls):
    test_argv = [
        "translate_mymemory.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es",
        "--use-local-fork",
        "--timeout", "8",
        "--retries", "1",
        "--retry-backoff", "1.5",
        "--max-total-time", "10",
        "--quiet",
        "--plain"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "hola"
    mock_translator_cls.return_value = mock_instance

    with patch.object(sys, "argv", test_argv):
        runpy.run_path("translate_mymemory.py", run_name="__main__")

    mock_translator_cls.assert_called_once()
    kwargs = mock_translator_cls.call_args[1]
    assert kwargs["timeout"] == 8.0
    assert kwargs["max_retries"] == 1
    assert kwargs["retry_backoff"] == 1.5
    assert kwargs["max_total_time"] == 10.0

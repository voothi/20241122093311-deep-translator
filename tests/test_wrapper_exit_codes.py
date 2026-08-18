import sys
import runpy
import pytest
from unittest.mock import patch, MagicMock

@patch("deep_translator.GoogleTranslator")
def test_exit_0_success(mock_translator_cls):
    test_argv = [
        "translate_google.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "hola"
    mock_translator_cls.return_value = mock_instance

    with patch.object(sys, "argv", test_argv):
        res = runpy.run_path("translate_google.py", run_name="__main__")
        assert res is not None

@patch("deep_translator.GoogleTranslator")
def test_exit_1_network_exhaustion(mock_translator_cls):
    test_argv = [
        "translate_google.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.side_effect = Exception("Request failed after 3 attempts")
    mock_translator_cls.return_value = mock_instance

    with patch.object(sys, "argv", test_argv):
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path("translate_google.py", run_name="__main__")
        assert excinfo.value.code == 1

@patch("deep_translator.GoogleTranslator")
def test_exit_130_keyboard_interrupt(mock_translator_cls):
    test_argv = [
        "translate_google.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.side_effect = KeyboardInterrupt()
    mock_translator_cls.return_value = mock_instance

    with patch.object(sys, "argv", test_argv):
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path("translate_google.py", run_name="__main__")
        assert excinfo.value.code == 130

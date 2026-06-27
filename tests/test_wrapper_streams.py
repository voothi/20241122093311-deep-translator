import sys
import runpy
import pytest
from unittest.mock import patch, MagicMock

@patch("deep_translator.GoogleTranslator")
@patch("sys.stdout")
@patch("sys.stderr")
def test_streams_success_with_retries(mock_stderr, mock_stdout, mock_translator_cls):
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
        runpy.run_path("translate_google.py", run_name="__main__")

    kwargs = mock_translator_cls.call_args[1]
    on_retry = kwargs["on_retry"]
    on_retry(1, 1.5, "Timeout")
    
    mock_stderr.write.assert_any_call("Attempt 1 failed: Timeout. Retrying in 1.50s...\n")

@patch("deep_translator.GoogleTranslator")
def test_quiet_suppresses_stderr(mock_translator_cls):
    test_argv = [
        "translate_google.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es",
        "--quiet"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "hola"
    mock_translator_cls.return_value = mock_instance

    with patch("sys.stderr") as mock_stderr:
        with patch.object(sys, "argv", test_argv):
            runpy.run_path("translate_google.py", run_name="__main__")
        
        on_retry = mock_translator_cls.call_args[1]["on_retry"]
        on_retry(1, 1.5, "Timeout")
        mock_stderr.write.assert_not_called()

@patch("deep_translator.GoogleTranslator")
def test_plain_on_failure(mock_translator_cls):
    test_argv = [
        "translate_google.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es",
        "--plain"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.side_effect = Exception("Outage")
    mock_translator_cls.return_value = mock_instance

    with patch("sys.stdout") as mock_stdout:
        with patch("sys.stderr") as mock_stderr:
            with patch.object(sys, "argv", test_argv):
                with pytest.raises(SystemExit):
                    runpy.run_path("translate_google.py", run_name="__main__")
            
            mock_stdout.write.assert_any_call("Error: Outage\n")
            mock_stderr.write.assert_any_call("Error: Outage\n")

@patch("deep_translator.GoogleTranslator")
def test_default_failure_keeps_stdout_empty(mock_translator_cls):
    test_argv = [
        "translate_google.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.side_effect = Exception("Outage")
    mock_translator_cls.return_value = mock_instance

    with patch("sys.stdout") as mock_stdout:
        with patch("sys.stderr") as mock_stderr:
            with patch.object(sys, "argv", test_argv):
                with pytest.raises(SystemExit):
                    runpy.run_path("translate_google.py", run_name="__main__")
            
            # stdout must not have "Error: Outage"
            for call in mock_stdout.write.call_args_list:
                assert "Error" not in call[0][0]
            mock_stderr.write.assert_any_call("Error: Outage\n")

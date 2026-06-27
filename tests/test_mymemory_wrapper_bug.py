import sys
import runpy
import pytest
from unittest.mock import patch, MagicMock

@patch("deep_translator.MyMemoryTranslator")
def test_mymemory_no_name_error_on_failure(mock_translator_cls):
    test_argv = [
        "translate_mymemory.py",
        "--text", "hello",
        "--source", "en",
        "--target", "es"
    ]
    mock_instance = MagicMock()
    mock_instance.translate.side_effect = Exception("Translation Outage")
    mock_translator_cls.return_value = mock_instance

    with patch("sys.stderr") as mock_stderr:
        with patch.object(sys, "argv", test_argv):
            with pytest.raises(SystemExit) as excinfo:
                runpy.run_path("translate_mymemory.py", run_name="__main__")
            assert excinfo.value.code == 2
        
        mock_stderr.write.assert_any_call("Error: Translation Outage\n")

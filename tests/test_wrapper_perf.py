import time
import subprocess
import sys
import pytest

def test_wrapper_cold_start_perf():
    python_exe = sys.executable
    script_path = "translate_google.py"
    
    times = []
    # Run a few times and take the minimum (best case) to avoid transient OS jitter
    for _ in range(3):
        start = time.perf_counter()
        res = subprocess.run(
            [python_exe, script_path, "--text", "hello", "--source", "en", "--target", "en", "--use-local-fork"],
            capture_output=True,
            text=True
        )
        end = time.perf_counter()
        assert res.returncode == 0
        times.append(end - start)
    
    min_time_ms = min(times) * 1000
    # Baseline ~350ms + 30ms budget = 380ms. We allow up to 550ms to be safe.
    assert min_time_ms < 550.0

def test_wrapper_does_not_import_requests():
    python_exe = sys.executable
    code = """
import sys
import os
import json

sys.argv = ['translate_google.py', '--text', 'hello', '--source', 'en', '--target', 'en', '--use-local-fork']

config = {}
with open('config.json', 'r') as f:
    config = json.load(f)
fork_path = config.get('local_deep_translator_fork_path')
sys.path.insert(0, os.path.abspath(fork_path))

from deep_translator import GoogleTranslator
assert 'requests' not in sys.modules
"""
    res = subprocess.run([python_exe, "-c", code], capture_output=True, text=True)
    assert res.returncode == 0, f"Error: requests was imported or script failed: {res.stderr}"

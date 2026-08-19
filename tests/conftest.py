import os
import sys
import json

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Automatically add the local fork path to sys.path before tests are loaded
config_path = os.path.abspath(os.path.join(root_dir, "config.json"))
if os.path.exists(config_path):
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        fork_path = config.get("local_deep_translator_fork_path")
        if fork_path:
            abs_fork_path = os.path.abspath(os.path.join(root_dir, fork_path))
            if abs_fork_path not in sys.path:
                sys.path.insert(0, abs_fork_path)
    except Exception:
        pass

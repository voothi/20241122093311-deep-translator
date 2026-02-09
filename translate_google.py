import argparse
import sys
import os
import json

parser = argparse.ArgumentParser(description="Translate text from one language to another.")
parser.add_argument('--text', type=str, required=True, help='Text to translate')
parser.add_argument('--source', type=str, required=True, help='Source language code (e.g., en, fr)')
parser.add_argument('--target', type=str, required=True, help='Target language code (e.g., en, fr)')
parser.add_argument('--use-local-fork', action='store_true', help='Use local fork from config.json')

args = parser.parse_args()

if args.use_local_fork:
    # Check config for local fork usage
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                if config.get('use_local_deep_translator_fork', False):
                    fork_path = config.get('local_deep_translator_fork_path', '20260209094544-deep-translator')
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), fork_path))
        except Exception:
            pass

from deep_translator import GoogleTranslator

translator = GoogleTranslator(source=args.source, target=args.target)
result = translator.translate(args.text)
print(result)

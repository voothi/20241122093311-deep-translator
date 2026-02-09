import argparse
import sys
import os
import json

parser = argparse.ArgumentParser(description="Translate text using DeepL.")
parser.add_argument('--text', type=str, required=True, help='Text to translate')
parser.add_argument('--source', type=str, required=True, help='Source language code (e.g., en, fr)')
parser.add_argument('--target', type=str, required=True, help='Target language code (e.g., en, fr)')
parser.add_argument('--deepl-api-key', type=str, required=True, help='Your DeepL API key')
parser.add_argument('--use-local-fork', action='store_true', help='Use local fork from config.json')

args = parser.parse_args()

if args.use_local_fork:
    # Check config for local fork usage
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                fork_path = config.get('local_deep_translator_fork_path')
                if fork_path:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), fork_path))
        except Exception:
            pass

from deep_translator import DeeplTranslator

try:
    translator = DeeplTranslator(api_key=args.deepl_api_key, source=args.source, target=args.target)
    result = translator.translate(args.text)
    print(result)
except Exception as e:
    print(f"Error: {e}")
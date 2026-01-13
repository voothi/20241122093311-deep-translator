import argparse
from deep_translator import DeeplTranslator

parser = argparse.ArgumentParser(description="Translate text using DeepL.")
parser.add_argument('--text', type=str, required=True, help='Text to translate')
parser.add_argument('--source', type=str, required=True, help='Source language code (e.g., en, fr)')
parser.add_argument('--target', type=str, required=True, help='Target language code (e.g., en, fr)')
parser.add_argument('--deepl-api-key', type=str, required=True, help='Your DeepL API key')

args = parser.parse_args()

translator = DeeplTranslator(api_key=args.deepl_api_key, source=args.source, target=args.target)
result = translator.translate(args.text)
print(result)
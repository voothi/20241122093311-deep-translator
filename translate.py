import argparse
from deep_translator import GoogleTranslator

parser = argparse.ArgumentParser(description="Translate text from one language to another.")
parser.add_argument('--text', type=str, required=True, help='Text to translate')
parser.add_argument('--source', type=str, required=True, help='Source language code (e.g., en, fr)')
parser.add_argument('--target', type=str, required=True, help='Target language code (e.g., en, fr)')

args = parser.parse_args()

translator = GoogleTranslator(source=args.source, target=args.target)
result = translator.translate(args.text)
print(result)

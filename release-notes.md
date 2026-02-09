# Release Notes

## v1.0.1 (2026-02-09)
**Fix DeepL Authorization Error**

- **Fix**: Patched `deep-translator` library (`deepl.py`) to support new DeepL API requirements (POST requests and header-based authentication).
- **Feature**: Added `--use-local-fork` flag and `config.json` support to allow testing with a local copy of the library.
- **RFC**: Created RFC `20260209093752-update-deepl-translator.md` detailing the fix.

## v1.0.0 (2026-01-13)
**Initial Documentation Release**

- **Documentation**: Added comprehensive `README.md` with:
  - Installation instructions for the virtual environment.
  - Verification of Python 3.11.1 and deep-translator 1.11.4.
  - Description of translation scripts for Google, DeepL, and MyMemory.
  - GoldenDict-ng integration configuration examples (with API keys removed).
- **RFC**: Created RFC `20260113220405-compile-documentation.md` to track the documentation project.

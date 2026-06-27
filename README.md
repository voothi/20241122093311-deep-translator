# Deep-Translator GoldenDict Integration

[![Version](https://img.shields.io/badge/version-v1.0.1-blue)](https://github.com/voothi/20241122093311-deep-translator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A configuration guide and scripts for integrating the `deep-translator` library with GoldenDict-ng. This setup supports multiple translation providers including Google, DeepL, and MyMemory.

## Table of Contents
- [Deep-Translator GoldenDict Integration](#deep-translator-goldendict-integration)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Features](#features)
  - [Tech Stack](#tech-stack)
  - [Installation](#installation)
    - [1. Environment Setup](#1-environment-setup)
    - [2. Supported Scripts](#2-supported-scripts)
    - [3. Developer Testing](#3-developer-testing)
  - [GoldenDict-ng Configuration](#goldendict-ng-configuration)
    - [Google Translate](#google-translate)
    - [DeepL Translator](#deepl-translator)
    - [MyMemory Translator](#mymemory-translator)
  - [Security Note](#security-note)
  - [License](#license)

---

## Description
This project provides a wrapper around the `deep-translator` Python library to enable seamless translation within GoldenDict-ng. By configuring external program calls, you can get translations directly in your dictionary interface using various online engines.

## Features
- **Multiple Providers**: Integration with Google Translate, DeepL (requires API key), and MyMemory.
- **Easy Integration**: Ready-to-use command line configurations for GoldenDict-ng.
- **Language Support**: Flexible source and target language selection.

## Tech Stack
- **Python**: 3.11.1
- **Library**: `deep-translator` v1.11.4

## Installation

### 1. Environment Setup
Clone the repository and set up a virtual environment.
```powershell
# Create venv
python -m venv venv

# Activate venv
.\venv\Scripts\activate

# Install dependencies (Secure Install)
# To install the verified version with hash checking:
pip install deep-translator==1.11.4 --hash=sha256:d635df037e23fa35d12fd42dab72a0b55c9dd19e6292009ee7207e3f30b9e60a
```

### 2. Supported Scripts
- `translate_google.py`: Uses **Google Translator** (Free/Unlimited).
- `translate_deepl.py`: Uses **DeepL Translator** (Requires `--deepl-api-key`).
- `translate_mymemory.py`: Uses **MyMemory Translator**.

### 3. Developer Testing
If you are modifying the `deep-translator` library and want to test changes using a local fork:

1.  Create a `config.json` file in the root directory:
    ```json
    {
        "local_deep_translator_fork_path": "path/to/your/fork"
    }
    ```
2.  Run the scripts with the `--use-local-fork` flag:
    ```powershell
    python translate_google.py --text "Test" --source en --target fr --use-local-fork
    ```

## GoldenDict-ng Configuration

To integrate these translators into GoldenDict-ng:
1. Open GoldenDict-ng.
2. Go to **Edit** > **Dictionaries** > **Sources** > **Programs**.
3. Add the following entries as needed.

### Google Translate
*Script: `translate_google.py` (Free, Unlimited)*

```xml
  <!-- English -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_google.py --text &quot;%GDWORD%&quot; --source en --target ru" enabled="1" name="dT-g En-Ru" type="1"/>
  <!-- English -> German -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_google.py --text &quot;%GDWORD%&quot; --source en --target de" enabled="1" name="dT-g En-De" type="1"/>
  <!-- English -> Ukrainian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_google.py --text &quot;%GDWORD%&quot; --source en --target uk" enabled="1" name="dT-g En-Uk" type="1"/>

  <!-- German -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_google.py --text &quot;%GDWORD%&quot; --source de --target ru" enabled="1" name="dT-g De-Ru" type="1"/>
  <!-- German -> English -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_google.py --text &quot;%GDWORD%&quot; --source de --target en" enabled="1" name="dT-g De-En" type="1"/>
  <!-- German -> Ukrainian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_google.py --text &quot;%GDWORD%&quot; --source de --target uk" enabled="1" name="dT-g De-Uk" type="1"/>

  <!-- Russian -> English -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_google.py --text &quot;%GDWORD%&quot; --source ru --target en" enabled="1" name="dT-g Ru-En" type="1"/>
  <!-- Russian -> German -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_google.py --text &quot;%GDWORD%&quot; --source ru --target de" enabled="1" name="dT-g Ru-De" type="1"/>
  <!-- Russian -> Ukrainian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_google.py --text &quot;%GDWORD%&quot; --source ru --target uk" enabled="1" name="dT-g Ru-Uk" type="1"/>

  <!-- Ukrainian -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_google.py --text &quot;%GDWORD%&quot; --source uk --target ru" enabled="1" name="dT-g Uk-Ru" type="1"/>
```

### DeepL Translator
*Script: `translate_deepl.py` (Requires API Key)*
*Replace `YOUR_DEEPL_API_KEY` with your actual key.*

```xml
  <!-- English -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_deepl.py --text &quot;%GDWORD%&quot; --source en --target ru --deepl-api-key &quot;YOUR_DEEPL_API_KEY&quot;" enabled="1" name="dT-d En-Ru" type="1"/>
  <!-- German -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_deepl.py --text &quot;%GDWORD%&quot; --source de --target ru --deepl-api-key &quot;YOUR_DEEPL_API_KEY&quot;" enabled="1" name="dT-d De-Ru" type="1"/>
  <!-- Russian -> English -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_deepl.py --text &quot;%GDWORD%&quot; --source ru --target en --deepl-api-key &quot;YOUR_DEEPL_API_KEY&quot;" enabled="1" name="dT-d Ru-En" type="1"/>
  <!-- Russian -> German -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_deepl.py --text &quot;%GDWORD%&quot; --source ru --target de --deepl-api-key &quot;YOUR_DEEPL_API_KEY&quot;" enabled="1" name="dT-d Ru-De" type="1"/>
```

### MyMemory Translator
*Script: `translate_mymemory.py` (Uses full language names)*

```xml
  <!-- English -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_mymemory.py --text &quot;%GDWORD%&quot; --source english --target russian" enabled="1" name="dT-m En-Ru" type="1"/>
  <!-- German -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_mymemory.py --text &quot;%GDWORD%&quot; --source german --target russian" enabled="1" name="dT-m De-Ru" type="1"/>
  <!-- Russian -> English -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_mymemory.py --text &quot;%GDWORD%&quot; --source russian --target english" enabled="1" name="dT-m Ru-En" type="1"/>
  <!-- Russian -> German -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate_mymemory.py --text &quot;%GDWORD%&quot; --source russian --target german" enabled="1" name="dT-m Ru-De" type="1"/>
```

## Network Resilience Configuration

The scripts include a network resilience layer that automatically handles flaky connections, timeouts, and transient errors (like 429 and 5xx). By default, the wrapper uses fail-fast settings optimized for interactive usage:
- **Default Timeout**: 5 seconds
- **Default Retries**: 2 (makes 3 attempts total)
- **Exponential Backoff**: Base of 1.0s with 1.0s jitter, capped at 30.0s.

### Configurable Keys (`config.json`)

You can customize these defaults in `config.json` using the following optional keys:
- `netTimeout`: Float representing the timeout in seconds (default `5` for wrapper).
- `maxRetries`: Integer for the maximum retry count. Set to `-1` for endless (default `2`).
- `retryBackoff`: Float for the exponential backoff base in seconds (default `1.0`).
- `maxTotalTime`: Float for the overall wall-clock deadline limit in seconds (default `null`).
- `retryDiagnostics`: Boolean to enable/disable retry diagnostics printed to stderr (default `true`).
- `echoErrorsToStdout`: Boolean to output a clean one-line error to stdout on failure (default `false`).

These can also be overridden per command invocation using:
- `--timeout <seconds>`
- `--retries <attempts>`
- `--retry-backoff <seconds>`
- `--max-total-time <seconds>`
- `--quiet` (disables retry diagnostics on stderr)
- `--plain` (enables one-line errors on stdout)

---

## Consumer Notes & Integration

### GoldenDict-ng (Programs)
GoldenDict captures only `stdout` for rendering the article and discards `stderr`. If a network failure occurs, the program exits non-zero and GoldenDict shows a blank page. 
To display a human-readable error reason in GoldenDict instead of a blank page, append the `--plain` flag to your command (or set `"echoErrorsToStdout": true` in `config.json`). This prints a single-line error message directly to `stdout` only on failure.

### AutoHotkey v2 (`translate-selection.ahk`)
The AHK integration runs the translation script and captures stdout/stderr. To prevent retry diagnostics on `stderr` from polluting your pasted text:
1. **With No AHK Edit**: Pass `--quiet` as a command-line flag or set `"retryDiagnostics": false` in `config.json`. This suppresses retry diagnostics on `stderr`, ensuring only the final translation is written to stdout.
2. **Stream-Separation (Recommended)**: Update `translate-selection.ahk` to separate the streams:
   - Change redirections from `> "outFile" 2>&1` to `> "outFile" 2> "errFile"`.
   - Read `outFile` for pasting on success (exit code 0), and read `errFile` for the error MsgBox on non-zero exit. This allows you to keep full retry diagnostics on `stderr` without risking pasting them into your document.

---

## Security Note
The scripts provided are designed for local integration. Please be aware of the following:
- **HTTPS vs HTTP**:
  - **Google & DeepL**: Use **HTTPS** for secure encrypted connections.
  - **MyMemory**: Uses **HTTP** (`http://api.mymemory.translated.net`). Traffic to this provider is not encrypted and may be visible on port 80.
- **API Key Visibility**: When using `translate_deepl.py` for DeepL, the API key is passed as a command-line argument. On multi-user systems, this key may be visible to other users via the process list.
- **Data Privacy**: Text to be translated is sent to external providers (Google, DeepL, MyMemory). Ensure you comply with your data privacy requirements.

## License
MIT

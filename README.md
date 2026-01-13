# Deep-Translator GoldenDict Integration

[![Version](https://img.shields.io/badge/version-v1.0.0-blue)](https://github.com/voothi/20241122093311-deep-translator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A configuration guide and scripts for integrating the `deep-translator` library with GoldenDict-ng. This setup supports multiple translation providers including Google, DeepL, and MyMemory.

## Table of Contents
- [Description](#description)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [GoldenDict-ng Configuration](#goldendict-ng-configuration)
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

# Install dependencies
pip install deep-translator==1.11.4
```

### 2. Supported Scripts
- `translate.py`: Uses **Google Translator** (Free/Unlimited).
- `translate.1.py`: Uses **DeepL Translator** (Requires `--deepl-api-key`).
- `translate.2.py`: Uses **MyMemory Translator**.

## GoldenDict-ng Configuration

To integrate these translators into GoldenDict-ng:
1. Open GoldenDict-ng.
2. Go to **Edit** > **Dictionaries** > **Sources** > **Programs**.
3. Add the following entries as needed.

### Configuration Snippets (XML format)
*Note: Ensure the paths match your local installation. API keys have been removed.*

```xml
  <!-- Google Translate (En-Ru) -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.py --text &quot;%GDWORD%&quot; --source en --target ru" enabled="1" icon="" id="ca0a918ab349225644b171a4caf460f5" name="dT-g En-Ru" type="1"/>
  
  <!-- DeepL Translate (En-Ru) - Requires API Key -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.1.py --text &quot;%GDWORD%&quot; --source en --target ru --deepl-api-key &quot;YOUR_DEEPL_API_KEY&quot;" enabled="1" icon="" id="55adc197c0dd34c2d84623beb56ddd9e" name="dT-d En-Ru" type="1"/>
  
  <!-- MyMemory Translate (En-Ru) -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.2.py --text &quot;%GDWORD%&quot; --source english --target russian" enabled="1" icon="" id="c769eac8c7864ae4021a27d4de065a3d" name="dT-m En-Ru" type="1"/>
```

### Full Configuration Examples
| Provider | Source  | Target  | Command Line Pattern                                                                              |
| :------- | :------ | :------ | :------------------------------------------------------------------------------------------------ |
| Google   | en      | ru      | `...python.exe ...translate.py --text "%GDWORD%" --source en --target ru`                         |
| DeepL    | en      | ru      | `...python.exe ...translate.1.py --text "%GDWORD%" --source en --target ru --deepl-api-key "..."` |
| MyMemory | english | russian | `...python.exe ...translate.2.py --text "%GDWORD%" --source english --target russian`             |

## License
MIT

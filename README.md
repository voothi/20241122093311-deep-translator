# Deep-Translator GoldenDict Integration

[![Version](https://img.shields.io/badge/version-v1.0.0-blue)](https://github.com/voothi/20241122093311-deep-translator)
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

### Google Translate
*Script: `translate.py` (Free, Unlimited)*

```xml
  <!-- English -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.py --text &quot;%GDWORD%&quot; --source en --target ru" enabled="1" name="dT-g En-Ru" type="1"/>
  <!-- English -> German -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.py --text &quot;%GDWORD%&quot; --source en --target de" enabled="1" name="dT-g En-De" type="1"/>
  <!-- English -> Ukrainian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.py --text &quot;%GDWORD%&quot; --source en --target uk" enabled="1" name="dT-g En-Uk" type="1"/>

  <!-- German -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.py --text &quot;%GDWORD%&quot; --source de --target ru" enabled="1" name="dT-g De-Ru" type="1"/>
  <!-- German -> English -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.py --text &quot;%GDWORD%&quot; --source de --target en" enabled="1" name="dT-g De-En" type="1"/>
  <!-- German -> Ukrainian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.py --text &quot;%GDWORD%&quot; --source de --target uk" enabled="1" name="dT-g De-Uk" type="1"/>

  <!-- Russian -> English -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.py --text &quot;%GDWORD%&quot; --source ru --target en" enabled="1" name="dT-g Ru-En" type="1"/>
  <!-- Russian -> German -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.py --text &quot;%GDWORD%&quot; --source ru --target de" enabled="1" name="dT-g Ru-De" type="1"/>
  <!-- Russian -> Ukrainian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.py --text &quot;%GDWORD%&quot; --source ru --target uk" enabled="1" name="dT-g Ru-Uk" type="1"/>

  <!-- Ukrainian -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.py --text &quot;%GDWORD%&quot; --source uk --target ru" enabled="1" name="dT-g Uk-Ru" type="1"/>
```

### DeepL Translator
*Script: `translate.1.py` (Requires API Key)*
*Replace `YOUR_DEEPL_API_KEY` with your actual key.*

```xml
  <!-- English -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.1.py --text &quot;%GDWORD%&quot; --source en --target ru --deepl-api-key &quot;YOUR_DEEPL_API_KEY&quot;" enabled="1" name="dT-d En-Ru" type="1"/>
  <!-- German -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.1.py --text &quot;%GDWORD%&quot; --source de --target ru --deepl-api-key &quot;YOUR_DEEPL_API_KEY&quot;" enabled="1" name="dT-d De-Ru" type="1"/>
  <!-- Russian -> English -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.1.py --text &quot;%GDWORD%&quot; --source ru --target en --deepl-api-key &quot;YOUR_DEEPL_API_KEY&quot;" enabled="1" name="dT-d Ru-En" type="1"/>
  <!-- Russian -> German -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.1.py --text &quot;%GDWORD%&quot; --source ru --target de --deepl-api-key &quot;YOUR_DEEPL_API_KEY&quot;" enabled="1" name="dT-d Ru-De" type="1"/>
```

### MyMemory Translator
*Script: `translate.2.py` (Uses full language names)*

```xml
  <!-- English -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.2.py --text &quot;%GDWORD%&quot; --source english --target russian" enabled="1" name="dT-m En-Ru" type="1"/>
  <!-- German -> Russian -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.2.py --text &quot;%GDWORD%&quot; --source german --target russian" enabled="1" name="dT-m De-Ru" type="1"/>
  <!-- Russian -> English -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.2.py --text &quot;%GDWORD%&quot; --source russian --target english" enabled="1" name="dT-m Ru-En" type="1"/>
  <!-- Russian -> German -->
  <program commandLine="U:\voothi\20241122093311-deep-translator\venv\Scripts\python.exe U:\voothi\20241122093311-deep-translator\translate.2.py --text &quot;%GDWORD%&quot; --source russian --target german" enabled="1" name="dT-m Ru-De" type="1"/>
```

## Security Note
The scripts provided are designed for local integration. Please be aware of the following:
- **API Key Visibility**: When using `translate.1.py` for DeepL, the API key is passed as a command-line argument. On multi-user systems, this key may be visible to other users via the process list.
- **Data Privacy**: Text to be translated is sent to external providers (Google, DeepL, MyMemory). Ensure you comply with your data privacy requirements.

## License
MIT

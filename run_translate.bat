@echo off
cd C:\Tools\deep-translator && call venv\Scripts\activate && python translate.py --text "%GDWORD%" --source en --target ru

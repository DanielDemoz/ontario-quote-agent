@echo off
REM Double-click this file to launch the comparison dashboard.
REM It activates the virtual environment and starts Streamlit.
cd /d "%~dp0"
call venv\Scripts\activate.bat
streamlit run app.py
pause

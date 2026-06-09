@echo off
echo.
echo ====================================
echo    RGPV Result Fetcher - Streamlit
echo ====================================
echo.
echo Starting Streamlit app...
echo.
echo Opening browser at http://localhost:8501
echo Press Ctrl+C to stop the server
echo.
timeout /t 2 /nobreak
python -m streamlit run app.py
pause

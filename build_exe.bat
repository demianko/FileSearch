@echo off
echo ===============================================
echo Building FileSearchUtil.exe with PyInstaller...
echo ===============================================

.\.venv\Scripts\pyinstaller.exe --noconsole --onefile --collect-all customtkinter --name "FileSearchUtil" FileSearchUtil.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo ===============================================
    echo Build Successful!
    echo Executable is ready at: dist\FileSearchUtil.exe
    echo ===============================================
) else (
    echo.
    echo Build Failed.
)

pause

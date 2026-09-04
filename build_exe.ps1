Write-Host "Building FileSearchUtil.exe..." -ForegroundColor Cyan

& ".\.venv\Scripts\pyinstaller.exe" --noconsole --onefile --collect-all customtkinter --name "FileSearchUtil" FileSearchUtil.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n===============================================" -ForegroundColor Green
    Write-Host "Build Successful!" -ForegroundColor Green
    Write-Host "Executable location: dist\FileSearchUtil.exe" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Green
} else {
    Write-Host "`nBuild Failed. Please check errors above." -ForegroundColor Red
}

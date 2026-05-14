@echo off
echo === Pixel Timer Build ===
echo.

call "%USERPROFILE%\.venvs\pixel_timer\Scripts\activate.bat"

pip show pyinstaller >nul 2>&1 || pip install pyinstaller==6.20.0

pyinstaller pixel_timer.spec --noconfirm

echo.
echo === Build complete: dist\PixelTimer\ ===
pause

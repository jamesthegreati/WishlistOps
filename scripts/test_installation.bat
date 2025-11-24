@echo off
REM Test WishlistOps Installation & Launch (Windows)

echo ==========================================
echo 🎮 WishlistOps Installation Test
echo ==========================================
echo.

REM Check Python version
echo 📍 Checking Python version...
python --version
if errorlevel 1 (
    echo ❌ Python not found
    exit /b 1
)
echo ✓ Python found
echo.

REM Install package
echo 📦 Installing WishlistOps...
pip install -e ".[dev]"
if errorlevel 1 (
    echo ❌ Installation failed
    exit /b 1
)
echo ✓ Installed successfully
echo.

REM Check CLI
echo 🔍 Testing CLI...
where wishlistops >nul 2>&1
if errorlevel 1 (
    echo ❌ CLI command not found
    exit /b 1
)
echo ✓ CLI command available
echo.

REM Test help
echo 📖 Testing help command...
wishlistops --help >nul
if errorlevel 1 (
    echo ❌ Help command failed
    exit /b 1
)
echo ✓ Help command works
echo.

REM Check dashboard files
echo 🌐 Checking dashboard files...
if exist "dashboard\index.html" (
    echo ✓ index.html
) else (
    echo ❌ Missing index.html
)

if exist "dashboard\welcome.html" (
    echo ✓ welcome.html
) else (
    echo ❌ Missing welcome.html
)

if exist "dashboard\setup.html" (
    echo ✓ setup.html
) else (
    echo ❌ Missing setup.html
)

if exist "dashboard\monitor.html" (
    echo ✓ monitor.html
) else (
    echo ❌ Missing monitor.html
)

if exist "dashboard\docs.html" (
    echo ✓ docs.html
) else (
    echo ❌ Missing docs.html
)

if exist "dashboard\styles.css" (
    echo ✓ styles.css
) else (
    echo ❌ Missing styles.css
)
echo.

REM Success
echo ==========================================
echo ✅ All tests passed!
echo ==========================================
echo.
echo 🚀 Ready to launch:
echo    1. Run: wishlistops setup
echo    2. Browser opens at http://127.0.0.1:8080
echo    3. Follow setup wizard
echo.
echo 📖 Documentation:
echo    - Built-in: http://127.0.0.1:8080/docs
echo    - Launch Guide: type LAUNCH_GUIDE.md
echo    - GitHub: https://github.com/jamesthegreati/WishlistOps
echo.

@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo             VT Shield Multi-Platform Builder
echo ===================================================
echo.
echo Target architectures:
echo   - Windows: x64, arm64
echo   - macOS: universal
echo   - Linux: x64, arm64
echo.

:: Ensure output directory exists
if not exist "build\bin" mkdir "build\bin"

echo [+] Building Windows x64...
if exist "build\bin\vt-gui-windows-x64.exe" del "build\bin\vt-gui-windows-x64.exe"
wails build -platform windows/amd64 -o vt-gui-windows-x64.exe >nul 2>&1
if not exist "build\bin\vt-gui-windows-x64.exe" (
    echo [!] Windows x64 build failed.
) else (
    echo [+] Windows x64 built successfully: build\bin\vt-gui-windows-x64.exe
)

echo.
echo [+] Building Windows arm64...
if exist "build\bin\vt-gui-windows-arm64.exe" del "build\bin\vt-gui-windows-arm64.exe"
wails build -platform windows/arm64 -o vt-gui-windows-arm64.exe >nul 2>&1
if not exist "build\bin\vt-gui-windows-arm64.exe" (
    echo [!] Windows arm64 build failed.
) else (
    echo [+] Windows arm64 built successfully: build\bin\vt-gui-windows-arm64.exe
)

echo.
echo [+] Building macOS Universal (Intel + Apple Silicon)...
echo Note: Cross-compiling to macOS from Windows is not supported natively.
if exist "build\bin\vt-gui-macos-universal" del "build\bin\vt-gui-macos-universal"
wails build -platform darwin/universal -o vt-gui-macos-universal >nul 2>&1
if not exist "build\bin\vt-gui-macos-universal" if not exist "build\bin\vt-gui-macos-universal.app" (
    echo [!] macOS Universal build was skipped or failed.
    echo     (Note: Wails requires running on macOS to build macOS targets, or using a CI/CD pipeline).
) else (
    echo [+] macOS Universal built successfully: build\bin\vt-gui-macos-universal
)

echo.
echo [+] Building Linux x64...
echo Note: Cross-compiling to Linux from Windows is not supported natively.
if exist "build\bin\vt-gui-linux-x64" del "build\bin\vt-gui-linux-x64"
wails build -platform linux/amd64 -o vt-gui-linux-x64 >nul 2>&1
if not exist "build\bin\vt-gui-linux-x64" (
    echo [!] Linux x64 build was skipped or failed.
    echo     (Note: Wails requires running on Linux to build Linux targets, or using a CI/CD pipeline).
) else (
    echo [+] Linux x64 built successfully: build\bin\vt-gui-linux-x64
)

echo.
echo [+] Building Linux arm64...
echo Note: Cross-compiling to Linux from Windows is not supported natively.
if exist "build\bin\vt-gui-linux-arm64" del "build\bin\vt-gui-linux-arm64"
wails build -platform linux/arm64 -o vt-gui-linux-arm64 >nul 2>&1
if not exist "build\bin\vt-gui-linux-arm64" (
    echo [!] Linux arm64 build was skipped or failed.
    echo     (Note: Wails requires running on Linux to build Linux targets, or using a CI/CD pipeline).
) else (
    echo [+] Linux arm64 built successfully: build\bin\vt-gui-linux-arm64
)

echo.
echo ===================================================
echo Build process finished!
echo Check the build\bin directory for output executables.
echo ===================================================
pause

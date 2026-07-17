#!/bin/bash

echo "==================================================="
echo "            VT Shield Multi-Platform Builder"
echo "==================================================="
echo ""
echo "Target architectures:"
echo "  - Windows: x64, arm64"
echo "  - macOS: universal"
echo "  - Linux: x64, arm64"
echo ""

# Ensure output directory exists
mkdir -p build/bin

echo "[+] Building Windows x64..."
rm -f build/bin/vt-gui-windows-x64.exe
wails build -platform windows/amd64 -o vt-gui-windows-x64.exe >/dev/null 2>&1
if [ ! -f "build/bin/vt-gui-windows-x64.exe" ]; then
    echo "[!] Windows x64 build failed."
else
    echo "[+] Windows x64 built successfully: build/bin/vt-gui-windows-x64.exe"
fi

echo ""
echo "[+] Building Windows arm64..."
rm -f build/bin/vt-gui-windows-arm64.exe
wails build -platform windows/arm64 -o vt-gui-windows-arm64.exe >/dev/null 2>&1
if [ ! -f "build/bin/vt-gui-windows-arm64.exe" ]; then
    echo "[!] Windows arm64 build failed."
else
    echo "[+] Windows arm64 built successfully: build/bin/vt-gui-windows-arm64.exe"
fi

echo ""
echo "[+] Building macOS Universal (Intel + Apple Silicon)..."
rm -f build/bin/vt-gui-macos-universal
rm -rf build/bin/vt-gui-macos-universal.app
wails build -platform darwin/universal -o vt-gui-macos-universal >/dev/null 2>&1
if [ ! -f "build/bin/vt-gui-macos-universal" ] && [ ! -d "build/bin/vt-gui-macos-universal.app" ]; then
    echo "[!] macOS Universal build was skipped or failed."
    echo "    (Note: Wails requires running on macOS to build macOS targets, or using a CI/CD pipeline)."
else
    echo "[+] macOS Universal built successfully: build/bin/vt-gui-macos-universal"
fi

echo ""
echo "[+] Building Linux x64..."
rm -f build/bin/vt-gui-linux-x64
wails build -platform linux/amd64 -o vt-gui-linux-x64 >/dev/null 2>&1
if [ ! -f "build/bin/vt-gui-linux-x64" ]; then
    echo "[!] Linux x64 build was skipped or failed."
    echo "    (Note: Wails requires running on Linux to build Linux targets, or using a CI/CD pipeline)."
else
    echo "[+] Linux x64 built successfully: build/bin/vt-gui-linux-x64"
fi

echo ""
echo "[+] Building Linux arm64..."
rm -f build/bin/vt-gui-linux-arm64
wails build -platform linux/arm64 -o vt-gui-linux-arm64 >/dev/null 2>&1
if [ ! -f "build/bin/vt-gui-linux-arm64" ]; then
    echo "[!] Linux arm64 build was skipped or failed."
    echo "    (Note: Wails requires running on Linux to build Linux targets, or using a CI/CD pipeline)."
else
    echo "[+] Linux arm64 built successfully: build/bin/vt-gui-linux-arm64"
fi

echo ""
echo "==================================================="
echo "Build process finished!"
echo "Check the build/bin directory for output executables."
echo "==================================================="

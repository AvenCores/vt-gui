#!/usr/bin/env python3
"""Build script for macOS that disables codesigning.

The Flet desktop client bundles FlutterMacOS.framework and other frameworks
with incompatible binary structure, causing codesign to fail on CI runners.
This script monkey-patches PyInstaller's signing function to a no-op.
"""
import sys
import PyInstaller.__main__
import PyInstaller.utils.osx as _osx

_osx.sign_binary = lambda *args, **kwargs: None

sys.exit(PyInstaller.__main__.run())

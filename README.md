# VirusTotal Shield (VT Shield)

VT Shield is a premium desktop application rewritten in Go using the **Wails** framework. It provides a visual interface for scanning files on VirusTotal and viewing scan outcomes.

## 🚀 Features

- **Direct Web API Mode**: Performs scans using direct HTTP requests to the VirusTotal V3 API without needing any external executables.
- **VirusTotal CLI Integration (`vt.exe`)**: Integrates with the official `vt` CLI tool.
- **Manual CLI Download**: Unlike the previous python version, the app doesn't auto-download files. If you want to use CLI mode, you should download `vt.exe` manually from [VirusTotal CLI Releases on GitHub](https://github.com/VirusTotal/vt-cli/releases) and place it in your system `PATH` or in the application directory.
- **Antivirus Detection Lists**: Displays the specific antivirus engines that flagged the file, along with their threat classification, category, and method.
- **Windows Explorer Right-Click Context Menu**: Integrates a "Scan with VirusTotal" option directly into the Windows right-click menu, opening the selected file automatically.
- **High-Tech Aesthetic**: Sleek glassmorphic dark interface with neon accents, verdict gauges, and real-time upload progress.

---

## 🛠️ How to Build

To build the executable yourself, make sure you have **Go** installed (v1.21+ recommended) and the **Wails CLI**.

1. Install Wails CLI (if not already installed):
   ```bash
   go install github.com/wailsapp/wails/v2/cmd/wails@latest
   ```

2. Build the production binary:
   ```bash
   wails build
   ```

The compiled binary will be saved to: `build/bin/vt-gui.exe`.

---

## ⚙️ Configuration

1. **VirusTotal API Key**: To use the application, configure your VirusTotal API key in the sidebar. This key is saved locally in `~/.vt.toml` (compatible with the official `vt` CLI config).
2. **Context Menu**: Toggle the right-click integration on or off from the sidebar settings.
3. **Scan Engine**: Switch between direct API connection and external `vt.exe` CLI binary.

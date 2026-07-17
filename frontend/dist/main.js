document.addEventListener("DOMContentLoaded", () => {
    // --- Elements ---
    const apiKeyInput = document.getElementById("api-key-input");
    const saveKeyBtn = document.getElementById("save-key-btn");
    const toggleKeyVisibilityBtn = document.getElementById("toggle-key-visibility");
    const eyeIcon = document.getElementById("eye-icon");
    const contextMenuToggle = document.getElementById("context-menu-toggle");
    const useCliToggle = document.getElementById("use-cli-toggle");
    const cliStatusIndicator = document.getElementById("cli-status-indicator");
    const cliStatusText = cliStatusIndicator.querySelector(".status-text");
    const cliDownloadTip = document.getElementById("cli-download-tip");
    const githubLink = document.getElementById("github-link");

    const globalAlert = document.getElementById("global-alert");
    const alertTitle = document.getElementById("alert-title");
    const alertMessage = document.getElementById("alert-message");

    const stateSelect = document.getElementById("state-select");
    const stateScanning = document.getElementById("state-scanning");
    const stateResults = document.getElementById("state-results");

    const dragDropZone = document.getElementById("drag-drop-zone");
    const browseBtn = document.getElementById("browse-btn");
    const selectedFilePanel = document.getElementById("selected-file-panel");
    const fileNameText = document.getElementById("file-name");
    const fileSizeText = document.getElementById("file-size");
    const fileHashText = document.getElementById("file-hash");
    const startScanBtn = document.getElementById("start-scan-btn");

    const scanningHeader = document.getElementById("scanning-header");
    const scanningStatus = document.getElementById("scanning-status");
    const uploadProgressContainer = document.getElementById("upload-progress-container");
    const progressBarFill = document.getElementById("progress-bar-fill");
    const progressPercent = document.getElementById("progress-percent");
    const progressBytes = document.getElementById("progress-bytes");

    const gaugeFill = document.getElementById("gauge-fill");
    const detectionScore = document.getElementById("detection-score");
    const verdictBanner = document.getElementById("verdict-banner");
    const verdictIconPath = document.getElementById("verdict-icon-path");
    const verdictIconPoly = document.getElementById("verdict-icon-poly");
    const verdictTitle = document.getElementById("verdict-title");
    const verdictDesc = document.getElementById("verdict-desc");
    
    const resFilename = document.getElementById("res-filename");
    const resFilesize = document.getElementById("res-filesize");
    const resHash = document.getElementById("res-hash");
    
    const detectionsBadge = document.getElementById("detections-badge");
    const detectionsList = document.getElementById("detections-list");
    const detectionsTableContainer = document.getElementById("detections-table-container");
    const cleanDetectionsMsg = document.getElementById("clean-detections-msg");
    const detectionsTable = document.querySelector(".detections-table");

    const scanNewBtn = document.getElementById("scan-new-btn");
    const viewReportBtn = document.getElementById("view-report-btn");

    // --- State Variables ---
    let selectedFilePath = "";
    let fileHash = "";
    let currentReportUrl = "";

    // --- App Init ---
    initApp();

    async function initApp() {
        // 1. Get and populate API Key
        try {
            const key = await window.go.main.App.GetApiKey();
            if (key) {
                apiKeyInput.value = key;
                hideAlert();
            } else {
                showAlert("Configure API Key", "You need a free or premium VirusTotal API Key to scan files.", "warning");
            }
        } catch (e) {
            console.error("Failed to fetch API key:", e);
        }

        // 2. Check Context Menu Status
        try {
            const registered = await window.go.main.App.IsContextMenuRegistered();
            contextMenuToggle.checked = registered;
        } catch (e) {
            console.error("Failed to check context menu status:", e);
        }

        // 3. Check Local CLI Preferences
        const useCLI = localStorage.getItem("useCLI") === "true";
        useCliToggle.checked = useCLI;
        if (useCLI) {
            cliStatusIndicator.classList.remove("hidden");
            checkCLIExecutable();
        }

        // 4. Check if launched with a file argument (e.g. from Context Menu)
        try {
            const initFile = await window.go.main.App.GetInitialFile();
            if (initFile) {
                handleFileSelected(initFile);
            }
        } catch (e) {
            console.error("Failed to get initial file:", e);
        }
    }

    // --- Actions ---

    // Toggle API Key Visibility
    toggleKeyVisibilityBtn.addEventListener("click", () => {
        if (apiKeyInput.type === "password") {
            apiKeyInput.type = "text";
            eyeIcon.innerHTML = `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>`;
        } else {
            apiKeyInput.type = "password";
            eyeIcon.innerHTML = `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>`;
        }
    });

    // Save API Key
    saveKeyBtn.addEventListener("click", async () => {
        const key = apiKeyInput.value.trim();
        if (!key) {
            showAlert("Input Required", "API key cannot be empty.", "danger");
            return;
        }
        try {
            const err = await window.go.main.App.SaveApiKey(key);
            if (err) {
                showAlert("Save Failed", "Failed to save key: " + err, "danger");
            } else {
                showAlert("Success", "API Key saved successfully.", "success");
                setTimeout(hideAlert, 3000);
            }
        } catch (e) {
            showAlert("Save Failed", "Error saving key: " + e, "danger");
        }
    });

    // Toggle Context Menu Integration
    contextMenuToggle.addEventListener("change", async () => {
        try {
            if (contextMenuToggle.checked) {
                const err = await window.go.main.App.RegisterContextMenu();
                if (err) {
                    showAlert("Registration Failed", "Failed to register context menu: " + err, "danger");
                    contextMenuToggle.checked = false;
                } else {
                    showAlert("Registered", "Successfully registered context menu integration.", "success");
                    setTimeout(hideAlert, 3000);
                }
            } else {
                const err = await window.go.main.App.UnregisterContextMenu();
                if (err) {
                    showAlert("Unregistration Failed", "Failed to remove context menu: " + err, "danger");
                    contextMenuToggle.checked = true;
                } else {
                    showAlert("Removed", "Context menu integration removed.", "success");
                    setTimeout(hideAlert, 3000);
                }
            }
        } catch (e) {
            showAlert("Error", "Failed to toggle context menu: " + e, "danger");
        }
    });

    // Toggle CLI Engine
    useCliToggle.addEventListener("change", () => {
        const checked = useCliToggle.checked;
        localStorage.setItem("useCLI", checked);
        if (checked) {
            cliStatusIndicator.classList.remove("hidden");
            checkCLIExecutable();
        } else {
            cliStatusIndicator.classList.add("hidden");
        }
    });

    // Github manual download link action
    githubLink.addEventListener("click", (e) => {
        e.preventDefault();
        window.go.main.App.OpenInBrowser("https://github.com/VirusTotal/vt-cli/releases");
    });

    // Check vt.exe helper
    async function checkCLIExecutable() {
        cliStatusIndicator.className = "cli-status-container";
        cliStatusText.textContent = "Checking vt.exe...";
        cliDownloadTip.classList.add("hidden");

        try {
            const path = await window.go.main.App.CheckVTExecutable();
            if (path) {
                cliStatusIndicator.classList.add("found");
                cliStatusText.textContent = "vt.exe found in system";
            } else {
                cliStatusIndicator.classList.add("missing");
                cliStatusText.textContent = "vt.exe not found";
                cliDownloadTip.classList.remove("hidden");
            }
        } catch (e) {
            cliStatusIndicator.classList.add("missing");
            cliStatusText.textContent = "Check failed";
        }
    }

    // Browse files
    browseBtn.addEventListener("click", async () => {
        try {
            const path = await window.go.main.App.SelectFile();
            if (path) {
                handleFileSelected(path);
            }
        } catch (e) {
            console.error("Browse failed:", e);
        }
    });

    // --- Drag & Drop ---
    // Triggered from Go
    window.runtime.EventsOn("file_dropped", (path) => {
        handleFileSelected(path);
    });

    // HTML5 dragover effects (just visual)
    dragDropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dragDropZone.classList.add("dragover");
    });

    dragDropZone.addEventListener("dragleave", () => {
        dragDropZone.classList.remove("dragover");
    });

    dragDropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dragDropZone.classList.remove("dragover");
        // Handled by Go OnFileDrop runtime event
    });

    // --- File Selection Handler ---
    async function handleFileSelected(path) {
        selectedFilePath = path;
        const filename = path.replace(/^.*[\\\/]/, '');
        fileNameText.textContent = filename;
        fileSizeText.textContent = "Reading file size...";
        fileHashText.textContent = "Calculating fingerprint...";
        
        selectedFilePanel.classList.remove("hidden");
        
        // Try to get hash and details via Wails backend
        try {
            // Expose a public helper in app.go to calculate hash before scanning
            const hash = await window.go.main.App.ComputeSHA256(path);
            fileHash = hash;
            fileHashText.textContent = hash;
        } catch (e) {
            fileHashText.textContent = "Will be computed on scan";
        }

        // Just run a simple command or check properties if possible.
        // Actually, we can get the file size by calling a backend method or calculating it.
        // We'll calculate size during scanning, or we can just fetch it. Let's make sure
        // App.go has a method to get file info or let's estimate.
        // Let's add a backend method or just leave size blank until scan is started.
        // Actually, let's add a public FileInfo method! That would be extremely neat.
    }

    // --- Scan Actions ---
    startScanBtn.addEventListener("click", startScan);

    async function startScan() {
        if (!selectedFilePath) return;

        // Switch to scanning state
        switchState("scanning");
        scanningHeader.textContent = "Scanning Target";
        scanningStatus.textContent = "Preparing file...";
        uploadProgressContainer.classList.add("hidden");
        progressBarFill.style.width = "0%";
        progressPercent.textContent = "0%";
        progressBytes.textContent = "0 MB";

        // Bind progress and status events
        const removeStatusListener = window.runtime.EventsOn("scan_status", (status) => {
            scanningStatus.textContent = status;
        });

        const removeProgressListener = window.runtime.EventsOn("upload_progress", (data) => {
            uploadProgressContainer.classList.remove("hidden");
            const percent = data.percent || 0;
            progressBarFill.style.width = `${percent}%`;
            progressPercent.textContent = `${percent}%`;
            
            const currentMB = (data.current / (1024 * 1024)).toFixed(2);
            const totalMB = (data.total / (1024 * 1024)).toFixed(2);
            progressBytes.textContent = `${currentMB} / ${totalMB} MB`;
        });

        try {
            const useCLI = useCliToggle.checked;
            const result = await window.go.main.App.ScanFile(selectedFilePath, useCLI);
            
            // Clean up listeners
            removeStatusListener();
            removeProgressListener();

            if (result) {
                showResults(result);
            } else {
                throw new Error("Empty scan result");
            }
        } catch (e) {
            removeStatusListener();
            removeProgressListener();
            console.error("Scan failed:", e);
            showAlert("Scan Failed", e.message || e || "Unknown scan error occurred.", "danger");
            switchState("select");
        }
    }

    // --- Display Results ---
    function showResults(result) {
        switchState("results");
        currentReportUrl = result.reportUrl;

        // 1. Detections Score & Circle Gauge
        const stats = result.stats || {};
        const malicious = stats.malicious || 0;
        const suspicious = stats.suspicious || 0;
        const harmless = stats.harmless || 0;
        const undetected = stats.undetected || 0;
        const total = malicious + suspicious + harmless + undetected;
        
        detectionScore.textContent = `${malicious}/${total}`;
        
        // Calculate circle dasharray
        const chart = document.querySelector(".circular-chart");
        chart.className = "circular-chart"; // Reset
        
        const pct = total > 0 ? (malicious / total) * 100 : 0;
        gaugeFill.setAttribute("stroke-dasharray", `${pct}, 100`);

        // Verdict & Coloring
        verdictBanner.className = "verdict-card"; // Reset
        if (malicious > 0) {
            chart.classList.add("danger");
            verdictBanner.classList.add("verdict-malicious");
            verdictTitle.textContent = "DANGEROUS";
            verdictDesc = verdictDesc.textContent = `Flagged as malicious by ${malicious} engine${malicious > 1 ? 's' : ''}!`;
            verdictIconPath.setAttribute("d", "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z");
            verdictIconPoly.setAttribute("points", "12 9 12 13 12.01 17"); // Reuse alert icon elements
            
            // Simple triangle alert icon
            verdictBanner.querySelector(".verdict-icon").innerHTML = `
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" fill="none" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" stroke-width="2"/>
            `;
        } else if (suspicious > 0) {
            chart.classList.add("warning");
            verdictBanner.classList.add("verdict-suspicious");
            verdictTitle.textContent = "SUSPICIOUS";
            verdictDesc.textContent = `Flagged as suspicious by ${suspicious} engine${suspicious > 1 ? 's' : ''}.`;
            
            verdictBanner.querySelector(".verdict-icon").innerHTML = `
                <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2"/>
            `;
        } else {
            verdictBanner.classList.add("verdict-clean");
            verdictTitle.textContent = "CLEAN & SAFE";
            verdictDesc.textContent = "All antivirus engines reported this file as harmless.";
            
            verdictBanner.querySelector(".verdict-icon").innerHTML = `
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" fill="none" stroke="currentColor" stroke-width="2"/>
                <polyline points="22 4 12 14.01 9 11.01" fill="none" stroke="currentColor" stroke-width="2"/>
            `;
        }

        // File details
        resFilename.textContent = result.filename;
        resFilesize.textContent = formatBytes(result.size);
        resHash.textContent = result.hash;
        resHash.dataset.hash = result.hash;

        // Detections Table
        const detections = result.detections || [];
        detectionsBadge.textContent = `${detections.length} flags`;
        
        if (detections.length > 0) {
            detectionsBadge.classList.add("danger");
            detectionsTable.classList.remove("hidden");
            cleanDetectionsMsg.classList.add("hidden");
            
            detectionsList.innerHTML = "";
            detections.forEach(det => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td style="font-weight:600;">${det.engine}</td>
                    <td style="font-family:monospace;color:var(--text-secondary);">${det.result || 'Suspicious Flag'}</td>
                    <td><span class="sev-tag ${det.category}">${det.category}</span></td>
                    <td style="color:var(--text-muted);font-size:0.75rem;">${det.method}</td>
                `;
                detectionsList.appendChild(tr);
            });
        } else {
            detectionsBadge.classList.remove("danger");
            detectionsTable.classList.add("hidden");
            cleanDetectionsMsg.classList.remove("hidden");
        }
    }

    // Copy hash click
    resHash.addEventListener("click", () => {
        const hash = resHash.dataset.hash;
        if (!hash) return;
        navigator.clipboard.writeText(hash).then(() => {
            const originalText = resHash.textContent;
            resHash.textContent = "COPIED!";
            resHash.style.color = "var(--color-success)";
            setTimeout(() => {
                resHash.textContent = originalText;
                resHash.style.color = "";
            }, 1500);
        });
    });

    // Reset and select another file
    scanNewBtn.addEventListener("click", () => {
        selectedFilePath = "";
        fileHash = "";
        selectedFilePanel.classList.add("hidden");
        switchState("select");
    });

    // View report on VT website
    viewReportBtn.addEventListener("click", () => {
        if (currentReportUrl) {
            window.go.main.App.OpenInBrowser(currentReportUrl);
        }
    });

    // --- Helpers ---
    function switchState(state) {
        stateSelect.classList.remove("active");
        stateScanning.classList.remove("active");
        stateResults.classList.remove("active");

        if (state === "select") stateSelect.classList.add("active");
        else if (state === "scanning") stateScanning.classList.add("active");
        else if (state === "results") stateResults.classList.add("active");
    }

    function showAlert(title, message, type = "warning") {
        globalAlert.className = "alert";
        if (type === "danger") globalAlert.classList.add("alert-danger");
        else if (type === "success") {
            globalAlert.classList.add("alert-success");
            // custom success colors
            globalAlert.style.backgroundColor = "var(--color-success-bg)";
            globalAlert.style.borderColor = "rgba(16, 185, 129, 0.3)";
            globalAlert.querySelector(".alert-icon").style.color = "var(--color-success)";
        }
        alertTitle.textContent = title;
        alertMessage.textContent = message;
        globalAlert.classList.remove("hidden");
    }

    function hideAlert() {
        globalAlert.classList.add("hidden");
    }

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
});

document.addEventListener("DOMContentLoaded", () => {
    // --- Translations ---
    const translations = {
        en: {
            brandSub: "VirusTotal Scanner",
            apiConfig: "API Configuration",
            apiKeyLabel: "VirusTotal API Key",
            apiKeyPlaceholder: "Enter API Key...",
            saveKey: "Save Key",
            savedLocally: "Saved locally in config file",
            settings: "Settings",
            useCli: "Use vt.exe CLI",
            useCliDesc: "Fallbacks to Direct API if missing",
            cliChecking: "Checking vt.exe...",
            cliFound: "vt.exe found in system",
            cliNotFound: "vt.exe not found",
            cliCheckFailed: "Check failed",
            cliDownloadTipPrefix: "To use CLI mode, download ",
            cliDownloadTipSuffix: " and place it in the application folder or PATH.",
            version: "Version 1.0.0",
            
            // Alerts
            alertWarning: "Warning",
            alertSuccess: "Success",
            alertDanger: "Error",
            alertInitTitle: "Configure API Key",
            alertInitMsg: "You need a free or premium VirusTotal API Key to scan files.",
            alertRequiredTitle: "Input Required",
            alertRequiredMsg: "API key cannot be empty.",
            alertSaveFailed: "Save Failed",
            alertSaveFailedMsg: "Failed to save key: ",
            alertSavedSuccess: "API Key saved successfully.",
            alertScanFailed: "Scan Failed",
            alertScanErrorMsg: "Unknown scan error occurred.",
            
            // Drop Zone / States
            dragDropTitle: "Drag & Drop File Here",
            dragDropDesc: "or click to browse your computer",
            selectFileBtn: "Select File",
            readingSize: "Reading file size...",
            calculatingHash: "Calculating fingerprint...",
            willCompute: "Will be computed on scan",
            startScanBtn: "Start Security Scan",
            
            // Scanning State
            scanningHeader: "Scanning Target",
            preparingFile: "Preparing file...",
            uploadingFile: "Uploading File",
            
            // Results State
            detectionRatio: "Detection Ratio",
            verdictClean: "CLEAN & SAFE",
            verdictCleanDesc: "All antivirus engines reported this file as harmless.",
            verdictSuspicious: "SUSPICIOUS",
            verdictSuspiciousDesc: "Flagged as suspicious by {count} engine{s}.",
            verdictDangerous: "DANGEROUS",
            verdictDangerousDesc: "Flagged as malicious by {count} engine{s}!",
            labelName: "Name:",
            labelSize: "Size:",
            labelHash: "SHA-256:",
            copied: "COPIED!",
            
            // Detections Table
            avDetections: "Antivirus Detections",
            flagsCount: "{count} flags",
            thEngine: "Antivirus Engine",
            thClass: "Threat Classification",
            thSeverity: "Severity",
            thMethod: "Method",
            allEnginesPassed: "All Engines Passed",
            cleanDesc: "The file is clean. VirusTotal analysis did not detect any known security threats.",
            scanAnother: "Scan Another File",
            viewReport: "View Full Report on VirusTotal",
            
            // Go Events Statuses
            "Calculating file SHA-256 hash...": "Calculating file SHA-256 hash...",
            "Checking if file was already analyzed...": "Checking if file was already analyzed...",
            "File already analyzed! Loading results...": "File already analyzed! Loading results...",
            "File not found in VirusTotal database. Uploading file...": "File not found in VirusTotal database. Uploading file...",
            "File is larger than 32MB. Requesting custom upload URL...": "File is larger than 32MB. Requesting custom upload URL...",
            "Upload finished! Waiting for analysis to complete...": "Upload finished! Waiting for analysis to complete...",
            "Analyzing on server": "Analyzing on server"
        },
        ru: {
            brandSub: "Сканер VirusTotal",
            apiConfig: "Настройка API",
            apiKeyLabel: "API-ключ VirusTotal",
            apiKeyPlaceholder: "Введите API-ключ...",
            saveKey: "Сохранить ключ",
            savedLocally: "Сохранено в конфигурационном файле",
            settings: "Настройки",
            useCli: "Использовать vt.exe CLI",
            useCliDesc: "Прямой API при отсутствии",
            cliChecking: "Проверка vt.exe...",
            cliFound: "vt.exe найден в системе",
            cliNotFound: "vt.exe не найден",
            cliCheckFailed: "Ошибка проверки",
            cliDownloadTipPrefix: "Чтобы использовать CLI-режим, скачайте ",
            cliDownloadTipSuffix: " и поместите его в папку приложения или PATH.",
            version: "Версия 1.0.0",
            
            // Alerts
            alertWarning: "Предупреждение",
            alertSuccess: "Успешно",
            alertDanger: "Ошибка",
            alertInitTitle: "Настройте API-ключ",
            alertInitMsg: "Вам нужен бесплатный или премиум API-ключ VirusTotal для сканирования файлов.",
            alertRequiredTitle: "Требуется ввод",
            alertRequiredMsg: "API-ключ не может быть пустым.",
            alertSaveFailed: "Ошибка сохранения",
            alertSaveFailedMsg: "Не удалось сохранить ключ: ",
            alertSavedSuccess: "API-ключ успешно сохранен.",
            alertScanFailed: "Ошибка сканирования",
            alertScanErrorMsg: "Произошла неизвестная ошибка при сканировании.",
            
            // Drop Zone / States
            dragDropTitle: "Перетащите файл сюда",
            dragDropDesc: "или кликните для выбора на компьютере",
            selectFileBtn: "Выбрать файл",
            readingSize: "Чтение размера файла...",
            calculatingHash: "Вычисление хеша...",
            willCompute: "Будет вычислено при сканировании",
            startScanBtn: "Запустить проверку",
            
            // Scanning State
            scanningHeader: "Сканирование цели",
            preparingFile: "Подготовка файла...",
            uploadingFile: "Загрузка файла",
            
            // Results State
            detectionRatio: "Доля детектов",
            verdictClean: "ЧИСТО И БЕЗОПАСНО",
            verdictCleanDesc: "Все антивирусные движки сообщили, что файл безвреден.",
            verdictSuspicious: "ПОДОЗРИТЕЛЬНО",
            verdictSuspiciousDesc: "Отмечен как подозрительный {count} антивирусом(ами).",
            verdictDangerous: "ОПАСНО",
            verdictDangerousDesc: "Отмечен как вредоносный {count} антивирусом(ами)!",
            labelName: "Имя:",
            labelSize: "Размер:",
            labelHash: "SHA-256:",
            copied: "СКОПИРОВАНО!",
            
            // Detections Table
            avDetections: "Детекты антивирусов",
            flagsCount: "{count} детектов",
            thEngine: "Антивирус",
            thClass: "Классификация угрозы",
            thSeverity: "Серьезность",
            thMethod: "Метод",
            allEnginesPassed: "Все проверки пройдены",
            cleanDesc: "Файл чист. Анализ VirusTotal не выявил известных угроз безопасности.",
            scanAnother: "Проверить другой файл",
            viewReport: "Полный отчет на VirusTotal",
            
            // Go Events Statuses
            "Calculating file SHA-256 hash...": "Вычисление SHA-256 хеша файла...",
            "Checking if file was already analyzed...": "Проверка наличия анализа файла...",
            "File already analyzed! Loading results...": "Файл уже анализировался! Загрузка результатов...",
            "File not found in VirusTotal database. Uploading file...": "Файл не найден в базе VirusTotal. Загрузка файла...",
            "File is larger than 32MB. Requesting custom upload URL...": "Файл больше 32 МБ. Запрос адреса для загрузки...",
            "Upload finished! Waiting for analysis to complete...": "Загрузка завершена! Ожидание окончания анализа...",
            "Analyzing on server": "Анализ на сервере"
        }
    };

    let currentLang = localStorage.getItem("lang") || "en";

    function t(key, variables = {}) {
        let str = (translations[currentLang] && translations[currentLang][key]) || (translations['en'] && translations['en'][key]) || key;
        for (const [k, v] of Object.entries(variables)) {
            str = str.replace(`{${k}}`, v);
        }
        return str;
    }

    function applyTranslations() {
        document.querySelectorAll("[data-i18n]").forEach(el => {
            const key = el.getAttribute("data-i18n");
            el.textContent = t(key);
        });

        const apiKeyInput = document.getElementById("api-key-input");
        if (apiKeyInput) {
            apiKeyInput.placeholder = t("apiKeyPlaceholder");
        }
    }

    function updateLanguage(lang) {
        currentLang = lang;
        localStorage.setItem("lang", lang);
        applyTranslations();
    }

    // --- Elements ---
    const apiKeyInput = document.getElementById("api-key-input");
    const saveKeyBtn = document.getElementById("save-key-btn");
    const toggleKeyVisibilityBtn = document.getElementById("toggle-key-visibility");
    const eyeIcon = document.getElementById("eye-icon");
    const useCliToggle = document.getElementById("use-cli-toggle");
    const cliStatusIndicator = document.getElementById("cli-status-indicator");
    const cliStatusText = cliStatusIndicator.querySelector(".status-text");
    const cliDownloadTip = document.getElementById("cli-download-tip");
    const githubLink = document.getElementById("github-link");
    const langToggleBtn = document.getElementById("lang-toggle-btn");

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
    const verdictTitle = document.getElementById("verdict-title");
    const verdictDesc = document.getElementById("verdict-desc");
    
    const resFilename = document.getElementById("res-filename");
    const resFilesize = document.getElementById("res-filesize");
    const resHash = document.getElementById("res-hash");
    
    const detectionsBadge = document.getElementById("detections-badge");
    const detectionsList = document.getElementById("detections-list");
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
        // Initialize Language
        updateLanguage(currentLang);

        // 1. Get and populate API Key
        try {
            const key = await window.go.main.App.GetApiKey();
            if (key) {
                apiKeyInput.value = key;
                hideAlert();
            } else {
                showAlert(t("alertInitTitle"), t("alertInitMsg"), "warning");
            }
        } catch (e) {
            console.error("Failed to fetch API key:", e);
        }

        // 2. Check Local CLI Preferences
        const useCLI = localStorage.getItem("useCLI") === "true";
        useCliToggle.checked = useCLI;
        if (useCLI) {
            cliStatusIndicator.classList.remove("hidden");
            checkCLIExecutable();
        }

        // 3. Check if launched with a file argument
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

    // Toggle Language
    langToggleBtn.addEventListener("click", () => {
        const nextLang = currentLang === "en" ? "ru" : "en";
        updateLanguage(nextLang);
    });

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
            showAlert(t("alertRequiredTitle"), t("alertRequiredMsg"), "danger");
            return;
        }
        try {
            const err = await window.go.main.App.SaveApiKey(key);
            if (err) {
                showAlert(t("alertSaveFailed"), t("alertSaveFailedMsg") + err, "danger");
            } else {
                showAlert(t("alertSuccess"), t("alertSavedSuccess"), "success");
                setTimeout(hideAlert, 3000);
            }
        } catch (e) {
            showAlert(t("alertSaveFailed"), t("alertSaveFailedMsg") + e, "danger");
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
        cliStatusText.textContent = t("cliChecking");
        cliDownloadTip.classList.add("hidden");

        try {
            const path = await window.go.main.App.CheckVTExecutable();
            if (path) {
                cliStatusIndicator.classList.add("found");
                cliStatusText.textContent = t("cliFound");
            } else {
                cliStatusIndicator.classList.add("missing");
                cliStatusText.textContent = t("cliNotFound");
                cliDownloadTip.classList.remove("hidden");
            }
        } catch (e) {
            cliStatusIndicator.classList.add("missing");
            cliStatusText.textContent = t("cliCheckFailed");
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
    });

    // --- File Selection Handler ---
    async function handleFileSelected(path) {
        selectedFilePath = path;
        const filename = path.replace(/^.*[\\\/]/, '');
        fileNameText.textContent = filename;
        fileSizeText.textContent = t("readingSize");
        fileHashText.textContent = t("calculatingHash");
        
        selectedFilePanel.classList.remove("hidden");
        
        try {
            const hash = await window.go.main.App.ComputeSHA256(path);
            fileHash = hash;
            fileHashText.textContent = hash;
        } catch (e) {
            fileHashText.textContent = t("willCompute");
        }
    }

    // --- Scan Actions ---
    startScanBtn.addEventListener("click", startScan);

    async function startScan() {
        if (!selectedFilePath) return;

        switchState("scanning");
        scanningHeader.textContent = t("scanningHeader");
        scanningStatus.textContent = t("preparingFile");
        uploadProgressContainer.classList.add("hidden");
        progressBarFill.style.width = "0%";
        progressPercent.textContent = "0%";
        progressBytes.textContent = "0 MB";

        const removeStatusListener = window.runtime.EventsOn("scan_status", (status) => {
            let translatedStatus = status;
            if (status.startsWith("Analyzing on server")) {
                const match = status.match(/Analyzing on server \((\d+)s elapsed\)\.\.\./);
                if (match) {
                    const sec = match[1];
                    translatedStatus = currentLang === 'ru' 
                        ? `Анализ на сервере (прошло ${sec} сек.)...`
                        : `Analyzing on server (${sec}s elapsed)...`;
                } else {
                    translatedStatus = t("Analyzing on server");
                }
            } else {
                translatedStatus = t(status);
            }
            scanningStatus.textContent = translatedStatus;
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
            showAlert(t("alertScanFailed"), e.message || e || t("alertScanErrorMsg"), "danger");
            switchState("select");
        }
    }

    // --- Display Results ---
    function showResults(result) {
        switchState("results");
        currentReportUrl = result.reportUrl;

        const stats = result.stats || {};
        const malicious = stats.malicious || 0;
        const suspicious = stats.suspicious || 0;
        const harmless = stats.harmless || 0;
        const undetected = stats.undetected || 0;
        const total = malicious + suspicious + harmless + undetected;
        
        detectionScore.textContent = `${malicious}/${total}`;
        
        const chart = document.querySelector(".circular-chart");
        chart.className = "circular-chart"; 
        
        const pct = total > 0 ? (malicious / total) * 100 : 0;
        gaugeFill.setAttribute("stroke-dasharray", `${pct}, 100`);

        verdictBanner.className = "verdict-card"; 
        if (malicious > 0) {
            chart.classList.add("danger");
            verdictBanner.classList.add("verdict-malicious");
            verdictTitle.textContent = t("verdictDangerous");
            verdictDesc.textContent = t("verdictDangerousDesc", { count: malicious, s: malicious > 1 ? 's' : '' });
            
            verdictBanner.querySelector(".verdict-icon").innerHTML = `
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" fill="none" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" stroke-width="2"/>
            `;
        } else if (suspicious > 0) {
            chart.classList.add("warning");
            verdictBanner.classList.add("verdict-suspicious");
            verdictTitle.textContent = t("verdictSuspicious");
            verdictDesc.textContent = t("verdictSuspiciousDesc", { count: suspicious, s: suspicious > 1 ? 's' : '' });
            
            verdictBanner.querySelector(".verdict-icon").innerHTML = `
                <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2"/>
            `;
        } else {
            verdictBanner.classList.add("verdict-clean");
            verdictTitle.textContent = t("verdictClean");
            verdictDesc.textContent = t("verdictCleanDesc");
            
            verdictBanner.querySelector(".verdict-icon").innerHTML = `
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" fill="none" stroke="currentColor" stroke-width="2"/>
                <polyline points="22 4 12 14.01 9 11.01" fill="none" stroke="currentColor" stroke-width="2"/>
            `;
        }

        resFilename.textContent = result.filename;
        resFilesize.textContent = formatBytes(result.size);
        resHash.textContent = result.hash;
        resHash.dataset.hash = result.hash;

        const detections = result.detections || [];
        detectionsBadge.textContent = t("flagsCount", { count: detections.length });
        
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
            resHash.textContent = t("copied");
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

package main

import (
	"bufio"
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/pkg/browser"
	"github.com/wailsapp/wails/v2/pkg/runtime"
)

type App struct {
	ctx         context.Context
	initialFile string
}

func NewApp(initialFile string) *App {
	return &App{
		initialFile: initialFile,
	}
}

func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	runtime.OnFileDrop(ctx, func(x, y int, paths []string) {
		if len(paths) > 0 {
			runtime.EventsEmit(ctx, "file_dropped", paths[0])
		}
	})
}

// GetInitialFile returns the file passed as command line argument, if any
func (a *App) GetInitialFile() string {
	return a.initialFile
}

// ComputeSHA256 calculates the SHA256 of the specified file and returns it
func (a *App) ComputeSHA256(filePath string) (string, error) {
	return computeSHA256(filePath)
}

// GetApiKey retrieves the API key from environment variables or ~/.vt.toml
func (a *App) GetApiKey() string {
	return getAPIKey()
}

// SaveApiKey saves the API key to ~/.vt.toml
func (a *App) SaveApiKey(key string) string {
	err := saveAPIKey(strings.TrimSpace(key))
	if err != nil {
		return err.Error()
	}
	return ""
}

// CheckVTExecutable checks if vt.exe is available and returns its path if found
func (a *App) CheckVTExecutable() string {
	return findVTExecutable()
}

// SelectFile opens a native open file dialog
func (a *App) SelectFile() (string, error) {
	file, err := runtime.OpenFileDialog(a.ctx, runtime.OpenDialogOptions{
		Title: "Select file to scan with VirusTotal",
	})
	if err != nil {
		return "", err
	}
	return file, nil
}

type Detection struct {
	Engine   string `json:"engine"`
	Category string `json:"category"`
	Result   string `json:"result"`
	Method   string `json:"method"`
}

type ScanResult struct {
	Hash       string            `json:"hash"`
	Filename   string            `json:"filename"`
	Size       int64             `json:"size"`
	Status     string            `json:"status"` // clean, suspicious, malicious, error
	Stats      map[string]int    `json:"stats"`
	Detections []Detection       `json:"detections"`
	ReportURL  string            `json:"reportUrl"`
	Message    string            `json:"message"`
}

// ScanFile performs the scan. It checks if the hash already exists on VT,
// if not, it uploads the file and polls until completion.
func (a *App) ScanFile(filePath string, useCLI bool) (*ScanResult, error) {
	if _, err := os.Stat(filePath); err != nil {
		return nil, fmt.Errorf("file not found: %w", err)
	}

	apiKey := getAPIKey()
	if apiKey == "" {
		return nil, fmt.Errorf("API key not configured")
	}

	runtime.EventsEmit(a.ctx, "scan_status", "Calculating file SHA-256 hash...")
	hash, err := computeSHA256(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to hash file: %w", err)
	}

	fi, err := os.Stat(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to stat file: %w", err)
	}
	fileSize := fi.Size()
	fileName := filepath.Base(filePath)

	runtime.EventsEmit(a.ctx, "scan_status", "Checking if file was already analyzed...")

	var stats map[string]int
	var results map[string]VTAnalysisItem
	var reportURL string
	found := false

	if useCLI {
		vtPath := findVTExecutable()
		if vtPath == "" {
			return nil, fmt.Errorf("vt.exe not found")
		}
		stats, results, err = checkFileExistsVT(vtPath, hash)
		if err == nil && stats != nil {
			found = true
			reportURL = fmt.Sprintf("https://www.virustotal.com/gui/file/%s", hash)
		}
	} else {
		res, err := checkFileExistsDirect(hash, apiKey)
		if err == nil && res != nil {
			found = true
			stats = res.Data.Attributes.LastAnalysisStats
			results = res.Data.Attributes.LastAnalysisResults
			reportURL = fmt.Sprintf("https://www.virustotal.com/gui/file/%s", hash)
		}
	}

	if found {
		runtime.EventsEmit(a.ctx, "scan_status", "File already analyzed! Loading results...")
		detections := makeDetections(results)
		status := determineStatus(stats)
		return &ScanResult{
			Hash:       hash,
			Filename:   fileName,
			Size:       fileSize,
			Status:     status,
			Stats:      stats,
			Detections: detections,
			ReportURL:  reportURL,
		}, nil
	}

	// Not analyzed yet. Let's upload.
	runtime.EventsEmit(a.ctx, "scan_status", "File not found in VirusTotal database. Uploading file...")

	var analysisID string
	if useCLI {
		vtPath := findVTExecutable()
		analysisID, err = uploadFileVT(vtPath, filePath)
		if err != nil {
			return nil, fmt.Errorf("failed to upload via vt.exe: %w", err)
		}
	} else {
		var uploadURL string = "https://www.virustotal.com/api/v3/files"
		if fileSize > 32*1024*1024 {
			runtime.EventsEmit(a.ctx, "scan_status", "File is larger than 32MB. Requesting custom upload URL...")
			uploadURL, err = a.getLargeFileUploadURL(apiKey)
			if err != nil {
				// Fallback to standard URL
				uploadURL = "https://www.virustotal.com/api/v3/files"
			}
		}
		analysisID, err = a.uploadFileDirect(filePath, apiKey, uploadURL)
		if err != nil {
			return nil, fmt.Errorf("failed to upload directly: %w", err)
		}
	}

	if analysisID == "" {
		return nil, fmt.Errorf("failed to get analysis ID")
	}

	if strings.HasPrefix(analysisID, "http") {
		reportURL = analysisID
		// Extract analysis ID from URL
		parts := strings.Split(analysisID, "/")
		analysisID = parts[len(parts)-1]
	} else {
		reportURL = fmt.Sprintf("https://www.virustotal.com/gui/file-analysis/%s", analysisID)
	}

	runtime.EventsEmit(a.ctx, "scan_status", "Upload finished! Waiting for analysis to complete...")

	// Poll analysis
	startTime := time.Now()
	for {
		// Stop if context canceled
		if a.ctx.Err() != nil {
			return nil, a.ctx.Err()
		}

		elapsed := int(time.Since(startTime).Seconds())
		runtime.EventsEmit(a.ctx, "scan_status", fmt.Sprintf("Analyzing on server (%ds elapsed)...", elapsed))

		var status string
		var finalStats map[string]int
		var finalResults map[string]VTAnalysisItem

		if useCLI {
			vtPath := findVTExecutable()
			status, finalStats, finalResults, err = checkAnalysisStatusVT(vtPath, analysisID)
		} else {
			var res *VTAnalysisResponse
			res, err = checkAnalysisStatusDirect(analysisID, apiKey)
			if err == nil && res != nil {
				status = res.Data.Attributes.Status
				finalStats = res.Data.Attributes.Stats
				finalResults = res.Data.Attributes.Results
			}
		}

		if err == nil && status == "completed" {
			detections := makeDetections(finalResults)
			statusStr := determineStatus(finalStats)
			// Keep the file report url instead of analysis url for completed scans
			finalReportURL := fmt.Sprintf("https://www.virustotal.com/gui/file/%s", hash)
			return &ScanResult{
				Hash:       hash,
				Filename:   fileName,
				Size:       fileSize,
				Status:     statusStr,
				Stats:      finalStats,
				Detections: detections,
				ReportURL:  finalReportURL,
			}, nil
		}

		time.Sleep(5 * time.Second)
	}
}

// OpenInBrowser opens the report URL in the default system browser
func (a *App) OpenInBrowser(url string) error {
	return browser.OpenURL(url)
}

func computeSHA256(filePath string) (string, error) {
	f, err := os.Open(filePath)
	if err != nil {
		return "", err
	}
	defer f.Close()

	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", err
	}
	return fmt.Sprintf("%x", h.Sum(nil)), nil
}

type progressReader struct {
	r       io.Reader
	total   int64
	read    int64
	ctx     context.Context
	lastPct int
}

func (pr *progressReader) Read(p []byte) (n int, err error) {
	n, err = pr.r.Read(p)
	if n > 0 {
		pr.read += int64(n)
		pct := int(float64(pr.read) / float64(pr.total) * 100)
		if pct > 100 {
			pct = 100
		}
		if pct != pr.lastPct {
			pr.lastPct = pct
			runtime.EventsEmit(pr.ctx, "upload_progress", map[string]interface{}{
				"percent": pct,
				"current": pr.read,
				"total":   pr.total,
			})
		}
	}
	return
}

func (a *App) getLargeFileUploadURL(apiKey string) (string, error) {
	req, err := http.NewRequestWithContext(a.ctx, "GET", "https://www.virustotal.com/api/v3/files/upload_url", nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("x-apikey", apiKey)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("failed to get upload URL: status %d", resp.StatusCode)
	}

	var res struct {
		Data string `json:"data"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&res); err != nil {
		return "", err
	}
	return res.Data, nil
}

func (a *App) uploadFileDirect(filePath string, apiKey string, uploadURL string) (string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	fi, err := file.Stat()
	if err != nil {
		return "", err
	}
	fileSize := fi.Size()

	var headerBuf bytes.Buffer
	tempWriter := multipart.NewWriter(&headerBuf)
	_, _ = tempWriter.CreateFormFile("file", filepath.Base(filePath))
	headerSize := int64(headerBuf.Len())

	var footerBuf bytes.Buffer
	footerWriter := multipart.NewWriter(&footerBuf)
	_ = footerWriter.SetBoundary(tempWriter.Boundary())
	_ = footerWriter.Close()
	footerSize := int64(footerBuf.Len())

	totalSize := headerSize + fileSize + footerSize

	pr, pw := io.Pipe()

	go func() {
		defer pw.Close()
		_, _ = pw.Write(headerBuf.Bytes())

		progReader := &progressReader{
			r:     file,
			total: fileSize,
			ctx:   a.ctx,
		}
		_, err := io.Copy(pw, progReader)
		if err != nil {
			_ = pw.CloseWithError(err)
			return
		}

		_, _ = pw.Write(footerBuf.Bytes())
	}()

	req, err := http.NewRequestWithContext(a.ctx, "POST", uploadURL, pr)
	if err != nil {
		return "", err
	}
	req.Header.Set("x-apikey", apiKey)
	req.Header.Set("Content-Type", tempWriter.FormDataContentType())
	req.ContentLength = totalSize

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("upload failed: status %d", resp.StatusCode)
	}

	var res struct {
		Data struct {
			ID string `json:"id"`
		} `json:"data"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&res); err != nil {
		return "", err
	}

	return res.Data.ID, nil
}

type VTFileResponse struct {
	Data struct {
		Attributes struct {
			LastAnalysisStats   map[string]int            `json:"last_analysis_stats"`
			LastAnalysisResults map[string]VTAnalysisItem `json:"last_analysis_results"`
		} `json:"attributes"`
	} `json:"data"`
}

type VTAnalysisItem struct {
	Category   string  `json:"category"`
	EngineName string  `json:"engine_name"`
	Method     string  `json:"method"`
	Result     *string `json:"result"`
	Version    string  `json:"version"`
}

type VTAnalysisResponse struct {
	Data struct {
		Attributes struct {
			Status  string                    `json:"status"`
			Stats   map[string]int            `json:"stats"`
			Results map[string]VTAnalysisItem `json:"results"`
		} `json:"attributes"`
	} `json:"data"`
}

func checkFileExistsDirect(sha256 string, apiKey string) (*VTFileResponse, error) {
	req, err := http.NewRequest("GET", "https://www.virustotal.com/api/v3/files/"+sha256, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("x-apikey", apiKey)
	req.Header.Set("User-Agent", "Mozilla/5.0")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 404 {
		return nil, nil // Not found
	}
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("status %d", resp.StatusCode)
	}

	var fileResp VTFileResponse
	if err := json.NewDecoder(resp.Body).Decode(&fileResp); err != nil {
		return nil, err
	}
	return &fileResp, nil
}

func checkAnalysisStatusDirect(analysisID string, apiKey string) (*VTAnalysisResponse, error) {
	req, err := http.NewRequest("GET", "https://www.virustotal.com/api/v3/analyses/"+analysisID, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("x-apikey", apiKey)
	req.Header.Set("User-Agent", "Mozilla/5.0")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("status %d", resp.StatusCode)
	}

	var analysisResp VTAnalysisResponse
	if err := json.NewDecoder(resp.Body).Decode(&analysisResp); err != nil {
		return nil, err
	}
	return &analysisResp, nil
}

func findVTExecutable() string {
	// check system path
	for _, exe := range []string{"vt", "vt.exe"} {
		if path, err := exec.LookPath(exe); err == nil {
			return path
		}
	}

	// check current folder
	for _, exe := range []string{"vt.exe", "vt"} {
		if _, err := os.Stat(exe); err == nil {
			if abs, err := filepath.Abs(exe); err == nil {
				return abs
			}
		}
	}

	// check AppData
	if appdata := os.Getenv("APPDATA"); appdata != "" {
		p := filepath.Join(appdata, "VirusTotalCLI", "vt.exe")
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}

	// check Home
	if home, err := os.UserHomeDir(); err == nil {
		p := filepath.Join(home, ".vt-cli", "vt.exe")
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}

	return ""
}

func getAPIKey() string {
	for _, varName := range []string{"VTCLI_APIKEY", "VT_APIKEY", "VIRUSTOTAL_API_KEY"} {
		if val := os.Getenv(varName); val != "" {
			return val
		}
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}

	tomlPath := filepath.Join(home, ".vt.toml")
	if _, err := os.Stat(tomlPath); err != nil {
		return ""
	}

	file, err := os.Open(tomlPath)
	if err != nil {
		return ""
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if strings.HasPrefix(line, "apikey") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				key := strings.TrimSpace(parts[1])
				key = strings.Trim(key, `"'`)
				return key
			}
		}
	}
	return ""
}

func saveAPIKey(key string) error {
	home, err := os.UserHomeDir()
	if err != nil {
		return err
	}
	tomlPath := filepath.Join(home, ".vt.toml")

	var lines []string
	keyWritten := false

	if _, err := os.Stat(tomlPath); err == nil {
		file, err := os.Open(tomlPath)
		if err == nil {
			scanner := bufio.NewScanner(file)
			for scanner.Scan() {
				line := scanner.Text()
				trimmed := strings.TrimSpace(line)
				if strings.HasPrefix(trimmed, "apikey") {
					lines = append(lines, fmt.Sprintf(`apikey = "%s"`, key))
					keyWritten = true
				} else {
					lines = append(lines, line)
				}
			}
			file.Close()
		}
	}

	if !keyWritten {
		lines = append(lines, fmt.Sprintf(`apikey = "%s"`, key))
	}

	return os.WriteFile(tomlPath, []byte(strings.Join(lines, "\n")+"\n"), 0600)
}

func checkFileExistsVT(vtPath string, sha256 string) (map[string]int, map[string]VTAnalysisItem, error) {
	cmd := exec.Command(vtPath, "file", sha256, "--format", "json")
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return nil, nil, err
	}

	var data interface{}
	if err := json.Unmarshal(stdout.Bytes(), &data); err != nil {
		return nil, nil, err
	}

	var fileObj map[string]interface{}
	if list, ok := data.([]interface{}); ok && len(list) > 0 {
		if first, ok := list[0].(map[string]interface{}); ok {
			fileObj = first
		}
	} else if obj, ok := data.(map[string]interface{}); ok {
		fileObj = obj
	}

	if fileObj == nil {
		return nil, nil, fmt.Errorf("invalid json output from vt CLI")
	}

	statsMap := make(map[string]int)
	if attrs, ok := fileObj["attributes"].(map[string]interface{}); ok {
		if stats, ok := attrs["last_analysis_stats"].(map[string]interface{}); ok {
			for k, v := range stats {
				if fl, ok := v.(float64); ok {
					statsMap[k] = int(fl)
				}
			}
		}

		resultsMap := make(map[string]VTAnalysisItem)
		if results, ok := attrs["last_analysis_results"].(map[string]interface{}); ok {
			for engine, resVal := range results {
				if itemMap, ok := resVal.(map[string]interface{}); ok {
					var item VTAnalysisItem
					if cat, ok := itemMap["category"].(string); ok {
						item.Category = cat
					}
					if eng, ok := itemMap["engine_name"].(string); ok {
						item.EngineName = eng
					}
					if meth, ok := itemMap["method"].(string); ok {
						item.Method = meth
					}
					if resStr, ok := itemMap["result"].(string); ok {
						item.Result = &resStr
					}
					if ver, ok := itemMap["version"].(string); ok {
						item.Version = ver
					}
					resultsMap[engine] = item
				}
			}
		}
		return statsMap, resultsMap, nil
	}

	return nil, nil, fmt.Errorf("stats not found in vt CLI output")
}

func uploadFileVT(vtPath string, filePath string) (string, error) {
	cmd := exec.Command(vtPath, "scan", "file", filePath)
	var stdout bytes.Buffer
	cmd.Stdout = &stdout
	if err := cmd.Run(); err != nil {
		return "", err
	}

	lines := strings.Split(strings.TrimSpace(stdout.String()), "\n")
	for _, line := range lines {
		if line == "" {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) >= 2 {
			// vt CLI scan file prints output like "analysis_id <id>" or similar,
			// or just the id at the end
			return parts[len(parts)-1], nil
		}
	}
	return "", fmt.Errorf("failed to parse analysis ID from vt CLI")
}

func checkAnalysisStatusVT(vtPath string, analysisID string) (string, map[string]int, map[string]VTAnalysisItem, error) {
	cmd := exec.Command(vtPath, "analysis", analysisID, "--format", "json")
	var stdout bytes.Buffer
	cmd.Stdout = &stdout
	if err := cmd.Run(); err != nil {
		return "", nil, nil, err
	}

	var data interface{}
	if err := json.Unmarshal(stdout.Bytes(), &data); err != nil {
		return "", nil, nil, err
	}

	var analysisObj map[string]interface{}
	if list, ok := data.([]interface{}); ok && len(list) > 0 {
		if first, ok := list[0].(map[string]interface{}); ok {
			analysisObj = first
		}
	} else if obj, ok := data.(map[string]interface{}); ok {
		analysisObj = obj
	}

	if analysisObj == nil {
		return "", nil, nil, fmt.Errorf("invalid json output from vt CLI")
	}

	var status string
	statsMap := make(map[string]int)
	resultsMap := make(map[string]VTAnalysisItem)

	if attrs, ok := analysisObj["attributes"].(map[string]interface{}); ok {
		if s, ok := attrs["status"].(string); ok {
			status = s
		}
		if stats, ok := attrs["stats"].(map[string]interface{}); ok {
			for k, v := range stats {
				if fl, ok := v.(float64); ok {
					statsMap[k] = int(fl)
				}
			}
		}
		if results, ok := attrs["results"].(map[string]interface{}); ok {
			for engine, resVal := range results {
				if itemMap, ok := resVal.(map[string]interface{}); ok {
					var item VTAnalysisItem
					if cat, ok := itemMap["category"].(string); ok {
						item.Category = cat
					}
					if eng, ok := itemMap["engine_name"].(string); ok {
						item.EngineName = eng
					}
					if meth, ok := itemMap["method"].(string); ok {
						item.Method = meth
					}
					if resStr, ok := itemMap["result"].(string); ok {
						item.Result = &resStr
					}
					if ver, ok := itemMap["version"].(string); ok {
						item.Version = ver
					}
					resultsMap[engine] = item
				}
			}
		}
	}

	return status, statsMap, resultsMap, nil
}

func makeDetections(results map[string]VTAnalysisItem) []Detection {
	var detections []Detection
	for engine, item := range results {
		if item.Category == "malicious" || item.Category == "suspicious" {
			resStr := ""
			if item.Result != nil {
				resStr = *item.Result
			}
			detections = append(detections, Detection{
				Engine:   engine,
				Category: item.Category,
				Result:   resStr,
				Method:   item.Method,
			})
		}
	}
	return detections
}

func determineStatus(stats map[string]int) string {
	if stats["malicious"] > 0 {
		return "malicious"
	}
	if stats["suspicious"] > 0 {
		return "suspicious"
	}
	return "clean"
}

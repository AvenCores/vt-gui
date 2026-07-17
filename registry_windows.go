//go:build windows

package main

import (
	"os"

	"golang.org/x/sys/windows/registry"
)

func (a *App) RegisterContextMenu() string {
	exePath, err := os.Executable()
	if err != nil {
		return err.Error()
	}

	key, _, err := registry.CreateKey(registry.CURRENT_USER, `Software\Classes\*\shell\VirusTotalScan`, registry.ALL_ACCESS)
	if err != nil {
		return err.Error()
	}
	defer key.Close()

	if err := key.SetStringValue("", "&Scan with VirusTotal"); err != nil {
		return err.Error()
	}
	if err := key.SetStringValue("Icon", "shell32.dll,224"); err != nil {
		return err.Error()
	}

	cmdKey, _, err := registry.CreateKey(registry.CURRENT_USER, `Software\Classes\*\shell\VirusTotalScan\command`, registry.ALL_ACCESS)
	if err != nil {
		return err.Error()
	}
	defer cmdKey.Close()

	commandStr := `"` + exePath + `" "%1"`
	if err := cmdKey.SetStringValue("", commandStr); err != nil {
		return err.Error()
	}

	return ""
}

func (a *App) UnregisterContextMenu() string {
	err := registry.DeleteKey(registry.CURRENT_USER, `Software\Classes\*\shell\VirusTotalScan\command`)
	if err != nil && err != registry.ErrNotExist {
		return err.Error()
	}

	err = registry.DeleteKey(registry.CURRENT_USER, `Software\Classes\*\shell\VirusTotalScan`)
	if err != nil && err != registry.ErrNotExist {
		return err.Error()
	}

	return ""
}

func (a *App) IsContextMenuRegistered() bool {
	key, err := registry.OpenKey(registry.CURRENT_USER, `Software\Classes\*\shell\VirusTotalScan\command`, registry.QUERY_VALUE)
	if err != nil {
		return false
	}
	defer key.Close()
	return true
}

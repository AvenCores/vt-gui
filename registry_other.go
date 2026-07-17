//go:build !windows

package main

func (a *App) RegisterContextMenu() string {
	return "Context menu is only supported on Windows"
}

func (a *App) UnregisterContextMenu() string {
	return "Context menu is only supported on Windows"
}

func (a *App) IsContextMenuRegistered() bool {
	return false
}

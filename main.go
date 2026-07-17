package main

import (
	"embed"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
)

//go:embed all:frontend/dist
var assets embed.FS

func main() {
	var initialFile string
	if len(os.Args) > 1 {
		arg := os.Args[1]
		if !strings.HasPrefix(arg, "-") {
			if _, err := os.Stat(arg); err == nil {
				if abs, err := filepath.Abs(arg); err == nil {
					initialFile = abs
				}
			}
		}
	}

	app := NewApp(initialFile)

	err := wails.Run(&options.App{
		Title:  "VirusTotal File Scanner",
		Width:  1080,
		Height: 800,
		AssetServer: &assetserver.Options{
			Assets: assets,
		},
		BackgroundColour: &options.RGBA{R: 15, G: 23, B: 42, A: 1}, // Sleek dark slate
		OnStartup:        app.startup,
		Bind: []interface{}{
			app,
		},
		DragAndDrop: &options.DragAndDrop{
			EnableFileDrop: true,
		},
	})

	if err != nil {
		fmt.Println("Error running application:", err)
	}
}

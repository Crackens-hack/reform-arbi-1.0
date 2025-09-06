package main

import (
	"fmt"
	"time"

	"github.com/fatih/color"
)

func main() {
	counter := 1

	green := color.New(color.FgGreen).SprintFunc()
	red := color.New(color.FgRed).SprintFunc()

	for {
		// alterna entre verde y rojo
		colorize := green
		if counter%2 == 0 {
			colorize = red
		}

		// sobrescribe en la misma línea
		fmt.Printf("\r%sHola Dominus 🚀 → Contador: %d", colorize(""), counter)

		counter++
		time.Sleep(1 * time.Second)
	}
}

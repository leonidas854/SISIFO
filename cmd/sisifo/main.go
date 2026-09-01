// sisifo es el punto de entrada único del taller académico. El ensamblaje vive
// aquí; las reglas están en aplicación y los efectos en adaptadores.
package main

import (
	"context"
	"os"

	"github.com/leonidas854/sisifo/internal/adaptadores/terminal"
	"github.com/leonidas854/sisifo/internal/aplicacion"
)

func main() {
	ejecutor := terminal.NuevoEjecutor(os.Stdin, os.Stdout, os.Stderr)
	servicio := aplicacion.NuevoServicio(ejecutor)
	tui := terminal.NuevaTUI(servicio, os.Stdin, os.Stdout, os.Stderr)
	cli := terminal.NuevaCLI(
		servicio,
		tui,
		os.Stdout,
		os.Stderr,
		terminal.EsTerminal(os.Stdin) && terminal.EsTerminal(os.Stdout),
	)
	os.Exit(cli.Ejecutar(context.Background(), os.Args[1:]))
}

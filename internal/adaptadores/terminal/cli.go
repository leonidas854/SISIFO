// Package terminal implementa los adaptadores de entrada y salida para una
// terminal. La aplicación permanece ajena a os.Exit y a los procesos externos.
package terminal

import (
	"context"
	"fmt"
	"io"
	"os"

	"github.com/leonidas854/sisifo/internal/aplicacion"
)

// Aplicacion es el puerto de entrada que comparten CLI y TUI.
type Aplicacion interface {
	Ejecutar(context.Context, []string) aplicacion.Resultado
	Catalogo() aplicacion.Catalogo
	Ayuda() string
}

// InterfazInteractiva permite probar la selección automática de la TUI sin
// abrir procesos ni depender de una terminal real.
type InterfazInteractiva interface {
	Ejecutar(context.Context) int
}

type CLI struct {
	aplicacion  Aplicacion
	tui         InterfazInteractiva
	salida      io.Writer
	errores     io.Writer
	interactiva bool
}

func NuevaCLI(
	app Aplicacion,
	tui InterfazInteractiva,
	salida, errores io.Writer,
	interactiva bool,
) *CLI {
	return &CLI{
		aplicacion:  app,
		tui:         tui,
		salida:      salida,
		errores:     errores,
		interactiva: interactiva,
	}
}

func (c *CLI) Ejecutar(ctx context.Context, argumentos []string) int {
	if len(argumentos) == 0 {
		if c.interactiva {
			return c.ejecutarTUI(ctx)
		}
		fmt.Fprintln(c.salida, c.aplicacion.Ayuda())
		return 0
	}

	switch argumentos[0] {
	case "-h", "--help", "ayuda":
		fmt.Fprintln(c.salida, c.aplicacion.Ayuda())
		return 0
	case "tui":
		return c.ejecutarTUI(ctx)
	}

	resultado := c.aplicacion.Ejecutar(ctx, argumentos)
	c.mostrarError(resultado)
	return resultado.Codigo
}

func (c *CLI) ejecutarTUI(ctx context.Context) int {
	if c.tui == nil {
		fmt.Fprintln(c.errores, "error: la interfaz interactiva no está configurada")
		return 1
	}
	return c.tui.Ejecutar(ctx)
}

func (c *CLI) mostrarError(resultado aplicacion.Resultado) {
	if resultado.Err == nil {
		return
	}
	fmt.Fprintln(c.errores, "error:", resultado.Err)
	if resultado.MostrarAyuda {
		fmt.Fprintln(c.errores)
		fmt.Fprintln(c.errores, c.aplicacion.Ayuda())
	}
}

// EsTerminal detecta descriptores conectados a un dispositivo de caracteres.
// Se mantiene aquí para que main solo ensamble adaptadores.
func EsTerminal(archivo *os.File) bool {
	if archivo == nil {
		return false
	}
	informacion, err := archivo.Stat()
	return err == nil && informacion.Mode()&os.ModeCharDevice != 0
}

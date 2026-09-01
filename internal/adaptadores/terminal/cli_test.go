package terminal

import (
	"bytes"
	"context"
	"strings"
	"testing"

	"github.com/leonidas854/sisifo/internal/aplicacion"
	"github.com/leonidas854/sisifo/internal/dominio"
)

type aplicacionFalsa struct {
	servicio *aplicacion.Servicio
	ejecutor *ejecutorFalso
}

type ejecutorFalso struct {
	llamadas [][]string
}

func (e *ejecutorFalso) Ejecutar(_ context.Context, invocacion dominioInvocacion) aplicacion.Resultado {
	e.llamadas = append(e.llamadas, append([]string{invocacion.Comando}, invocacion.Argumentos...))
	return aplicacion.Resultado{}
}

// dominioInvocacion se declara como alias abajo para que el falso implemente
// exactamente el puerto sin introducir un ejecutor de procesos.
type dominioInvocacion = dominio.Invocacion

func nuevaAplicacionFalsa() *aplicacionFalsa {
	ejecutor := &ejecutorFalso{}
	return &aplicacionFalsa{
		servicio: aplicacion.NuevoServicio(ejecutor),
		ejecutor: ejecutor,
	}
}

func (a *aplicacionFalsa) Ejecutar(ctx context.Context, args []string) aplicacion.Resultado {
	return a.servicio.Ejecutar(ctx, args)
}

func (a *aplicacionFalsa) Catalogo() aplicacion.Catalogo { return a.servicio.Catalogo() }
func (a *aplicacionFalsa) Ayuda() string                 { return a.servicio.Ayuda() }

type tuiFalsa struct{ llamadas int }

func (t *tuiFalsa) Ejecutar(context.Context) int {
	t.llamadas++
	return 0
}

func TestCLISinArgumentosAbreTUISoloSiEsInteractiva(t *testing.T) {
	app := nuevaAplicacionFalsa()
	interfaz := &tuiFalsa{}
	var salida, errores bytes.Buffer
	cli := NuevaCLI(app, interfaz, &salida, &errores, true)

	if codigo := cli.Ejecutar(context.Background(), nil); codigo != 0 {
		t.Fatalf("código: %d", codigo)
	}
	if interfaz.llamadas != 1 {
		t.Fatalf("la TUI recibió %d llamadas", interfaz.llamadas)
	}
	if len(app.ejecutor.llamadas) != 0 {
		t.Fatal("abrir la TUI no debe ejecutar una orden")
	}
}

func TestCLISinArgumentosNoInteractivaMuestraAyuda(t *testing.T) {
	app := nuevaAplicacionFalsa()
	interfaz := &tuiFalsa{}
	var salida, errores bytes.Buffer
	cli := NuevaCLI(app, interfaz, &salida, &errores, false)

	cli.Ejecutar(context.Background(), nil)

	if interfaz.llamadas != 0 {
		t.Fatal("una tubería no debe abrir la TUI automáticamente")
	}
	if !strings.Contains(salida.String(), "sisifo tui") {
		t.Fatalf("no mostró ayuda: %s", salida.String())
	}
}

func TestCLIExplicitaAbreTUIAunqueLaEntradaEsteRedirigida(t *testing.T) {
	app := nuevaAplicacionFalsa()
	interfaz := &tuiFalsa{}
	cli := NuevaCLI(app, interfaz, &bytes.Buffer{}, &bytes.Buffer{}, false)

	cli.Ejecutar(context.Background(), []string{"tui"})

	if interfaz.llamadas != 1 {
		t.Fatal("sisifo tui debe ser explícito y funcionar con entrada redirigida")
	}
}

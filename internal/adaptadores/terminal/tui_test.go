package terminal

import (
	"bytes"
	"context"
	"reflect"
	"strings"
	"testing"
)

func TestTUIMuestraCategoriasYLanzaElMismoCasoDeUso(t *testing.T) {
	app := nuevaAplicacionFalsa()
	entrada := strings.NewReader("1\n2\n\"ética de IA\" --n 5\nq\n")
	var salida, errores bytes.Buffer
	tui := NuevaTUI(app, entrada, &salida, &errores)

	if codigo := tui.Ejecutar(context.Background()); codigo != 0 {
		t.Fatalf("código: %d; errores: %s", codigo, errores.String())
	}
	quiere := [][]string{{"buscar", "ética de IA", "--n", "5"}}
	if !reflect.DeepEqual(app.ejecutor.llamadas, quiere) {
		t.Fatalf("invocaciones: %#v; quiere %#v", app.ejecutor.llamadas, quiere)
	}
	for _, nombre := range []string{
		"Investigación", "Producción", "Visuales", "Medios",
		"Verificación", "Configuración", "Doctor",
	} {
		if !strings.Contains(salida.String(), nombre) {
			t.Errorf("el menú no muestra %q", nombre)
		}
	}
}

func TestTUISalirNoEjecutaNada(t *testing.T) {
	app := nuevaAplicacionFalsa()
	tui := NuevaTUI(app, strings.NewReader("q\n"), &bytes.Buffer{}, &bytes.Buffer{})

	if codigo := tui.Ejecutar(context.Background()); codigo != 0 {
		t.Fatalf("código: %d", codigo)
	}
	if len(app.ejecutor.llamadas) != 0 {
		t.Fatal("salir del menú ejecutó una orden")
	}
}

func TestTUIVisualUsaLaOrdenCanonica(t *testing.T) {
	app := nuevaAplicacionFalsa()
	entrada := strings.NewReader("3\n2\n\nq\n")
	tui := NuevaTUI(app, entrada, &bytes.Buffer{}, &bytes.Buffer{})

	if codigo := tui.Ejecutar(context.Background()); codigo != 0 {
		t.Fatalf("código: %d", codigo)
	}
	quiere := [][]string{{"visual", "validar"}}
	if !reflect.DeepEqual(app.ejecutor.llamadas, quiere) {
		t.Fatalf("invocaciones: %#v; quiere %#v", app.ejecutor.llamadas, quiere)
	}
}

func TestParsearArgumentosSinEvaluarShell(t *testing.T) {
	obtuvo, err := ParsearArgumentos(`"tema con espacios" '--literal $HOME' x\ y`)
	if err != nil {
		t.Fatal(err)
	}
	quiere := []string{"tema con espacios", "--literal $HOME", "x y"}
	if !reflect.DeepEqual(obtuvo, quiere) {
		t.Fatalf("obtuvo %#v; quiere %#v", obtuvo, quiere)
	}
}

func TestParsearArgumentosRechazaComillaAbierta(t *testing.T) {
	if _, err := ParsearArgumentos(`"sin cerrar`); err == nil {
		t.Fatal("debe rechazar una comilla abierta")
	}
}

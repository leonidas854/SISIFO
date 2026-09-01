package terminal

import (
	"reflect"
	"slices"
	"testing"
)

func TestPrepararArgumentosVisualInsertaCarpetaTrasSubcomando(t *testing.T) {
	obtuvo := prepararArgumentosVisual(
		[]string{"auditar", "--pptx", "salida/exposicion.pptx"},
		"/tmp/trabajo",
	)
	quiere := []string{
		"auditar", "--carpeta", "/tmp/trabajo",
		"--pptx", "salida/exposicion.pptx",
	}
	if !reflect.DeepEqual(obtuvo, quiere) {
		t.Fatalf("obtuvo %#v; quiere %#v", obtuvo, quiere)
	}
}

func TestPrepararArgumentosVisualNoResuelveTrabajoParaAyuda(t *testing.T) {
	argumentos := []string{"plan", "--help"}
	obtuvo := prepararArgumentosVisual(argumentos, "/tmp/trabajo")
	if !reflect.DeepEqual(obtuvo, argumentos) {
		t.Fatalf("la ayuda fue alterada: %#v", obtuvo)
	}
}

func TestPrepararArgumentosVisualRespetaCarpetaExplicita(t *testing.T) {
	argumentos := []string{"validar", "--carpeta=/otra"}
	obtuvo := prepararArgumentosVisual(argumentos, "/tmp/trabajo")
	if !reflect.DeepEqual(obtuvo, argumentos) {
		t.Fatalf("la carpeta explícita fue alterada: %#v", obtuvo)
	}
}

func TestEntornoMotorSincronizaNombreNuevoYLegado(t *testing.T) {
	obtuvo := entornoMotor(
		[]string{"PATH=/bin", "SISIFO_HOME=/viejo", "TALLER_HOME=/mas-viejo"},
		"/motor/activo",
	)
	for _, quiere := range []string{
		"PATH=/bin", "SISIFO_HOME=/motor/activo", "TALLER_HOME=/motor/activo",
	} {
		if !slices.Contains(obtuvo, quiere) {
			t.Errorf("falta %q en %#v", quiere, obtuvo)
		}
	}
	if slices.Contains(obtuvo, "SISIFO_HOME=/viejo") || slices.Contains(obtuvo, "TALLER_HOME=/mas-viejo") {
		t.Fatalf("sobrevivió una configuración cruzada: %#v", obtuvo)
	}
}

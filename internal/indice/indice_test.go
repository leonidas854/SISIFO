package indice

import (
	"strings"
	"testing"
)

func TestTrocearCorto(t *testing.T) {
	if got := Trocear("hola mundo"); len(got) != 1 || got[0] != "hola mundo" {
		t.Fatalf("un texto corto debe salir en un solo fragmento, salió %v", got)
	}
	if got := Trocear("   "); got != nil {
		t.Fatalf("el texto vacío no debe producir fragmentos, salió %v", got)
	}
}

func TestTrocearLargoNoPartePalabras(t *testing.T) {
	texto := strings.Repeat("palabra ", 900) // ~7200 caracteres
	trozos := Trocear(texto)
	if len(trozos) < 2 {
		t.Fatalf("se esperaban varios fragmentos, salió %d", len(trozos))
	}
	for i, tr := range trozos {
		if tr == "" {
			t.Fatalf("fragmento %d vacío", i)
		}
		// ningún fragmento debe empezar o acabar cortando "palabra"
		for _, p := range strings.Fields(tr) {
			if p != "palabra" {
				t.Fatalf("fragmento %d partió una palabra: %q", i, p)
			}
		}
	}
}

func TestTrocearCubreTodoElTexto(t *testing.T) {
	texto := strings.Repeat("alfa beta gamma delta ", 200)
	trozos := Trocear(texto)
	unido := strings.Join(trozos, " ")
	// con solape el resultado es más largo, pero no puede perder contenido
	if len(unido) < len(strings.Join(strings.Fields(texto), " ")) {
		t.Fatalf("el troceado perdió texto: %d < %d", len(unido), len(texto))
	}
}

func TestCoseno(t *testing.T) {
	a := []float32{1, 0, 0}
	casos := []struct {
		nombre string
		b      []float32
		quiero float64
	}{
		{"idéntico", []float32{1, 0, 0}, 1},
		{"ortogonal", []float32{0, 1, 0}, 0},
		{"opuesto", []float32{-1, 0, 0}, -1},
		{"escalado", []float32{5, 0, 0}, 1},
	}
	for _, c := range casos {
		if got := coseno(a, c.b); got < c.quiero-1e-6 || got > c.quiero+1e-6 {
			t.Errorf("%s: quiero %.2f, obtuve %.4f", c.nombre, c.quiero, got)
		}
	}
	if got := coseno(a, []float32{1, 0}); got != 0 {
		t.Errorf("dimensiones distintas deben dar 0, dio %v", got)
	}
	if got := coseno([]float32{0, 0, 0}, a); got != 0 {
		t.Errorf("el vector nulo debe dar 0, dio %v", got)
	}
}

package dominio

import "testing"

func TestGuionValidaBloques(t *testing.T) {
	casos := []struct {
		nombre string
		b      Bloque
		valido bool
	}{
		{"título con nivel", Bloque{Clase: Titulo, Nivel: 1, Texto: "Intro"}, true},
		{"título sin texto", Bloque{Clase: Titulo, Nivel: 1}, false},
		{"título con nivel fuera de rango", Bloque{Clase: Titulo, Nivel: 9, Texto: "x"}, false},
		{"párrafo", Bloque{Clase: Parrafo, Texto: "algo"}, true},
		{"tabla con filas", Bloque{Clase: Tabla, Cabecera: []string{"a"},
			Filas: [][]string{{"1"}}}, true},
		{"tabla con fila descuadrada", Bloque{Clase: Tabla, Cabecera: []string{"a", "b"},
			Filas: [][]string{{"1"}}}, false},
		{"figura sin ruta", Bloque{Clase: Figura, Leyenda: "x"}, false},
		{"clase inventada", Bloque{Clase: "chirimoya", Texto: "x"}, false},
	}
	for _, c := range casos {
		err := c.b.Validar()
		if (err == nil) != c.valido {
			t.Errorf("%s: válido=%v, err=%v", c.nombre, c.valido, err)
		}
	}
}

// Un guion no puede citar una clave que no está en la bibliografía: es
// exactamente el error que produce una bibliografía inventada.
func TestGuionRechazaCitaFueraDeLaBibliografia(t *testing.T) {
	g := Guion{
		Tipo:   "docx",
		Titulo: "T",
		Bloques: []Bloque{
			{Clase: Parrafo, Texto: "Algo", Citas: []string{"existe"}},
			{Clase: Parrafo, Texto: "Otro", Citas: []string{"fantasma"}},
		},
	}
	disponibles := map[string]bool{"existe": true}
	err := g.Validar(disponibles)
	if err == nil {
		t.Fatal("citar una clave inexistente tiene que fallar")
	}
}

func TestGuionValidoPasa(t *testing.T) {
	g := Guion{Tipo: "docx", Titulo: "T", Bloques: []Bloque{
		{Clase: Titulo, Nivel: 1, Texto: "Introducción"},
		{Clase: Parrafo, Texto: "Texto", Citas: []string{"k"}},
		{Clase: Bibliografia},
	}}
	if err := g.Validar(map[string]bool{"k": true}); err != nil {
		t.Fatalf("debería ser válido: %v", err)
	}
}

func TestGuionExigeTipoConocido(t *testing.T) {
	g := Guion{Tipo: "jeroglifico", Titulo: "T",
		Bloques: []Bloque{{Clase: Parrafo, Texto: "x"}}}
	if err := g.Validar(nil); err == nil {
		t.Fatal("un tipo de salida desconocido tiene que fallar")
	}
}

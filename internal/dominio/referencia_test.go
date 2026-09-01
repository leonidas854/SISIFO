package dominio

import "testing"

// Una referencia solo puede citarse si su identificador se comprobó contra un
// registro real. Esta es la regla que impide publicar una cita inventada.
func TestCitabilidadSegunEstado(t *testing.T) {
	casos := []struct {
		estado  EstadoVerificacion
		manual  bool
		citable bool
		porque  string
	}{
		{Verificada, false, true, "el DOI resuelve y el título coincide"},
		{NoVerificada, false, false, "todavía no se comprobó"},
		{NoExiste, false, false, "el DOI no está en ningún registro"},
		{NoCoincide, false, false, "el DOI es de otro trabajo"},
		{SinDOI, false, false, "sin DOI y sin confirmar a mano"},
		{SinDOI, true, true, "sin DOI pero confirmada a mano (libro, norma)"},
		{NoExiste, true, false, "confirmar a mano no resucita un DOI inexistente"},
		{NoCoincide, true, false, "confirmar a mano no arregla una atribución falsa"},
	}
	for _, c := range casos {
		r := Referencia{Clave: "x", Estado: c.estado, ConfirmadaAMano: c.manual}
		if got := r.Citable(); got != c.citable {
			t.Errorf("estado %s, manual %v: quiero citable=%v (%s), obtuve %v",
				c.estado, c.manual, c.citable, c.porque, got)
		}
	}
}

func TestTitulosCoinciden(t *testing.T) {
	casos := []struct {
		nombre   string
		a, b     string
		coincide bool
	}{
		{"idénticos", "Chain of Custody", "Chain of Custody", true},
		{"mayúsculas y tildes", "Análisis Forense", "analisis forense", true},
		{"puntuación distinta", "B-CoC: A Blockchain Model", "B CoC A Blockchain Model", true},
		{"subtítulo añadido", "Digital Evidence Chain of Custody",
			"Digital Evidence Chain of Custody: Navigating New Realities", true},
		{"trabajos distintos", "Chain of custody in digital forensics",
			"Nanometre-scale thermometry in a living cell", false},
		{"uno vacío", "", "Cualquier cosa", false},
		{"ambos vacíos", "", "", false},
	}
	for _, c := range casos {
		if got := TitulosCoinciden(c.a, c.b); got != c.coincide {
			t.Errorf("%s: quiero %v, obtuve %v", c.nombre, c.coincide, got)
		}
	}
}

func TestReferenciaExigeClave(t *testing.T) {
	if err := (Referencia{Titulo: "algo"}).Validar(); err == nil {
		t.Error("una referencia sin clave no debe validar: no se podría citar")
	}
	if err := (Referencia{Clave: "k"}).Validar(); err == nil {
		t.Error("una referencia sin título no debe validar")
	}
	if err := (Referencia{Clave: "k", Titulo: "t"}).Validar(); err != nil {
		t.Errorf("clave y título deberían bastar: %v", err)
	}
}

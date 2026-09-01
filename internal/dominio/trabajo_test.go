package dominio

import "testing"

func trabajoDemo() Trabajo {
	return Trabajo{
		Slug: "tesis",
		Ruta: "/tmp/tesis",
		Entregables: []Entregable{
			{Ruta: "salida/tesis.docx", Tipo: "docx", Minimo: 40},
		},
		CriteriosManuales: []string{"revisado por mí"},
	}
}

func TestTrabajoNoListoSiFaltaTamano(t *testing.T) {
	tr := trabajoDemo()
	inf := tr.Evaluar(EstadoEntrega{
		Producidos: map[string]int{"salida/tesis.docx": 12},
	})
	if inf.Listo() {
		t.Fatal("12 páginas cuando el brief pide 40 no puede estar listo")
	}
	if len(inf.Bloqueantes) != 1 {
		t.Fatalf("quiero 1 bloqueante, hay %d: %v", len(inf.Bloqueantes), inf.Bloqueantes)
	}
}

func TestTrabajoNoListoSiFaltaEntregable(t *testing.T) {
	inf := trabajoDemo().Evaluar(EstadoEntrega{Producidos: map[string]int{}})
	if inf.Listo() {
		t.Fatal("sin el entregable no puede estar listo")
	}
}

func TestTrabajoNoListoConAfirmacionSinRespaldo(t *testing.T) {
	inf := trabajoDemo().Evaluar(EstadoEntrega{
		Producidos:   map[string]int{"salida/tesis.docx": 45},
		Afirmaciones: []Afirmacion{{ID: "a1", Texto: "El 87% falla."}},
	})
	if inf.Listo() {
		t.Fatal("una cifra sin fuente tiene que impedir la entrega")
	}
}

func TestTrabajoNoListoConReferenciaInventada(t *testing.T) {
	inf := trabajoDemo().Evaluar(EstadoEntrega{
		Producidos: map[string]int{"salida/tesis.docx": 45},
		Referencias: []Referencia{
			{Clave: "bueno", Titulo: "T", Estado: Verificada},
			{Clave: "falso", Titulo: "T", Estado: NoExiste},
		},
	})
	if inf.Listo() {
		t.Fatal("una referencia inexistente tiene que impedir la entrega")
	}
}

// Todo bien salvo lo que solo puede confirmar una persona: el sistema no debe
// declararlo listo por su cuenta, pero tampoco tratarlo como un fallo.
func TestCriteriosManualesQuedanPendientesNoFallidos(t *testing.T) {
	inf := trabajoDemo().Evaluar(EstadoEntrega{
		Producidos:  map[string]int{"salida/tesis.docx": 45},
		Referencias: []Referencia{{Clave: "k", Titulo: "T", Estado: Verificada}},
	})
	if len(inf.Bloqueantes) != 0 {
		t.Fatalf("no debería haber bloqueantes: %v", inf.Bloqueantes)
	}
	if !inf.Listo() {
		t.Error("sin bloqueantes, lo automático está listo")
	}
	if len(inf.Pendientes) == 0 {
		t.Error("los criterios manuales tienen que aparecer como pendientes")
	}
	if inf.Confirmado() {
		t.Error("no puede darse por confirmado sin que la persona lo confirme")
	}
}

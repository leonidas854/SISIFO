package dominio

import "testing"

// El corazón del sistema: una afirmación con dato necesita fuente y cita
// literal, y la cita tiene que aparecer de verdad en el texto de esa fuente.
func TestAfirmacionConCifraExigeFuente(t *testing.T) {
	sinFuente := Afirmacion{ID: "a1", Texto: "El 87% de los casos presentan ruptura."}
	if p := sinFuente.Problema(); p == nil {
		t.Fatal("una cifra sin fuente debe ser un problema")
	} else if !p.Bloqueante {
		t.Error("una cifra sin fuente tiene que bloquear la entrega")
	}

	prosa := Afirmacion{ID: "a2", Texto: "La cadena de custodia es central en el proceso."}
	if p := prosa.Problema(); p != nil && p.Bloqueante {
		t.Errorf("la prosa sin cifras no debe bloquear: %v", p)
	}
}

func TestDetectaDatosQueExigenRespaldo(t *testing.T) {
	casos := []struct {
		texto string
		exige bool
	}{
		{"El 87% de los casos", true},
		{"Según la norma 27037", true},
		{"En 2019 se aprobó la reforma", true},
		{"La evidencia debe preservarse íntegra", false},
		{"El procedimiento es claro y ordenado", false},
	}
	for _, c := range casos {
		if got := ExigeRespaldo(c.texto); got != c.exige {
			t.Errorf("%q: quiero exige=%v, obtuve %v", c.texto, c.exige, got)
		}
	}
}

func TestAfirmacionConFuenteExigeCita(t *testing.T) {
	a := Afirmacion{ID: "a3", Texto: "El 40% falla.", Fuente: "nath2024"}
	p := a.Problema()
	if p == nil || !p.Bloqueante {
		t.Fatal("declarar fuente sin cita literal tiene que bloquear")
	}
}

func TestCitaSeHallaEnElTexto(t *testing.T) {
	documento := `El Oficial de Seguridad de la Información es responsable de
	tener el implemento adecuado para el tratamiento de evidencia física.`

	casos := []struct {
		nombre string
		cita   string
		halla  bool
	}{
		{"literal exacta", "es responsable de tener el implemento adecuado", true},
		{"con tildes y mayúsculas distintas", "ES RESPONSABLE DE TENER EL IMPLEMENTO", true},
		{"con espacios y saltos", "responsable  de\ttener   el implemento", true},
		{"inventada", "deberá conservarse por un periodo mínimo de diez años", false},
		{"vacía", "", false},
	}
	for _, c := range casos {
		hallada, _ := HallarCita(c.cita, documento)
		if hallada != c.halla {
			t.Errorf("%s: quiero hallada=%v, obtuve %v", c.nombre, c.halla, hallada)
		}
	}
}

func TestHallarCitaDevuelveParecidoUtil(t *testing.T) {
	doc := "la evidencia digital debe ser copiada a un disco estéril"
	_, parecido := HallarCita("la evidencia digital deberá conservarse diez años", doc)
	if parecido <= 0 || parecido >= 1 {
		t.Errorf("una cita distinta debe dar un parecido intermedio, dio %.2f", parecido)
	}
}

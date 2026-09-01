package dominio

import (
	"fmt"
	"strings"
	"unicode"
)

// UmbralCita es cuánto tiene que parecerse una cita al texto de la fuente para
// darla por hallada. Alto a propósito: mejor pedir revisión de más que colar
// una cita que la fuente no dice.
const UmbralCita = 0.90

// Afirmacion es una frase del trabajo que dice algo comprobable.
type Afirmacion struct {
	ID          string
	Texto       string
	Fuente      string // clave de la referencia que la respalda
	Cita        string // texto COPIADO de la fuente, no una paráfrasis
	Localizador string // "p. 12", "sec. 3"
}

// Problema describe por qué una afirmación no puede publicarse todavía.
type Problema struct {
	ID         string
	Motivo     string
	Detalle    string
	Bloqueante bool // si es true, el trabajo no se entrega
}

func (p *Problema) Error() string { return p.ID + ": " + p.Motivo }

// Problema aplica las reglas que no dependen de tener el texto de la fuente.
// Devuelve nil si, hasta donde se puede saber sin leer el documento, está bien.
func (a Afirmacion) Problema() *Problema {
	if a.Fuente == "" {
		if ExigeRespaldo(a.Texto) {
			return &Problema{a.ID, "lleva un dato y no dice de dónde sale",
				recorte(a.Texto, 70), true}
		}
		return nil
	}
	if strings.TrimSpace(a.Cita) == "" {
		return &Problema{a.ID, "declara fuente pero no la cita literal que la respalda",
			"fuente: " + a.Fuente, true}
	}
	return nil
}

// ExigeRespaldo dice si una frase afirma algo que necesita fuente.
//
// El criterio es la presencia de un dato duro —una cifra, un año, el número de
// una norma—. La prosa argumental no necesita cita; un número, siempre.
func ExigeRespaldo(texto string) bool {
	for _, r := range texto {
		if unicode.IsDigit(r) {
			return true
		}
	}
	return false
}

// HallarCita busca la cita dentro del texto de la fuente. Devuelve si se dio
// por hallada y cuánto se parece lo más próximo que se encontró.
//
// Es la barrera que hace imposible inventarse una frase: si la cita no está en
// ningún documento, no hay forma de que pase.
func HallarCita(cita, documento string) (bool, float64) {
	c, d := Normalizar(cita), Normalizar(documento)
	if c == "" || d == "" {
		return false, 0
	}
	if strings.Contains(d, c) {
		return true, 1
	}
	mejor := 0.0
	paso := len(c) / 2
	if paso < 20 {
		paso = 20
	}
	for i := 0; i < len(d); i += paso {
		fin := i + len(c) + 60
		if fin > len(d) {
			fin = len(d)
		}
		if p := ParecidoLetras(c, d[i:fin]); p > mejor {
			mejor = p
		}
		if fin == len(d) {
			break
		}
	}
	return mejor >= UmbralCita, mejor
}

// Verificar comprueba la afirmación contra el texto real de su fuente.
func (a Afirmacion) Verificar(textoFuente string) *Problema {
	if p := a.Problema(); p != nil {
		return p
	}
	if a.Fuente == "" {
		return nil
	}
	if textoFuente == "" {
		return &Problema{a.ID, "no tengo el documento de la fuente para comprobar la cita",
			"fuente: " + a.Fuente, false}
	}
	hallada, parecido := HallarCita(a.Cita, textoFuente)
	if !hallada {
		return &Problema{a.ID, "la cita NO aparece en la fuente",
			fmt.Sprintf("mejor coincidencia %.0f%% · «%s»", parecido*100,
				recorte(a.Cita, 60)), true}
	}
	return nil
}

func recorte(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "…"
}

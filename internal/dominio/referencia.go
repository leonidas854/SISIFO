// Package dominio contiene las entidades y las reglas del taller.
//
// No importa nada fuera de la biblioteca estándar: aquí viven las decisiones
// que no deben cambiar porque cambiemos de API, de formato o de generador.
package dominio

import (
	"errors"
	"strings"
)

// EstadoVerificacion dice qué sabemos del identificador de una referencia.
type EstadoVerificacion string

const (
	NoVerificada EstadoVerificacion = "no-verificada"
	Verificada   EstadoVerificacion = "verificada"
	NoExiste     EstadoVerificacion = "no-existe"
	NoCoincide   EstadoVerificacion = "no-coincide"
	SinDOI       EstadoVerificacion = "sin-doi"
)

func (e EstadoVerificacion) String() string { return string(e) }

// Explicacion traduce el estado a algo que se le pueda decir a una persona.
func (e EstadoVerificacion) Explicacion() string {
	switch e {
	case Verificada:
		return "el identificador resuelve y el título coincide"
	case NoExiste:
		return "el DOI no está en ningún registro: la referencia es inventada"
	case NoCoincide:
		return "el DOI existe pero pertenece a otro trabajo"
	case SinDOI:
		return "no tiene DOI; puede ser legítima (libro, norma, informe)"
	default:
		return "todavía no se ha comprobado"
	}
}

// Referencia es una obra citable.
type Referencia struct {
	Clave           string // apellido2020palabra, la que se usa en el texto
	Titulo          string
	DOI             string
	Estado          EstadoVerificacion
	Registro        string // Crossref, DataCite… dónde se comprobó
	TituloRegistrado string
	ConfirmadaAMano bool
}

// Citable decide si esta referencia puede aparecer en el trabajo.
//
// Es la regla que impide publicar una cita inventada: sin comprobación no se
// cita, y confirmar a mano solo rescata el caso de las obras sin DOI —nunca
// un DOI que no existe o que apunta a otro trabajo.
func (r Referencia) Citable() bool {
	switch r.Estado {
	case Verificada:
		return true
	case SinDOI:
		return r.ConfirmadaAMano
	default:
		return false
	}
}

func (r Referencia) Validar() error {
	if strings.TrimSpace(r.Clave) == "" {
		return errors.New("la referencia no tiene clave: no se podría citar en el texto")
	}
	if strings.TrimSpace(r.Titulo) == "" {
		return errors.New("la referencia no tiene título")
	}
	return nil
}

// TitulosCoinciden compara el título que tenemos con el que devuelve el
// registro. Tolera tildes, mayúsculas, puntuación y subtítulos añadidos, pero
// no dos trabajos distintos.
func TitulosCoinciden(a, b string) bool {
	na, nb := Normalizar(a), Normalizar(b)
	if na == "" || nb == "" {
		return false
	}
	if strings.HasPrefix(na, nb) || strings.HasPrefix(nb, na) {
		return true
	}
	return ParecidoPalabras(na, nb) >= 0.60
}

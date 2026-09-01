package dominio

import "fmt"

// Entregable es un archivo que el trabajo debe producir, con su tamaño mínimo.
type Entregable struct {
	Ruta   string
	Tipo   string // docx | pptx | xlsx | pdf | md
	Minimo int    // páginas o diapositivas; 0 = sin mínimo
}

// Trabajo es una entrega: lo que hay que producir y bajo qué condiciones.
type Trabajo struct {
	Slug              string
	Ruta              string
	Titulo            string
	Entregables       []Entregable
	CriteriosManuales []string
	LineasRojas       []string
}

// EstadoEntrega es la foto de lo que hay ahora mismo en disco.
type EstadoEntrega struct {
	Producidos   map[string]int // ruta -> páginas/diapositivas medidas
	Referencias  []Referencia
	Afirmaciones []Afirmacion
	TextosFuente map[string]string // clave de referencia -> texto completo
}

// Informe separa lo que la máquina puede decidir de lo que no.
type Informe struct {
	Bloqueantes []string // fallos objetivos: impiden entregar
	Avisos      []string // merecen mirada, no bloquean
	Pendientes  []string // solo los confirma una persona
}

// Listo dice si lo comprobable automáticamente está en orden.
// No dice que el trabajo esté terminado: eso lo dice Confirmado.
func (i Informe) Listo() bool { return len(i.Bloqueantes) == 0 }

// Confirmado nunca es true por sí solo: los criterios manuales los confirma
// la persona, no el sistema. Existe para que ningún código pueda saltárselo.
func (i Informe) Confirmado() bool { return false }

// Evaluar aplica todas las reglas del trabajo contra el estado actual.
func (t Trabajo) Evaluar(e EstadoEntrega) Informe {
	var inf Informe

	for _, ent := range t.Entregables {
		medida, existe := e.Producidos[ent.Ruta]
		if !existe {
			inf.Bloqueantes = append(inf.Bloqueantes,
				fmt.Sprintf("%s: no existe", ent.Ruta))
			continue
		}
		if ent.Minimo > 0 && medida < ent.Minimo {
			inf.Bloqueantes = append(inf.Bloqueantes,
				fmt.Sprintf("%s: %d, el brief pide %d", ent.Ruta, medida, ent.Minimo))
		}
	}

	for _, r := range e.Referencias {
		if !r.Citable() {
			msg := fmt.Sprintf("referencia %s: %s", r.Clave, r.Estado.Explicacion())
			if r.Estado == SinDOI || r.Estado == NoVerificada {
				inf.Avisos = append(inf.Avisos, msg)
			} else {
				inf.Bloqueantes = append(inf.Bloqueantes, msg)
			}
		}
	}

	claves := map[string]bool{}
	for _, r := range e.Referencias {
		claves[r.Clave] = true
	}
	for _, a := range e.Afirmaciones {
		if a.Fuente != "" && len(claves) > 0 && !claves[a.Fuente] {
			inf.Bloqueantes = append(inf.Bloqueantes,
				fmt.Sprintf("%s: la fuente «%s» no está en la bibliografía", a.ID, a.Fuente))
			continue
		}
		if p := a.Verificar(e.TextosFuente[a.Fuente]); p != nil {
			linea := fmt.Sprintf("%s: %s", p.ID, p.Motivo)
			if p.Bloqueante {
				inf.Bloqueantes = append(inf.Bloqueantes, linea)
			} else {
				inf.Avisos = append(inf.Avisos, linea)
			}
		}
	}

	inf.Pendientes = append(inf.Pendientes, t.CriteriosManuales...)
	for _, l := range t.LineasRojas {
		inf.Pendientes = append(inf.Pendientes, "línea roja: "+l)
	}
	return inf
}

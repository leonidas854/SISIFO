package dominio

import (
	"errors"
	"fmt"
)

// ClaseBloque es cada cosa que puede aparecer en un documento.
type ClaseBloque string

const (
	Titulo       ClaseBloque = "titulo"
	Parrafo      ClaseBloque = "parrafo"
	Lista        ClaseBloque = "lista"
	Tabla        ClaseBloque = "tabla"
	Figura       ClaseBloque = "figura"
	Cita         ClaseBloque = "cita"
	SaltoPagina  ClaseBloque = "salto"
	Bibliografia ClaseBloque = "bibliografia"
)

var clasesValidas = map[ClaseBloque]bool{
	Titulo: true, Parrafo: true, Lista: true, Tabla: true,
	Figura: true, Cita: true, SaltoPagina: true, Bibliografia: true,
}

var tiposSalida = map[string]bool{"docx": true, "pptx": true, "xlsx": true, "md": true}

// Bloque es una unidad del documento, independiente del formato final.
type Bloque struct {
	Clase    ClaseBloque `json:"clase"`
	Nivel    int         `json:"nivel,omitempty"`
	Texto    string      `json:"texto,omitempty"`
	Items    []string    `json:"items,omitempty"`
	Cabecera []string    `json:"cabecera,omitempty"`
	Filas    [][]string  `json:"filas,omitempty"`
	Ruta     string      `json:"ruta,omitempty"`
	Leyenda  string      `json:"leyenda,omitempty"`
	Fuente   string      `json:"fuente,omitempty"`
	Citas    []string    `json:"citas,omitempty"`
	Notas    string      `json:"notas,omitempty"`
}

func (b Bloque) Validar() error {
	if !clasesValidas[b.Clase] {
		return fmt.Errorf("clase de bloque desconocida: %q", b.Clase)
	}
	switch b.Clase {
	case Titulo:
		if b.Texto == "" {
			return errors.New("un título sin texto no sirve de nada")
		}
		if b.Nivel < 1 || b.Nivel > 6 {
			return fmt.Errorf("nivel de título fuera de rango: %d", b.Nivel)
		}
	case Parrafo, Cita:
		if b.Texto == "" {
			return fmt.Errorf("un bloque %s necesita texto", b.Clase)
		}
	case Lista:
		if len(b.Items) == 0 {
			return errors.New("una lista sin elementos")
		}
	case Tabla:
		if len(b.Filas) == 0 {
			return errors.New("una tabla sin filas")
		}
		if n := len(b.Cabecera); n > 0 {
			for i, f := range b.Filas {
				if len(f) != n {
					return fmt.Errorf("la fila %d tiene %d celdas y la cabecera %d",
						i+1, len(f), n)
				}
			}
		}
	case Figura:
		if b.Ruta == "" {
			return errors.New("una figura sin ruta de imagen")
		}
	}
	return nil
}

// Guion describe un documento sin comprometerse con el formato: el mismo guion
// produce el informe, las diapositivas y la hoja de cálculo.
type Guion struct {
	Tipo    string   `json:"tipo"`
	Titulo  string   `json:"titulo"`
	Autor   string   `json:"autor,omitempty"`
	Bloques []Bloque `json:"bloques"`
}

// Validar comprueba el guion entero. `disponibles` son las claves de la
// bibliografía: citar algo que no está ahí es el error que produce una
// referencia inventada, así que se rechaza aquí.
func (g Guion) Validar(disponibles map[string]bool) error {
	if !tiposSalida[g.Tipo] {
		return fmt.Errorf("tipo de salida desconocido: %q", g.Tipo)
	}
	if g.Titulo == "" {
		return errors.New("el guion no tiene título")
	}
	if len(g.Bloques) == 0 {
		return errors.New("el guion no tiene bloques")
	}
	for i, b := range g.Bloques {
		if err := b.Validar(); err != nil {
			return fmt.Errorf("bloque %d: %w", i+1, err)
		}
		for _, c := range b.Citas {
			if disponibles != nil && !disponibles[c] {
				return fmt.Errorf("bloque %d cita «%s», que no está en la bibliografía", i+1, c)
			}
		}
	}
	return nil
}

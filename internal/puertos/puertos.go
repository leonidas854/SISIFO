// Package puertos declara lo que el dominio necesita del mundo exterior.
//
// Son interfaces a propósito: el dominio no sabe si las referencias vienen de
// OpenAlex o de un fichero, ni si el .docx lo escribe python-docx u otra cosa.
// Cambiar un proveedor es escribir otro adaptador, no tocar las reglas.
package puertos

import (
	"context"

	"github.com/leonidas854/taller/internal/dominio"
)

// BuscadorAcademico encuentra referencias reales sobre un tema.
type BuscadorAcademico interface {
	Nombre() string
	Buscar(ctx context.Context, consulta string, n int, idioma string) ([]dominio.Referencia, error)
}

// ResultadoDOI es lo que un registro sabe de un identificador.
type ResultadoDOI struct {
	Existe   bool
	Titulo   string
	Registro string // Crossref, DataCite…
}

// VerificadorDOI comprueba que un identificador existe y de qué obra es.
type VerificadorDOI interface {
	Verificar(ctx context.Context, doi string) (ResultadoDOI, error)
}

// ExtractorTexto saca el texto de un documento.
type ExtractorTexto interface {
	Extraer(ruta string) (string, error)
	Soporta(extension string) bool
}

// Pasaje es un fragmento recuperado del índice.
type Pasaje struct {
	Fuente     string
	Posicion   int
	Texto      string
	Puntuacion float64
}

// Indice recupera los pasajes que responden a una pregunta.
type Indice interface {
	Construir(ctx context.Context, carpeta string, avisar func(string)) (int, error)
	Consultar(ctx context.Context, carpeta, pregunta string, n int) ([]Pasaje, error)
}

// Documento es el resultado de generar un entregable.
type Documento struct {
	Ruta     string
	Unidades int // páginas o diapositivas producidas
}

// GeneradorDocumento convierte un guion en un archivo real.
type GeneradorDocumento interface {
	Tipos() []string // "docx", "pptx", "xlsx"
	Generar(ctx context.Context, g dominio.Guion, destino string,
		bibliografia map[string]string) (Documento, error)
}

// MedidorEntregable cuenta páginas o diapositivas de un archivo ya producido.
type MedidorEntregable interface {
	Medir(ruta, tipo string) (int, error)
}

// AlmacenTrabajo lee y escribe el estado de un trabajo en disco.
type AlmacenTrabajo interface {
	Cargar(ruta string) (dominio.Trabajo, error)
	Referencias(ruta string) ([]dominio.Referencia, error)
	Afirmaciones(ruta string) ([]dominio.Afirmacion, error)
	TextosFuente(ruta string) (map[string]string, error)
}

package aplicacion

import (
	"context"
	"fmt"

	"github.com/leonidas854/sisifo/internal/dominio"
)

// Resultado conserva el código de salida de una orden sin terminar el proceso.
// Esto permite reutilizar el mismo caso de uso desde CLI, TUI y pruebas.
type Resultado struct {
	Codigo       int
	Err          error
	MostrarAyuda bool
}

// EjecutorOrdenes es el puerto de salida. Un adaptador decide cómo ejecutar
// Python, el índice local y las herramientas del sistema.
type EjecutorOrdenes interface {
	Ejecutar(context.Context, dominio.Invocacion) Resultado
}

// Servicio valida y despacha las órdenes públicas de SISIFO.
type Servicio struct {
	catalogo Catalogo
	ejecutor EjecutorOrdenes
	ordenes  map[string]string
}

func NuevoServicio(ejecutor EjecutorOrdenes) *Servicio {
	return NuevoServicioConCatalogo(ejecutor, CatalogoPredeterminado())
}

func NuevoServicioConCatalogo(ejecutor EjecutorOrdenes, catalogo Catalogo) *Servicio {
	s := &Servicio{
		catalogo: catalogo.Copia(),
		ejecutor: ejecutor,
		ordenes:  make(map[string]string),
	}
	for _, comando := range catalogo.Comandos {
		s.ordenes[comando.Nombre] = comando.Nombre
		for _, alias := range comando.Alias {
			s.ordenes[alias] = comando.Nombre
		}
	}
	return s
}

func (s *Servicio) Catalogo() Catalogo { return s.catalogo.Copia() }

func (s *Servicio) Ayuda() string { return s.catalogo.Ayuda() }

// Ejecutar es el puerto de entrada común de CLI y TUI.
func (s *Servicio) Ejecutar(ctx context.Context, entrada []string) Resultado {
	if len(entrada) == 0 {
		return Resultado{Codigo: 2, Err: fmt.Errorf("falta una orden"), MostrarAyuda: true}
	}
	nombre, existe := s.ordenes[entrada[0]]
	if !existe {
		return Resultado{
			Codigo:       2,
			Err:          fmt.Errorf("no conozco «%s»", entrada[0]),
			MostrarAyuda: true,
		}
	}
	if s.ejecutor == nil {
		return Resultado{Codigo: 1, Err: fmt.Errorf("no hay un ejecutor configurado")}
	}
	args := append([]string(nil), entrada[1:]...)
	return s.ejecutor.Ejecutar(ctx, dominio.Invocacion{Comando: nombre, Argumentos: args})
}

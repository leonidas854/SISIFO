package aplicacion

import (
	"context"
	"strings"
	"testing"

	"github.com/leonidas854/sisifo/internal/dominio"
)

type ejecutorFalso struct {
	llamadas []dominio.Invocacion
}

func (e *ejecutorFalso) Ejecutar(_ context.Context, inv dominio.Invocacion) Resultado {
	e.llamadas = append(e.llamadas, inv)
	return Resultado{}
}

func TestCatalogoIncluyeTodasLasCategoriasDeLaTUI(t *testing.T) {
	catalogo := CatalogoPredeterminado()
	quiere := []string{
		"investigacion", "produccion", "visuales", "medios",
		"verificacion", "configuracion", "doctor",
	}
	vistas := make(map[string]bool)
	for _, categoria := range catalogo.Categorias {
		vistas[categoria.Clave] = true
	}
	for _, clave := range quiere {
		if !vistas[clave] {
			t.Errorf("falta la categoría %q", clave)
		}
	}
}

func TestServicioNormalizaAliasSinEjecutarProcesos(t *testing.T) {
	falso := &ejecutorFalso{}
	servicio := NuevoServicio(falso)

	resultado := servicio.Ejecutar(context.Background(), []string{"configuracion"})

	if resultado.Codigo != 0 || resultado.Err != nil {
		t.Fatalf("resultado inesperado: %+v", resultado)
	}
	if len(falso.llamadas) != 1 || falso.llamadas[0].Comando != "config" {
		t.Fatalf("el alias no llegó como orden canónica: %+v", falso.llamadas)
	}
}

func TestServicioRechazaOrdenDesconocidaSinLanzarla(t *testing.T) {
	falso := &ejecutorFalso{}
	resultado := NuevoServicio(falso).Ejecutar(context.Background(), []string{"inventar"})

	if resultado.Codigo != 2 || resultado.Err == nil || !resultado.MostrarAyuda {
		t.Fatalf("resultado inesperado: %+v", resultado)
	}
	if len(falso.llamadas) != 0 {
		t.Fatal("una orden desconocida nunca debe llegar al adaptador")
	}
}

func TestCatalogoDevuelveCopiasDefensivas(t *testing.T) {
	servicio := NuevoServicio(&ejecutorFalso{})
	primero := servicio.Catalogo()
	primero.Acciones[0].Invocacion[0] = "alterado"

	segundo := servicio.Catalogo()
	if segundo.Acciones[0].Invocacion[0] == "alterado" {
		t.Fatal("el adaptador pudo modificar el catálogo de la aplicación")
	}
}

func TestAyudaPublicaElCanalVisual(t *testing.T) {
	ayuda := NuevoServicio(&ejecutorFalso{}).Ayuda()
	if !strings.Contains(ayuda, "sisifo visual <plan|validar|generar|auditar|migrar>") {
		t.Fatalf("la ayuda no publica el canal visual:\n%s", ayuda)
	}
}

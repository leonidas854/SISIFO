package trabajo

import (
	"os"
	"path/filepath"
	"testing"
)

func TestActualEncuentraSubiendo(t *testing.T) {
	base := t.TempDir()
	trabajo := filepath.Join(base, "mi-tesis")
	hondo := filepath.Join(trabajo, "fuentes", "textos")
	if err := os.MkdirAll(hondo, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(trabajo, "BRIEF.md"), []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}
	got, err := Actual(hondo)
	if err != nil {
		t.Fatalf("debería encontrarlo subiendo: %v", err)
	}
	if evaluado, _ := filepath.EvalSymlinks(got); evaluado != mustEval(t, trabajo) {
		t.Fatalf("quiero %s, obtuve %s", trabajo, got)
	}
}

func TestActualFallaSinBrief(t *testing.T) {
	base := t.TempDir()
	if _, err := Actual(base); err == nil {
		t.Fatal("sin BRIEF.md debe fallar, no devolver una carpeta cualquiera")
	}
}

func TestRegistroNoDuplica(t *testing.T) {
	motor := t.TempDir()
	for i := 0; i < 3; i++ {
		if err := Anotar(motor, "/ruta/uno", "Uno"); err != nil {
			t.Fatal(err)
		}
	}
	if err := Anotar(motor, "/ruta/dos", "Dos"); err != nil {
		t.Fatal(err)
	}
	rs := Registrados(motor)
	if len(rs) != 2 {
		t.Fatalf("quiero 2 registros sin duplicar, hay %d", len(rs))
	}
}

func TestRegistroDetectaCarpetaBorrada(t *testing.T) {
	r := Registro{Ruta: "/no/existe/en/ningun/sitio"}
	if r.Existe() {
		t.Fatal("una carpeta borrada no debe darse por existente")
	}
}

func mustEval(t *testing.T, p string) string {
	t.Helper()
	e, err := filepath.EvalSymlinks(p)
	if err != nil {
		t.Fatal(err)
	}
	return e
}

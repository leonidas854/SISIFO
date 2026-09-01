// Package trabajo localiza el motor y la carpeta de trabajo activa.
package trabajo

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"time"
)

// Python devuelve el intérprete del motor, o python3 si no hay venv.
func Python(motor string) string {
	v := filepath.Join(motor, ".venv", "bin", "python")
	if _, err := os.Stat(v); err == nil {
		return v
	}
	return "python3"
}

// Actual sube desde dir hasta encontrar un BRIEF.md, sin pasar de $HOME.
func Actual(dir string) (string, error) {
	abs, err := filepath.Abs(dir)
	if err != nil {
		return "", err
	}
	home, _ := os.UserHomeDir()
	for {
		if _, err := os.Stat(filepath.Join(abs, "BRIEF.md")); err == nil {
			return abs, nil
		}
		padre := filepath.Dir(abs)
		if padre == abs || abs == home {
			return "", errors.New("no hay ningún BRIEF.md desde aquí hacia arriba")
		}
		abs = padre
	}
}

// ── registro de trabajos: sobrevive a que se borre cualquier proyecto ──

type Registro struct {
	Ruta   string `json:"ruta"`
	Titulo string `json:"titulo"`
	Creado string `json:"creado"`
}

func rutaRegistro(motor string) string {
	return filepath.Join(motor, "trabajos.json")
}

func Registrados(motor string) []Registro {
	var rs []Registro
	b, err := os.ReadFile(rutaRegistro(motor))
	if err != nil {
		return rs
	}
	_ = json.Unmarshal(b, &rs)
	return rs
}

// Anotar añade el trabajo al registro si no estaba.
func Anotar(motor, ruta, titulo string) error {
	rs := Registrados(motor)
	for _, r := range rs {
		if r.Ruta == ruta {
			return nil
		}
	}
	rs = append(rs, Registro{Ruta: ruta, Titulo: titulo,
		Creado: time.Now().Format("2006-01-02")})
	b, err := json.MarshalIndent(rs, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(rutaRegistro(motor), b, 0o644)
}

// Existe dice si la carpeta del trabajo sigue en disco.
func (r Registro) Existe() bool {
	_, err := os.Stat(filepath.Join(r.Ruta, "BRIEF.md"))
	return err == nil
}

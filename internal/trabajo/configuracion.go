package trabajo

import (
	"errors"
	"os"
	"path/filepath"
)

// Configuracion identifica la instalación resuelta y explica de dónde salió.
// Fuente es deliberadamente legible: se muestra en `sisifo config`.
type Configuracion struct {
	Motor  string
	Fuente string
}

// ResolverConfiguracion localiza la raíz donde viven py/ y plantillas/.
// SISIFO_HOME es el nombre vigente; TALLER_HOME sigue funcionando como legado.
func ResolverConfiguracion() (Configuracion, error) {
	variables := []struct {
		nombre string
		valor  string
	}{
		{nombre: "SISIFO_HOME", valor: os.Getenv("SISIFO_HOME")},
		{nombre: "TALLER_HOME", valor: os.Getenv("TALLER_HOME")},
	}
	for _, variable := range variables {
		if variable.valor == "" || !esMotor(variable.valor) {
			continue
		}
		return Configuracion{Motor: rutaLimpia(variable.valor), Fuente: variable.nombre}, nil
	}

	if exe, err := os.Executable(); err == nil {
		if resuelto, err := filepath.EvalSymlinks(exe); err == nil {
			exe = resuelto
		}
		// bin/sisifo -> raíz está un nivel arriba. El segundo candidato
		// conserva instalaciones antiguas que dejaban el binario en la raíz.
		for _, candidato := range []string{
			filepath.Dir(filepath.Dir(exe)),
			filepath.Dir(exe),
		} {
			if esMotor(candidato) {
				return Configuracion{Motor: rutaLimpia(candidato), Fuente: "binario"}, nil
			}
		}
	}

	if home, err := os.UserHomeDir(); err == nil {
		for _, nombre := range []string{".sisifo", ".taller"} {
			candidato := filepath.Join(home, nombre)
			if esMotor(candidato) {
				return Configuracion{Motor: rutaLimpia(candidato), Fuente: nombre}, nil
			}
		}
	}

	return Configuracion{}, errors.New(
		"no encuentro la instalación de SISIFO; define SISIFO_HOME " +
			"(TALLER_HOME sigue admitido como nombre legado)",
	)
}

// Motor conserva la API anterior para los consumidores existentes.
func Motor() (string, error) {
	configuracion, err := ResolverConfiguracion()
	if err != nil {
		return "", err
	}
	return configuracion.Motor, nil
}

func esMotor(dir string) bool {
	informacion, err := os.Stat(filepath.Join(dir, "py", "dockit"))
	return err == nil && informacion.IsDir()
}

func rutaLimpia(ruta string) string {
	abs, err := filepath.Abs(ruta)
	if err != nil {
		return filepath.Clean(ruta)
	}
	return filepath.Clean(abs)
}

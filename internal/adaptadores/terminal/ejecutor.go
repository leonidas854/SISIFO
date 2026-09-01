package terminal

import (
	"context"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/leonidas854/sisifo/internal/aplicacion"
	"github.com/leonidas854/sisifo/internal/dominio"
	"github.com/leonidas854/sisifo/internal/indice"
	"github.com/leonidas854/sisifo/internal/trabajo"
)

// Ejecutor es el adaptador de salida que conecta los casos de uso con Python,
// el índice local y las herramientas instaladas. Es el único lugar que conoce
// las rutas físicas de los scripts.
type Ejecutor struct {
	entrada          io.Reader
	salida           io.Writer
	errores          io.Writer
	resolver         func() (trabajo.Configuracion, error)
	directorioActual func() (string, error)
	buscarEjecutable func(string) (string, error)
}

func NuevoEjecutor(entrada io.Reader, salida, errores io.Writer) *Ejecutor {
	return &Ejecutor{
		entrada:          entrada,
		salida:           salida,
		errores:          errores,
		resolver:         trabajo.ResolverConfiguracion,
		directorioActual: os.Getwd,
		buscarEjecutable: exec.LookPath,
	}
}

var scriptsPython = map[string]string{
	"nuevo":     "nuevo.py",
	"buscar":    "buscar.py",
	"descargar": "descargar.py",
	"extraer":   "afirmaciones.py",
	"datos":     "afirmaciones.py",
	"bib":       "bibliografia.py",
	"producir":  "../producir.py",
	"redactar":  "../redaccion/cli.py",
	"pdf":       "../exportar_pdf.py",
	"verificar": "verificar.py",
}

func (e *Ejecutor) Ejecutar(ctx context.Context, invocacion dominio.Invocacion) aplicacion.Resultado {
	configuracion, err := e.resolver()
	if err != nil {
		return fallo(1, err)
	}

	switch invocacion.Comando {
	case "config":
		return e.configuracion(configuracion)
	case "doctor":
		return e.doctor(ctx, configuracion.Motor)
	case "estado":
		return e.estado(ctx, configuracion.Motor)
	case "indexar":
		return e.indexar()
	case "consultar":
		return e.consultar(invocacion.Argumentos)
	case "visual":
		return e.ejecutarVisual(ctx, configuracion.Motor, invocacion.Argumentos)
	default:
		script, existe := scriptsPython[invocacion.Comando]
		if !existe {
			return fallo(2, fmt.Errorf("el adaptador no implementa «%s»", invocacion.Comando))
		}
		return e.ejecutarPython(ctx, configuracion.Motor, invocacion.Comando, script, invocacion.Argumentos)
	}
}

func (e *Ejecutor) ejecutarVisual(
	ctx context.Context,
	motor string,
	argumentos []string,
) aplicacion.Resultado {
	ruta := filepath.Join(motor, "py", "dockit", "visual", "cli.py")
	comando := []string{ruta}
	carpeta := ""
	if len(argumentos) > 0 && !contieneAyuda(argumentos) && !tieneCarpeta(argumentos) {
		var resultado aplicacion.Resultado
		carpeta, resultado = e.carpetaActual()
		if resultado.Codigo != 0 {
			return resultado
		}
	}
	comando = append(comando, prepararArgumentosVisual(argumentos, carpeta)...)
	return e.ejecutarProcesoPython(ctx, motor, comando)
}

func prepararArgumentosVisual(argumentos []string, carpeta string) []string {
	if len(argumentos) == 0 || carpeta == "" || contieneAyuda(argumentos) || tieneCarpeta(argumentos) {
		return append([]string(nil), argumentos...)
	}
	// argparse declara --carpeta en cada subcomando, por eso debe ir
	// inmediatamente después de plan/validar/generar/auditar/migrar.
	salida := []string{argumentos[0], "--carpeta", carpeta}
	return append(salida, argumentos[1:]...)
}

func contieneAyuda(argumentos []string) bool {
	for _, argumento := range argumentos {
		if argumento == "-h" || argumento == "--help" {
			return true
		}
	}
	return false
}

func fallo(codigo int, err error) aplicacion.Resultado {
	return aplicacion.Resultado{Codigo: codigo, Err: err}
}

func (e *Ejecutor) carpetaActual() (string, aplicacion.Resultado) {
	cwd, err := e.directorioActual()
	if err != nil {
		return "", fallo(1, err)
	}
	carpeta, err := trabajo.Actual(cwd)
	if err != nil {
		return "", fallo(2, fmt.Errorf(
			"no encuentro ningún BRIEF.md desde aquí hacia arriba; "+
				"entra en la carpeta del trabajo o crea una con "+
				"sisifo nuevo <slug> --titulo \"...\"",
		))
	}
	return carpeta, aplicacion.Resultado{}
}

func (e *Ejecutor) ejecutarPython(
	ctx context.Context,
	motor, orden, script string,
	argumentos []string,
) aplicacion.Resultado {
	ruta := filepath.Join(motor, "py", "dockit", "verificar", script)
	comando := []string{ruta}

	switch orden {
	case "nuevo":
		comando = append(comando, argumentos...)
	case "verificar":
		carpeta, resultado := e.carpetaActual()
		if resultado.Codigo != 0 {
			return resultado
		}
		comando = append(comando, carpeta)
		comando = append(comando, argumentos...)
	default:
		comando = append(comando, argumentos...)
		if !tieneCarpeta(argumentos) {
			carpeta, resultado := e.carpetaActual()
			if resultado.Codigo != 0 {
				return resultado
			}
			comando = append(comando, "--carpeta", carpeta)
		}
		if orden == "extraer" {
			comando = append(comando, "--extraer")
		}
	}

	resultado := e.ejecutarProcesoPython(ctx, motor, comando)
	if resultado.Codigo != 0 || resultado.Err != nil {
		return resultado
	}
	if orden == "nuevo" {
		e.anotarNuevos(motor)
	}
	return aplicacion.Resultado{}
}

func (e *Ejecutor) ejecutarProcesoPython(
	ctx context.Context,
	motor string,
	comando []string,
) aplicacion.Resultado {
	proceso := exec.CommandContext(ctx, trabajo.Python(motor), comando...)
	proceso.Stdout = e.salida
	proceso.Stderr = e.errores
	proceso.Stdin = e.entrada
	proceso.Env = entornoMotor(os.Environ(), motor)
	if err := proceso.Run(); err != nil {
		if salida, ok := err.(*exec.ExitError); ok {
			return aplicacion.Resultado{Codigo: salida.ExitCode()}
		}
		return fallo(1, err)
	}
	return aplicacion.Resultado{}
}

func entornoMotor(entorno []string, motor string) []string {
	salida := make([]string, 0, len(entorno)+2)
	for _, variable := range entorno {
		if strings.HasPrefix(variable, "SISIFO_HOME=") || strings.HasPrefix(variable, "TALLER_HOME=") {
			continue
		}
		salida = append(salida, variable)
	}
	// Varios scripts históricos todavía consultan TALLER_HOME. Ambos nombres
	// apuntan al motor que ya resolvió Go, sin permitir configuraciones cruzadas.
	return append(salida, "SISIFO_HOME="+motor, "TALLER_HOME="+motor)
}

func tieneCarpeta(argumentos []string) bool {
	for _, argumento := range argumentos {
		if argumento == "--carpeta" || strings.HasPrefix(argumento, "--carpeta=") {
			return true
		}
	}
	return false
}

func (e *Ejecutor) anotarNuevos(motor string) {
	cwd, err := e.directorioActual()
	if err != nil {
		return
	}
	entradas, err := os.ReadDir(cwd)
	if err != nil {
		return
	}
	for _, entrada := range entradas {
		if !entrada.IsDir() {
			continue
		}
		ruta := filepath.Join(cwd, entrada.Name())
		if _, err := os.Stat(filepath.Join(ruta, "BRIEF.md")); err == nil {
			_ = trabajo.Anotar(motor, ruta, entrada.Name())
		}
	}
}

func (e *Ejecutor) indexar() aplicacion.Resultado {
	carpeta, resultado := e.carpetaActual()
	if resultado.Codigo != 0 {
		return resultado
	}
	fmt.Fprintf(e.salida, "indexando %s con %s\n", filepath.Base(carpeta), indice.Modelo)
	idx, err := indice.Construir(carpeta, func(aviso string) {
		fmt.Fprintln(e.salida, aviso)
	})
	if err != nil {
		return fallo(1, err)
	}
	if err := idx.Guardar(carpeta); err != nil {
		return fallo(1, err)
	}
	fmt.Fprintf(e.salida, "\n%d fragmentos indexados en fuentes/indice.gob\n", len(idx.Fragmentos))
	fmt.Fprintln(e.salida, "ahora: sisifo consultar \"tu pregunta\"")
	return aplicacion.Resultado{}
}

func (e *Ejecutor) consultar(argumentos []string) aplicacion.Resultado {
	if len(argumentos) == 0 {
		return fallo(2, fmt.Errorf("uso: sisifo consultar \"tu pregunta\" [n]"))
	}
	carpeta, resultado := e.carpetaActual()
	if resultado.Codigo != 0 {
		return resultado
	}
	idx, err := indice.Cargar(carpeta)
	if err != nil {
		return fallo(1, err)
	}
	n := 5
	if len(argumentos) > 1 {
		n, err = strconv.Atoi(argumentos[1])
		if err != nil || n < 1 {
			return fallo(2, fmt.Errorf("n debe ser un entero positivo, no %q", argumentos[1]))
		}
	}
	resultados, err := idx.Consultar(argumentos[0], n)
	if err != nil {
		return fallo(1, err)
	}
	fmt.Fprintf(e.salida, "%d fragmentos más cercanos de %d indexados:\n\n", len(resultados), len(idx.Fragmentos))
	for _, pasaje := range resultados {
		fmt.Fprintf(
			e.salida,
			"── %s  (frag. %d, cercanía %.0f%%)\n%s\n\n",
			pasaje.Fuente,
			pasaje.Pos,
			pasaje.Puntuacion*100,
			recortar(pasaje.Texto, 400),
		)
	}
	fmt.Fprintln(e.salida, "Cita SOLO lo que aparezca literalmente aquí arriba.")
	return aplicacion.Resultado{}
}

func recortar(texto string, maximo int) string {
	runas := []rune(texto)
	if len(runas) <= maximo {
		return texto
	}
	return string(runas[:maximo]) + "…"
}

func (e *Ejecutor) estado(ctx context.Context, motor string) aplicacion.Resultado {
	registros := trabajo.Registrados(motor)
	if len(registros) == 0 {
		fmt.Fprintln(e.salida, "todavía no hay trabajos registrados.")
		fmt.Fprintln(e.salida, "  sisifo nuevo <slug> --titulo \"...\"")
		return aplicacion.Resultado{}
	}
	fmt.Fprintf(e.salida, "%d trabajo(s) registrados\n\n", len(registros))
	for _, registro := range registros {
		if !registro.Existe() {
			fmt.Fprintf(e.salida, " x %-30s %s  (la carpeta ya no está)\n", registro.Titulo, registro.Ruta)
			continue
		}
		proceso := exec.CommandContext(
			ctx,
			trabajo.Python(motor),
			filepath.Join(motor, "py", "dockit", "verificar", "verificar.py"),
			registro.Ruta,
			"--rapido",
		)
		proceso.Env = entornoMotor(os.Environ(), motor)
		salida, _ := proceso.Output()
		resumen := "?"
		for _, linea := range strings.Split(string(salida), "\n") {
			if strings.Contains(linea, "fallo(s)") {
				resumen = strings.TrimSpace(linea)
			}
		}
		fmt.Fprintf(e.salida, " · %-30s %s\n   %s\n", registro.Titulo, resumen, registro.Ruta)
	}
	return aplicacion.Resultado{}
}

func (e *Ejecutor) configuracion(config trabajo.Configuracion) aplicacion.Resultado {
	fmt.Fprintf(e.salida, "motor:    %s\n", config.Motor)
	fmt.Fprintf(e.salida, "origen:   %s\n", config.Fuente)
	fmt.Fprintf(e.salida, "python:   %s\n", trabajo.Python(config.Motor))
	fmt.Fprintln(e.salida, "variable preferida: SISIFO_HOME")
	fmt.Fprintln(e.salida, "variable legada:    TALLER_HOME")
	return aplicacion.Resultado{}
}

func (e *Ejecutor) doctor(ctx context.Context, motor string) aplicacion.Resultado {
	fmt.Fprintf(e.salida, "motor:    %s\n", motor)
	fmt.Fprintf(e.salida, "python:   %s\n\n", trabajo.Python(motor))

	type chequeo struct {
		nombre string
		fn     func() (bool, string)
	}
	binario := func(nombre string) func() (bool, string) {
		return func() (bool, string) {
			ruta, err := e.buscarEjecutable(nombre)
			if err != nil {
				return false, "no está en el PATH"
			}
			return true, ruta
		}
	}
	modulo := func(nombre string) func() (bool, string) {
		return func() (bool, string) {
			proceso := exec.CommandContext(ctx, trabajo.Python(motor), "-c", "import "+nombre)
			proceso.Env = entornoMotor(os.Environ(), motor)
			if err := proceso.Run(); err != nil {
				return false, "falta en el intérprete del motor"
			}
			return true, "importable"
		}
	}
	chequeos := []chequeo{
		{"python-pptx", modulo("pptx")}, {"python-docx", modulo("docx")},
		{"pypdf", modulo("pypdf")}, {"citeproc-py", modulo("citeproc")},
		{"reportlab", modulo("reportlab")}, {"requests", modulo("requests")},
		{"libreoffice", binario("libreoffice")}, {"pdftotext", binario("pdftotext")},
		{"ffmpeg", binario("ffmpeg")}, {"ollama", binario("ollama")},
		{"rsvg-convert", binario("rsvg-convert")},
		{"node", binario("node")},
		{"pptxgenjs", func() (bool, string) {
			// opcional: sin él, el PPTX sale por python-pptx y pierde los
			// gráficos nativos, pero el sistema sigue funcionando
			if _, err := os.Stat(filepath.Join(motor, "node_modules", "pptxgenjs")); err != nil {
				return false, "opcional — sin él, PPTX sin gráficos nativos (npm install)"
			}
			return true, "gráficos y notas nativas en PPTX"
		}},
	}
	fallos := 0
	for _, comprobacion := range chequeos {
		ok, detalle := comprobacion.fn()
		marca := "ok"
		if !ok {
			marca = "--"
			fallos++
		}
		fmt.Fprintf(e.salida, "  [%s] %-14s %s\n", marca, comprobacion.nombre, detalle)
	}

	ok, detalle := func() (bool, string) {
		if _, err := indice.Embeder([]string{"prueba"}); err != nil {
			return false, err.Error()
		}
		return true, indice.Modelo + " responde"
	}()
	marca := "ok"
	if !ok {
		marca = "--"
		fallos++
	}
	fmt.Fprintf(e.salida, "  [%s] %-14s %s\n", marca, "índice", detalle)
	fmt.Fprintf(e.salida, "\n%d comprobación(es) fallidas\n", fallos)
	return aplicacion.Resultado{}
}

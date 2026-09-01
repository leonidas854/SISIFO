// sisifo — punto de entrada único del taller de trabajos e investigación.
//
// El motor vive fuera de los proyectos: borrar una carpeta de trabajo no se
// lleva nada del sistema.
package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/leonidas854/sisifo/internal/indice"
	"github.com/leonidas854/sisifo/internal/trabajo"
)

const ayuda = `SISIFO — trabajos académicos e investigación verificable

  sisifo nuevo <slug> --titulo "..."   crea la carpeta y su BRIEF, aquí mismo
  sisifo buscar "consulta"             busca en fuentes académicas reales
  sisifo descargar                     baja los PDF de acceso abierto
  sisifo extraer                       PDF -> texto
  sisifo indexar                       índice semántico local (bge-m3)
  sisifo consultar "pregunta"          recupera los pasajes que responden
  sisifo datos                         ¿cada afirmación tiene respaldo?
  sisifo bib [--verificar]             bibliografía APA 7 comprobada
  sisifo producir [--tipo docx,pptx]   genera los entregables desde guion.json
  sisifo verificar                     ¿está listo?
  sisifo estado                        todos tus trabajos, estén donde estén
  sisifo doctor                        revisa el entorno

Funciona desde cualquier carpeta: encuentra el trabajo subiendo hasta el BRIEF.md.`

// subcomandos que ejecuta Python, con el script que les toca
var enPython = map[string]string{
	"nuevo":     "nuevo.py",
	"buscar":    "buscar.py",
	"descargar": "descargar.py",
	"extraer":   "afirmaciones.py",
	"datos":     "afirmaciones.py",
	"bib":       "bibliografia.py",
	"producir":  "../producir.py",
	"verificar": "verificar.py",
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println(ayuda)
		return
	}
	orden, args := os.Args[1], os.Args[2:]

	motor, err := trabajo.Motor()
	if err != nil {
		fatal(err)
	}

	switch orden {
	case "-h", "--help", "ayuda":
		fmt.Println(ayuda)
	case "doctor":
		doctor(motor)
	case "estado":
		estado(motor)
	case "indexar":
		indexar(motor)
	case "consultar":
		consultar(motor, args)
	default:
		script, ok := enPython[orden]
		if !ok {
			fmt.Fprintf(os.Stderr, "no conozco «%s»\n\n%s\n", orden, ayuda)
			os.Exit(2)
		}
		os.Exit(aPython(motor, orden, script, args))
	}
}

func fatal(err error) {
	fmt.Fprintln(os.Stderr, "error:", err)
	os.Exit(1)
}

func carpetaActual() string {
	cwd, err := os.Getwd()
	if err != nil {
		fatal(err)
	}
	c, err := trabajo.Actual(cwd)
	if err != nil {
		fmt.Fprintln(os.Stderr,
			"no encuentro ningún BRIEF.md desde aquí hacia arriba.\n"+
				"Métete en la carpeta del trabajo, o créala:\n"+
				"  sisifo nuevo <slug> --titulo \"...\"")
		os.Exit(2)
	}
	return c
}

// aPython lanza el script correspondiente resolviendo la carpeta del trabajo.
func aPython(motor, orden, script string, args []string) int {
	ruta := filepath.Join(motor, "py", "dockit", "verificar", script)
	cmd := []string{ruta}

	switch orden {
	case "nuevo":
		cmd = append(cmd, args...)
	case "verificar":
		cmd = append(cmd, carpetaActual())
		cmd = append(cmd, args...)
	default:
		cmd = append(cmd, args...)
		if !tieneCarpeta(args) {
			cmd = append(cmd, "--carpeta", carpetaActual())
		}
		if orden == "extraer" {
			cmd = append(cmd, "--extraer")
		}
	}

	c := exec.Command(trabajo.Python(motor), cmd...)
	c.Stdout, c.Stderr, c.Stdin = os.Stdout, os.Stderr, os.Stdin
	if err := c.Run(); err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			return ee.ExitCode()
		}
		fatal(err)
	}
	// tras crear un trabajo, anotarlo para que 'estado' lo encuentre siempre
	if orden == "nuevo" {
		anotarNuevos(motor)
	}
	return 0
}

func tieneCarpeta(args []string) bool {
	for _, a := range args {
		if a == "--carpeta" {
			return true
		}
	}
	return false
}

func anotarNuevos(motor string) {
	cwd, err := os.Getwd()
	if err != nil {
		return
	}
	entradas, err := os.ReadDir(cwd)
	if err != nil {
		return
	}
	for _, e := range entradas {
		if !e.IsDir() {
			continue
		}
		ruta := filepath.Join(cwd, e.Name())
		if _, err := os.Stat(filepath.Join(ruta, "BRIEF.md")); err == nil {
			_ = trabajo.Anotar(motor, ruta, e.Name())
		}
	}
}

// ── índice ────────────────────────────────────────────────────────────────

func indexar(motor string) {
	c := carpetaActual()
	fmt.Printf("indexando %s con %s\n", filepath.Base(c), indice.Modelo)
	idx, err := indice.Construir(c, func(s string) { fmt.Println(s) })
	if err != nil {
		fatal(err)
	}
	if err := idx.Guardar(c); err != nil {
		fatal(err)
	}
	fmt.Printf("\n%d fragmentos indexados en fuentes/indice.gob\n", len(idx.Fragmentos))
	fmt.Println("ahora: sisifo consultar \"tu pregunta\"")
}

func consultar(motor string, args []string) {
	if len(args) == 0 {
		fmt.Fprintln(os.Stderr, "uso: sisifo consultar \"tu pregunta\" [n]")
		os.Exit(2)
	}
	c := carpetaActual()
	idx, err := indice.Cargar(c)
	if err != nil {
		fatal(err)
	}
	n := 5
	if len(args) > 1 {
		fmt.Sscanf(args[1], "%d", &n)
	}
	res, err := idx.Consultar(args[0], n)
	if err != nil {
		fatal(err)
	}
	fmt.Printf("%d fragmentos más cercanos de %d indexados:\n\n",
		len(res), len(idx.Fragmentos))
	for _, r := range res {
		fmt.Printf("── %s  (frag. %d, cercanía %.0f%%)\n", r.Fuente, r.Pos,
			r.Puntuacion*100)
		fmt.Printf("%s\n\n", recortar(r.Texto, 400))
	}
	fmt.Println("Cita SOLO lo que aparezca literalmente aquí arriba.")
}

func recortar(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "…"
}

// ── estado y doctor ───────────────────────────────────────────────────────

func estado(motor string) {
	rs := trabajo.Registrados(motor)
	if len(rs) == 0 {
		fmt.Println("todavía no hay trabajos registrados.\n  sisifo nuevo <slug> --titulo \"...\"")
		return
	}
	fmt.Printf("%d trabajo(s) registrados\n\n", len(rs))
	for _, r := range rs {
		if !r.Existe() {
			fmt.Printf(" x %-30s %s  (la carpeta ya no está)\n", r.Titulo, r.Ruta)
			continue
		}
		out, _ := exec.Command(trabajo.Python(motor),
			filepath.Join(motor, "py", "dockit", "verificar", "verificar.py"),
			r.Ruta, "--rapido").Output()
		resumen := "?"
		for _, l := range strings.Split(string(out), "\n") {
			if strings.Contains(l, "fallo(s)") {
				resumen = strings.TrimSpace(l)
			}
		}
		fmt.Printf(" · %-30s %s\n   %s\n", r.Titulo, resumen, r.Ruta)
	}
}

func doctor(motor string) {
	fmt.Printf("motor:    %s\n", motor)
	fmt.Printf("python:   %s\n\n", trabajo.Python(motor))

	type chequeo struct {
		nombre string
		fn     func() (bool, string)
	}
	bin := func(n string) func() (bool, string) {
		return func() (bool, string) {
			p, err := exec.LookPath(n)
			if err != nil {
				return false, "no está en el PATH"
			}
			return true, p
		}
	}
	mod := func(n string) func() (bool, string) {
		return func() (bool, string) {
			err := exec.Command(trabajo.Python(motor), "-c", "import "+n).Run()
			if err != nil {
				return false, "falta en el intérprete del motor"
			}
			return true, "importable"
		}
	}
	chequeos := []chequeo{
		{"python-pptx", mod("pptx")}, {"python-docx", mod("docx")},
		{"pypdf", mod("pypdf")}, {"citeproc-py", mod("citeproc")},
		{"reportlab", mod("reportlab")}, {"requests", mod("requests")},
		{"libreoffice", bin("libreoffice")}, {"pdftotext", bin("pdftotext")},
		{"ffmpeg", bin("ffmpeg")}, {"ollama", bin("ollama")},
		{"rsvg-convert", bin("rsvg-convert")},
	}
	fallos := 0
	for _, c := range chequeos {
		ok, det := c.fn()
		marca := "ok"
		if !ok {
			marca, fallos = "--", fallos+1
		}
		fmt.Printf("  [%s] %-14s %s\n", marca, c.nombre, det)
	}

	ok, det := func() (bool, string) {
		if _, err := indice.Embeder([]string{"prueba"}); err != nil {
			return false, err.Error()
		}
		return true, indice.Modelo + " responde"
	}()
	marca := "ok"
	if !ok {
		marca, fallos = "--", fallos+1
	}
	fmt.Printf("  [%s] %-14s %s\n", marca, "índice", det)

	fmt.Printf("\n%d comprobación(es) fallidas\n", fallos)
}

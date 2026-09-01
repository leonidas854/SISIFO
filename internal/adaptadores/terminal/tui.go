package terminal

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"strconv"
	"strings"
	"unicode"

	"github.com/leonidas854/sisifo/internal/dominio"
)

// TUI es un selector lineal deliberadamente sencillo. Funciona en cualquier
// terminal, por SSH y también con entrada redirigida, sin secuencias ANSI.
type TUI struct {
	aplicacion Aplicacion
	lector     *bufio.Reader
	salida     io.Writer
	errores    io.Writer
}

func NuevaTUI(app Aplicacion, entrada io.Reader, salida, errores io.Writer) *TUI {
	return &TUI{
		aplicacion: app,
		lector:     bufio.NewReader(entrada),
		salida:     salida,
		errores:    errores,
	}
}

func (t *TUI) Ejecutar(ctx context.Context) int {
	catalogo := t.aplicacion.Catalogo()
	fmt.Fprintln(t.salida, "SISIFO · taller académico verificable")
	fmt.Fprintln(t.salida, "Selecciona con un número; 0 o q sale.")

	for {
		fmt.Fprintln(t.salida)
		for i, categoria := range catalogo.Categorias {
			fmt.Fprintf(t.salida, "  %d. %-15s %s\n", i+1, categoria.Nombre, categoria.Descripcion)
		}
		fmt.Fprint(t.salida, "\nÁrea > ")
		seleccion, terminar, err := t.leerSeleccion(len(catalogo.Categorias))
		if err != nil {
			fmt.Fprintln(t.errores, "error:", err)
			continue
		}
		if terminar {
			fmt.Fprintln(t.salida, "Hasta luego.")
			return 0
		}

		categoria := catalogo.Categorias[seleccion]
		acciones := accionesDe(catalogo.Acciones, categoria.Clave)
		if codigo, salir := t.elegirAccion(ctx, categoria, acciones); salir {
			return codigo
		}
	}
}

func (t *TUI) elegirAccion(
	ctx context.Context,
	categoria dominio.Categoria,
	acciones []dominio.AccionMenu,
) (int, bool) {
	if len(acciones) == 0 {
		fmt.Fprintf(t.salida, "\n%s todavía no tiene acciones públicas estables.\n", categoria.Nombre)
		return 0, false
	}

	fmt.Fprintf(t.salida, "\n%s\n", categoria.Nombre)
	for i, accion := range acciones {
		fmt.Fprintf(t.salida, "  %d. %-30s %s\n", i+1, accion.Titulo, accion.Descripcion)
	}
	fmt.Fprint(t.salida, "  0. Volver\n\nAcción > ")
	seleccion, volver, err := t.leerSeleccion(len(acciones))
	if err != nil {
		fmt.Fprintln(t.errores, "error:", err)
		return 0, false
	}
	if volver {
		return 0, false
	}

	accion := acciones[seleccion]
	invocacion := append([]string(nil), accion.Invocacion...)
	if accion.AdmiteArgumentos {
		fmt.Fprintf(t.salida, "\nOrden: sisifo %s\n", unirVisible(invocacion))
		fmt.Fprint(t.salida, "Argumentos adicionales (vacío para ninguno) > ")
		linea, eof, err := t.leerLinea()
		if err != nil {
			fmt.Fprintln(t.errores, "error:", err)
			return 1, true
		}
		extra, err := ParsearArgumentos(linea)
		if err != nil {
			fmt.Fprintln(t.errores, "error:", err)
			if eof {
				return 1, true
			}
			return 0, false
		}
		invocacion = append(invocacion, extra...)
	}

	fmt.Fprintf(t.salida, "\n$ sisifo %s\n", unirVisible(invocacion))
	resultado := t.aplicacion.Ejecutar(ctx, invocacion)
	if resultado.Err != nil {
		fmt.Fprintln(t.errores, "error:", resultado.Err)
	}
	if resultado.Codigo != 0 {
		fmt.Fprintf(t.errores, "la orden terminó con código %d\n", resultado.Codigo)
	}
	return 0, false
}

func (t *TUI) leerSeleccion(maximo int) (indice int, terminar bool, err error) {
	linea, _, lecturaErr := t.leerLinea()
	if lecturaErr != nil {
		if errors.Is(lecturaErr, io.EOF) {
			return 0, true, nil
		}
		return 0, false, lecturaErr
	}
	valor := strings.TrimSpace(linea)
	if valor == "0" || strings.EqualFold(valor, "q") || strings.EqualFold(valor, "salir") {
		return 0, true, nil
	}
	numero, conversionErr := strconv.Atoi(valor)
	if conversionErr != nil || numero < 1 || numero > maximo {
		return 0, false, fmt.Errorf("selección inválida %q; usa un número entre 1 y %d", valor, maximo)
	}
	return numero - 1, false, nil
}

func (t *TUI) leerLinea() (linea string, eof bool, err error) {
	linea, err = t.lector.ReadString('\n')
	linea = strings.TrimSuffix(strings.TrimSuffix(linea, "\n"), "\r")
	if errors.Is(err, io.EOF) && linea != "" {
		return linea, true, nil
	}
	return linea, errors.Is(err, io.EOF), err
}

func accionesDe(todas []dominio.AccionMenu, categoria string) []dominio.AccionMenu {
	var salida []dominio.AccionMenu
	for _, accion := range todas {
		if accion.Categoria == categoria {
			salida = append(salida, accion)
		}
	}
	return salida
}

func unirVisible(argumentos []string) string {
	visibles := make([]string, len(argumentos))
	for i, argumento := range argumentos {
		if strings.IndexFunc(argumento, unicode.IsSpace) >= 0 {
			visibles[i] = strconv.Quote(argumento)
		} else {
			visibles[i] = argumento
		}
	}
	return strings.Join(visibles, " ")
}

// ParsearArgumentos separa una línea como lo haría una shell pequeña: reconoce
// comillas simples, dobles y barra inversa, pero nunca expande variables ni
// ejecuta sustituciones. Así la TUI no convierte texto del usuario en shell.
func ParsearArgumentos(linea string) ([]string, error) {
	var (
		argumentos []string
		actual     strings.Builder
		comilla    rune
		escapado   bool
		iniciado   bool
	)

	guardar := func() {
		if iniciado {
			argumentos = append(argumentos, actual.String())
			actual.Reset()
			iniciado = false
		}
	}

	for _, caracter := range linea {
		if escapado {
			actual.WriteRune(caracter)
			escapado = false
			iniciado = true
			continue
		}
		if caracter == '\\' && comilla != '\'' {
			escapado = true
			iniciado = true
			continue
		}
		if comilla != 0 {
			if caracter == comilla {
				comilla = 0
				iniciado = true
				continue
			}
			actual.WriteRune(caracter)
			iniciado = true
			continue
		}
		switch {
		case caracter == '\'' || caracter == '"':
			comilla = caracter
			iniciado = true
		case unicode.IsSpace(caracter):
			guardar()
		default:
			actual.WriteRune(caracter)
			iniciado = true
		}
	}

	if escapado {
		return nil, errors.New("la línea termina con una barra inversa incompleta")
	}
	if comilla != 0 {
		return nil, errors.New("hay una comilla sin cerrar")
	}
	guardar()
	return argumentos, nil
}

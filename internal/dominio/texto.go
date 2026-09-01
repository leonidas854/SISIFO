package dominio

import (
	"strings"
	"unicode"
)

// Normalizar deja el texto comparable: sin tildes, en minúscula, sin
// puntuación y con los espacios colapsados.
func Normalizar(s string) string {
	var b strings.Builder
	b.Grow(len(s))
	espacioPendiente := false
	for _, r := range strings.ToLower(s) {
		r = sinTilde(r)
		switch {
		case unicode.IsLetter(r) || unicode.IsDigit(r):
			if espacioPendiente && b.Len() > 0 {
				b.WriteByte(' ')
			}
			espacioPendiente = false
			b.WriteRune(r)
		default:
			espacioPendiente = true
		}
	}
	return b.String()
}

var tildes = map[rune]rune{
	'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a', 'ã': 'a', 'å': 'a',
	'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e',
	'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i',
	'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o', 'õ': 'o',
	'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u',
	'ñ': 'n', 'ç': 'c', 'ý': 'y',
}

func sinTilde(r rune) rune {
	if s, ok := tildes[r]; ok {
		return s
	}
	return r
}

// ParecidoPalabras compara dos textos por las palabras que comparten
// (coeficiente de Dice). Va bien para títulos, donde el orden importa poco.
func ParecidoPalabras(a, b string) float64 {
	pa, pb := strings.Fields(a), strings.Fields(b)
	if len(pa) == 0 || len(pb) == 0 {
		return 0
	}
	cuenta := map[string]int{}
	for _, p := range pa {
		cuenta[p]++
	}
	comunes := 0
	for _, p := range pb {
		if cuenta[p] > 0 {
			cuenta[p]--
			comunes++
		}
	}
	return 2 * float64(comunes) / float64(len(pa)+len(pb))
}

// ParecidoLetras compara por pares de caracteres. Detecta variaciones menores
// —una palabra cambiada, una errata del OCR— dentro de una frase.
func ParecidoLetras(a, b string) float64 {
	ba, bb := bigramas(a), bigramas(b)
	if len(ba) == 0 || len(bb) == 0 {
		if a == b {
			return 1
		}
		return 0
	}
	cuenta := map[string]int{}
	for _, g := range ba {
		cuenta[g]++
	}
	comunes := 0
	for _, g := range bb {
		if cuenta[g] > 0 {
			cuenta[g]--
			comunes++
		}
	}
	return 2 * float64(comunes) / float64(len(ba)+len(bb))
}

func bigramas(s string) []string {
	r := []rune(s)
	if len(r) < 2 {
		return nil
	}
	out := make([]string, 0, len(r)-1)
	for i := 0; i+1 < len(r); i++ {
		out = append(out, string(r[i:i+2]))
	}
	return out
}

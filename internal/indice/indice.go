// Package indice construye y consulta un índice semántico local de las fuentes
// de un trabajo, usando bge-m3 a través de ollama. Sin dependencias externas:
// el almacén es un fichero gob y la búsqueda es coseno por fuerza bruta, que
// para unos miles de fragmentos es instantáneo y no puede romperse.
package indice

import (
	"bytes"
	"encoding/gob"
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

const (
	Modelo      = "bge-m3"
	OllamaURL   = "http://localhost:11434/api/embed"
	TamFragmento = 1200 // caracteres
	Solape       = 200
	Lote         = 16
)

type Fragmento struct {
	Fuente string    // clave de la referencia o nombre del archivo
	Pos    int       // nº de fragmento dentro de la fuente
	Texto  string
	Vector []float32
}

type Indice struct {
	Modelo     string
	Creado     time.Time
	Fragmentos []Fragmento
}

func ruta(carpeta string) string {
	return filepath.Join(carpeta, "fuentes", "indice.gob")
}

// ── troceado ──────────────────────────────────────────────────────────────

// Trocear parte el texto en ventanas con solape, cortando por espacio para no
// partir palabras a la mitad.
func Trocear(texto string) []string {
	texto = strings.Join(strings.Fields(texto), " ")
	if len(texto) <= TamFragmento {
		if texto == "" {
			return nil
		}
		return []string{texto}
	}
	var out []string
	for i := 0; i < len(texto); {
		fin := i + TamFragmento
		if fin >= len(texto) {
			out = append(out, texto[i:])
			break
		}
		// retrocede hasta un espacio para no cortar una palabra
		corte := fin
		for corte > i && texto[corte] != ' ' {
			corte--
		}
		if corte == i {
			corte = fin
		}
		out = append(out, texto[i:corte])
		i = corte - Solape
		if i < 0 || corte-Solape <= 0 {
			i = corte
		}
	}
	return out
}

// ── embeddings vía ollama ─────────────────────────────────────────────────

type peticion struct {
	Model string   `json:"model"`
	Input []string `json:"input"`
}

type respuesta struct {
	Embeddings [][]float32 `json:"embeddings"`
	Error      string      `json:"error"`
}

func Embeder(textos []string) ([][]float32, error) {
	cuerpo, err := json.Marshal(peticion{Model: Modelo, Input: textos})
	if err != nil {
		return nil, err
	}
	cli := &http.Client{Timeout: 5 * time.Minute}
	r, err := cli.Post(OllamaURL, "application/json", bytes.NewReader(cuerpo))
	if err != nil {
		return nil, fmt.Errorf("¿está ollama corriendo? %w", err)
	}
	defer r.Body.Close()
	var resp respuesta
	if err := json.NewDecoder(r.Body).Decode(&resp); err != nil {
		return nil, err
	}
	if resp.Error != "" {
		return nil, fmt.Errorf("ollama: %s", resp.Error)
	}
	if len(resp.Embeddings) != len(textos) {
		return nil, fmt.Errorf("pedí %d vectores y devolvió %d",
			len(textos), len(resp.Embeddings))
	}
	return resp.Embeddings, nil
}

// ── construcción ──────────────────────────────────────────────────────────

// Construir indexa todos los .txt de fuentes/textos/ de la carpeta.
func Construir(carpeta string, avisar func(string)) (*Indice, error) {
	dir := filepath.Join(carpeta, "fuentes", "textos")
	entradas, err := os.ReadDir(dir)
	if err != nil {
		return nil, fmt.Errorf("no hay fuentes/textos/ — usa 'taller extraer' antes")
	}

	idx := &Indice{Modelo: Modelo, Creado: time.Now()}
	for _, e := range entradas {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".txt") {
			continue
		}
		b, err := os.ReadFile(filepath.Join(dir, e.Name()))
		if err != nil {
			continue
		}
		fuente := strings.TrimSuffix(e.Name(), ".txt")
		trozos := Trocear(string(b))
		avisar(fmt.Sprintf("  %-40s %3d fragmentos", fuente, len(trozos)))

		for i := 0; i < len(trozos); i += Lote {
			fin := min(i+Lote, len(trozos))
			vecs, err := Embeder(trozos[i:fin])
			if err != nil {
				return nil, err
			}
			for j, v := range vecs {
				idx.Fragmentos = append(idx.Fragmentos, Fragmento{
					Fuente: fuente, Pos: i + j, Texto: trozos[i+j], Vector: v,
				})
			}
		}
	}
	if len(idx.Fragmentos) == 0 {
		return nil, fmt.Errorf("no había texto que indexar en %s", dir)
	}
	return idx, nil
}

func (i *Indice) Guardar(carpeta string) error {
	p := ruta(carpeta)
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		return err
	}
	f, err := os.Create(p)
	if err != nil {
		return err
	}
	defer f.Close()
	return gob.NewEncoder(f).Encode(i)
}

func Cargar(carpeta string) (*Indice, error) {
	f, err := os.Open(ruta(carpeta))
	if err != nil {
		return nil, fmt.Errorf("no hay índice — usa 'taller indexar' antes")
	}
	defer f.Close()
	var i Indice
	if err := gob.NewDecoder(f).Decode(&i); err != nil {
		return nil, err
	}
	return &i, nil
}

// ── consulta ──────────────────────────────────────────────────────────────

type Resultado struct {
	Fragmento
	Puntuacion float64
}

func coseno(a, b []float32) float64 {
	if len(a) != len(b) {
		return 0
	}
	var pa, na, nb float64
	for i := range a {
		x, y := float64(a[i]), float64(b[i])
		pa += x * y
		na += x * x
		nb += y * y
	}
	if na == 0 || nb == 0 {
		return 0
	}
	return pa / (math.Sqrt(na) * math.Sqrt(nb))
}

// Consultar devuelve los n fragmentos más cercanos a la pregunta.
func (i *Indice) Consultar(pregunta string, n int) ([]Resultado, error) {
	vs, err := Embeder([]string{pregunta})
	if err != nil {
		return nil, err
	}
	q := vs[0]
	res := make([]Resultado, 0, len(i.Fragmentos))
	for _, f := range i.Fragmentos {
		res = append(res, Resultado{Fragmento: f, Puntuacion: coseno(q, f.Vector)})
	}
	sort.Slice(res, func(a, b int) bool {
		return res[a].Puntuacion > res[b].Puntuacion
	})
	if n > len(res) {
		n = len(res)
	}
	return res[:n], nil
}

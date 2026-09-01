// Package aplicacion contiene los casos de uso de SISIFO. No conoce terminales,
// procesos, Python ni el sistema de archivos.
package aplicacion

import (
	"fmt"
	"strings"

	"github.com/leonidas854/sisifo/internal/dominio"
)

// Catalogo es la fuente única de las órdenes públicas y de cómo se presentan
// en las interfaces. Los adaptadores no vuelven a declarar estas reglas.
type Catalogo struct {
	Categorias []dominio.Categoria
	Comandos   []dominio.Comando
	Acciones   []dominio.AccionMenu
}

// CatalogoPredeterminado devuelve las capacidades estables de la aplicación.
func CatalogoPredeterminado() Catalogo {
	return Catalogo{
		Categorias: []dominio.Categoria{
			{Clave: "investigacion", Nombre: "Investigación", Descripcion: "Fuentes académicas, extracción, índice y consulta semántica"},
			{Clave: "produccion", Nombre: "Producción", Descripcion: "Documentos y entregables derivados de un guion"},
			{Clave: "visuales", Nombre: "Visuales", Descripcion: "Diapositivas y recursos visuales con sentido editorial"},
			{Clave: "medios", Nombre: "Medios", Descripcion: "Audio, vídeo y sus dependencias locales"},
			{Clave: "verificacion", Nombre: "Verificación", Descripcion: "Respaldo, criterios de entrega y estado de los trabajos"},
			{Clave: "configuracion", Nombre: "Configuración", Descripcion: "Instalación activa e intérprete de trabajo"},
			{Clave: "doctor", Nombre: "Doctor", Descripcion: "Diagnóstico completo del entorno"},
		},
		Comandos: []dominio.Comando{
			{Nombre: "nuevo", Uso: "nuevo <slug> --titulo \"...\"", Descripcion: "crea la carpeta y su BRIEF", Categoria: "investigacion"},
			{Nombre: "buscar", Uso: "buscar \"consulta\"", Descripcion: "busca en fuentes académicas reales", Categoria: "investigacion"},
			{Nombre: "descargar", Uso: "descargar", Descripcion: "descarga los PDF de acceso abierto", Categoria: "investigacion"},
			{Nombre: "extraer", Uso: "extraer", Descripcion: "extrae texto de las fuentes", Categoria: "investigacion"},
			{Nombre: "indexar", Uso: "indexar", Descripcion: "construye el índice semántico local", Categoria: "investigacion"},
			{Nombre: "consultar", Uso: "consultar \"pregunta\" [n]", Descripcion: "recupera pasajes pertinentes", Categoria: "investigacion"},
			{Nombre: "bib", Uso: "bib [--verificar]", Descripcion: "genera bibliografía APA 7 comprobada", Categoria: "investigacion"},
			{Nombre: "redactar", Uso: "redactar [--modelo llama3.2]", Descripcion: "redacta el borrador con un modelo local, anclado a las fuentes", Categoria: "produccion"},
			{Nombre: "producir", Uso: "producir [--tipo docx,pptx]", Descripcion: "genera entregables desde guion.json", Categoria: "produccion"},
			{Nombre: "pdf", Uso: "pdf [--archivo salida/informe.docx]", Descripcion: "exporta a PDF con los índices ya calculados", Categoria: "produccion"},
			{Nombre: "visual", Uso: "visual <plan|validar|generar|auditar|migrar>", Descripcion: "gestiona el contrato visual y su control semántico", Categoria: "visuales"},
			{Nombre: "datos", Uso: "datos", Descripcion: "comprueba el respaldo de las afirmaciones", Categoria: "verificacion"},
			{Nombre: "verificar", Uso: "verificar", Descripcion: "comprueba el criterio de terminado", Categoria: "verificacion"},
			{Nombre: "estado", Uso: "estado", Descripcion: "resume todos los trabajos registrados", Categoria: "verificacion"},
			{Nombre: "config", Uso: "config", Descripcion: "muestra la configuración resuelta", Categoria: "configuracion", Alias: []string{"configuracion"}},
			{Nombre: "doctor", Uso: "doctor", Descripcion: "revisa el entorno y sus dependencias", Categoria: "doctor"},
		},
		Acciones: []dominio.AccionMenu{
			{Categoria: "investigacion", Titulo: "Crear un trabajo", Descripcion: "Capturar el contexto en un BRIEF", Invocacion: []string{"nuevo"}, AdmiteArgumentos: true},
			{Categoria: "investigacion", Titulo: "Buscar bibliografía", Descripcion: "Consultar fuentes académicas reales", Invocacion: []string{"buscar"}, AdmiteArgumentos: true},
			{Categoria: "investigacion", Titulo: "Descargar fuentes", Descripcion: "Obtener PDF de acceso abierto", Invocacion: []string{"descargar"}, AdmiteArgumentos: true},
			{Categoria: "investigacion", Titulo: "Extraer textos", Descripcion: "Preparar las fuentes para comprobación", Invocacion: []string{"extraer"}, AdmiteArgumentos: true},
			{Categoria: "investigacion", Titulo: "Indexar fuentes", Descripcion: "Crear el índice semántico local", Invocacion: []string{"indexar"}},
			{Categoria: "investigacion", Titulo: "Consultar el índice", Descripcion: "Recuperar evidencia para una pregunta", Invocacion: []string{"consultar"}, AdmiteArgumentos: true},
			{Categoria: "investigacion", Titulo: "Bibliografía APA 7", Descripcion: "Formatear y opcionalmente verificar DOI", Invocacion: []string{"bib"}, AdmiteArgumentos: true},
			{Categoria: "produccion", Titulo: "Redactar borrador (local)", Descripcion: "Escribir con el modelo local anclado a las fuentes", Invocacion: []string{"redactar"}, AdmiteArgumentos: true},
			{Categoria: "produccion", Titulo: "Generar entregables", Descripcion: "Producir desde el guion común", Invocacion: []string{"producir"}, AdmiteArgumentos: true},
			{Categoria: "visuales", Titulo: "Crear contrato visual", Descripcion: "Derivar plan_visual.json desde el guion", Invocacion: []string{"visual", "plan"}, AdmiteArgumentos: true},
			{Categoria: "visuales", Titulo: "Validar semántica visual", Descripcion: "Detectar imágenes vacías, ajenas o sin procedencia", Invocacion: []string{"visual", "validar"}, AdmiteArgumentos: true},
			{Categoria: "visuales", Titulo: "Generar SVG", Descripcion: "Crear gráficos informativos con texto vectorial", Invocacion: []string{"visual", "generar"}, AdmiteArgumentos: true},
			{Categoria: "visuales", Titulo: "Auditar diapositivas", Descripcion: "Contrastar el PPTX real contra el contrato", Invocacion: []string{"visual", "auditar"}, AdmiteArgumentos: true},
			{Categoria: "visuales", Titulo: "Migrar un plan legado", Descripcion: "Convertir planes anteriores al contrato vigente", Invocacion: []string{"visual", "migrar"}, AdmiteArgumentos: true},
			{Categoria: "medios", Titulo: "Diagnosticar soporte multimedia", Descripcion: "Comprobar FFmpeg y el resto del entorno", Invocacion: []string{"doctor"}},
			{Categoria: "verificacion", Titulo: "Verificar afirmaciones", Descripcion: "Contrastar datos contra sus fuentes", Invocacion: []string{"datos"}, AdmiteArgumentos: true},
			{Categoria: "verificacion", Titulo: "Revisar la entrega", Descripcion: "Aplicar el contrato de terminado", Invocacion: []string{"verificar"}, AdmiteArgumentos: true},
			{Categoria: "verificacion", Titulo: "Ver estado general", Descripcion: "Listar los trabajos registrados", Invocacion: []string{"estado"}},
			{Categoria: "configuracion", Titulo: "Mostrar configuración", Descripcion: "Ver motor, origen e intérprete activos", Invocacion: []string{"config"}},
			{Categoria: "doctor", Titulo: "Ejecutar diagnóstico", Descripcion: "Comprobar todas las herramientas", Invocacion: []string{"doctor"}},
		},
	}
}

// Copia devuelve una copia defensiva para que un adaptador no pueda alterar el
// catálogo compartido por las demás interfaces.
func (c Catalogo) Copia() Catalogo {
	salida := Catalogo{
		Categorias: append([]dominio.Categoria(nil), c.Categorias...),
		Comandos:   append([]dominio.Comando(nil), c.Comandos...),
		Acciones:   append([]dominio.AccionMenu(nil), c.Acciones...),
	}
	for i := range salida.Comandos {
		salida.Comandos[i].Alias = append([]string(nil), salida.Comandos[i].Alias...)
	}
	for i := range salida.Acciones {
		salida.Acciones[i].Invocacion = append([]string(nil), salida.Acciones[i].Invocacion...)
	}
	return salida
}

// Ayuda genera la ayuda de la CLI desde el mismo catálogo que consume la TUI.
func (c Catalogo) Ayuda() string {
	var b strings.Builder
	b.WriteString("SISIFO — trabajos académicos e investigación verificable\n\n")
	for _, comando := range c.Comandos {
		fmt.Fprintf(&b, "  sisifo %-38s %s\n", comando.Uso, comando.Descripcion)
	}
	b.WriteString("  sisifo tui")
	b.WriteString(strings.Repeat(" ", 28))
	b.WriteString("abre el menú interactivo\n\n")
	b.WriteString("Funciona desde cualquier carpeta: encuentra el trabajo subiendo hasta BRIEF.md.\n")
	b.WriteString("El alias histórico «taller» sigue siendo compatible.")
	return b.String()
}

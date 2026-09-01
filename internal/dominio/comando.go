package dominio

// Categoria agrupa capacidades del taller por intención de la persona, no por
// la tecnología que las implementa.
type Categoria struct {
	Clave       string
	Nombre      string
	Descripcion string
}

// Comando describe una orden pública de SISIFO. Es información del dominio:
// no contiene rutas de scripts ni detalles del sistema operativo.
type Comando struct {
	Nombre      string
	Uso         string
	Descripcion string
	Categoria   string
	Alias       []string
}

// AccionMenu es una entrada orientada a una tarea. Invocacion siempre empieza
// con un Comando conocido y puede llevar argumentos predeterminados.
type AccionMenu struct {
	Categoria        string
	Titulo           string
	Descripcion      string
	Invocacion       []string
	AdmiteArgumentos bool
}

// Invocacion es una petición ya validada por la capa de aplicación.
type Invocacion struct {
	Comando    string
	Argumentos []string
}

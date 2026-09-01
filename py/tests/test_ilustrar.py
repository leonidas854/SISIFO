"""De las viñetas de una diapositiva a un diagrama que le corresponda.

La queja fue «algunas imágenes nada que ver, sin sentido con lo que dice la
diapositiva». El puente elige iconos y arquetipo a partir del texto real de la
lámina, y los rótulos son las propias viñetas: la imagen no puede hablar de
otra cosa porque sale de ahí.
"""
import pytest

from dockit.imagen import ilustrar


def test_elige_iconos_por_el_significado():
    ic = ilustrar.iconos_para(["Seguridad y cifrado del dato",
                               "Acceso a fuentes externas",
                               "Tiempo de respuesta"])
    assert ic[0] == "candado", "«seguridad/cifrado» debería dar un candado"
    assert ic[1] == "mundo", "«fuentes externas» debería dar el mundo"
    assert ic[2] == "reloj", "«tiempo» debería dar un reloj"


def test_todos_los_iconos_existen_en_el_catalogo():
    from dockit.imagen import diagramas
    ic = ilustrar.iconos_para(["cualquier cosa rara", "otra más", "y otra"])
    for nombre in ic:
        assert nombre in diagramas.ICONS, f"«{nombre}» no está en el catálogo"


def test_no_repite_iconos_en_la_misma_lamina():
    ic = ilustrar.iconos_para(["seguridad", "seguridad", "seguridad"])
    assert len(set(ic)) == 3, "tres iconos iguales no ilustran nada"


def test_el_arquetipo_sigue_a_la_forma_del_contenido():
    assert ilustrar.arquetipo_para(["Primero", "Después", "Finalmente"]) == "flujo"
    assert ilustrar.arquetipo_para(["Ventaja clara", "Desventaja seria"]) == "contraste"
    assert ilustrar.arquetipo_para(["Uno", "Dos", "Tres", "Cuatro"]) == "fila"


def test_la_especificacion_usa_las_vinetas_como_rotulos():
    spec = ilustrar.spec_para("Riesgos del oráculo",
                              ["Manipulación de precios", "Centralización"])
    assert spec["titulo"] == "Riesgos del oráculo"
    assert spec["rotulos"] == ["Manipulación de precios", "Centralización"]
    assert len(spec["iconos"]) == 2


def test_una_lamina_sin_vinetas_no_produce_imagen():
    assert ilustrar.spec_para("Título suelto", []) is None


def test_genera_el_png_de_una_lamina(tmp_path):
    ruta = ilustrar.ilustrar_lamina("Arquitectura", ["Oráculo", "Contrato"],
                                    tmp_path, "l1")
    assert ruta and ruta.exists() and ruta.stat().st_size > 3000
    svg = ruta.with_suffix(".svg").read_text()
    # los rótulos sí; el título no, porque lo pone la lámina
    assert "Oráculo" in svg and "Contrato" in svg
    assert "Arquitectura" not in svg


def test_no_repite_el_titulo_que_ya_lleva_la_lamina():
    """El .pptx ya pone el título arriba; repetirlo dentro del diagrama
    desperdicia espacio y compite con él."""
    spec = ilustrar.spec_para("Riesgos", ["Uno", "Dos"], con_titulo=False)
    assert not spec.get("titulo")


def test_prefiere_arquetipos_que_se_leen():
    """«capas» dibujaba anillos concéntricos con los rótulos encimados."""
    for n in range(2, 6):
        vinetas = [f"Idea número {i}" for i in range(n)]
        tipo = ilustrar.arquetipo_para(vinetas)
        assert tipo in ("fila", "contraste", "flujo"), \
            f"{n} viñetas eligieron «{tipo}», que no se lee bien"

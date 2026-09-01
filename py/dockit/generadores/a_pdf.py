"""Exporta a PDF con los índices ya calculados.

`libreoffice --convert-to pdf` NO actualiza los campos: el PDF sale con
«pulse F9 para actualizar» donde debería ir el índice. Word y OnlyOffice sí los
calculan al abrir el .docx —para eso está `w:updateFields`—, pero para exportar
sin abrir nada hace falta pilotar LibreOffice por UNO: abrir el documento,
refrescar índices y campos, y entonces exportar.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

PUERTO = 2002
ARRANQUE_MAX = 30


class ErrorPDF(RuntimeError):
    pass


def _contexto():
    import uno
    from com.sun.star.connection import NoConnectException

    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    url = (f"uno:socket,host=127.0.0.1,port={PUERTO};urp;"
           "StarOffice.ComponentContext")
    for _ in range(ARRANQUE_MAX * 2):
        try:
            return resolver.resolve(url)
        except NoConnectException:
            time.sleep(0.5)
    raise ErrorPDF("LibreOffice no respondió en el puerto UNO")


def _arrancar_servicio() -> subprocess.Popen:
    return subprocess.Popen(
        ["libreoffice", "--headless", "--norestore", "--invisible",
         f"--accept=socket,host=127.0.0.1,port={PUERTO};urp;"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def exportar(origen: str, destino: str | None = None) -> str:
    """Abre, actualiza índices y campos, y exporta a PDF."""
    import uno
    from com.sun.star.beans import PropertyValue

    org = Path(origen).resolve()
    if not org.exists():
        raise ErrorPDF(f"no existe {org}")
    dst = Path(destino) if destino else org.with_suffix(".pdf")

    servicio = _arrancar_servicio()
    try:
        ctx = _contexto()
        escritorio = ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", ctx)

        oculto = PropertyValue(); oculto.Name = "Hidden"; oculto.Value = True
        doc = escritorio.loadComponentFromURL(
            uno.systemPathToFileUrl(str(org)), "_blank", 0, (oculto,))
        if doc is None:
            raise ErrorPDF("LibreOffice no pudo abrir el documento")

        try:
            doc.getTextFields().refresh()
            indices = doc.getDocumentIndexes()
            for i in range(indices.getCount()):
                indices.getByIndex(i).update()
            # segunda vuelta: al actualizar el índice cambia la paginación
            doc.getTextFields().refresh()
        finally:
            filtro = PropertyValue()
            filtro.Name, filtro.Value = "FilterName", "writer_pdf_Export"
            doc.storeToURL(uno.systemPathToFileUrl(str(dst)), (filtro,))
            doc.close(False)
        return str(dst)
    finally:
        servicio.terminate()
        try:
            servicio.wait(timeout=15)
        except subprocess.TimeoutExpired:
            servicio.kill()

"""Pruebas del servidor MCP de la CREG sobre el corpus público que trae el paquete."""
import re
from pathlib import Path

import pytest

from creg_mcp import server
from creg_mcp.server import BuscarInput, LeerDocumentoInput, RelacionesInput
from creg_mcp.vigencia import REPO

RAIZ = Path(__file__).resolve().parent.parent
ES_CREG = re.compile(r"(?i)^(resoluci[óo]n_creg_|concepto_creg_|creg\d)")


def test_corpus_solo_creg():
    """Solo resoluciones y conceptos de la CREG: ni normas técnicas, ni notas, ni datos."""
    archivos = [p for p in REPO.rglob("*") if p.is_file()]
    assert archivos, "el corpus está vacío"
    for p in archivos:
        rel = p.relative_to(REPO).as_posix()
        assert p.suffix == ".md", rel
        assert p.parent.name in ("resoluciones", "conceptos"), rel
        assert ES_CREG.match(p.name), rel


def test_corpus_coincide_con_la_lista():
    """corpus.txt es el inventario publicado: ni sobra ni falta un documento."""
    lista = (RAIZ / "corpus.txt").read_text(encoding="utf-8").split()
    en_disco = sorted(p.relative_to(REPO).as_posix() for p in REPO.rglob("*.md"))
    assert sorted(lista) == en_disco


def test_sin_resumenes_a_mano():
    for p in REPO.rglob("*.md"):
        t = p.read_text(encoding="utf-8")
        assert server.MARCA_RESUMEN not in t, p.name


async def test_listar_categorias():
    r = await server.listar_categorias()
    assert "Corpus público de la CREG" in r
    assert "Decretos" not in r
    # cada fila cuenta sus resoluciones (antes el plural mal armado las dejaba en 0)
    filas = re.findall(r"^\| [^|]+ \| (\d+) \| (\d+) \| (\d+) \|$", r, re.M)
    assert filas and sum(int(f[0]) for f in filas) > 0
    assert all(int(a) + int(b) == int(t) for a, b, t in filas)


async def test_buscar_agpe():
    r = await server.buscar_documentos(BuscarInput(query="AGPE excedentes", limite=5))
    assert "Ruta" in r


async def test_030_derogada_por_174():
    """La prueba de fuego: la CREG 030/2018 no se cita como vigente."""
    r = await server.buscar_documentos(BuscarInput(query="030 2018", limite=10))
    ruta = re.search(r"`([^`]*030_2018[^`]*)`", r).group(1)
    leido = await server.leer_documento(LeerDocumentoInput(ruta=ruta, max_caracteres=500))
    cabecera = leido.split("\n\n", 1)[0].lower()
    assert "derogada" in cabecera and "174" in cabecera, cabecera
    rel = await server.relaciones(RelacionesInput(norma="030 de 2018"))
    assert "174" in rel


async def test_174_vigente():
    rel = await server.relaciones(RelacionesInput(norma="174 de 2021"))
    assert "174" in rel
    r = await server.buscar_documentos(BuscarInput(query="174 2021", limite=10))
    ruta = re.search(r"`([^`]*174[-_]2021[^`]*)`", r).group(1)
    leido = await server.leer_documento(LeerDocumentoInput(ruta=ruta, max_caracteres=500))
    assert "vigente" in leido.split("\n\n", 1)[0].lower()


async def test_no_escapa_del_corpus():
    r = await server.leer_documento(LeerDocumentoInput(ruta="../../server.py"))
    assert r.startswith("Error")


@pytest.mark.parametrize("texto", ["ARTÍCULO 23", "excedentes"])
async def test_buscar_dentro(texto):
    r = await server.buscar_documentos(BuscarInput(query="174 2021", limite=10))
    ruta = re.search(r"`([^`]*174[-_]2021[^`]*)`", r).group(1)
    leido = await server.leer_documento(LeerDocumentoInput(ruta=ruta, buscar=texto, max_caracteres=2000))
    assert "aparece" in leido

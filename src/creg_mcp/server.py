#!/usr/bin/env python3
"""
Servidor MCP de consulta de la regulación de la CREG.

Expone el texto de resoluciones y conceptos de la Comisión de Regulación de
Energía y Gas (CREG) de Colombia, con la vigencia de cada norma calculada desde
los propios textos y el grafo normativo (fundamento, predecesoras y reemplazos).

Herramientas:
  - creg_listar_categorias: inventario del corpus por categoría y tipo
  - creg_buscar: buscar documentos por palabra clave
  - creg_leer_documento: leer una norma por tramos o buscando dentro, con su vigencia calculada
  - creg_relaciones: grafo normativo de una norma

Uso:
  creg-mcp              # servidor stdio
  creg-mcp --test       # prueba rápida de las herramientas

Autor: Juan Pablo Salamanca. Licencia MIT (el código). Los textos de la CREG
son documentos oficiales publicados por la entidad; ver NOTICE.md.
"""

import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from mcp.server.fastmcp import FastMCP

from .vigencia import REPO as REPO_DIR

# Separa la norma de un resumen escrito a mano (el corpus público no trae ninguno).
MARCA_RESUMEN = "<!-- resumen no normativo -->"

TIPO_SINGULAR = {
    "resoluciones": "resolucion",
    "conceptos": "concepto",
}

CATEGORIA_NOMBRES = {
    "01_FNCER_y_Generacion_Distribuida": "FNCER y Generación Distribuida",
    "02_Comercializacion_y_Mercado": "Comercialización y Mercado",
    "03_Distribucion_y_Conexion": "Distribución y Conexión",
    "04_Medida": "Medida",
    "05_Tarifas": "Tarifas",
    "06_Cargo_por_Confiabilidad": "Cargo por Confiabilidad",
    "10_ZNI": "Zonas No Interconectadas",
    "11_Almacenamiento": "Almacenamiento de Energía",
}

mcp = FastMCP("creg_mcp")


def _escanear_repositorio() -> list:
    """Escanea el repositorio y devuelve lista de documentos con metadata."""
    docs = []
    for carpeta in sorted(REPO_DIR.iterdir()):
        if not carpeta.is_dir() or not carpeta.name[:2].isdigit():
            continue
        categoria = carpeta.name
        for subtipo, tipo_singular in TIPO_SINGULAR.items():
            subdir = carpeta / subtipo
            if not subdir.is_dir():
                continue
            for md_file in sorted(subdir.glob("*.md")):
                titulo = md_file.stem.replace("_", " ")
                tema = ""
                resumen = ""
                try:
                    with open(md_file, "r", encoding="utf-8") as f:
                        content = f.read(2000)
                    h1 = re.search(r"^#\s+(.+)", content, re.MULTILINE)
                    if h1:
                        titulo = h1.group(1).strip()
                    tema_match = re.search(r"\*\*Tema\*\*\s*\|\s*(.+)", content)
                    if tema_match:
                        tema = tema_match.group(1).strip()
                    # Primer párrafo después del metadata como resumen
                    after_hr = content.split("---")
                    if len(after_hr) > 1:
                        text = re.sub(r"[#|*\[\]]", "", after_hr[-1]).strip()
                        resumen = text[:300]
                except Exception:
                    pass

                docs.append({
                    "archivo": md_file.name,
                    "ruta": str(md_file.relative_to(REPO_DIR)),
                    "categoria": CATEGORIA_NOMBRES.get(categoria, categoria),
                    "categoria_id": categoria,
                    "tipo": tipo_singular,  # resolucion, concepto, decreto
                    "titulo": titulo,
                    "tema": tema,
                    "resumen": resumen[:200],
                })
    return docs



class BuscarInput(BaseModel):
    """Input para búsqueda en documentos regulatorios."""
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(
        ...,
        description="Palabra clave para buscar (ej: 'AGPE', 'excedentes', 'tarifa', 'conexion solar', 'Resolucion 174')",
        min_length=2,
        max_length=200,
    )
    categoria: Optional[str] = Field(
        default=None,
        description="Filtrar por ID de categoría (ej: '01_FNCER_y_Generacion_Distribuida'). Dejar vacío para buscar en todas.",
    )
    tipo: Optional[str] = Field(
        default=None,
        description="Filtrar por tipo: 'resolucion' o 'concepto'. Dejar vacío para todos.",
    )
    limite: int = Field(
        default=10,
        description="Máximo de resultados a retornar",
        ge=1,
        le=50,
    )
    todos: bool = Field(
        default=False,
        description=("Si es true, un documento solo cuenta si contiene TODOS los términos. "
                     "Por defecto basta con uno (OR), así que un término inventado no estrecha nada."),
    )


class LeerDocumentoInput(BaseModel):
    """Input para leer un documento regulatorio."""
    model_config = ConfigDict(str_strip_whitespace=True)

    ruta: str = Field(
        ...,
        description="Ruta relativa del documento dentro del repositorio (ej: '01_FNCER_y_Generacion_Distribuida/conceptos/concepto_creg_0003525_2025.md')",
        min_length=5,
    )
    max_caracteres: int = Field(
        default=8000,
        description="Máximo de caracteres a retornar del contenido",
        ge=500,
        le=50000,
    )
    desde: int = Field(
        default=0,
        description=("Posición (en caracteres) desde la que leer. Los documentos largos se leen "
                     "por tramos: la respuesta dice cuál es el siguiente 'desde'."),
        ge=0,
    )
    buscar: Optional[str] = Field(
        default=None,
        description=("Texto a localizar dentro del documento (ej: 'ARTÍCULO 20', 'excedentes'). "
                     "Devuelve los fragmentos donde aparece, con su posición para leer con 'desde'. "
                     "Sin distinguir mayúsculas ni tildes."),
        min_length=3,
        max_length=200,
    )


class RelacionesInput(BaseModel):
    """Input para ver las relaciones de una norma en el grafo normativo."""
    model_config = ConfigDict(str_strip_whitespace=True)

    norma: str = Field(
        ...,
        description=("Norma como '174 de 2021', '174/2021', '101-099/2026', o la ruta de su documento "
                     "(la que devuelve creg_buscar)."),
        min_length=4,
        max_length=300,
    )
    profundidad: int = Field(
        default=1,
        description="1: solo sus relaciones directas. 2 o 3: también las de sus predecesoras y reemplazos.",
        ge=1,
        le=3,
    )



@mcp.tool(
    name="creg_listar_categorias",
    annotations={
        "title": "Listar categorías del repositorio regulatorio",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def listar_categorias() -> str:
    """Lista las categorías del repositorio regulatorio CREG con conteo de documentos.

    Retorna un resumen del inventario: cuántas resoluciones, conceptos y decretos
    hay en cada carpeta temática. Útil para entender qué regulación está disponible
    antes de buscar documentos específicos.

    Returns:
        str: Resumen en Markdown con categorías y conteos.
    """
    docs = _escanear_repositorio()

    # Agrupar por categoría
    por_cat = {}
    for d in docs:
        cat = d["categoria"]
        por_cat.setdefault(cat, {"resoluciones": 0, "conceptos": 0, "total": 0})
        tipo_key = {v: k for k, v in TIPO_SINGULAR.items()}.get(d["tipo"], d["tipo"])
        if tipo_key in por_cat[cat]:
            por_cat[cat][tipo_key] += 1
        por_cat[cat]["total"] += 1

    lines = [
        f"# Corpus público de la CREG — {len(docs)} documentos\n",
        "| Categoría | Resoluciones | Conceptos | Total |",
        "|-----------|:---:|:---:|:---:|",
    ]
    for cat, counts in por_cat.items():
        lines.append(
            f"| {cat} | {counts['resoluciones']} | {counts['conceptos']} | {counts['total']} |"
        )

    lines.append(f"\n**Total**: {len(docs)} documentos")
    lines.append("\nCategorías temáticas disponibles para filtrar:")
    for cat_id, cat_name in CATEGORIA_NOMBRES.items():
        lines.append(f"- `{cat_id}` → {cat_name}")

    return "\n".join(lines)


@mcp.tool(
    name="creg_buscar",
    annotations={
        "title": "Buscar en documentos regulatorios CREG",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def buscar_documentos(params: BuscarInput) -> str:
    """Busca documentos regulatorios del sector eléctrico colombiano por palabra clave.

    Busca en títulos, temas, nombres de archivo y resúmenes de los documentos
    .md del repositorio. Útil para encontrar resoluciones CREG, conceptos jurídicos,
    leyes y decretos sobre FNCER, generación distribuida, tarifas, conexión, etc.

    Args:
        params (BuscarInput): Parámetros de búsqueda:
            - query (str): Palabra clave (ej: 'AGPE', 'excedentes', 'solar')
            - categoria (Optional[str]): Filtrar por categoría
            - tipo (Optional[str]): 'resolucion', 'concepto', o 'decreto'
            - limite (int): Máximo resultados (default 10)
            - todos (bool): exigir todos los términos. Por defecto la búsqueda
              puntúa término a término (OR): 'zanahoria AGPE' devuelve lo mismo
              que 'AGPE'.

    Returns:
        str: Resultados en Markdown con título, categoría, tipo y ruta de cada documento.
    """
    docs = _escanear_repositorio()
    q = params.query.lower()

    # Filtrar por categoría y tipo
    if params.categoria:
        docs = [d for d in docs if d["categoria_id"] == params.categoria]
    if params.tipo:
        # Se acepta singular o plural: "resolucion" y "resoluciones" filtran igual.
        pedido = params.tipo.strip().lower()
        pedido = TIPO_SINGULAR.get(pedido, pedido)
        docs = [d for d in docs if d["tipo"] == pedido]

    # Buscar por query (scoring simple)
    resultados = []
    for d in docs:
        score = 0
        searchable = f"{d['titulo']} {d['tema']} {d['archivo']} {d['resumen']}".lower()
        for term in q.split():
            if term in searchable:
                score += 1
                # Bonus por match en título
                if term in d["titulo"].lower():
                    score += 2
                if term in d["tema"].lower():
                    score += 1
        if params.todos and not all(t in searchable for t in q.split()):
            continue
        if score > 0:
            resultados.append((score, d))

    resultados.sort(key=lambda x: x[0], reverse=True)
    resultados = resultados[: params.limite]

    if not resultados:
        return f"No se encontraron documentos para '{params.query}'. Intenta con otros términos o sin filtros de categoría/tipo."

    lines = [f"# Resultados para '{params.query}' — {len(resultados)} documentos\n"]
    for i, (score, d) in enumerate(resultados, 1):
        lines.append(f"## {i}. {d['titulo']}")
        lines.append(f"- **Tipo**: {d['tipo'].capitalize()}")
        lines.append(f"- **Categoría**: {d['categoria']}")
        if d["tema"]:
            lines.append(f"- **Tema**: {d['tema']}")
        lines.append(f"- **Ruta**: `{d['ruta']}`")
        if d["resumen"]:
            lines.append(f"- **Extracto**: {d['resumen'][:150]}...")
        lines.append("")

    lines.append("---")
    lines.append("Usa `creg_leer_documento` con la ruta para ver el contenido completo.")
    return "\n".join(lines)


@mcp.tool(
    name="creg_leer_documento",
    annotations={
        "title": "Leer documento regulatorio CREG",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def leer_documento(params: LeerDocumentoInput) -> str:
    """Lee el contenido completo de un documento regulatorio .md del repositorio.

    Dado la ruta relativa de un documento (obtenida de creg_buscar),
    retorna su contenido en Markdown. Incluye la tabla de metadata y el texto
    completo de la resolución, concepto o decreto.

    Antepone la vigencia CALCULADA por vigencia.py desde la propia
    norma (cláusula de vigencia y derogatorias del corpus). Esa es la que se
    cita, no la fila Estado del documento.

    Varias normas pasan de 50 000 caracteres (la 174/2021 tiene más de 200 000):
    para citar un artículo, localizarlo con `buscar` y leerlo con `desde`.

    Args:
        params (LeerDocumentoInput): Parámetros:
            - ruta (str): Ruta relativa del documento
            - max_caracteres (int): Límite de caracteres (default 8000)
            - desde (int): Posición desde la que leer (default 0)
            - buscar (str): Texto a localizar; devuelve fragmentos con su posición

    Returns:
        str: Vigencia calculada y el tramo pedido del documento, o los fragmentos
        donde aparece `buscar`.
    """
    filepath = REPO_DIR / params.ruta

    # Validación de seguridad: no escapar del repositorio
    try:
        filepath.resolve().relative_to(REPO_DIR.resolve())
    except ValueError:
        return "Error: La ruta está fuera del repositorio regulatorio."

    if not filepath.exists():
        return f"Error: Documento no encontrado en '{params.ruta}'. Usa creg_buscar para encontrar rutas válidas."

    if not filepath.suffix == ".md":
        return "Error: Solo se pueden leer archivos .md del repositorio."

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return f"Error al leer el archivo: {e}"

    cabecera = _vigencia_de(params.ruta)
    if MARCA_RESUMEN in content:
        content, resumen = content.split(MARCA_RESUMEN, 1)

    total = len(content)

    if params.buscar:
        norm, mapa = _normalizar_con_mapa(content)
        aguja = _normalizar_con_mapa(params.buscar)[0]
        posiciones, i = [], norm.find(aguja)
        while i >= 0 and len(posiciones) < 200:
            posiciones.append(mapa[i])
            i = norm.find(aguja, i + max(len(aguja), 1))
        if not posiciones:
            return f"{cabecera}\n\n'{params.buscar}' no aparece en `{params.ruta}` ({total} caracteres)."
        lineas = [cabecera, "",
                  f"'{params.buscar}' aparece {len(posiciones)} veces en `{params.ruta}` ({total} caracteres)."]
        usado = 0
        for n, pos in enumerate(posiciones, 1):
            ini, fin = max(0, pos - 150), min(total, pos + 700)
            fragmento = content[ini:fin].strip()
            if usado + len(fragmento) > params.max_caracteres:
                resto = ", ".join(str(x) for x in posiciones[n - 1:n + 19])
                lineas.append(f"\n*[{len(posiciones) - n + 1} apariciones más no mostradas; "
                              f"posiciones {resto}{'...' if len(posiciones) > n + 19 else ''}. "
                              f"Subir max_caracteres o leer con desde.]*")
                break
            usado += len(fragmento)
            lineas.append(f"\n### {n}. posición {pos} (leer con desde={ini})\n\n{fragmento}")
        return "\n".join(lineas)

    if params.desde >= total:
        return f"{cabecera}\n\nError: desde={params.desde} pasa del final del documento ({total} caracteres)."
    fin = min(total, params.desde + params.max_caracteres)
    tramo = content[params.desde:fin]
    if params.desde == 0 and fin == total:
        return f"{cabecera}\n\n{tramo}"
    pie = (f"\n\n---\n*[Caracteres {params.desde}-{fin} de {total}. "
           + (f"Siguiente tramo: desde={fin}. " if fin < total else "Fin del documento. ")
           + "Para ubicar un artículo, usar buscar.]*")
    return f"{cabecera}\n\n{tramo}{pie}"


@mcp.tool(
    name="creg_relaciones",
    annotations={
        "title": "Grafo normativo: fundamento, predecesoras y reemplazos de una norma",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def relaciones(params: RelacionesInput) -> str:
    """Muestra de dónde viene una norma, qué deroga o modifica y quién la derogó o modificó.

    Sale de grafo.py, que lee las cláusulas de los propios textos
    (deroga, modifica, adiciona, sustituye, "derogado por" en las anotaciones del
    Gestor, y las leyes invocadas en el preámbulo). Cada relación trae la cita y
    la ruta del documento para abrirlo.

    NO sustituye la lectura: para citar una norma, aunque sea para decir que está
    derogada, abrir su documento con creg_leer_documento. Esto dice dónde
    mirar; la cita sale de lo leído.

    Args:
        params (RelacionesInput): norma ('174 de 2021' o ruta) y profundidad (1-3).

    Returns:
        str: Árbol en texto con fundamento, predecesoras, reemplazos, proyectos y
        conceptos que la mencionan.
    """
    g = _grafo()
    from . import grafo as gn

    clave = None
    ruta = params.norma.replace("\\", "/")
    for c, n in g["nodos"].items():
        if any(ruta.endswith(a) or a.endswith(ruta) for a in n["archivos"]):
            clave = c
            break
    clave = clave or gn.clave_de(params.norma)
    if not clave:
        return f"No entiendo '{params.norma}': usar '174 de 2021', '174/2021' o la ruta del documento."
    return (gn.arbol(g, clave, params.profundidad)
            + "\n\n---\nPara citar cualquiera de estas normas, abrirla con creg_leer_documento "
              "(las 'fuera del repositorio' no se pueden leer con el MCP: no se citan como leídas).")



_CACHE_GRAFO: dict = {}


def _grafo() -> dict:
    """Grafo normativo, recalculado si cambia algún documento del corpus."""
    from . import grafo as gn, vigencia as verificar_vigencia
    firma = tuple((str(x), x.stat().st_mtime_ns) for x in verificar_vigencia.documentos())
    if _CACHE_GRAFO.get("firma") != firma:
        _CACHE_GRAFO.update(firma=firma, grafo=gn.construir())
    return _CACHE_GRAFO["grafo"]


def _normalizar_con_mapa(texto: str) -> tuple[str, list[int]]:
    """Minúsculas y sin tildes, con el índice de cada carácter en el original."""
    salida, mapa = [], []
    for i, c in enumerate(texto):
        for b in unicodedata.normalize("NFD", c.lower()):
            if not unicodedata.combining(b):
                salida.append(b)
                mapa.append(i)
    return "".join(salida), mapa


_CACHE_VIGENCIA: dict = {}


def _vigencia_de(ruta: str) -> str:
    """Línea con la vigencia calculada del documento; se recalcula si cambia el corpus."""
    try:
        from . import vigencia as verificar_vigencia
        firma = tuple((str(x), x.stat().st_mtime_ns) for x in verificar_vigencia.documentos())
        if _CACHE_VIGENCIA.get("firma") != firma:
            docs, _ = verificar_vigencia.calcular_todo()
            _CACHE_VIGENCIA.update(firma=firma, docs={d["archivo"]: d for d in docs})
        d = _CACHE_VIGENCIA["docs"].get(ruta.replace("\\", "/"))
    except Exception as e:  # noqa: BLE001 — el cálculo no debe impedir leer la norma
        return f"> **Vigencia calculada**: no se pudo calcular ({type(e).__name__}: {e})"
    if d is None:
        return "> **Vigencia calculada**: el documento no está en el corpus que calcula vigencia.py"
    mod = f" — modificada parcialmente por {', '.join(d['modificada_por'])}" if d["modificada_por"] else ""
    return (f"> **Vigencia calculada** (vigencia.py, desde la propia norma y el corpus): "
            f"**{d['calculado']}**{mod}. Evidencia: {d['evidencia']}")



async def _test():
    """Prueba rápida de las herramientas."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(await listar_categorias())
    print(await buscar_documentos(BuscarInput(query="excedentes AGPE", limite=3)))
    print((await relaciones(RelacionesInput(norma="030 de 2018")))[:1500])


def main() -> None:
    if "--test" in sys.argv:
        import asyncio
        asyncio.run(_test())
    else:
        mcp.run()


if __name__ == "__main__":
    main()

"""Prueba de protocolo: el servidor arranca por stdio como lo lanza un cliente MCP
(python -m creg_mcp.server con PYTHONPATH=src), responde a tools/list con las
cuatro tools y sus schemas, y ejecuta una de punta a punta.
"""

from __future__ import annotations

import os
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

TOOLS_ESPERADAS = {"creg_listar_categorias", "creg_buscar", "creg_leer_documento", "creg_relaciones"}


def _parametros() -> StdioServerParameters:
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    return StdioServerParameters(command=sys.executable, args=["-m", "creg_mcp.server"], env=env)


async def test_tools_list_por_stdio():
    async with stdio_client(_parametros()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resultado = await session.list_tools()
    tools = {t.name: t for t in resultado.tools}
    assert set(tools) == TOOLS_ESPERADAS, f"tools distintas: {sorted(set(tools) ^ TOOLS_ESPERADAS)}"
    assert all((t.description or "").strip() for t in tools.values())


async def test_relaciones_por_stdio():
    async with stdio_client(_parametros()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            r = await session.call_tool("creg_relaciones", {"params": {"norma": "030 de 2018"}})
    texto = "".join(c.text for c in r.content if getattr(c, "type", "") == "text")
    assert "174" in texto

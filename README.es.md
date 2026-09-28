# CREG MCP Server

*[Read in English](README.md)*

Servidor MCP (Model Context Protocol) para consultar la regulación de la Comisión de Regulación de Energía y Gas (CREG) de Colombia. Un cliente MCP (Claude Desktop, Claude Code u otro) puede buscar resoluciones y conceptos, leerlos por tramos o buscando dentro, y ver el grafo normativo de cada norma: de qué ley viene, qué deroga o modifica y quién la derogó o la modificó.

Lo que lo distingue de un buscador es que **la vigencia no se teclea: se calcula desde los propios textos**. Cada lectura antepone la vigencia calculada de la norma (su cláusula de vigencia y las derogatorias del corpus, con la evidencia), de modo que una resolución derogada no se cita como vigente. La CREG 030 de 2018, por ejemplo, sale derogada por la 174 de 2021.

## Tools

| Tool | Qué hace |
|---|---|
| `creg_listar_categorias` | Inventario del corpus por categoría temática y tipo |
| `creg_buscar` | Busca documentos por palabra clave, con filtro por categoría y por tipo (`resolucion`, `concepto`) |
| `creg_leer_documento` | Lee una norma por tramos (`desde`) o buscando dentro (`buscar`), con su vigencia calculada al inicio |
| `creg_relaciones` | Grafo normativo de una norma (`174 de 2021`, `174/2021` o su ruta): fundamento, predecesoras, reemplazos y conceptos que la mencionan |

Cada tool recibe un único objeto `params`, por ejemplo `creg_relaciones(params={"norma": "030 de 2018"})`.

Uso recomendado: `creg_buscar` para encontrar la norma, `creg_relaciones` para saber dónde mirar y `creg_leer_documento` para citar. El grafo dice dónde mirar; la cita sale de lo leído.

## Corpus

Resoluciones y conceptos de la CREG en Markdown, dentro del paquete (`src/creg_mcp/corpus/`), organizados por categoría temática: FNCER y generación distribuida, comercialización y mercado, distribución y conexión, medida, tarifas, cargo por confiabilidad, zonas no interconectadas y almacenamiento. La lista completa está en `corpus.txt`.

- Solo textos de la CREG. No trae normas técnicas (IEC, IEEE, NTC), que tienen derechos de autor, ni leyes, decretos o el RETIE.
- Solo el texto de la norma: los resúmenes de trabajo escritos a mano no se incluyen.
- El corpus es una selección con fecha de corte, no el universo de la CREG. Una norma que no está en el corpus aparece en el grafo como «fuera del repositorio» y no se puede leer con el servidor: no se cita como leída.
- Para usar otro corpus con la misma estructura (`<categoría>/resoluciones|conceptos/*.md`), definir `CREG_MCP_CORPUS` con su ruta.

## Instalación

Requiere Python 3.10 o posterior.

```bash
git clone https://github.com/jpsalamanca-co/creg-mcp.git
cd creg-mcp
pip install -e ".[dev]"   # [dev] agrega pytest, pytest-asyncio y ruff
python -m pytest tests -q
```

## Configuración en el cliente

Claude Desktop (`claude_desktop_config.json`) o Claude Code (`.mcp.json`):

```json
{
  "mcpServers": {
    "creg": {
      "command": "creg-mcp",
      "env": { "PYTHONIOENCODING": "utf-8" }
    }
  }
}
```

Para ejecutarlo directamente por stdio: `creg-mcp` o `python -m creg_mcp.server`. Prueba rápida sin cliente: `creg-mcp --test`.

## Pruebas

`python -m pytest tests -q` comprueba:

- el corpus trae solo resoluciones y conceptos de la CREG, sin resúmenes a mano, y coincide con `corpus.txt`;
- la CREG 030 de 2018 sale derogada por la 174 de 2021 y la 174 de 2021 sale vigente;
- la lectura no escapa de la carpeta del corpus;
- por stdio, el servidor lista sus cuatro tools y responde el grafo de una norma.

## Alcance

Es una herramienta de consulta, no un concepto jurídico. La vigencia calculada sale de las reglas escritas en `vigencia.py` sobre el corpus que trae el paquete: una norma posterior que no esté en el corpus no puede tenerse en cuenta. Antes de aplicar una norma, confirmar su texto y su estado en la fuente oficial de la CREG.

## Licencia

El código, MIT (ver [LICENSE](LICENSE)). Los textos de la CREG son documentos oficiales publicados por la entidad; ver [NOTICE.md](NOTICE.md).

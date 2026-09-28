# CREG MCP Server

*[Leer en español](README.es.md)*

An MCP (Model Context Protocol) server for querying the regulation of Colombia's Energy and Gas Regulatory Commission (CREG, *Comisión de Regulación de Energía y Gas*). Claude Desktop, Claude Code or any other MCP client can search CREG resolutions and legal opinions (*conceptos*), read them in chunks or by searching inside, and see each rule's regulatory graph: which law it rests on, what it repeals or amends, and what later repealed or amended it.

What sets it apart from a search engine is that **validity is not typed in by hand: it is computed from the texts themselves**. Every read starts with the rule's computed status (its effective-date clause and the repeals found in the corpus, with the evidence), so a repealed resolution is not cited as current. For example, CREG 030 of 2018 comes out repealed by CREG 174 of 2021.

The documents are in Spanish, as published by the CREG; tool names and outputs are in Spanish too.

## Tools

| Tool | What it does |
|---|---|
| `creg_listar_categorias` | Corpus inventory by topic and document type |
| `creg_buscar` | Keyword search, filtered by topic and type (`resolucion`, `concepto`) |
| `creg_leer_documento` | Reads a rule in chunks (`desde`) or by searching inside (`buscar`), with its computed validity first |
| `creg_relaciones` | Regulatory graph of a rule (`174 de 2021`, `174/2021` or its path): legal basis, predecessors, replacements and the opinions that cite it |

Each tool takes a single `params` object, for example `creg_relaciones(params={"norma": "030 de 2018"})`.

Suggested use: `creg_buscar` to find the rule, `creg_relaciones` to know where to look, `creg_leer_documento` to cite. The graph tells you where to look; the citation comes from what you read.

## Corpus

CREG resolutions and opinions in Markdown, shipped inside the package (`src/creg_mcp/corpus/`), organised by topic: renewables and distributed generation (AGPE, GD), trading and wholesale market, distribution and grid connection, metering, tariffs, reliability charge, non-interconnected zones (ZNI) and energy storage. The full list is in `corpus.txt`.

- CREG texts only: no technical standards (IEC, IEEE, NTC), which are copyrighted, and no laws, decrees or RETIE.
- Only the text of the rule: handwritten working summaries are not included.
- It is a dated selection, not the whole of CREG regulation. A rule outside the corpus shows up in the graph as "fuera del repositorio" and cannot be read through the server: do not cite it as read.
- To use another corpus with the same layout (`<topic>/resoluciones|conceptos/*.md`), set `CREG_MCP_CORPUS` to its path.

## Installation

Requires Python 3.10 or later.

```bash
git clone https://github.com/jpsalamanca-co/creg-mcp.git
cd creg-mcp
pip install -e ".[dev]"   # [dev] adds pytest, pytest-asyncio and ruff
python -m pytest tests -q
```

## Client configuration

Claude Desktop (`claude_desktop_config.json`) or Claude Code (`.mcp.json`):

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

To run it directly over stdio: `creg-mcp` or `python -m creg_mcp.server`. Quick check without a client: `creg-mcp --test`.

## Tests

`python -m pytest tests -q` checks that:

- the corpus holds only CREG resolutions and opinions, with no handwritten summaries, and matches `corpus.txt`;
- CREG 030 of 2018 comes out repealed by 174 of 2021, and 174 of 2021 comes out in force;
- reads cannot escape the corpus folder;
- over stdio, the server lists its four tools and answers a rule's graph.

## Scope

A lookup tool, not legal advice. Computed validity comes from the rules written in `vigencia.py` applied to the corpus in the package: a later rule that is not in the corpus cannot be taken into account. Before applying a rule, confirm its text and status at the CREG's official source.

## License

Code: MIT, see [LICENSE](LICENSE). The CREG texts are official documents published by the Commission; see [NOTICE.md](NOTICE.md).

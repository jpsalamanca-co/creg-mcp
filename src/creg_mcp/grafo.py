#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grafo normativo: de dónde viene cada norma, qué reemplaza y qué la reemplazó.

POR QUÉ EXISTE
    En la corrida en vivo de D5-2 (2026-09-12) el analista citó la 030/2018 como
    derogada sin abrirla, y leyendo encontró que la 101-099/2026 modifica los
    artículos 1 y 2 de la 174/2021, algo que ningún resumen registraba. Las dos
    cosas son relaciones entre normas. Leídas una por una no se ven; puestas en
    un grafo se ven de un vistazo, y se pueden revisar con código.

QUÉ ES
    Nodos: cada norma del repositorio y cada norma que alguna de ellas nombra
    (las de fuera quedan marcadas "fuera del repositorio").
    Aristas, siempre de la norma que actúa a la norma sobre la que actúa:
        deroga                la mata entera
        deroga parcialmente   mata un artículo, parágrafo, anexo...
        modifica              modifica, adiciona o sustituye algo de ella
        fundamenta            ley o decreto invocado en el preámbulo del acto
        interpreta            concepto -> norma que menciona
        propone: ...          lo mismo, dicho por un proyecto (no actúa)
    Cada arista lleva la cita y si sale del texto dispositivo o de una anotación
    del Gestor. Las aristas son las mismas que usa vigencia.py: una
    sola lectura de los textos, dos vistas.

CHEQUEOS
    Errores (salida 1):
      - derogación en ciclo: A deroga a B y B deroga a A
      - modificada después de muerta: una norma derogada por completo en el año
        Y que otra norma de un año posterior modifica o deroga parcialmente. O
        la derogatoria está mal leída, o la modificación cita el número mal.
    Avisos (no fallan, se revisan):
      - conceptos que mencionan una norma que ya estaba derogada cuando se
        emitieron (el concepto 3726/2025 y la 030/2018): puede ser historia, o
        puede ser un concepto que se apoya en una norma muerta
      - conceptos que interpretan una norma que otra del repositorio modificó
        después de emitido el concepto: el 1867/2024 liquida a bolsa con la 174
        original, y la 101-072/2025 lo pasó a MC
      - normas de fuera del repositorio que más actúan sobre las de dentro:
        candidatas a traer, porque sin su texto su efecto solo se ve de lado

USO
    python grafo.py                         resumen y chequeos
    python grafo.py --norma "174 de 2021"   árbol de una norma
    python grafo.py --norma 174/2021 --profundidad 2
    python grafo.py --json                  grafo completo
    python grafo.py --escribir              regenera regulacion/GRAFO_NORMATIVO.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from . import vigencia as vv  # noqa: E402

SALIDA_MD = vv.REPO / "GRAFO_NORMATIVO.md"
ACTUAN = ("deroga", "deroga parcialmente", "modifica")


def orden(clave) -> tuple:
    """Por año y luego por número como número: 1867 antes que 11483."""
    return (clave[1], [int(x) if x.isdigit() else 0 for x in str(clave[0]).split("-")])


def etiqueta(clave) -> str:
    return f"{clave[0]} de {clave[1]}"


def clave_de(texto: str):
    """'174 de 2021', '174/2021', '101-099/2026', 'CREG 101 099 de 2026' -> clave."""
    # Acuerdos del CNO: 'CNO 2229 de 2026' -> ('CNO-2229', 2026), como los guarda vigencia.py
    m = re.search(r"(?i)\bCNO\s+(\d{1,5})\s*(?:de\s+|/)\s*(\d{4})", texto)
    if m:
        return vv.canon("CNO " + m.group(1)), int(m.group(2))
    m = re.search(r"(\d{1,4}(?:[\s_-]\d{1,3})?)\s*(?:de\s+|/)\s*(\d{4})", texto)
    return (vv.canon(m.group(1)), int(m.group(2))) if m else None


def construir() -> dict:
    """Nodos, aristas y descartadas. Mismo corpus y mismas reglas que la vigencia."""
    docs = [vv.analizar(p) for p in vv.documentos()]
    aristas, descartadas = vv.aristas_del_corpus(docs)
    derogada_por, modificada_por, _ = vv.grafo(docs)
    nodos: dict = {}
    for d in docs:
        if not d["numero"]:
            continue
        estado, evidencia = vv.calcular(d, derogada_por)
        n = nodos.setdefault((d["numero"], d["anio"]), {"archivos": []})
        # La referencia cruzada (101-072/2025 tiene dos archivos) no pisa a la norma:
        # el nodo toma estado y primer archivo del texto completo.
        if d["tipo"] == "referencia" and n.get("tipo") not in (None, "referencia"):
            n["archivos"].append(d["archivo"])
            continue
        n.update(clave=(d["numero"], d["anio"]), tipo=d["tipo"], estado=estado, evidencia=evidencia,
                 en_repositorio=True)
        n["archivos"].insert(0, d["archivo"])
    for a in aristas:
        for extremo, clase in ((a["origen"], None), (a["destino"], a.get("clase_destino"))):
            if extremo not in nodos:
                nodos[extremo] = {"clave": extremo, "tipo": (clase or "norma").lower(),
                                  "estado": "fuera del repositorio", "evidencia": "", "archivos": [],
                                  "en_repositorio": False}
    # Aristas repetidas (la misma norma anotada 40 veces) se agrupan con sus citas.
    agrupadas: dict = {}
    for a in aristas:
        k = (a["origen"], a["destino"], a["tipo"])
        g = agrupadas.setdefault(k, {"origen": a["origen"], "destino": a["destino"], "tipo": a["tipo"],
                                     "citas": [], "fuentes": set(), "archivos": set(), "articulos": set()})
        g["articulos"].update(a.get("articulos") or [])
        if len(g["citas"]) < 3:
            g["citas"].append(a["cita"])
        g["fuentes"].add(a["fuente"])
        g["archivos"].add(a["archivo"])
    return {"nodos": nodos, "aristas": list(agrupadas.values()), "descartadas": descartadas}


def chequear(g: dict) -> tuple[list[str], list[str]]:
    nodos, aristas = g["nodos"], g["aristas"]
    errores, avisos = [], []
    deroga = {(a["origen"], a["destino"]) for a in aristas if a["tipo"] == "deroga"}
    for o, t in sorted(deroga):
        if (t, o) in deroga and o < t:
            errores.append(f"derogación en ciclo: la {etiqueta(o)} deroga a la {etiqueta(t)} y al revés")
    muerte = defaultdict(list)
    for o, t in deroga:
        muerte[t].append(o)
    for a in aristas:
        if a["tipo"] in ("deroga parcialmente", "modifica") and a["destino"] in muerte:
            anio_muerte = min(o[1] for o in muerte[a["destino"]])
            if a["origen"][1] > anio_muerte:
                errores.append(f"la {etiqueta(a['destino'])} está derogada desde {anio_muerte} "
                               f"(por la {', '.join(etiqueta(o) for o in muerte[a['destino']])}) y la "
                               f"{etiqueta(a['origen'])} la {a['tipo']} después: \"{a['citas'][0][:100]}\"")
    for a in aristas:
        if a["tipo"] == "interpreta" and a["destino"] in muerte:
            anio_muerte = min(o[1] for o in muerte[a["destino"]])
            if a["origen"][1] > anio_muerte:
                avisos.append(f"el concepto {etiqueta(a['origen'])} menciona la {etiqueta(a['destino'])}, "
                              f"derogada desde {anio_muerte} ({a['citas'][0]})")
    # Un concepto interpreta la norma tal como estaba cuando se emitió. Si después
    # otra norma la modificó, la interpretación puede estar superada: el concepto
    # 1867/2024 liquida excedentes a bolsa con la 174 original y la 101-072/2025
    # los pasó a MC (lo encontró la segunda corrida de D5-2).
    modificadas = defaultdict(set)
    for a in aristas:
        if a["tipo"] in ACTUAN:
            modificadas[a["destino"]].add(a["origen"])
    for a in sorted((a for a in aristas if a["tipo"] == "interpreta"), key=lambda a: orden(a["origen"])):
        if a["destino"] not in muerte:
            posteriores = sorted((o for o in modificadas[a["destino"]] if o[1] > a["origen"][1]
                                  and nodos[o]["en_repositorio"]), key=orden)
            if posteriores:
                avisos.append(f"el concepto {etiqueta(a['origen'])} interpreta la {etiqueta(a['destino'])}, "
                              f"modificada después por la {', '.join(etiqueta(o) for o in posteriores)}: "
                              f"su lectura puede estar superada")
    externas = Counter(a["origen"] for a in aristas
                       if a["tipo"] in ACTUAN and not nodos[a["origen"]]["en_repositorio"])
    for clave, n in externas.most_common(8):
        destinos = sorted({etiqueta(a["destino"]) for a in aristas
                           if a["origen"] == clave and a["tipo"] in ACTUAN})
        avisos.append(f"fuera del repositorio, actúa sobre {n} normas del corpus: la {etiqueta(clave)} "
                      f"-> {', '.join(destinos)}")
    return errores, avisos


def arbol(g: dict, clave, profundidad: int = 1) -> str:
    nodos, aristas = g["nodos"], g["aristas"]
    if clave not in nodos:
        return f"la {etiqueta(clave)} no aparece en el grafo (ni en el repositorio ni citada por él)"

    def linea(c):
        n = nodos[c]
        donde = f" `{n['archivos'][0]}`" if n["archivos"] else ""
        return f"{etiqueta(c)} — {n['estado']}{donde}"

    out = [f"# {linea(clave)}"]
    if nodos[clave]["evidencia"]:
        out.append(f"  evidencia: {nodos[clave]['evidencia'][:160]}")

    def seccion(titulo, filtro, extremo, nivel, visto):
        filas = [a for a in aristas if filtro(a)]
        if not filas:
            return
        out.append(f"{'  ' * nivel}{titulo}:")
        for a in sorted(filas, key=lambda a: orden(a[extremo])):
            c = a[extremo]
            fuente = " [anotación del Gestor]" if a["fuentes"] == {"anotación del Gestor"} else ""
            arts = f" (arts. {', '.join(map(str, sorted(a['articulos'])))} de la {etiqueta(a['destino'])})" if a["articulos"] else ""
            out.append(f"{'  ' * nivel}  - {a['tipo']}{arts}: {linea(c)}{fuente}")
            out.append(f"{'  ' * nivel}      \"{a['citas'][0][:140]}\"")
            if nivel + 1 < profundidad and c not in visto and a["tipo"] in ACTUAN:
                visto.add(c)
                recorrer(c, nivel + 2, visto)

    def recorrer(c, nivel, visto):
        seccion("fundamento (leyes y decretos que invoca)",
                lambda a: a["destino"] == c and a["tipo"] == "fundamenta", "origen", nivel, visto)
        seccion("predecesoras (lo que esta norma deroga o modifica)",
                lambda a: a["origen"] == c and a["tipo"] in ACTUAN, "destino", nivel, visto)
        seccion("reemplazos (quién la deroga o modifica)",
                lambda a: a["destino"] == c and a["tipo"] in ACTUAN, "origen", nivel, visto)
        seccion("propuestas (proyectos que la tocarían)",
                lambda a: a["destino"] == c and a["tipo"].startswith("propone"), "origen", nivel, visto)
        if nivel == 0:
            seccion("conceptos que la interpretan",
                    lambda a: a["destino"] == c and a["tipo"] == "interpreta", "origen", nivel, visto)

    recorrer(clave, 0, {clave})
    return "\n".join(out)


def markdown(g: dict, errores: list[str], avisos: list[str]) -> str:
    """Documento generado: diagrama de derogaciones y modificaciones y una ficha por norma."""
    nodos, aristas = g["nodos"], g["aristas"]
    ids = {}

    def nid(c):
        return ids.setdefault(c, f"n{len(ids)}")

    corpus = sorted((c for c, n in nodos.items() if n["en_repositorio"] and n["tipo"] != "concepto"),
                    key=orden)
    lineas = [
        "# Grafo normativo",
        "",
        "> Generado por `grafo.py`. No se edita a mano:",
        "> sale de los mismos textos y reglas que `vigencia.py`.",
        "",
        f"{sum(1 for n in nodos.values() if n['en_repositorio'])} documentos del repositorio, "
        f"{sum(1 for n in nodos.values() if not n['en_repositorio'])} normas citadas que no están, "
        f"{len(aristas)} relaciones.",
        "",
        "## Derogaciones y modificaciones entre normas del repositorio",
        "",
        "Flecha continua: deroga. Gruesa: deroga parcialmente. Punteada: modifica.",
        "",
        "```mermaid",
        "flowchart LR",
    ]
    usados = set()
    for a in sorted(aristas, key=lambda a: (orden(a["origen"]), orden(a["destino"]))):
        if a["tipo"] not in ACTUAN:
            continue
        if not (nodos[a["origen"]]["en_repositorio"] and nodos[a["destino"]]["en_repositorio"]):
            continue
        flecha = {"deroga": "-->", "deroga parcialmente": "==>", "modifica": "-.->"}[a["tipo"]]
        lineas.append(f"  {nid(a['origen'])} {flecha} {nid(a['destino'])}")
        usados.update((a["origen"], a["destino"]))
    for c in sorted(usados, key=orden):
        marca = " ✗" if nodos[c]["estado"] == "derogada" else ""
        lineas.append(f"  {nid(c)}[\"{etiqueta(c)}{marca}\"]")
    lineas += ["```", ""]

    lineas += ["## Chequeos", ""]
    lineas += [f"- **Error:** {e}" for e in errores] or ["- Sin errores."]
    lineas += [f"- Aviso: {x}" for x in avisos]
    lineas += ["", "## Ficha por norma", ""]
    for c in corpus:
        n = nodos[c]
        lineas.append(f"### {etiqueta(c)} — {n['estado']}")
        lineas.append("")
        lineas.append(f"`{n['archivos'][0]}`")
        lineas.append("")
        for titulo, filtro, extremo in (
                ("Fundamento", lambda a: a["destino"] == c and a["tipo"] == "fundamenta", "origen"),
                ("Deroga o modifica", lambda a: a["origen"] == c and a["tipo"] in ACTUAN, "destino"),
                ("Derogada o modificada por", lambda a: a["destino"] == c and a["tipo"] in ACTUAN, "origen"),
                ("Proyectos que la tocarían", lambda a: a["destino"] == c and a["tipo"].startswith("propone"), "origen"),
                ("Conceptos que la mencionan", lambda a: a["destino"] == c and a["tipo"] == "interpreta", "origen")):
            filas = sorted((a for a in aristas if filtro(a)), key=lambda a: orden(a[extremo]))
            if not filas:
                continue
            partes = []
            for a in filas:
                otro = a[extremo]
                fuera = "" if nodos[otro]["en_repositorio"] else " (fuera)"
                tipo = "" if a["tipo"] in ("fundamenta", "interpreta") else f" {a['tipo']}"
                if a["articulos"]:
                    tipo += f" (arts. {', '.join(map(str, sorted(a['articulos'])))})"
                partes.append(f"{etiqueta(otro)}{fuera}{tipo}")
            lineas.append(f"- **{titulo}:** " + "; ".join(partes))
        lineas.append("")
    return "\n".join(lineas).rstrip() + "\n"


def serializable(g: dict) -> dict:
    return {
        "nodos": [dict(n, clave=etiqueta(n["clave"])) for n in g["nodos"].values()],
        "aristas": [dict(a, origen=etiqueta(a["origen"]), destino=etiqueta(a["destino"]),
                         fuentes=sorted(a["fuentes"]), archivos=sorted(a["archivos"]),
                         articulos=sorted(a["articulos"]))
                    for a in g["aristas"]],
        "descartadas": g["descartadas"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Grafo de derogaciones, modificaciones y fundamentos")
    ap.add_argument("--norma", help='"174 de 2021" o "174/2021"')
    ap.add_argument("--profundidad", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--escribir", action="store_true", help="regenera regulacion/GRAFO_NORMATIVO.md")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    g = construir()
    errores, avisos = chequear(g)
    if args.norma:
        clave = clave_de(args.norma)
        if not clave:
            print(f"no entiendo '{args.norma}': usar '174 de 2021' o '174/2021'")
            return 2
        print(arbol(g, clave, args.profundidad))
        return 0
    if args.json:
        print(json.dumps(dict(serializable(g), errores=errores, avisos=avisos), ensure_ascii=False, indent=2))
        return 1 if errores else 0
    if args.escribir:
        SALIDA_MD.write_text(markdown(g, errores, avisos), encoding="utf-8")
        print(f"escrito {SALIDA_MD.relative_to(vv.REPO.parent)}")

    nodos = g["nodos"]
    print(f"{sum(1 for n in nodos.values() if n['en_repositorio'])} documentos, "
          f"{sum(1 for n in nodos.values() if not n['en_repositorio'])} normas de fuera, "
          f"{len(g['aristas'])} relaciones")
    for tipo, n in sorted(Counter(a["tipo"] for a in g["aristas"]).items()):
        print(f"  {tipo:28} {n:>4}")
    if g["descartadas"]:
        print(f"\ndescartadas por orden de años ({len(g['descartadas'])}):")
        for x in g["descartadas"]:
            print("  -", x)
    if avisos:
        print(f"\navisos ({len(avisos)}):")
        for x in avisos:
            print("  -", x)
    if errores:
        print(f"\nERRORES ({len(errores)}):")
        for x in errores:
            print("  -", x)
        return 1
    print("\nVERIFICACION OK: sin ciclos de derogación ni normas modificadas después de derogadas.")
    return 0


if __name__ == "__main__":
    # Consola de Windows en cp1252: la salida va en UTF-8 para quien la lea
    for _flujo in (sys.stdout, sys.stderr):
        if hasattr(_flujo, "reconfigure"):
            _flujo.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())

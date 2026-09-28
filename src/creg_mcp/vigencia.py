#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calcula el estado de vigencia de cada norma del repositorio, a partir de la norma misma.

POR QUÉ EXISTE
    La vigencia de una resolución no la decide quien la lee. La fijan cosas
    escritas en los propios documentos: su cláusula de vigencia, su publicación
    en el Diario Oficial y las normas posteriores que la deroguen. Eso se
    comprueba, no se opina. Que un humano lea la resolución sirve para saber qué
    dice y no equivocarse al aplicarla, que es harina de otro costal.

    Hasta el 2026-09-12 el campo **Estado** lo tecleaba quien convertía el
    documento (`--estado`, por defecto "Por verificar"). De 80 documentos, 43 no
    tenían el campo y 20 decían "Vigente" sin ninguna prueba al lado.

EL TIPO MANDA
    concepto    Interpreta la norma, no rige: no tiene vigencia propia. Decir que
                un concepto está "vigente" es un error de categoría. (0 de 50
                conceptos del corpus traen cláusula de vigencia: es lo esperado.)
    referencia  Documento que solo remite al texto completo en otra carpeta. No
                es una norma aparte; no se le calcula nada.
    proyecto    Serie 701-xxx o título marcado. Sin fuerza vinculante.
    norma       Resolución, ley o decreto. La única a la que se le calcula.

LAS TRES REGLAS QUE COSTARON SANGRE (D5-6, 2026-09-12)

    1. La VOZ decide qué significa "artículo".
       Activa:  "deroga el parágrafo 3 del artículo 22 de la Resolución 174 de
                2021"  -> muere ese parágrafo. La 174 sigue viva. PARCIAL.
       Pasiva:  "DEROGADA por el artículo 31 de la Resolución 174 de 2021"
                -> el artículo 31 identifica a QUIEN DEROGA. El documento que lo
                dice muere entero. TOTAL.
       Una primera versión de este script confundió las dos y declaró derogada la
       Resolución 174 de 2021, que es la que sostiene todo el marco AGPE/GD.

    2. Solo el PRESENTE es operativo.
       "deroga", "derógase" mandan. "derogando lo dispuesto en la Resolución 084
       de 1996" y "derogó tácitamente el Decreto 2469 de 2014" son considerandos
       que relatan historia ajena, no derogatorias de este acto.

    3. La prueba de vigencia necesita FECHA o PUBLICACIÓN.
       Una fila tecleada "Vigente (con modificaciones por Res 701-098-2025)" no
       prueba nada: es la afirmación humana sin respaldo que esto viene a
       reemplazar, y encima invoca un proyecto como si modificara. Se rechaza.
       También se rechazan "Vigencia de la Obligación" (es el período de la OEF)
       y "vigencia de la resolución - Presentar estudio..." (es un requisito).

CUATRO MÁS, AL TRAER LA NORMA COMPLETA DEL GESTOR (D5, 2026-09-12)

    4. La cláusula es la del artículo titulado VIGENCIA, el último antes de
       "Publíquese y cúmplase". La 101-064/2024 transcribe en sus considerandos
       el "ARTÍCULO 20. VIGENCIA Y DEROGATORIAS" de otra resolución 300 líneas
       antes del suyo, y la 015/2018 tiene un "VIGENCIA DE LOS CARGOS POR USO"
       que no es la vigencia del acto.

    5. Las anotaciones del Gestor ("<Artículo derogado por el artículo 20 de la
       Resolución 51 de 2012>") no son disposiciones de la norma que las lleva.
       En pasiva, lo que decide si la norma muere entera es el SUJETO: "Artículo",
       "Anexo", "Formato"... es parcial. Sin esta regla, la 071/2006 completa
       salía derogada por sus 58 anotaciones. Las mismas anotaciones dicen qué
       norma posterior modificó cuál elemento, y eso entra en "modificada por"
       aunque la modificadora no esté en el repositorio.

    6. "deroga la Resolución CREG 094 de 2012 excepto el Capítulo 3" es parcial.

    7. Lo que va después de la marca de resumen no normativo es un resumen
       escrito a mano: no se lee como norma.

    8. "modifica los artículos 1 y 2 de la Resolución CREG 174 de 2021" (101-099/
       2026, art. 60) es modificación parcial, pero solo en la parte resolutiva
       (después de RESUELVE): en un considerando el mismo verbo relata lo que hizo
       otra norma. No la veía nadie; la encontró el analista leyendo el artículo
       en la corrida en vivo de D5-2.

CUÁNDO SÍ DECIDE UNA PERSONA
    "no determinable" no es un fallo del método: es que el texto guardado no dice
    desde cuándo rige, o que la cláusula es ambigua. Esos casos se anotan y los
    resuelve la revisión humana, casi siempre trayendo el texto completo del
    Gestor, que es lo que falta. Pero es el residuo, no la regla: eran 6 de 30
    normas y las 6 eran resúmenes; con el texto del Gestor quedaron en 0. No se usa "que lo revise un humano" como respuesta por defecto para lo
    que el documento sí dice de sí mismo.

USO
    python vigencia.py
    python vigencia.py --json

SALIDA
    0  ningún estado declarado contradice al calculado
    1  hay contradicciones: un documento se declara vigente y otra norma lo derogó
       por completo, se declara derogado sin que nada lo derogue, es un concepto
       que se declara vigente o derogado, o se declara vigente sin cláusula que
       lo pruebe. Se listan con la cita.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

# El corpus público viaja dentro del paquete; CREG_MCP_CORPUS lo cambia.
REPO = Path(os.environ.get("CREG_MCP_CORPUS") or Path(__file__).resolve().parent / "corpus")
# normas_tecnicas: NTC e IEC que el RETIE cita (N-b, 2026-09-16). No tienen cláusula de vigencia ni
# se derogan: la edición que rige la fija el reglamento que la cita.
SUBCARPETAS = ("resoluciones", "conceptos", "decretos", "normas_tecnicas", "acuerdos")
# Separa la norma del resumen de trabajo escrito a mano que se conserva al final.
MARCA_RESUMEN = "<!-- resumen no normativo -->"

MES = r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)"
# Una cláusula sirve de prueba solo si dice CUÁNDO: una fecha real o la publicación.
PRUEBA_TEMPORAL = re.compile(
    r"(?i)(publicaci[óo]n|se\s+publique|promulgaci[óo]n|expedici[óo]n|\d{1,2}\s+de\s+" + MES
    + r"|" + MES + r"\s+\d{1,2}\s+de\s+\d{4}|" + MES + r"\s+de\s+\d{4}|EL\s+\d{1,2}\s+DE)")

# Frases que hablan de "vigencia" pero no de la vigencia de la norma.
FALSA_VIGENCIA = re.compile(r"(?i)vigencia\s+de\s+la\s+obligaci|vigencia\s+de\s+la\s+resoluci[óo]n\s*[-–]\s*present")

PATRONES_VIGENCIA = (
    ("rige a partir", r"(?i)\brige\s+a\s+partir[^.\n]{0,140}"),
    ("rige desde", r"(?i)\brige\s+desde[^.\n]{0,140}"),
    ("entra en vigencia", r"(?i)entrad?[ao]?\s*(?:en)?\s*vigenci[ao][^.\n]{0,140}"),
    ("vigente desde", r"(?i)\bvigente\s+desde[^.\n]{0,140}"),
    ("a partir de la publicación", r"(?i)a\s+partir\s+de\s+la\s+fecha\s+de\s+su\s+publicaci[^.\n]{0,140}"),
    ("fila Vigencia", r"\*\*Vigencia\*\*\s*\|\s*([^|\n]+)"),
    ("encabezado Vigencia", r"(?im)^#+\s*Vigencia\s*\n+([^\n]+)"),
)

# El artículo de vigencia del acto, por su epígrafe. "VIGENCIA DE LOS CARGOS POR
# USO" (015/2018, art. 23) no es la vigencia de la resolución: el epígrafe tiene
# que ser VIGENCIA a secas o VIGENCIA Y DEROGATORIA(S).
EPIGRAFE_VIGENCIA = re.compile(
    r"(?i)ART[ÍI]CULO\s+\d+\s*[oº°]?\s*\.?\s*VIGENCIA(?:\s*,\s*MODIFICACIONES)?(?:\s+Y\s+DEROGATORIAS?)?(?:\s+DE\s+LA\s+(?:PRESENTE\s+)?RESOLUCI[ÓO]N)?\s*\.")
# Filas de la tabla de metadatos ("| **Estado** | vigente (calculado ...) |"). No
# son texto de la norma: la fila Estado la escribe este mismo cálculo, y usarla
# como prueba de vigencia sería circular (pasó con la 119/2007 y la 091/2007).
FILA_METADATOS = re.compile(r"(?m)^\|\s*\*\*[^*|]+\*\*\s*\|.*\|\s*$")
# Modificación activa, solo en la parte resolutiva: "modifica los artículos 1 y 2
# de la Resolución CREG 174 de 2021" (101-099/2026, art. 60). En los
# considerandos el mismo verbo relata lo que hizo otra norma.
PAT_MODIFICA = re.compile(
    r"(?i)\b(?:modifica|modif[íi]case|modif[íi]quese|modif[íi]canse|adiciona|adici[óo]nase|adici[óo]nese|"
    r"sustituye|sustit[úu]yase|sub[íi]rogase|subr[óo]guese)\b")
# "Modifíquese el artículo 25 de la Resolución CREG 174 de 2021" (101-072/2025, art. 28):
# sin el subjuntivo, el grafo solo veía el art. 22 y un analista citó el art. 25
# original, que liquidaba a bolsa, cuando el vigente liquida a MC.
ART_CITADOS = re.compile(r"(?i)\bart[íi]culos?\s+((?:\d{1,3}\s*[°º]?\s*(?:,|y|e)\s*)*\d{1,3})")
RESUELVE = re.compile(r"(?i)\bR\s*E\s*S\s*U\s*E\s*L\s*V\s*E\s*:")
# Fórmula de cierre del acto: lo que va después son anexos o firmas.
CIERRE_ACTO = re.compile(r"(?i)publ[íi]quese\s+y\s+c[úu]mplase|comun[íi]quese|dada\s+en\s+bogot")
# Anotaciones que el Gestor intercala en el texto: "<Artículo derogado por el
# artículo 20 de la Resolución 51 de 2012>". Hablan de otra norma sobre un
# elemento de esta, no son disposiciones de esta.
ANOTACION_GESTOR = re.compile(r"<[^<>\n]{0,600}>")

# Operativo = presente. El gerundio y el pasado relatan historia ajena.
PAT_ACTIVA = re.compile(r"(?i)\b(?:deroga|derogan|der[óo]gase|der[óo]ganse)\b")
PAT_PASIVA = re.compile(r"(?i)\bderogad[ao]s?\b[^.\n]{0,40}?\b(?:por|mediante)\b")
# Sujeto de la pasiva: si lo derogado es un elemento, la norma sigue viva.
SUJETO_ELEMENTO = re.compile(
    r"(?i)(art[íi]culo|par[áa]grafo|numeral|literal|inciso|anexo|cap[íi]tulo|t[íi]tulo|"
    r"formato|definici[óo]n|aparte|secci[óo]n|tabla|expresi[óo]n)s?\b[^<>.\n]{0,40}$")
PAT_REF = re.compile(
    r"(?i)(?:resoluci[óo]n(?:es)?|ley|decreto)\s+(?:creg\s+)?(\d{1,4}(?:[\s_-]\d{1,3})?)\s+de\s+(\d{4})")
HISTORIA_DEL_ELEMENTO = re.compile(
    r"(?i)\b(?:modificad|adicionad|sustituid|subrogad|derogad)[oa]s?\s+(?:por|mediante)\s+"
    r"(?:el\s+art[íi]culo\s+\d+\s+de\s+)?(?:la\s+)?$")
PAT_PARCIAL = re.compile(
    r"(?i)(art[íi]culo|par[áa]grafo|numeral|literal|inciso|anexo|cap[íi]tulo|t[íi]tulo)s?\b[^.]{0,60}$")

# Dónde termina la frase dispositiva: punto seguido de mayúscula, salto de
# párrafo, encabezado, o las fórmulas de cierre del acto administrativo.
FIN_CLAUSULA = re.compile(
    r"(?:\.\s+(?=[A-ZÁÉÍÓÚÑ])|\n\s*\n|\n#{1,6}\s|PUBL[ÍI]QUESE|C[ÚU]MPLASE|ANEXO\s+\d|Dada\s+en\s+Bogot)")


def canon(numero: str) -> str:
    """'101 097' y '101-97' son la misma norma; '030' y '30' también."""
    partes = [p for p in re.split(r"[\s_-]+", numero.strip()) if p and not p.upper() == "CREG"]
    out = []
    for p in partes:
        out.append(str(int(p)) if p.isdigit() else p)
    return "-".join(out)


def documentos() -> list[Path]:
    return sorted(p for p in REPO.rglob("*.md")
                  if p.parent.name in SUBCARPETAS and p.parent.parent.name[:2].isdigit())


def numero_y_anio(ruta: Path, texto: str) -> tuple[str | None, int | None]:
    m = re.search(r"\*\*N[úu]mero\*\*\s*\|\s*([^|\n]+)", texto[:3000])
    if m:
        mm = re.match(r"(.+?)\s+de\s+(\d{4})", m.group(1).strip())
        if mm:
            return canon(mm.group(1)), int(mm.group(2))
    # Nombre de archivo: Resolucion_CREG_101_113_2026, Ley_1715_2014, Decreto_2236_de_2023
    tallo = re.sub(r"(?i)^(resoluci[óo]n|ley|decreto|creg)[_\s-]*", "", ruta.stem)
    tallo = re.sub(r"(?i)^creg[_\s-]*", "", tallo)
    # Hasta 5 cifras: los conceptos llegan a 14763 (con 4, concepto_creg_0014763_2025 salía 4763).
    mm = re.search(r"(\d{1,5}(?:[\s_-]\d{1,3})?)[\s_-](?:de[\s_-])?(\d{4})(?:\D|$)", tallo)
    if mm:
        return canon(mm.group(1)), int(mm.group(2))
    return None, None


ANEXO_DE = re.compile(r"(?m)^\|\s*\*\*Anexo de\*\*\s*\|\s*(.+?)\s*\|\s*$")


def norma_que_lo_adopta(texto: str) -> str | None:
    """La norma declarada en la fila **Anexo de**, si la hay."""
    m = ANEXO_DE.search(texto[:1500])
    return m.group(1).strip() if m else None


def clasificar(ruta: Path, texto: str, numero: str | None) -> str:
    if ruta.parent.name == "conceptos":
        return "concepto"
    # Un libro o anexo no rige por si mismo: rige la resolucion que lo adopta. Los cinco
    # libros del RETIE no traen articulo de vigencia ni formula de cierre porque los lleva
    # la resolucion que los expide (E6).
    if norma_que_lo_adopta(texto):
        return "anexo"
    if re.search(r"(?i)referencia cruzada", texto[:400]):
        return "referencia"
    if ruta.parent.name == "normas_tecnicas":
        return "norma_tecnica"
    if ruta.parent.name == "acuerdos":
        return "acuerdo_cno"
    if numero and numero.split("-")[0] == "701":
        return "proyecto"
    if re.search(r"(?i)\(proyecto\)|proyecto de resoluci[óo]n para consulta", texto[:400]):
        return "proyecto"
    return "norma"


def clausula_vigencia(texto: str) -> tuple[str, str] | None:
    # Las anotaciones del Gestor ("<... Rige a partir de la derogatoria de la
    # Resolución 167 de 2017>") hablan de la vigencia de un aparte modificado.
    texto = ANOTACION_GESTOR.sub(" ", texto)

    # 1) El artículo titulado VIGENCIA, el último antes del cierre del acto. Los
    #    considerandos citan artículos de vigencia de OTRAS resoluciones: la
    #    101-064/2024 transcribe el "ARTÍCULO 20. VIGENCIA Y DEROGATORIAS" de la
    #    que modifica 300 líneas antes de su propio artículo 14.
    cierre = CIERRE_ACTO.search(texto)
    limite = cierre.start() if cierre else len(texto)
    epigrafes = [e for e in EPIGRAFE_VIGENCIA.finditer(texto) if e.start() < limite]
    if epigrafes:
        cuerpo = texto[epigrafes[-1].end():epigrafes[-1].end() + 600]
        for nombre, pat in PATRONES_VIGENCIA[:5]:
            m = re.search(pat, cuerpo)
            if m:
                frase = " ".join(m.group(0).split())
                if PRUEBA_TEMPORAL.search(frase) and not FALSA_VIGENCIA.search(frase):
                    return f"artículo de vigencia, {nombre}", frase[:170]

    # 2) Sin epígrafe (resúmenes, textos parciales): la primera frase que diga cuándo.
    for nombre, pat in PATRONES_VIGENCIA:
        for m in re.finditer(pat, texto):
            frase = " ".join((m.group(1) if m.groups() else m.group(0)).split())
            if FALSA_VIGENCIA.search(frase):
                continue
            if not PRUEBA_TEMPORAL.search(frase):
                continue  # dice "vigente" pero no dice desde cuándo: no prueba nada
            return nombre, frase[:170]
    return None


def publicacion(texto: str) -> str | None:
    for pat in (r"\*\*Diario Oficial\*\*\s*\|\s*([^|\n]+)",
                r"\*\*Publicaci[óo]n[^*]*\*\*\s*\|?\s*:?\s*([^|\n]+)",
                r"(?i)(diario oficial[^\n.]{0,80}\d[^\n.]{0,40})"):
        m = re.search(pat, texto[:4000]) or re.search(pat, texto)
        if m:
            return " ".join(m.group(1).split())[:120]
    return None


def estado_declarado(texto: str) -> str | None:
    m = re.search(r"\*\*Estado\*\*\s*\|\s*([^|\n]+)", texto[:3000])
    return " ".join(m.group(1).split()) if m else None


def _en_anotacion(texto: str, pos: int) -> bool:
    """¿La posición cae dentro de una anotación <...> del Gestor?"""
    ini = texto.rfind("<", max(0, pos - 600), pos)
    return ini >= 0 and texto.find(">", ini) >= pos and "\n" not in texto[ini:pos]


def _clase(ref: re.Match) -> str:
    return {"l": "Ley", "d": "Decreto"}.get(ref.group(0)[0].lower(), "Resolución")


def articulos_citados(prefijo: str) -> list[int]:
    """Artículos de la norma destino nombrados justo antes de ella: "los artículos 9,
    23, 25 y 26 de la Resolución CREG 174" -> [9, 23, 25, 26]. Se mira solo desde
    la última norma nombrada, para no heredar los artículos de la anterior."""
    corte = [m.end() for m in re.finditer(r"\bde\s+(?:19|20)\d{2}\b", prefijo)]
    tramo = prefijo[corte[-1]:] if corte else prefijo
    hallados = ART_CITADOS.findall(tramo)
    return sorted({int(n) for n in re.findall(r"\d{1,3}", hallados[-1])}) if hallados else []


def aristas_de_texto(texto: str, yo: tuple) -> list[dict]:
    """Relaciones que el texto de UNA norma declara, con tipo, sentido y cita.

    Cada arista va de la norma que actúa (origen) a la norma sobre la que actúa
    (destino): "la 174/2021 deroga la 030/2018" es 174 -> 030, tipo deroga, la
    diga la 174 en activa o la 030 en pasiva. `fuente` distingue el texto
    dispositivo de las anotaciones del Gestor.
    """
    salida: list[dict] = []

    def nueva(origen, destino, tipo, cita, pos, clase="Resolución", articulos=()):
        if origen == destino:
            return  # una norma no actúa sobre sí misma
        salida.append({"origen": origen, "destino": destino, "tipo": tipo, "clase_destino": clase,
                       "articulos": list(articulos),
                       "cita": " ".join(cita.split())[:200],
                       "fuente": "anotación del Gestor" if _en_anotacion(texto, pos) else "texto"})

    for m in PAT_ACTIVA.finditer(texto):
        # El alcance de un "deroga" termina donde termina su frase dispositiva.
        # Sin este corte, "deroga las normas que le sean contrarias." se comía el
        # "PUBLÍQUESE Y CÚMPLASE ... ANEXO 1 ... RESOLUCIÓN CREG 060 DE 2019" que
        # venía detrás, y declaraba derogada la 060/2019 con el encabezado de un
        # anexo como prueba (D5-6, 2026-09-12).
        resto = texto[m.end():m.end() + 400]
        cortes = [len(resto)]
        for pat in (PAT_ACTIVA, FIN_CLAUSULA):
            mm = pat.search(resto)
            if mm:
                cortes.append(mm.start())
        resto = resto[:min(cortes)]
        for r in PAT_REF.finditer(resto):
            clave = (canon(r.group(1)), int(r.group(2)))
            previo = resto[:r.start()]
            # "deroga el numeral 1.1 ... de la Resolución CREG 086 de 1996, modificado
            # por la Resolución CREG 096 de 2019" (174/2021): la 096 es la historia
            # del numeral, no otra norma derogada.
            if HISTORIA_DEL_ELEMENTO.search(previo):
                continue
            # "deroga la Resolución CREG 094 de 2012 excepto el Capítulo 3 del
            # anexo general" (015/2018): la 094 sobrevive en ese capítulo.
            despues = resto[r.end():r.end() + 40]
            parcial = PAT_PARCIAL.search(previo) or re.match(r"(?i)\s*,?\s*(excepto|salvo)\b", despues)
            nueva(yo, clave, "deroga parcialmente" if parcial else "deroga",
                  resto[max(0, r.start() - 90):r.end()], m.start(), _clase(r),
                  articulos_citados(resto[:r.start()]))

    for m in PAT_PASIVA.finditer(texto):
        resto = texto[m.end():m.end() + 200]
        r = PAT_REF.search(resto)
        if r:
            clave = (canon(r.group(1)), int(r.group(2)))
            # En pasiva el "artículo N" que sigue identifica a quien deroga.
            # Lo que decide si muero entera es el SUJETO, lo que va antes:
            # "<Artículo derogado por el artículo 20 de la Resolución 51 de
            # 2012>" (071/2006, anotación del Gestor) mata ese artículo, no
            # la resolución. Sin sujeto o con "Resolución" delante, TOTAL.
            antes = texto[max(0, m.start() - 60):m.start()].split("<")[-1]
            nueva(clave, yo, "deroga parcialmente" if SUJETO_ELEMENTO.search(antes) else "deroga",
                  texto[max(0, m.start() - 40):m.end() + r.end()], m.start())

    resuelve = RESUELVE.search(texto)
    if resuelve:
        base = resuelve.end()
        dispositivo = ANOTACION_GESTOR.sub(lambda a: " " * len(a.group(0)), texto[base:])
        for m in PAT_MODIFICA.finditer(dispositivo):
            resto = dispositivo[m.end():m.end() + 300]
            cortes = [len(resto)] + [mm.start() for mm in (PAT_MODIFICA.search(resto),
                                                          PAT_ACTIVA.search(resto),
                                                          FIN_CLAUSULA.search(resto)) if mm]
            resto = resto[:min(cortes)]
            for r in PAT_REF.finditer(resto):
                nueva(yo, (canon(r.group(1)), int(r.group(2))), "modifica",
                      resto[max(0, r.start() - 60):r.end()], base + m.start(), _clase(r),
                      articulos_citados(resto[:r.start()]))

    # Las anotaciones del Gestor también registran lo que se modificó, adicionó o
    # sustituyó: "<Definición modificada por el artículo 2 de la Resolución 101 97
    # de 2026>". Es la CREG diciendo qué norma posterior tocó cuál elemento.
    for a in ANOTACION_GESTOR.finditer(texto):
        m = re.search(r"(?i)\b(?:modificad|adicionad|sustituid|subrogad)[oa]s?\b[^<>]{0,40}?\bpor\b", a.group(0))
        r = PAT_REF.search(a.group(0), m.end()) if m else None
        if r:
            nueva((canon(r.group(1)), int(r.group(2))), yo, "modifica", a.group(0)[:160], a.start() + 1)

    # Fundamento: las leyes y decretos que el acto invoca antes de CONSIDERANDO
    # ("en ejercicio de las atribuciones conferidas por las Leyes 142 y 143 de 1994").
    pre = re.search(r"(?is)en\s+(?:ejercicio|uso|cumplimiento|desarrollo)\s+de(.{0,900}?)C\s*O\s*N\s*S\s*I\s*D\s*E\s*R\s*A\s*N\s*D\s*O",
                    texto[:30000])
    if pre:
        frag = pre.group(1)
        for mm in re.finditer(r"(?i)\b(leyes|decretos)\s+((?:\d{1,4}\s*(?:,|y)\s*)+\d{1,4})\s+de\s+(\d{4})", frag):
            for n in re.findall(r"\d{1,4}", mm.group(2)):
                nueva((canon(n), int(mm.group(3))), yo, "fundamenta", mm.group(0), 0,
                      "Ley" if mm.group(1)[0].lower() == "l" else "Decreto")
        for r in re.finditer(r"(?i)\b(?:ley|decreto)\s+(\d{1,4})\s+de\s+(\d{4})", frag):
            nueva((canon(r.group(1)), int(r.group(2))), yo, "fundamenta", r.group(0), 0,
                  "Ley" if r.group(0)[0].lower() == "l" else "Decreto")
    return salida


def citas_de_concepto(texto: str, yo: tuple) -> list[dict]:
    """Concepto -> cada norma que menciona, con cuántas veces."""
    cuenta: Counter = Counter()
    clase: dict = {}
    for r in PAT_REF.finditer(ANOTACION_GESTOR.sub(" ", texto)):
        clave = (canon(r.group(1)), int(r.group(2)))
        if clave != yo:
            cuenta[clave] += 1
            clase[clave] = _clase(r)
    return [{"origen": yo, "destino": k, "tipo": "interpreta", "clase_destino": clase[k],
             "cita": f"la menciona {n} veces", "fuente": "texto", "menciones": n}
            for k, n in cuenta.items()]


def derogatorias(texto: str, yo: tuple) -> tuple[list, list, list, list]:
    """Vista de las aristas desde una norma: (totales_que_yo_derogo,
    parciales_que_yo_toco, quien_me_derogo, quien_me_toca_un_elemento), cada una
    como pares (norma, cita)."""
    tot, par, pas, rec = [], [], [], []
    for a in aristas_de_texto(texto, yo):
        if a["tipo"] == "fundamenta":
            continue
        if a["origen"] == yo:
            (tot if a["tipo"] == "deroga" else par).append((a["destino"], a["cita"]))
        else:
            (pas if a["tipo"] == "deroga" else rec).append((a["origen"], a["cita"]))
    return tot, par, pas, rec


# Acuerdos del CNO (convertir_cno.py): la ficha del sitio del CNO trae la fecha de entrada en
# vigencia y los acuerdos que sustituye, en campos propios. Se leen de la tabla de metadatos,
# no del texto: es la única fuente estructurada, y el texto del acuerdo no trae cláusula de
# vigencia (la fija la ficha).
FILA_ENTRADA_VIGENCIA = re.compile(r"(?m)^\|\s*\*\*Entrada en vigencia\*\*\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|")
FILA_SUSTITUYE = re.compile(r"(?m)^\|\s*\*\*Sustituye\*\*\s*\|\s*(.+?)\s*\|\s*$")
RELACION_CNO = re.compile(r"Acuerdo CNO (\d+) de (\d{4}) \((\w+)")
VERBO_CNO = {"sustituye": "deroga", "deroga": "deroga", "modifica": "modifica", "adiciona": "modifica"}


def ficha_cno(texto: str, yo: tuple) -> tuple[tuple[str, str] | None, list[dict]]:
    """(vigencia, aristas) de un acuerdo del CNO desde su tabla de metadatos."""
    m = FILA_ENTRADA_VIGENCIA.search(texto[:4000])
    vig = ("ficha del CNO", f"entrada en vigencia {m.group(1)}") if m else None
    aristas = []
    fila = FILA_SUSTITUYE.search(texto[:4000])
    for r in RELACION_CNO.finditer(fila.group(1) if fila else ""):
        tipo = VERBO_CNO.get(r.group(3).lower())
        if tipo:
            aristas.append({"origen": yo, "destino": (canon("CNO " + r.group(1)), int(r.group(2))), "tipo": tipo,
                            "clase_destino": "acuerdo CNO", "fuente": "ficha del CNO",
                            "cita": f"{r.group(3)} el Acuerdo CNO {r.group(1)} de {r.group(2)} (ficha del CNO)"})
    return vig, aristas


def analizar(ruta: Path) -> dict:
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    # Lo que va después de la marca es un resumen escrito a mano, no la norma:
    # "la 101-098 deroga..." dicho en un resumen no es una derogatoria de este acto.
    texto = texto.split(MARCA_RESUMEN, 1)[0]
    numero, anio = numero_y_anio(ruta, texto)
    tipo = clasificar(ruta, texto, numero)
    yo = (numero, anio)
    cuerpo = FILA_METADATOS.sub("", texto)
    vig = clausula_vigencia(cuerpo) if tipo == "norma" else None
    if tipo == "acuerdo_cno":
        vig, aristas = ficha_cno(texto, yo)
    elif tipo in ("norma", "proyecto"):
        aristas = aristas_de_texto(cuerpo, yo)
    elif tipo == "concepto" and numero:
        aristas = citas_de_concepto(cuerpo, yo)
    else:
        aristas = []
    tot, par, pas, rec = [], [], [], []
    for a in aristas:
        if a["tipo"] in ("fundamenta", "interpreta"):
            continue
        if a["origen"] == yo:
            (tot if a["tipo"] == "deroga" else par).append((a["destino"], a["cita"]))
        else:
            (pas if a["tipo"] == "deroga" else rec).append((a["origen"], a["cita"]))
    return {
        "archivo": str(ruta.relative_to(REPO)).replace("\\", "/"),
        "numero": numero, "anio": anio, "tipo": tipo,
        "anexo_de": norma_que_lo_adopta(texto),
        "vigencia": {"patron": vig[0], "texto": vig[1]} if vig else None,
        "publicacion": publicacion(texto) if tipo in ("norma", "proyecto") else None,
        "declarado": estado_declarado(texto),
        "_aristas": aristas,
        "_tot": tot, "_par": par, "_pas": pas, "_rec": rec,
    }


def aristas_del_corpus(docs: list[dict]) -> tuple[list[dict], list[str]]:
    """Todas las relaciones del corpus, ya filtradas por orden de años.

    Una norma no deroga ni modifica a otra posterior, y una ley no fundamenta a
    un acto anterior: esas aristas se descartan y se reportan, porque casi
    siempre son un número o un año mal leído. Lo que declara un proyecto queda
    como "propone": no actúa sobre nada.
    """
    validas, descartadas = [], []
    for d in docs:
        if not d["numero"]:
            continue
        for a in d["_aristas"]:
            a = dict(a, archivo=d["archivo"])
            if d["tipo"] == "proyecto":
                a["tipo"] = "propone: " + a["tipo"]
            (o, yo_o), (t, yo_t) = a["origen"], a["destino"]
            if a["tipo"] in ("deroga", "deroga parcialmente", "modifica") and yo_o < yo_t:
                descartadas.append(f"{d['archivo']}: la {o} de {yo_o} {a['tipo']} a la {t} de {yo_t}, "
                                   f"posterior a ella; no puede ser")
                continue
            if a["tipo"] == "fundamenta" and yo_o > yo_t:
                descartadas.append(f"{d['archivo']}: la {o} de {yo_o} no puede fundamentar a la "
                                   f"{t} de {yo_t}, anterior a ella")
                continue
            validas.append(a)
    return validas, descartadas


def grafo(docs: list[dict]) -> tuple[dict, dict, list]:
    """Derogadas y modificadas por, derivadas de las aristas (una sola fuente)."""
    derogada_por: dict = {}
    modificada_por: dict = {}
    aristas, descartadas = aristas_del_corpus(docs)
    for a in aristas:
        o = a["origen"]
        if a["tipo"] == "deroga":
            derogada_por.setdefault(a["destino"], []).append((o[0], o[1], a["cita"]))
        elif a["tipo"] in ("deroga parcialmente", "modifica"):
            modificada_por.setdefault(a["destino"], []).append((o[0], o[1], a["cita"]))
    return derogada_por, modificada_por, descartadas


def calcular(d: dict, derogada_por: dict) -> tuple[str, str]:
    if d["tipo"] == "concepto":
        return "no aplica", "un concepto interpreta la norma, no rige"
    if d["tipo"] == "referencia":
        return "remite", "solo remite al texto completo en otra carpeta"
    if d["tipo"] == "anexo":
        return ("rige con la norma que lo adopta",
                f"es anexo de {d.get('anexo_de') or 'otra norma'}: su vigencia es la de esa norma")
    if d["tipo"] == "proyecto":
        return "sin fuerza vinculante", "es proyecto de resolución"
    if d["tipo"] == "norma_tecnica":
        return ("rige la edición citada",
                "norma técnica: no tiene cláusula de vigencia ni se deroga; la edición que rige la fija el "
                "reglamento que la cita")
    q = derogada_por.get((d["numero"], d["anio"]))
    if d["tipo"] == "acuerdo_cno":
        if q:
            return "derogada", f"sustituido por el Acuerdo {q[0][0].replace('CNO-', 'CNO ')} de {q[0][1]} (ficha del CNO)"
        if d["vigencia"]:
            return "vigente", f"{d['vigencia']['patron']}: {d['vigencia']['texto']}"
        return "no determinable", "la ficha del CNO no trae fecha de entrada en vigencia"
    if q:
        return "derogada", f"derogada por la {q[0][0]} de {q[0][1]}: \"{q[0][2][:110]}\""
    if d["vigencia"]:
        pub = f" | publicación: {d['publicacion']}" if d["publicacion"] else ""
        return "vigente", f"{d['vigencia']['patron']}: \"{d['vigencia']['texto']}\"{pub}"
    return "no determinable", "el texto guardado no dice desde cuándo rige"


def calcular_todo() -> tuple[list[dict], list[str]]:
    """Estado calculado de cada documento del corpus. Lo usa también el MCP,
    que lo antepone a cada lectura: el analista ve la vigencia calculada, no
    una fila tecleada."""
    docs = [analizar(p) for p in documentos()]
    derogada_por, modificada_por, descartadas = grafo(docs)
    for d in docs:
        d["calculado"], d["evidencia"] = calcular(d, derogada_por)
        mod = modificada_por.get((d["numero"], d["anio"]))
        # Sin repetir: la 071/2006 trae 46 anotaciones de la misma 101-6 de 2023.
        d["modificada_por"] = list(dict.fromkeys(f"{a} de {b}" for a, b, _ in mod)) if mod else []
        for k in ("_tot", "_par", "_pas", "_rec", "_aristas"):
            d.pop(k)
    return docs, descartadas


def main() -> int:
    ap = argparse.ArgumentParser(description="Calcula la vigencia desde las propias normas")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    docs, descartadas = calcular_todo()

    contradicciones = []
    for d in docs:
        dec = (d["declarado"] or "").lower()
        if d["calculado"] == "derogada" and dec.startswith("vigente"):
            contradicciones.append((d, "se declara vigente y otra norma la derogó por completo"))
        elif d["calculado"] == "vigente" and dec.startswith("derogad"):
            contradicciones.append((d, "se declara derogada y nada la deroga"))
        # Hasta el 2026-09-12 estas dos eran avisos y el corpus las acumuló (15
        # conceptos "Vigente", 4 normas "Vigente" sin cláusula). Un aviso que no
        # rompe nada se vuelve paisaje: ahora fallan.
        elif d["calculado"] == "no aplica" and (dec.startswith("derogad") or dec.startswith("vigente")):
            contradicciones.append((d, "un concepto no rige: no puede declararse vigente ni derogado"))
        elif d["calculado"] == "no determinable" and dec.startswith("vigente"):
            contradicciones.append((d, "se declara vigente y el texto guardado no dice desde cuándo rige"))

    if args.json:
        print(json.dumps({"documentos": docs,
                          "contradicciones": [{"archivo": d["archivo"], "motivo": m}
                                              for d, m in contradicciones],
                          "aristas_descartadas": descartadas}, ensure_ascii=False, indent=2))
        return 1 if contradicciones else 0

    print(f"{len(docs)} documentos\n")
    for d in sorted(docs, key=lambda x: (x["tipo"], x["archivo"])):
        if d["tipo"] == "concepto":
            continue
        etiqueta = f"{d['numero']} de {d['anio']}" if d["numero"] else d["archivo"][-40:]
        extra = f"  [modificada por {', '.join(d['modificada_por'])}]" if d["modificada_por"] else ""
        print(f"  {etiqueta:20} {d['calculado']:22} {d['evidencia'][:64]}{extra}")

    print("\nresumen:")
    for (t, c), n in sorted(Counter((d["tipo"], d["calculado"]) for d in docs).items()):
        print(f"  {t:11} {c:24} {n:>3}")

    if descartadas:
        print(f"\naristas descartadas por orden de años ({len(descartadas)}):")
        for x in descartadas:
            print("  -", x)
    if contradicciones:
        print(f"\nCONTRADICCIONES ({len(contradicciones)}):")
        for d, motivo in contradicciones:
            print(f"  - {d['archivo']}\n      declarado : {d['declarado']}"
                  f"\n      calculado : {d['calculado']} — {d['evidencia']}\n      motivo    : {motivo}")
        return 1

    print("\nVERIFICACION OK: ningún estado declarado contradice al calculado.")
    return 0


if __name__ == "__main__":
    # Consola de Windows en cp1252: la salida va en UTF-8 para quien la lea
    for _flujo in (sys.stdout, sys.stderr):
        if hasattr(_flujo, "reconfigure"):
            _flujo.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())

# Concepto CREG 3951 de 2026

| Campo | Detalle |
|-------|---------|
| **Numero** | 3951 de 2026 |
| **Tema** | Criterios para determinar capacidad instalada/nominal y verificación de exportación en configuraciones de Generación Distribuida con Almacenamiento (SAEB) y acople AC |
| **Tipo** | Concepto |
| **Estado** | no aplica: un concepto interpreta la norma, no rige (verificar_vigencia.py) |
| **Fuente** | Archivo original `concepto_creg_0003951_2026.pdf` (convertido con pdfplumber) |

---

## Contenido

<!-- pagina 1 -->
CONCEPTO 3951 DE 2026
(mayo 4)
<Fuente: Archivo interno entidad emisora>
COMISIÓN DE REGULACIÓN DE ENERGÍA Y GAS - CREG
Bogotá, D.C.,
Señora
XXXXXX
Asunto: Criterios para determinar capacidad instalada/nominal y verificación de exportación en
configuraciones de Generación Distribuida con Almacenamiento (SAEB) y acople AC
Radicado CREG: S2026003951
Id de referencia: E2026002262
Expediente CREG (Escriba aquí el número del expediente (si aplica))
Respetada señora XXXXXXXX:
Antes de dar respuesta a su solicitud, le informamos que de acuerdo con lo dispuesto en las
Leyes 142 [1] y 143 [2] de 1994, y el Decreto 1260 de 2013, a la Comisión de Regulación de
Energía y Gas (CREG) se le asignó, aparte de las funciones genéricas que toda Comisión de
Regulación tiene, la regulación económica de los servicios públicos domiciliarios de energía
eléctrica y gas combustible, así como de las actividades de la cadena de combustibles líquidos
derivados de los hidrocarburos.
En ese orden, es pertinente aclarar que la función consultiva que, conforme al numeral 24 del
artículo 73 de la Ley 142 de 1994 debe cumplir esta Comisión, se circunscribe exclusivamente
al ámbito de las materias de su competencia y, en cumplimiento de ésta, no resuelve casos
particulares o concretos, pues ello corresponde a la Superintendencia de Servicios Públicos
Domiciliarios, en lo relacionado con la prestación de los servicios públicos domiciliarios, y a la
Superintendencia de Industria y Comercio, en relación con prácticas contrarias a la libre
competencia, a través de los procedimientos dispuestos para tal fin.
Realizadas las anteriores consideraciones y antes de dar repuesta de fondo a su solicitud, a
continuación, y a modo de contexto, transcribimos sus consultas:
Pregunta 1
(...) nos permitimos elevar ante la Comisión una consulta de carácter general relacionada con la
aplicación de la regulación vigente a configuraciones tecnológicas de Generación Distribuida
(GD) con Sistemas de Almacenamiento de Energía con Baterías (SAEB), particularmente bajo
esquemas de acople en corriente alterna (AC coupling).
La presente consulta se formula sin referencia a un caso particular, sino con el propósito de
contar con criterios generales que permitan a los agentes del mercado y a los Operadores de
Red evaluar, de manera consistente y verificable, la clasificación, medición y límites de

<!-- pagina 2 -->
exportación de soluciones GD+SAEB que buscan aportar beneficios técnicos al Sistema de
Distribución Local (SDL).
1. Contexto general y motivación
En el marco del crecimiento acelerado de proyectos de Generación Distribuida conectados al
SDL, los Operadores de Red enfrentan desafíos operativos asociados a:
- variaciones de tensión y rampas rápidas de potencia,
- cambios en flujos (incluyendo flujo reverso),
- impactos sobre coordinación de protecciones y niveles de cortocircuito,
- y aumento de incertidumbre en la operación de nodos con alta penetración de recursos
distribuidos.
En este contexto, las configuraciones GD + SAEB pueden contribuir a una operación más
robusta del SDL, al permitir desplazar energía y gestionar la entrega controlada en horarios
distintos a la disponibilidad solar.
Adicionalmente, dependiendo de la tecnología de conversión y control, estas soluciones pueden
aportar capacidades funcionales como soporte dinámico (P/Q), contribución al desempeño ante
perturbaciones e incluso funcionalidades avanzadas (p. ej. modos de control tipo grid-forming),
aun cuando no exista hoy un esquema explícito de remuneración para dichos servicios.
2. Razones técnicas para preferir AC coupling en GD+SAEB
En términos tecnológicos, el acople AC (por ejemplo, en barras internas de baja tensión) suele
considerarse favorable para:
i. Flexibilidad de control y despacho interno: permite que el SAEB opere con independencia
relativa del bloque fotovoltaico y soporte estrategias de control orientadas a robustez del nodo
(p. ej., suavización de rampas, control de potencia reactiva, limitación de exportación al punto
de conexión).
ii. Gestión operativa para exportación en horas sin sol: habilita que la energía almacenada se
exporte cuando el recurso solar no está disponible, mediante el PCS (Power Conversion
System) del SAEB.
iii. Eficiencia y aprovechamiento de excedentes (clipping): en ciertos diseños, se busca habilitar
la captura de energía que de otro modo se perdería por “clipping” del bloque FV, almacenándola
para entrega posterior
No obstante, bajo AC coupling puede requerirse instalar una capacidad de conversión AC
interna mayor para maximizar el aprovechamiento energético y viabilizar la estrategia de
almacenamiento, sin que ello implique necesariamente una mayor potencia exportada al punto
de conexión.
3. Dificultad interpretativa/práctica bajo la definición de capacidad instalada/nominal por
inversores
Entendemos que la regulación vigente establece que, cuando la conexión al SIN (Sistema

<!-- pagina 3 -->
Interconectado Nacional) se realiza mediante inversores, la capacidad instalada o nominal se
asocia a la suma de las capacidades nominales de los inversores del lado AC o con conexión al
SIN, y que la capacidad nominal del inversor corresponde a la potencia activa nominal indicada
por el fabricante
En la práctica, ello genera una tensión regulatoria para diseños AC-coupled, porque puede
existir:
- un conjunto de convertidores/inversores cuyo propósito es la exportación al punto de conexión
(exportación limitada a <1 MW), y
- otro conjunto de convertidores/inversores cuyo propósito es capturar energía para cargar el
SAEB (energía destinada a almacenamiento), con exportación posterior a través del PCS del
SAEB o del bloque exportador, conforme a límites definidos.
Así, surge la necesidad de criterios generales para responder: ¿cómo demostrar al Operador de
Red que la potencia exportable al punto de interconexión está limitada a <1MW, aun si existen
convertidores/inversores adicionales en la instalación destinados a almacenamiento (y no a exportación
directa) en esquemas AC-coupled?
Con base en lo anterior, solicitamos conceptuar, en términos generales, sobre los siguientes
aspectos en las siguientes diez (10) consultas
A. Criterio para determinar si un inversor “tiene conexión al SIN”
1. Criterio general de “conexión al SIN”: ¿Debe interpretarse que un inversor solar está “con conexión al
SIN" únicamente por estar en un bus AC interno de la planta fotovoltaica, o el criterio depende de la
existencia de una ruta eléctrica físicamente disponible hacia el punto de interconexión (capacidad de
sincronizar y exportar)? (...)
Respuesta:
Al respecto le informamos que el Sistema Interconectado Nacional (SIN) comprende incluso la
carga del usuario, por lo cual se comprende están incluidas sus redes internas puesto que son
cargas eléctricas:
(.) Sistema Interconectado Nacional (SIN). Es el sistema compuesto por los siguientes
elementos conectados entre sí: las plantas y equipos de generación, la red de interconexión, las
redes regionales e interregionales de transmisión, las redes de distribución, y las cargas
eléctricas de los usuarios. (...)
Por lo tanto, cualquier conexión que tenga influencia en los anteriores elementos (que pueda
transmitir flujo eléctrico en cualquier momento del tiempo o que una falla incida sobre los
mismos), incluida las cargas eléctricas de los usuarios, se considera parte del SIN.
Preguntas 2 y 3
(.) 2. En una configuración del generador solar distribuido con bloques diferenciados
(exportación vs carga), ¿puede considerarse que un conjunto de inversores solares no hace
parte del cálculo de capacidad instalada/nominal si se demuestra que dicho conjunto no tiene
ruta física de exportación al punto de interconexión, aun cuando esté en AC dentro del
predio/instalación? (.)

<!-- pagina 4 -->
(.) 3. ¿Qué condiciones mínimas deberían verificarse para concluir que un inversor/convertidor
no tiene conexión funcional al SIN (por ejemplo: seccionamiento eléctrico permanente,
enclavamientos, aislamiento de barras, impedimento de paralelismo eléctrico, etc.)? (.)
Respuesta:
Al respecto le informamos que la definición de capacidad instalada o nominal del artículo 3 de
la Resolución CREG 174 de 2021 recae sobre el sistema de generación y no sobre el sistema
de almacenamiento. De hecho, el sistema de almacenamiento se declara de forma
independiente indicando por separado la capacidad en potencia y energía (anexo de formulario
de conexión simplificado en la Circular CREG 21 de 2022) y no existe una definición de su
capacidad instalada en potencia y energía de forma específica, por lo cual se comprende que
es la de fabricante.
En cuanto a si los inversores del sistema de generación o los del sistema de almacenamiento
están o no conectados al SIN, referirse a la respuesta de la pregunta 1.
Pregunta 4 y 5
(...) 4. ¿Qué criterios generales recomienda la CREG para demostrar a un Operador de Red
que una instalación GD+SAEB tiene una potencia máxima exportable (PMD) en el punto de
interconexión inferior a 1 MW, incluyendo requisitos de:
- medición en punto de conexión,
- medición adicional en la entrada del SAEB
- filosofía de control,
- pruebas de aceptación (SAT),
- respuesta ante fallas de comunicación/control?
5. ¿Considera la CREG que, para efectos de aceptación por el OR, el límite de exportación
debe estar garantizado mediante medidas físicas/arquitectónicas (además de control por
software), o sería suficiente un esquema de control verificable con pruebas y registros? (...)
Respuesta:
Como citamos en la respuesta a la pregunta 1, en el formulario de conexión simplificado se
declara la capacidad del sistema de generación e independiente el del sistema de
almacenamiento.
Por otra parte, si bien en el artículo 14 de la Resolución CREG 174 de 2021 se cita que a un
GD no le aplica el documento tipo D sobre entregar documentación que pruebe que se tiene un
control de inyección al SDL, al GD le aplica declarar la potencia máxima declarada (PMD) que,
según el artículo 3 de la misma resolución, corresponde con la misma capacidad efectiva neta
(CEN), la cual debe ser verificada en las visitas de puesta en servicio y que es la que se mide
en el punto de conexión al SDL y que coincide con la frontera de generación.
Es decir, en la visita de puesta en servicio se verifica que el proyecto de GD tenga la capacidad
instalada o nominal declarada del activo de generación sin superar 1 MW y, de forma
independiente, se verifica que el sistema de almacenamiento tenga también sus valores

<!-- pagina 5 -->
declarados (en los cuales no se definió un límite). No obstante, lo anterior,
complementariamente se verifica que la CEN o PMD (sea sistema GD independiente o hibrido
con SAEB), que por defecto se mide en el punto conexión con el SDL, no supere el valor
declarado mediante las verificaciones y/o pruebas a que haya lugar en el sitio. La verificación
y/o pruebas buscan determinar que la PMD o CEN debe ser menor o igual que la capacidad
instalada o nominal del activo de generación (artículo 3 resolución CREG 174 de 2021).
Pregunta 6 y 7
(...) 6. En configuraciones GD+SAEB, ¿cómo deben interpretarse y coexistir los conceptos de:
- capacidad instalada o nominal, y
- potencia máxima declarada / potencia máxima exportable al punto de interconexión,
particularmente cuando el diseño requiere conversión interna adicional para fines de
almacenamiento, sin pretender exceder el umbral de exportación del punto de interconexión?
7. ¿Es viable (desde una perspectiva regulatoria general) que, para configuraciones híbridas
GD+SAEB, el criterio de clasificación y evaluación por parte del OR considere la capacidad
exportable al punto de interconexión como variable operativa verificable, sin que ello implique
redefinir la "capacidad nominal" del conjunto? (...)
Respuesta:
En la respuesta a las preguntas 2 a 7 anteriores ya se brindó el concepto.
Preguntas 8, 9 y 10
(.) 8. Para GD+SAEB con acople AC, ¿cómo debe tratarse la potencia nominal del PCS del
SAEB frente a la evaluación de la instalación (capacidad nominal, PMD, y condiciones de
conexión)?
9. En caso de que el PCS tenga capacidades avanzadas de control (por ejemplo, soporte
dinámico o modos tipo grid-forming), ¿existe algún criterio general adicional que deba exigirse o
evaluarse por parte del OR para asegurar operación segura del SDL?
(.) 10. Dada la necesidad del SDL de contar con recursos flexibles, ¿la CREG contempla emitir
lineamientos o ajustes normativos (p. ej. guía interpretativa, actualización de definiciones,
pilotos regulatorios) que faciliten la integración de GD+SAEB con AC coupling, asegurando:
- límites verificables de exportación,
- transparencia para el OR,
- y preservación de la calidad y confiabilidad del servicio? (...)
Respuesta:
En la respuesta a las preguntas 2 y 3 se brindo el concepto sobre la capacidad del sistema de
almacenamiento, la cual se declara en el formulario de conexión simplificado y verifica en la
visita de puesta en servicio.
Sobre los requerimientos técnicos de un sistema de almacenamiento, en la regulación no
existen requerimientos técnicos sobre los mismos y esto es a decisión del inversionista. No

<!-- pagina 6 -->
obstante, lo anterior, deben cumplirse los requerimientos de pruebas y protecciones que estén
implementados para GD en Acuerdos CNO en aplicación del artículo 12 de la Resolución
CREG 174 de 2021. Sugerimos revisarlos en la página web del CNO https://www.cno.org.co/
Así mismo le informamos que actualmente existe una regulación en consulta para SAEB, la
resolución CREG 701 103 de 2025, la cual está en análisis de comentarios. Pero esta última es
sobre SAEB que no están híbridos a un GD, por lo cual, se tendrá en cuenta su comentario
sobre SAEB de capacidades pequeñas.
El presente concepto se emite en los términos y con el alcance previsto en el artículo 28 del
Código de Procedimiento Administrativo y de lo Contencioso Administrativo, sustituido mediante
el artículo 1 de la Ley 1755 de 2015.
Cordialmente,
ANTONIO JIMENEZ RIVERA
Director Ejecutivo
<NOTAS DE PIE DE PÁGINA>
1. “Por la cual se establece el régimen de los servicios públicos domiciliarios y se dictan otras
disposiciones”.
2. “Por la cual se establece el régimen para la generación, interconexión, transmisión, distribución y
comercialización de electricidad en el territorio nacional, se conceden unas autorizaciones y se dictan
otras disposiciones en materia energética”.
Disposiciones analizadas por Avance Jurídico Casa Editorial Ltda.
Comisión de Regulación de Energía y Gas CREG
n.d.
Última actualización: 3 de julio de 2026

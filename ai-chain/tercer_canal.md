# El tercer canal: crédito privado para comprar cómputo

Nota de trabajo, 7 de octubre de 2026. No es resultado medido: es el canal que
la medición actual no cubre y las fuentes que lo documentan.

## Los tres canales

El indicador de Greenwood, Hanson, Shleifer y Sørensen mide crédito empresarial
sobre PIB. En la cadena de la IA ese crédito llega por tres vías, y solo la
primera entra en la medición oficial.

**Uno, deuda en balance.** Bonos y préstamos reconocidos. Es lo que el
indicador lee, y es lo que calculamos en `zona_roja_v3.py`.

**Dos, arrendamientos firmados sin comenzar.** No se reconocen como pasivo
hasta que el arrendamiento empieza, y no están etiquetados en XBRL. Es lo que
medimos leyendo los informes (`extraer_no_iniciados_b.py`). A junio de 2026,
830.504 millones en cuatro empresas, más 35.500 de CoreWeave. Oracle declara
que la categoría existe pero no publica el importe, así que esta medición
también se queda corta y hay que decirlo.

**Tres, crédito privado para comprar cómputo.** Una empresa se endeuda para
comprar chips, y el prestamista es un fondo de crédito privado. Ni está en el
balance del comprador en el momento del compromiso, ni es un arrendamiento, ni
lo captura bien el denominador agregado del artículo.

## El caso que abre el canal

SpaceX busca 40.000 millones para comprar chips de Nvidia: unos 10.000 en
préstamos bancarios y 30.000 en bonos de grado de inversión. Apollo Global
Management lidera la colocación y Pimco está entre los prestamistas en
negociación. La operación se cierra en 2027 (Financial Times, 6-oct-2026, vía
MarketScreener).

Dos cosas importan aquí, y ninguna es el tamaño.

La primera es el calendario. Al cerrarse en 2027, hoy no aparece en ningún
sitio: ni en balance, ni en arrendamientos firmados, ni en avales. Es presión
que ya existe como compromiso y que ningún instrumento lee todavía, ni el
oficial ni el nuestro.

La segunda es dónde acaba el riesgo. En agosto de 2026 Nvidia se asoció con
Apollo, BlackRock, Blackstone, Brookfield, Goldman Sachs y KKR en plataformas
para movilizar más de 500.000 millones en infraestructura de IA. El umbral del
artículo está calibrado sobre series históricas de deuda empresarial agregada,
construidas en un mundo donde el crédito corporativo pasaba por bancos y
mercados públicos. Si el canal se muda al crédito privado, el umbral sigue
donde estaba pero el termómetro mide otra cosa.

## Qué significa para el resultado

Refuerza la tesis en vez de debilitarla. El argumento no es solo que las
empresas no declaren una partida: es que el crédito de esta cadena se está
desplazando por tres canales de visibilidad decreciente, y la medición
estándar solo ve el primero.

Nuestro barómetro ajustado ve el primero y el segundo. No ve el tercero. Eso
hay que escribirlo como limitación declarada, igual que Van Nieuwerburgh
declara la suya.

## Pendiente

Decidir si el tercer canal es medible o solo nombrable. Las operaciones de
crédito privado no tienen una fuente única y sistemática como EDGAR. Si no hay
forma de construir una serie, se nombra como límite y no se estima: un número
inventado aquí estropearía los dos canales que sí están medidos.

## Fuentes

1. Greenwood, R., Hanson, S. G., Shleifer, A. y Sørensen, J. A. (2022).
   Predictable financial crises. *The Journal of Finance*, 77(2), 863-921.
2. Financial Times (6-oct-2026). SpaceX busca 40.000 millones liderados por
   Apollo para comprar chips de Nvidia. Resumen en MarketScreener, 7-oct-2026.
3. Financial Times (20-sep-2026). Las grandes tecnológicas mantienen unos
   300.000 millones de exposición a infraestructura de IA fuera de balance
   mediante garantías y vehículos de propósito especial.
4. Van Nieuwerburgh, S. (2026). Financing the AI Buildout. *Brookings Papers
   on Economic Activity*, otoño de 2026.

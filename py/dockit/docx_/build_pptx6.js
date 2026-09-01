const pptxgen = require('pptxgenjs');
const React = require('react');
const RDS = require('react-dom/server');
const sharp = require('sharp');
const Fi = require('react-icons/fi');

// ─── Paleta ───────────────────────────────────────────────────────────────
const C = {
  bg: '0B1524', panel: '13233A', panel2: '1B3049', line: '24405E', ghost: '101E31',
  white: 'FFFFFF', text: 'C7D8E6', muted: '7D9BB3', accent: '22B8CF',
  g1: 'E05555', g2: 'E8873A', g3: '3D9BE0', g4: '9B7EDE', g5: '2FB37A', g6: 'F0A202',
};
const F = 'Calibri';
const W = 10, H = 5.625;

const G = [
  { name: 'RFC 3227',       col: C.g1, ic: 'clock',  year: '2002', org: 'IETF' },
  { name: 'SWGDE',          col: C.g2, ic: 'award',  year: '1998', org: 'Estados Unidos' },
  { name: 'ACPO',           col: C.g3, ic: 'shield', year: '2012', org: 'Reino Unido' },
  { name: 'CP4DF',          col: C.g4, ic: 'merge',  year: '2007', org: 'Academia (Alemania)' },
  { name: 'NIST SP 800-86', col: C.g5, ic: 'grid',   year: '2006', org: 'NIST — EE. UU.' },
  { name: 'ISO/IEC 27037',  col: C.g6, ic: 'globe',  year: '2012', org: 'Internacional' },
];

// ─── Iconos ───────────────────────────────────────────────────────────────
const ICONS = {};
async function makeIcon(key, Comp, color) {
  let svg = RDS.renderToStaticMarkup(React.createElement(Comp, { size: 256 }));
  svg = svg.replace(/currentColor/g, '#' + color);
  ICONS[key] = 'image/png;base64,' +
    (await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer()).toString('base64');
}
async function buildIcons() {
  const spec = [
    ['clock', Fi.FiClock, C.white], ['award', Fi.FiAward, C.white],
    ['shield', Fi.FiShield, C.white], ['merge', Fi.FiGitMerge, C.white],
    ['grid', Fi.FiGrid, C.white], ['globe', Fi.FiGlobe, C.white],
    ['alert', Fi.FiAlertTriangle, C.g6], ['loop', Fi.FiRefreshCw, C.white],
    ['user', Fi.FiUser, C.g6], ['users', Fi.FiUsers, C.g6],
    ['layers', Fi.FiLayers, C.accent],
  ];
  for (const [k, comp, col] of spec) await makeIcon(k, comp, col);
}

// ─── Composición ──────────────────────────────────────────────────────────
const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.author = 'Informática Forense — EMI';
pres.title = 'Seis guías del proceso forense digital';

function bg(s) { s.addShape('rect', { x: 0, y: 0, w: W, h: H, fill: { color: C.bg } }); }

function card(s, x, y, w, h, fill, border) {
  const o = { x, y, w, h, fill: { color: fill || C.panel }, rectRadius: 0.08 };
  if (border) o.line = { color: border, width: 1.25 };
  s.addShape('roundRect', o);
}

function header(s, kicker, title, color) {
  const col = color || C.accent;
  s.addShape('ellipse', { x: 0.5, y: 0.44, w: 0.15, h: 0.15, fill: { color: col } });
  s.addText(kicker.toUpperCase(), {
    x: 0.76, y: 0.38, w: 8.7, h: 0.27, fontSize: 9.5, bold: true, color: col,
    fontFace: F, charSpacing: 1.6, margin: 0, valign: 'middle',
  });
  s.addText(title, {
    x: 0.5, y: 0.68, w: 9, h: 0.52, fontSize: 27, bold: true, color: C.white,
    fontFace: F, margin: 0, valign: 'middle',
  });
}

let pageNo = 0;
function footer(s, label) {
  pageNo++;
  s.addText('Guías del proceso forense digital  ·  ' + label, {
    x: 0.5, y: 5.24, w: 7.5, h: 0.24, fontSize: 8, color: C.muted, fontFace: F,
    margin: 0, valign: 'middle',
  });
  s.addText(String(pageNo).padStart(2, '0'), {
    x: 8.9, y: 5.24, w: 0.6, h: 0.24, fontSize: 8, bold: true, color: C.accent,
    fontFace: F, align: 'right', margin: 0, valign: 'middle',
  });
}

function iconCircle(s, key, x, y, d, fill) {
  s.addShape('ellipse', { x, y, w: d, h: d, fill: { color: fill } });
  const p = d * 0.3;
  s.addImage({ data: ICONS[key], x: x + p / 2, y: y + p / 2, w: d - p, h: d - p });
}

// Filas apiladas: badge numerado + título + cuerpo
function stageRows(s, items, col, y0, rowH, step) {
  items.forEach((it, i) => {
    const y = y0 + i * step;
    card(s, 0.5, y, 9, rowH, C.panel);
    s.addShape('ellipse', { x: 0.7, y: y + 0.11, w: 0.3, h: 0.3, fill: { color: col } });
    s.addText(String(i + 1), {
      x: 0.7, y: y + 0.11, w: 0.3, h: 0.3, fontSize: 9.5, bold: true, color: C.white,
      fontFace: F, align: 'center', valign: 'middle', margin: 0,
    });
    s.addText(it[0], {
      x: 1.12, y: y + 0.08, w: 7.9, h: 0.28, fontSize: 11.5, bold: true, color: C.white,
      fontFace: F, margin: 0, valign: 'middle',
    });
    s.addText(it[1], {
      x: 1.12, y: y + 0.35, w: 8.0, h: rowH - 0.4, fontSize: 9.2, color: C.text,
      fontFace: F, margin: 0, valign: 'top', lineSpacingMultiple: 1.16,
    });
  });
}

// ══════════════════════════════════════════════════════════════════════════
async function build() {
await buildIcons();

// ── 1. PORTADA ─────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
s.addShape('roundRect', {
  x: 0.5, y: 0.6, w: 3.15, h: 0.42, fill: { color: C.panel },
  line: { color: C.accent, width: 1.1 }, rectRadius: 0.21,
});
s.addText('INFORMÁTICA FORENSE', {
  x: 0.5, y: 0.6, w: 3.15, h: 0.42, fontSize: 9.5, bold: true, color: C.accent,
  fontFace: F, align: 'center', valign: 'middle', margin: 0, charSpacing: 1.4,
});
s.addText('Seis guías del\nproceso forense digital', {
  x: 0.5, y: 1.2, w: 5.7, h: 1.5, fontSize: 34, bold: true, color: C.white,
  fontFace: F, valign: 'middle', margin: 0, lineSpacingMultiple: 1.05,
});
s.addText('Quiénes las desarrollan, qué alcance tienen, qué etapas\nestablecen, qué contiene cada etapa y cómo se aplican', {
  x: 0.5, y: 2.82, w: 5.7, h: 0.7, fontSize: 12, color: C.text, fontFace: F,
  valign: 'top', margin: 0, lineSpacingMultiple: 1.25,
});
G.forEach((g, i) => {
  const y = 1.02 + i * 0.56;
  s.addShape('ellipse', { x: 6.5, y: y + 0.09, w: 0.3, h: 0.3, fill: { color: g.col } });
  s.addText(g.name, {
    x: 6.95, y: y + 0.02, w: 1.9, h: 0.24, fontSize: 12, bold: true, color: C.white,
    fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(g.org, {
    x: 6.95, y: y + 0.25, w: 2.0, h: 0.22, fontSize: 8.5, color: C.muted,
    fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(g.year, {
    x: 8.95, y: y + 0.09, w: 0.55, h: 0.3, fontSize: 9.5, bold: true, color: g.col,
    fontFace: F, align: 'right', margin: 0, valign: 'middle',
  });
});
const meta = [
  ['MATERIA', 'Informática Forense'],
  ['INSTITUCIÓN', 'Escuela Militar de Ingeniería'],
  ['GESTIÓN', 'Cochabamba, Bolivia — 2026'],
];
meta.forEach((m, i) => {
  const x = 0.5 + i * 3.05;
  s.addText(m[0], { x, y: 4.42, w: 2.9, h: 0.22, fontSize: 8, bold: true, color: C.accent, fontFace: F, charSpacing: 1.2, margin: 0 });
  s.addText(m[1], { x, y: 4.66, w: 2.9, h: 0.28, fontSize: 11, color: C.text, fontFace: F, margin: 0 });
});
s.addNotes('Presentación sobre las seis guías que estructuran el trabajo forense digital. No son alternativas entre sí: cada una cubre un tramo distinto del mismo problema y en la práctica se usan combinadas.');
footer(s, 'Portada');
}

// ── 2. AGENDA ──────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Contenido', 'Las seis preguntas del trabajo');
const items = [
  ['1', '¿Quiénes desarrollan cada guía?', 'Organismo, autores, país y año de publicación.'],
  ['2', '¿Cuál es su alcance?', 'A quién se dirige y qué tramo del problema cubre.'],
  ['3', '¿Qué proceso y etapas establece?', 'La secuencia de trabajo que define cada una.'],
  ['4', '¿Qué contiene cada etapa?', 'Las actividades concretas dentro de cada fase.'],
  ['5', 'Ejemplo de aplicación', 'Un mismo caso resuelto con las seis guías.'],
  ['6', 'Conclusiones', 'Cómo se complementan y cuándo usar cada una.'],
];
items.forEach((t, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.5 + col * 4.6, y = 1.38 + row * 1.24;
  card(s, x, y, 4.4, 1.12, C.panel);
  s.addShape('ellipse', { x: x + 0.2, y: y + 0.2, w: 0.42, h: 0.42, fill: { color: C.panel2 } });
  s.addText(t[0], {
    x: x + 0.2, y: y + 0.2, w: 0.42, h: 0.42, fontSize: 13, bold: true, color: C.accent,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(t[1], {
    x: x + 0.75, y: y + 0.17, w: 3.5, h: 0.32, fontSize: 12.5, bold: true, color: C.white,
    fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(t[2], {
    x: x + 0.75, y: y + 0.53, w: 3.5, h: 0.5, fontSize: 9.5, color: C.text,
    fontFace: F, margin: 0, valign: 'top', lineSpacingMultiple: 1.18,
  });
});
s.addNotes('Estas son las seis preguntas que el trabajo debe responder. Las preguntas 3 y 4 se responden juntas: hay una diapositiva por guía donde se ve la secuencia de etapas y, dentro de cada etapa, su contenido.');
footer(s, 'Agenda');
}

// ── 3. PANORAMA ────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Visión de conjunto', 'Las seis guías de un vistazo');
const desc = [
  'Cómo recolectar y archivar la evidencia; define el orden de volatilidad',
  'Calidad del laboratorio forense: procedimientos, validación y competencia',
  'Cuatro principios de conducta para quien manipula la evidencia',
  'Proceso común que une la respuesta a incidentes con la pericia forense',
  'Proceso de cuatro fases integrado a la respuesta a incidentes',
  'Identificar, recolectar, adquirir y preservar la evidencia digital',
];
G.forEach((g, i) => {
  const y = 1.32 + i * 0.59;
  card(s, 0.5, y, 9, 0.53, C.panel);
  iconCircle(s, g.ic, 0.66, y + 0.095, 0.34, g.col);
  s.addText(g.name, {
    x: 1.12, y, w: 1.62, h: 0.53, fontSize: 11.5, bold: true, color: g.col,
    fontFace: F, valign: 'middle', margin: 0,
  });
  s.addShape('rect', { x: 2.8, y: y + 0.13, w: 0.02, h: 0.27, fill: { color: C.line } });
  s.addText(desc[i], {
    x: 2.95, y, w: 5.75, h: 0.53, fontSize: 9.6, color: C.text,
    fontFace: F, valign: 'middle', margin: 0,
  });
  s.addText(g.year, {
    x: 8.75, y, w: 0.6, h: 0.53, fontSize: 10, bold: true, color: C.muted,
    fontFace: F, align: 'right', valign: 'middle', margin: 0,
  });
});
s.addText('Ninguna sustituye a las otras: se ordenan por el tramo del proceso que cubren, no por jerarquía.', {
  x: 0.5, y: 4.92, w: 9, h: 0.24, fontSize: 9, italic: true, color: C.muted,
  fontFace: F, valign: 'middle', margin: 0,
});
s.addNotes('Ubicar el conjunto antes de entrar en el detalle. Señalar que las fechas van de 1998 a 2012: son referencias consolidadas, no documentos nuevos, y por eso todas siguen vigentes.');
footer(s, 'Panorama');
}

// ── 4. PREGUNTA 1: QUIÉNES ─────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Pregunta 1', '¿Quiénes desarrollan cada guía?');
const who = [
  'Dominique Brezinski y Tom Killalea, dentro del Network Working Group de la IETF. Publicada en febrero de 2002 como BCP 55.',
  'Creado en 1998 por los directores de laboratorios criminalísticos federales de EE. UU. Reúne al FBI, la DEA, el Secret Service y el NIST.',
  'Association of Chief Police Officers del Reino Unido, con apoyo técnico de 7Safe. Versión 5 de 2012; hoy la continúa el NPCC.',
  'Felix Freiling y Bastian Schwittay, Universidad de Mannheim (Alemania). Presentado en la conferencia IMF 2007. Es un modelo académico.',
  'Karen Kent, Suzanne Chevalier, Tim Grance y Hung Dang, de la Computer Security Division del NIST. Publicado en 2006.',
  'Subcomité ISO/IEC JTC 1/SC 27, grupo de trabajo 4, con expertos de los países miembros. Publicada en octubre de 2012.',
];
G.forEach((g, i) => {
  const col = i % 3, row = Math.floor(i / 3);
  const x = 0.5 + col * 3.06, y = 1.32 + row * 1.95;
  card(s, x, y, 2.88, 1.8, C.panel);
  iconCircle(s, g.ic, x + 0.2, y + 0.18, 0.44, g.col);
  s.addText(g.name, {
    x: x + 0.74, y: y + 0.18, w: 2.0, h: 0.44, fontSize: 12, bold: true, color: g.col,
    fontFace: F, valign: 'middle', margin: 0,
  });
  s.addText(who[i], {
    x: x + 0.2, y: y + 0.7, w: 2.52, h: 1.0, fontSize: 9.2, color: C.text,
    fontFace: F, valign: 'top', margin: 0, lineSpacingMultiple: 1.18,
  });
});
s.addNotes('Vale la pena notar de dónde viene cada una: dos nacen de la ingeniería de internet y de la normalización (RFC e ISO), dos del mundo policial y de laboratorio (ACPO y SWGDE), una de una agencia de estándares (NIST) y una de la academia (CP4DF). Ese origen explica el enfoque de cada documento.');
footer(s, 'Pregunta 1 · Autoría');
}

// ── 5. PREGUNTA 2: ALCANCE ─────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Pregunta 2', 'Alcance de cada guía');
const scope = [
  'Cómo recolectar y archivar la evidencia durante un incidente. Dirigida a administradores y equipos de respuesta; no cubre el análisis.',
  'Calidad y estandarización del laboratorio forense: procedimientos escritos, validación de herramientas y competencia del personal.',
  'Manejo de evidencia digital por la policía y sus agentes en el Reino Unido, desde la escena del hecho hasta la declaración ante el tribunal.',
  'Modelo que unifica en un solo proceso la respuesta a incidentes y la pericia forense, con un análisis iterativo basado en hipótesis.',
  'Integrar las técnicas forenses en la respuesta a incidentes y construir una capacidad forense organizacional. De acceso libre y gratuito.',
  'Solo las etapas iniciales: identificar, recolectar, adquirir y preservar. El análisis y el informe los cubren la 27042 y la 27043.',
];
G.forEach((g, i) => {
  const y = 1.32 + i * 0.59;
  card(s, 0.5, y, 9, 0.53, C.panel);
  s.addShape('roundRect', { x: 0.5, y, w: 0.07, h: 0.53, fill: { color: g.col }, rectRadius: 0.03 });
  s.addText(g.name, {
    x: 0.72, y, w: 1.75, h: 0.53, fontSize: 11, bold: true, color: g.col,
    fontFace: F, valign: 'middle', margin: 0,
  });
  s.addText(scope[i], {
    x: 2.5, y, w: 6.85, h: 0.53, fontSize: 9.4, color: C.text,
    fontFace: F, valign: 'middle', margin: 0, lineSpacingMultiple: 1.1,
  });
});
s.addText('Lectura clave: RFC 3227 e ISO 27037 cubren la escena; SWGDE y ACPO regulan al actor; NIST y CP4DF definen el proceso completo.', {
  x: 0.5, y: 4.92, w: 9, h: 0.24, fontSize: 9, italic: true, color: C.accent,
  fontFace: F, valign: 'middle', margin: 0,
});
s.addNotes('Aquí se ve por qué las guías no compiten. Tres tipos de alcance: las que dicen qué hacer en la escena, las que dicen quién puede hacerlo y con qué calidad, y las que ordenan el proceso completo de principio a fin.');
footer(s, 'Pregunta 2 · Alcance');
}

// ── 6. RFC 3227 ────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Preguntas 3 y 4  ·  Guía 1 de 6', 'RFC 3227 — Etapas y contenido', C.g1);
stageRows(s, [
  ['Principios rectores',
   'Capturar una imagen lo más fiel posible del sistema, anotar todo con fecha y hora, minimizar los cambios en los datos, recolectar primero y analizar después, y estar preparado para declarar ante un tribunal.'],
  ['Orden de volatilidad',
   'Registros y caché → tablas del kernel, procesos y memoria → sistemas de archivos temporales → disco → registros remotos → topología física de la red → medios de respaldo.'],
  ['Procedimiento de recolección',
   'Método transparente y verificable. Usar herramientas propias almacenadas en medio de solo lectura, no confiar en los binarios del sistema comprometido y no apagar el equipo antes de recolectar.'],
  ['Procedimiento de archivado',
   'Cadena de custodia que registre quién descubrió, recolectó y manejó la evidencia, cuándo, dónde y cómo se almacenó y transfirió. Archivado en medio seguro con acceso restringido.'],
  ['Marco legal y de privacidad',
   'La evidencia debe ser admisible, auténtica, completa, confiable y creíble. No se invade la privacidad de las personas sin justificación ni autorización previa.'],
], C.g1, 1.35, 0.7, 0.76);
s.addNotes('El RFC 3227 es el más corto y el más operativo de los seis. Su aporte insustituible es el orden de volatilidad de la etapa 2: es la regla que evita destruir evidencia en los primeros minutos. La etapa 5 lista los cinco atributos que debe cumplir la evidencia: admisible, auténtica, completa, confiable y creíble.');
footer(s, 'RFC 3227');
}

// ── 7. SWGDE ───────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Preguntas 3 y 4  ·  Guía 2 de 6', 'SWGDE — Etapas y contenido', C.g2);
stageRows(s, [
  ['Preparación del laboratorio',
   'Procedimientos operativos estándar escritos, aprobados y revisados periódicamente; herramientas validadas antes de su uso en casos reales, y personal con competencia técnica demostrada.'],
  ['Inspección visual y documentación',
   'Registrar marca, modelo, número de serie, estado físico y daños del dispositivo recibido. Fotografiar y etiquetar la evidencia antes de cualquier manipulación técnica.'],
  ['Duplicación forense',
   'Adquirir la imagen del medio con bloqueo de escritura, calcular el valor hash y verificar que la copia coincide exactamente con el original antes de trabajar sobre ella.'],
  ['Examen del medio',
   'Todo el análisis se ejecuta sobre la copia verificada, dejando constancia en la bitácora del caso de cada acción realizada, con la herramienta y la versión utilizadas.'],
  ['Devolución y control de calidad',
   'Retorno documentado de la evidencia, revisión técnica y administrativa del informe por un segundo examinador, y archivo completo del expediente del caso.'],
], C.g2, 1.35, 0.7, 0.76);
s.addNotes('SWGDE no es una guía sino un cuerpo de documentos: mejores prácticas de adquisición, procedimientos modelo, requisitos de redacción de informes y de capacitación. Su diferencia con las demás es que regula el sistema de calidad del laboratorio, no solo el caso individual. La etapa 5 —la revisión por un segundo examinador— es su sello distintivo.');
footer(s, 'SWGDE');
}

// ── 8. ACPO ────────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Preguntas 3 y 4  ·  Guía 3 de 6', 'ACPO — Cuatro principios y etapas', C.g3);
const prin = [
  ['No alterar los datos', 'Ninguna acción de la autoridad o de sus agentes debe modificar los datos que después se presentarán ante un tribunal.'],
  ['Competencia justificada', 'Si es imprescindible acceder al original, quien lo haga debe ser competente y capaz de explicar la relevancia de sus actos.'],
  ['Registro de auditoría', 'Debe conservarse el registro de todos los procesos aplicados. Un tercero independiente debe poder repetirlos y obtener el mismo resultado.'],
  ['Responsabilidad del jefe', 'El responsable de la investigación garantiza que todo el equipo cumpla la ley y estos cuatro principios.'],
];
prin.forEach((p, i) => {
  const x = 0.5 + i * 2.3;
  card(s, x, 1.32, 2.1, 2.28, C.panel, C.g3);
  s.addShape('ellipse', { x: x + 0.84, y: 1.44, w: 0.42, h: 0.42, fill: { color: C.g3 } });
  s.addText('P' + (i + 1), {
    x: x + 0.84, y: 1.44, w: 0.42, h: 0.42, fontSize: 11, bold: true, color: C.white,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(p[0], {
    x: x + 0.12, y: 1.94, w: 1.86, h: 0.44, fontSize: 11.5, bold: true, color: C.white,
    fontFace: F, align: 'center', valign: 'middle', margin: 0, lineSpacingMultiple: 1.02,
  });
  s.addText(p[1], {
    x: x + 0.15, y: 2.42, w: 1.8, h: 1.1, fontSize: 8.7, color: C.text,
    fontFace: F, align: 'center', valign: 'top', margin: 0, lineSpacingMultiple: 1.16,
  });
});
s.addText('ETAPAS OPERATIVAS DEL PROCESO', {
  x: 0.5, y: 3.72, w: 5, h: 0.24, fontSize: 8.5, bold: true, color: C.muted,
  fontFace: F, charSpacing: 1.3, margin: 0,
});
const chain = [
  ['PLANIFICACIÓN', 'Autorización legal y preparación del operativo'],
  ['CAPTURA EN ESCENA', 'Fotografiar, etiquetar, decidir incautar o capturar en vivo'],
  ['ANÁLISIS', 'Examen sobre la copia por personal competente'],
  ['PRESENTACIÓN', 'Informe y declaración testimonial ante el tribunal'],
];
chain.forEach((t, i) => {
  const x = 0.5 + i * 2.3;
  card(s, x, 4.03, 2.1, 0.78, C.panel2);
  s.addText(t[0], {
    x: x + 0.08, y: 4.09, w: 1.94, h: 0.24, fontSize: 9, bold: true, color: C.g3,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(t[1], {
    x: x + 0.1, y: 4.33, w: 1.9, h: 0.44, fontSize: 8, color: C.text,
    fontFace: F, align: 'center', valign: 'top', margin: 0, lineSpacingMultiple: 1.1,
  });
  if (i < 3) s.addShape('rightArrow', { x: x + 2.14, y: 4.34, w: 0.12, h: 0.16, fill: { color: C.line } });
});
s.addText('Transversal a las cuatro etapas: la continuidad de la evidencia y el registro de auditoría se mantienen sin interrupción.', {
  x: 0.5, y: 4.9, w: 9, h: 0.24, fontSize: 8.5, italic: true, color: C.muted,
  fontFace: F, valign: 'middle', margin: 0,
});
s.addNotes('ACPO es la única de las seis que empieza por la conducta y no por el procedimiento. Sus cuatro principios son el corazón: no alterar, justificar el acceso, dejar rastro auditable y asignar responsabilidad. El principio 3 es el que permite que otro perito repita el trabajo, que es lo que le da valor probatorio.');
footer(s, 'ACPO');
}

// ── 9. CP4DF ───────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Preguntas 3 y 4  ·  Guía 4 de 6', 'CP4DF — Modelo de proceso común', C.g4);
const fases = [
  ['01', 'Pre-análisis', 'Pre-Analysis', 'loop', [
    'Preparación previa al incidente',
    'Detección y respuesta inicial',
    'Formulación de la estrategia',
    'Recolección y preservación de datos volátiles',
  ]],
  ['02', 'Análisis', 'Analysis', 'loop', [
    'Examen de los datos recolectados',
    'Formulación de una hipótesis',
    'Verificación o refutación',
    'El ciclo se repite hasta que la hipótesis resiste',
  ]],
  ['03', 'Post-análisis', 'Post-Analysis', 'loop', [
    'Documentación del procedimiento',
    'Presentación de los resultados',
    'Restauración del servicio afectado',
    'Lecciones aprendidas para el futuro',
  ]],
];
fases.forEach((f, i) => {
  const x = 0.5 + i * 3.05;
  card(s, x, 1.32, 2.9, 2.62, C.panel, C.g4);
  s.addShape('roundRect', { x, y: 1.32, w: 2.9, h: 0.52, fill: { color: C.g4 }, rectRadius: 0.08 });
  s.addShape('rect', { x, y: 1.62, w: 2.9, h: 0.22, fill: { color: C.g4 } });
  s.addText(f[0] + '   ' + f[1], {
    x, y: 1.32, w: 2.9, h: 0.52, fontSize: 12.5, bold: true, color: C.white,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(f[2], {
    x, y: 1.9, w: 2.9, h: 0.22, fontSize: 8.5, italic: true, color: C.muted,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  f[4].forEach((b, j) => {
    const y = 2.2 + j * 0.42;
    s.addShape('ellipse', { x: x + 0.18, y: y + 0.14, w: 0.12, h: 0.12, fill: { color: C.g4 } });
    s.addText(b, {
      x: x + 0.4, y, w: 2.36, h: 0.4, fontSize: 8.8, color: C.text,
      fontFace: F, valign: 'middle', margin: 0, lineSpacingMultiple: 1.12,
    });
  });
  if (i < 2) s.addShape('rightArrow', { x: x + 2.94, y: 2.55, w: 0.12, h: 0.16, fill: { color: C.line } });
});
card(s, 0.5, 4.08, 9, 0.92, C.panel2);
s.addText('APORTE DEL MODELO', {
  x: 0.72, y: 4.16, w: 3, h: 0.22, fontSize: 8, bold: true, color: C.g4,
  fontFace: F, charSpacing: 1.1, margin: 0,
});
s.addText('Reconcilia dos lógicas que suelen chocar: la urgencia operativa de la respuesta a incidentes y el rigor probatorio de la pericia forense. Además convierte el análisis en un ciclo de hipótesis y verificación —método científico— en lugar de una búsqueda lineal de indicios.', {
  x: 0.72, y: 4.4, w: 8.55, h: 0.55, fontSize: 9.3, color: C.text, fontFace: F,
  valign: 'top', margin: 0, lineSpacingMultiple: 1.16,
});
s.addNotes('CP4DF es el único modelo académico del conjunto y el único con solo tres fases. Su idea central: cuando ocurre un incidente hay dos equipos con objetivos opuestos —el que quiere restablecer el servicio ya y el que quiere preservar la evidencia intacta—. El modelo los pone en un solo proceso. La fase 2 es iterativa: si la hipótesis se refuta, se vuelve al examen.');
footer(s, 'CP4DF');
}

// ── 10. NIST SP 800-86 ─────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Preguntas 3 y 4  ·  Guía 5 de 6', 'NIST SP 800-86 — Cuatro fases', C.g5);
const nf = [
  ['01', 'Recolección', 'Collection', 'Identificar, etiquetar y adquirir los datos preservando su integridad mediante imagen bit a bit y hash.'],
  ['02', 'Examen', 'Examination', 'Filtrar el volumen, descartar archivos conocidos y recuperar borrados para extraer lo pertinente.'],
  ['03', 'Análisis', 'Analysis', 'Correlacionar fuentes, reconstruir la línea de tiempo e identificar los artefactos del incidente.'],
  ['04', 'Reporte', 'Reporting', 'Documentar en informe técnico, informe ejecutivo y anexo legal con la cadena de custodia.'],
];
nf.forEach((p, i) => {
  const x = 0.5 + i * 2.3;
  card(s, x, 1.32, 2.1, 2.6, C.panel, C.g5);
  s.addShape('ellipse', { x: x + 0.83, y: 1.5, w: 0.44, h: 0.44, fill: { color: C.g5 } });
  s.addText(p[0], {
    x: x + 0.83, y: 1.5, w: 0.44, h: 0.44, fontSize: 11, bold: true, color: C.white,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(p[1], {
    x: x + 0.1, y: 2.06, w: 1.9, h: 0.3, fontSize: 13.5, bold: true, color: C.white,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(p[2], {
    x: x + 0.1, y: 2.36, w: 1.9, h: 0.22, fontSize: 8.5, italic: true, color: C.muted,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(p[3], {
    x: x + 0.14, y: 2.64, w: 1.82, h: 1.18, fontSize: 8.8, color: C.text,
    fontFace: F, align: 'center', valign: 'top', margin: 0, lineSpacingMultiple: 1.16,
  });
  if (i < 3) s.addShape('rightArrow', { x: x + 2.14, y: 2.54, w: 0.12, h: 0.16, fill: { color: C.line } });
});
s.addText('CADA FASE TRANSFORMA LO QUE RECIBE', {
  x: 0.5, y: 4.04, w: 5, h: 0.24, fontSize: 8.5, bold: true, color: C.muted,
  fontFace: F, charSpacing: 1.3, margin: 0,
});
const chain = ['MEDIOS', 'DATOS', 'INFORMACIÓN', 'EVIDENCIA', 'INFORME'];
chain.forEach((t, i) => {
  const x = 0.5 + i * 1.87;
  const last = i === chain.length - 1;
  s.addShape('roundRect', {
    x, y: 4.35, w: 1.54, h: 0.46, fill: { color: last ? '17394A' : C.panel },
    rectRadius: 0.22, line: last ? { color: C.g5, width: 1 } : undefined,
  });
  s.addText(t, {
    x, y: 4.35, w: 1.54, h: 0.46, fontSize: 9.5, bold: true,
    color: last ? C.g5 : C.text, fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  if (!last) s.addShape('rightArrow', { x: x + 1.62, y: 4.5, w: 0.18, h: 0.16, fill: { color: C.line } });
});
s.addNotes('El NIST es el modelo de proceso más difundido. Su aporte propio es la cadena de abajo: define qué recibe y qué entrega cada fase. Si se salta una, la siguiente trabaja con material que no puede sostener.');
footer(s, 'NIST SP 800-86');
}

// ── 11. ISO/IEC 27037 ──────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Preguntas 3 y 4  ·  Guía 6 de 6', 'ISO/IEC 27037 — Los cuatro procesos', C.g6);
const iso = [
  ['01', 'Identificación', 'Localizar y reconocer los dispositivos y medios que pueden contener evidencia, en su forma física y lógica, priorizando según su volatilidad.'],
  ['02', 'Recolección', 'Retirar los dispositivos del lugar de los hechos y trasladarlos a un entorno controlado, cuando corresponde llevarse el original.'],
  ['03', 'Adquisición', 'Producir una copia verificable de la evidencia y documentar el método, cuando no es viable o conveniente llevarse el original.'],
  ['04', 'Preservación', 'Proteger la integridad y la originalidad de la evidencia en el embalaje, el traslado y el almacenamiento, con cadena de custodia.'],
];
iso.forEach((p, i) => {
  const x = 0.5 + i * 2.3;
  card(s, x, 1.32, 2.1, 2.3, C.panel, C.g6);
  s.addShape('ellipse', { x: x + 0.83, y: 1.48, w: 0.44, h: 0.44, fill: { color: C.g6 } });
  s.addText(p[0], {
    x: x + 0.83, y: 1.48, w: 0.44, h: 0.44, fontSize: 11, bold: true, color: '0B1524',
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(p[1], {
    x: x + 0.1, y: 2.02, w: 1.9, h: 0.3, fontSize: 12.5, bold: true, color: C.white,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(p[2], {
    x: x + 0.14, y: 2.36, w: 1.82, h: 1.18, fontSize: 8.7, color: C.text,
    fontFace: F, align: 'center', valign: 'top', margin: 0, lineSpacingMultiple: 1.16,
  });
  if (i < 3) s.addShape('rightArrow', { x: x + 2.14, y: 2.4, w: 0.12, h: 0.16, fill: { color: C.line } });
});
const roles = [
  ['user', 'DEFR', 'Digital Evidence First Responder', 'Primer respondiente: persona autorizada y capacitada para actuar primero en la escena y recolectar la evidencia.'],
  ['users', 'DES', 'Digital Evidence Specialist', 'Especialista: interviene en casos técnicamente complejos como arreglos RAID, redes y servidores de correo.'],
];
roles.forEach((r, i) => {
  const x = 0.5 + i * 4.6;
  card(s, x, 3.76, 4.4, 1.06, C.panel2);
  iconCircle(s, r[0], x + 0.18, 3.92, 0.4, C.panel);
  s.addText(r[1], {
    x: x + 0.68, y: 3.88, w: 1.0, h: 0.26, fontSize: 11.5, bold: true, color: C.g6,
    fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(r[2], {
    x: x + 1.6, y: 3.88, w: 2.7, h: 0.26, fontSize: 8.2, italic: true, color: C.muted,
    fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(r[3], {
    x: x + 0.68, y: 4.16, w: 3.55, h: 0.6, fontSize: 8.8, color: C.text,
    fontFace: F, margin: 0, valign: 'top', lineSpacingMultiple: 1.14,
  });
});
s.addText('Principios que exige la norma: relevancia, confiabilidad, suficiencia, auditabilidad, repetibilidad, reproducibilidad y justificabilidad.', {
  x: 0.5, y: 4.9, w: 9, h: 0.26, fontSize: 8.6, italic: true, color: C.muted,
  fontFace: F, valign: 'middle', margin: 0,
});
s.addNotes('La ISO 27037 es la única norma certificable del conjunto y la única de pago. Cubre solo las etapas iniciales: el análisis lo trata la 27042 y el marco general de la investigación la 27043. Su aporte propio son los roles DEFR y DES: define quién puede hacer qué según su nivel de competencia.');
footer(s, 'ISO/IEC 27037');
}

// ── 12. MAPEO COMPARATIVO ──────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Síntesis de las preguntas 3 y 4', 'Cómo se alinean las etapas de las seis guías');
const cols = ['Preparación', 'Identificación\ny recolección', 'Adquisición\ny preservación', 'Examen\ny análisis', 'Informe\ny presentación'];
cols.forEach((c, i) => {
  const x = 2.3 + i * 1.43;
  s.addText(c, {
    x, y: 1.26, w: 1.4, h: 0.5, fontSize: 8, bold: true, color: C.muted, fontFace: F,
    align: 'center', valign: 'middle', margin: 0, lineSpacingMultiple: 1.05,
  });
});
const grid = [
  ['Kit de herramientas', 'Orden de volatilidad', 'Archivado y custodia', null, 'Notas para declarar'],
  ['SOP y validación', 'Inspección visual', 'Duplicación forense', 'Examen del medio', 'Informe revisado'],
  ['Planificación', 'Captura en escena', 'Continuidad', 'Personal competente', 'Declaración'],
  ['Pre-análisis', 'Pre-análisis', 'Pre-análisis', 'Análisis iterativo', 'Post-análisis'],
  ['Capacidad forense', 'Collection', 'Collection', 'Examination y Analysis', 'Reporting'],
  [null, 'Identificación\ny recolección', 'Adquisición\ny preservación', 'Lo cubre la 27042', 'Lo cubre la 27043'],
];
G.forEach((g, r) => {
  const y = 1.83 + r * 0.54;
  s.addShape('roundRect', { x: 0.5, y, w: 1.72, h: 0.48, fill: { color: C.panel }, rectRadius: 0.06 });
  s.addShape('roundRect', { x: 0.5, y, w: 0.06, h: 0.48, fill: { color: g.col }, rectRadius: 0.03 });
  s.addText(g.name, {
    x: 0.66, y, w: 1.5, h: 0.48, fontSize: 9.3, bold: true, color: g.col,
    fontFace: F, valign: 'middle', margin: 0,
  });
  grid[r].forEach((cell, i) => {
    const x = 2.3 + i * 1.43;
    const empty = cell === null;
    const soft = !empty && cell.startsWith('Lo cubre');
    s.addShape('roundRect', {
      x, y, w: 1.4, h: 0.48, fill: { color: empty ? '0F1B2C' : (soft ? C.panel2 : C.panel) },
      rectRadius: 0.06,
    });
    s.addText(empty ? '—' : cell, {
      x: x + 0.05, y, w: 1.3, h: 0.48, fontSize: empty ? 10 : 7.8,
      color: empty ? C.line : (soft ? C.muted : C.text), italic: soft,
      fontFace: F, align: 'center', valign: 'middle', margin: 0, lineSpacingMultiple: 1.02,
    });
  });
});
s.addNotes('Esta es la diapositiva que responde de forma comparada las preguntas 3 y 4. Los guiones marcan lo que cada guía deliberadamente no cubre: el RFC 3227 no analiza y la ISO 27037 no prepara ni analiza. Ahí se ve que hay que combinarlas.');
footer(s, 'Mapeo de etapas');
}

// ── 13. EJEMPLO — PLANTEAMIENTO ────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Pregunta 5', 'Ejemplo de aplicación: fuga de información', C.g6);
card(s, 0.5, 1.3, 9, 0.78, C.panel, C.g6);
iconCircle(s, 'alert', 0.68, 1.48, 0.42, C.panel2);
s.addText('CASO HIPOTÉTICO:  la gerencia de una empresa denuncia la filtración del listado de clientes. Se sospecha de un funcionario del área comercial y se solicita una investigación que sirva de respaldo ante la autoridad competente.', {
  x: 1.24, y: 1.3, w: 8.1, h: 0.78, fontSize: 10, color: C.g6, fontFace: F,
  valign: 'middle', margin: 0, lineSpacingMultiple: 1.12,
});
const blocks = [
  ['La escena', 'El equipo del sospechoso sigue encendido y conectado a la red. Existe además un servidor de archivos con arreglo RAID y los registros del proxy corporativo.'],
  ['Lo que se pide', 'Determinar si hubo salida de información confidencial, por qué medio y en qué momento, con material que pueda sostenerse ante la autoridad.'],
  ['La complicación', 'No se puede apagar el equipo sin perder la memoria, y el arreglo RAID del servidor no puede trasladarse sin detener la operación de la empresa.'],
];
blocks.forEach((b, i) => {
  const x = 0.5 + i * 3.06;
  card(s, x, 2.24, 2.88, 1.74, C.panel);
  s.addShape('ellipse', { x: x + 0.2, y: 2.42, w: 0.28, h: 0.28, fill: { color: C.accent } });
  s.addText(String(i + 1), {
    x: x + 0.2, y: 2.42, w: 0.28, h: 0.28, fontSize: 9, bold: true, color: '0B1524',
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(b[0], {
    x: x + 0.58, y: 2.4, w: 2.2, h: 0.32, fontSize: 12, bold: true, color: C.white,
    fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(b[1], {
    x: x + 0.2, y: 2.82, w: 2.52, h: 1.0, fontSize: 9.2, color: C.text,
    fontFace: F, margin: 0, valign: 'top', lineSpacingMultiple: 1.18,
  });
});
s.addText('CADA GUÍA INTERVIENE EN UN MOMENTO DISTINTO DEL MISMO CASO', {
  x: 0.5, y: 4.14, w: 9, h: 0.24, fontSize: 8.5, bold: true, color: C.muted,
  fontFace: F, charSpacing: 1.3, margin: 0,
});
G.forEach((g, i) => {
  const x = 0.5 + i * 1.52;
  s.addShape('roundRect', { x, y: 4.45, w: 1.4, h: 0.5, fill: { color: C.panel }, line: { color: g.col, width: 1 }, rectRadius: 0.25 });
  s.addText(g.name, {
    x, y: 4.45, w: 1.4, h: 0.5, fontSize: 8.5, bold: true, color: g.col,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
});
s.addNotes('Un solo caso que obliga a usar las seis. El equipo encendido activa el RFC 3227, el RAID activa el rol DES de la ISO, el acceso en vivo activa los principios del ACPO, el laboratorio activa el SWGDE, la organización del trabajo activa el NIST y el razonamiento activa el CP4DF.');
footer(s, 'Pregunta 5 · El caso');
}

// ── 14. EJEMPLO — APLICACIÓN DE LAS SEIS ───────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Pregunta 5', 'Qué aporta cada guía al mismo caso', C.g6);
const app = [
  'El equipo está encendido: primero se vuelca la memoria RAM y las conexiones activas, después el disco. Prohíbe apagar antes de recolectar.',
  'El laboratorio aplica su procedimiento: inspección visual, fotografía, número de serie y duplicación con una herramienta previamente validada.',
  'Quien accede al equipo encendido debe ser competente y justificar cada acción; el registro de auditoría se abre desde el primer minuto.',
  'El análisis se plantea como hipótesis —la fuga salió por el correo personal— que se verifica o se descarta, volviendo al examen si se refuta.',
  'Ordena todo el trabajo en las cuatro fases y define qué entrega cada una a la siguiente, evitando saltos por urgencia.',
  'El DEFR asegura la escena y el DES resuelve la adquisición del arreglo RAID en caliente; se documenta la preservación de cada elemento.',
];
G.forEach((g, i) => {
  const y = 1.32 + i * 0.59;
  card(s, 0.5, y, 9, 0.53, C.panel);
  s.addShape('roundRect', { x: 0.5, y, w: 0.07, h: 0.53, fill: { color: g.col }, rectRadius: 0.03 });
  s.addText(g.name, {
    x: 0.72, y, w: 1.75, h: 0.53, fontSize: 11, bold: true, color: g.col,
    fontFace: F, valign: 'middle', margin: 0,
  });
  s.addText(app[i], {
    x: 2.5, y, w: 6.85, h: 0.53, fontSize: 9.4, color: C.text,
    fontFace: F, valign: 'middle', margin: 0, lineSpacingMultiple: 1.1,
  });
});
s.addText('Resultado: un informe que resiste el cuestionamiento técnico y el legal, porque cada decisión tomada está respaldada por una guía reconocida.', {
  x: 0.5, y: 4.92, w: 9, h: 0.24, fontSize: 9, italic: true, color: C.g6,
  fontFace: F, valign: 'middle', margin: 0,
});
s.addNotes('Recorrer las seis filas en orden cronológico del caso, no en el orden de la lista: primero ACPO y RFC 3227 en la escena, después ISO y SWGDE en la adquisición, luego CP4DF en el razonamiento y NIST ordenando todo el conjunto.');
footer(s, 'Pregunta 5 · Aplicación');
}

// ── 15. CONCLUSIONES ───────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Pregunta 6', 'Conclusiones');
const cons = [
  'Las seis guías no compiten entre sí: cubren tramos distintos del mismo problema y en la práctica se aplican combinadas, no de forma excluyente.',
  'RFC 3227 e ISO/IEC 27037 son las más operativas en la escena: el RFC aporta el orden de volatilidad y la ISO formaliza los roles y la preservación.',
  'SWGDE y ACPO regulan al actor antes que al procedimiento: la calidad del laboratorio y la conducta de quien manipula la evidencia.',
  'NIST SP 800-86 y CP4DF son los modelos de proceso: el primero organiza el trabajo en fases con entradas y salidas, el segundo lo convierte en un ciclo de hipótesis y verificación.',
  'Una investigación sólida combina las seis: la conducta del ACPO, la calidad del SWGDE, el orden del RFC 3227, la preservación de la ISO, las fases del NIST y el razonamiento del CP4DF.',
];
cons.forEach((t, i) => {
  const y = 1.35 + i * 0.75;
  card(s, 0.5, y, 9, 0.68, C.panel);
  s.addShape('ellipse', { x: 0.7, y: y + 0.17, w: 0.34, h: 0.34, fill: { color: C.panel2 } });
  s.addText(String(i + 1).padStart(2, '0'), {
    x: 0.7, y: y + 0.17, w: 0.34, h: 0.34, fontSize: 9.5, bold: true, color: C.accent,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(t, {
    x: 1.18, y, w: 8.1, h: 0.68, fontSize: 10.3, color: C.text, fontFace: F,
    valign: 'middle', margin: 0, lineSpacingMultiple: 1.14,
  });
});
s.addNotes('Cerrar con la conclusión 5: la pregunta correcta no es cuál guía usar, sino en qué momento del caso aplica cada una. Un perito que solo conoce una queda expuesto en el tramo que esa guía no cubre.');
footer(s, 'Pregunta 6 · Conclusiones');
}

// ── 16. CIERRE ─────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
s.addText('Gracias por su atención', {
  x: 0.5, y: 0.95, w: 6.5, h: 0.7, fontSize: 34, bold: true, color: C.white,
  fontFace: F, valign: 'middle', margin: 0,
});
s.addText('Espacio para preguntas y comentarios', {
  x: 0.5, y: 1.68, w: 6.5, h: 0.32, fontSize: 12.5, color: C.accent, fontFace: F, margin: 0,
});
s.addText('REFERENCIAS', {
  x: 0.5, y: 2.4, w: 4, h: 0.24, fontSize: 8.5, bold: true, color: C.muted,
  fontFace: F, charSpacing: 1.3, margin: 0,
});
const refs = [
  'Brezinski, D. y Killalea, T. (2002). Guidelines for Evidence Collection and Archiving (RFC 3227, BCP 55). IETF.',
  'SWGDE (2018). Best Practices for Computer Forensic Acquisitions y Model Standard Operation Procedures for Computer Forensics.',
  'ACPO (2012). Good Practice Guide for Digital Evidence, versión 5. Reino Unido.',
  'Freiling, F. C. y Schwittay, B. (2007). A Common Process Model for Incident Response and Computer Forensics. IMF 2007, Alemania.',
  'Kent, K., Chevalier, S., Grance, T. y Dang, H. (2006). Guide to Integrating Forensic Techniques into Incident Response (NIST SP 800-86).',
  'ISO/IEC (2012). ISO/IEC 27037: Guidelines for identification, collection, acquisition and preservation of digital evidence.',
];
refs.forEach((r, i) => {
  const y = 2.7 + i * 0.37;
  s.addShape('ellipse', { x: 0.53, y: y + 0.11, w: 0.09, h: 0.09, fill: { color: G[i].col } });
  s.addText(r, {
    x: 0.78, y, w: 8.7, h: 0.32, fontSize: 8.6, color: C.muted, fontFace: F,
    valign: 'middle', margin: 0,
  });
});
s.addText('Materia: Informática Forense  ·  Escuela Militar de Ingeniería  ·  Cochabamba, 2026', {
  x: 0.5, y: 4.92, w: 9, h: 0.28, fontSize: 9.5, color: C.text, fontFace: F, margin: 0, valign: 'middle',
});
s.addNotes('Agradecer y abrir preguntas. Tener presente que cinco de las seis referencias son de descarga gratuita; solo la ISO/IEC 27037 se compra.');
footer(s, 'Cierre');
}

await pres.writeFile({ fileName: 'Guias_Forenses_Presentacion.pptx' });
console.log('OK — Guias_Forenses_Presentacion.pptx (' + pageNo + ' diapositivas)');
}

build().catch((e) => { console.error(e); process.exit(1); });

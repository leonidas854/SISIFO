const pptxgen = require('pptxgenjs');
const React = require('react');
const RDS = require('react-dom/server');
const sharp = require('sharp');
const Fi = require('react-icons/fi');

// ─── Paleta ───────────────────────────────────────────────────────────────
const C = {
  bg:     '0B1524',
  panel:  '13233A',
  panel2: '1B3049',
  line:   '24405E',
  ghost:  '101E31',
  white:  'FFFFFF',
  text:   'C7D8E6',
  muted:  '7D9BB3',
  accent: '22B8CF',
  amber:  'F0A202',
  p1:     'E05555',
  p2:     'E8873A',
  p3:     '3D9BE0',
  p4:     '2FB37A',
};
const F = 'Calibri';
const W = 10, H = 5.625;

// ─── Iconos (react-icons → PNG base64) ────────────────────────────────────
const ICONS = {};
async function makeIcon(key, Comp, color) {
  let svg = RDS.renderToStaticMarkup(React.createElement(Comp, { size: 256 }));
  svg = svg.replace(/currentColor/g, '#' + color);
  const buf = await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer();
  ICONS[key] = 'image/png;base64,' + buf.toString('base64');
}

async function buildIcons() {
  const spec = [
    ['flag',    Fi.FiFlag,          C.accent],
    ['target',  Fi.FiTarget,        C.accent],
    ['book',    Fi.FiBookOpen,      C.accent],
    ['alert',   Fi.FiAlertTriangle, C.p1],
    ['search',  Fi.FiSearch,        C.p2],
    ['server',  Fi.FiServer,        C.p3],
    ['case',    Fi.FiBriefcase,     C.p4],
    ['dl',      Fi.FiDownload,      C.white],
    ['filter',  Fi.FiFilter,        C.white],
    ['activity',Fi.FiActivity,      C.white],
    ['file',    Fi.FiFileText,      C.white],
    ['lock',    Fi.FiLock,          C.accent],
    ['edit',    Fi.FiEdit3,         C.accent],
    ['hash',    Fi.FiHash,          C.accent],
    ['link',    Fi.FiLink,          C.accent],
    ['tool',    Fi.FiTool,          C.accent],
    ['users',   Fi.FiUsers,         C.accent],
    ['shield',  Fi.FiShield,        C.accent],
    ['clock',   Fi.FiClock,         C.amber],
  ];
  for (const [k, comp, col] of spec) await makeIcon(k, comp, col);
}

// ─── Ayudantes de composición ─────────────────────────────────────────────
const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.author = 'Informática Forense — EMI';
pres.title  = 'NIST SP 800-86 — Proceso Forense Digital';

function bg(s) {
  s.addShape('rect', { x: 0, y: 0, w: W, h: H, fill: { color: C.bg } });
}

function card(s, x, y, w, h, fill, border) {
  const o = { x, y, w, h, fill: { color: fill || C.panel }, rectRadius: 0.08 };
  if (border) o.line = { color: border, width: 1.25 };
  s.addShape('roundRect', o);
}

function header(s, kicker, title, color) {
  const col = color || C.accent;
  s.addShape('ellipse', { x: 0.5, y: 0.44, w: 0.15, h: 0.15, fill: { color: col } });
  s.addText(kicker.toUpperCase(), {
    x: 0.76, y: 0.38, w: 8.7, h: 0.27, fontSize: 9.5, bold: true,
    color: col, fontFace: F, charSpacing: 1.6, margin: 0, valign: 'middle',
  });
  s.addText(title, {
    x: 0.5, y: 0.68, w: 9, h: 0.52, fontSize: 27, bold: true,
    color: C.white, fontFace: F, margin: 0, valign: 'middle',
  });
}

let pageNo = 0;
function footer(s, label) {
  pageNo++;
  s.addText('NIST SP 800-86  ·  ' + label, {
    x: 0.5, y: 5.24, w: 7, h: 0.24, fontSize: 8, color: C.muted,
    fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(String(pageNo).padStart(2, '0'), {
    x: 8.9, y: 5.24, w: 0.6, h: 0.24, fontSize: 8, bold: true, color: C.accent,
    fontFace: F, align: 'right', margin: 0, valign: 'middle',
  });
}

function iconCircle(s, key, x, y, d, fill) {
  s.addShape('ellipse', { x, y, w: d, h: d, fill: { color: fill } });
  const p = d * 0.28;
  s.addImage({ data: ICONS[key], x: x + p / 2, y: y + p / 2, w: d - p, h: d - p });
}

// ═══════════════════════════════════════════════════════════════════════════
async function build() {
await buildIcons();

const PHASES = [
  { n: '01', es: 'Recolección', en: 'Collection',  col: C.p1, ic: 'dl',
    desc: 'Identificar, etiquetar, registrar y adquirir los datos de las fuentes relevantes, preservando su integridad.' },
  { n: '02', es: 'Examen',      en: 'Examination', col: C.p2, ic: 'filter',
    desc: 'Procesar grandes volúmenes de datos —de forma automatizada y manual— para extraer lo que interesa al caso.' },
  { n: '03', es: 'Análisis',    en: 'Analysis',    col: C.p3, ic: 'activity',
    desc: 'Correlacionar la información obtenida y derivar conclusiones útiles que respondan a las preguntas del caso.' },
  { n: '04', es: 'Reporte',     en: 'Reporting',   col: C.p4, ic: 'file',
    desc: 'Documentar el proceso, los hallazgos y las conclusiones de forma técnica, ejecutiva y legalmente admisible.' },
];

// ── 1. PORTADA ─────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
s.addText('800-86', {
  x: 2.55, y: 3.05, w: 6.95, h: 2.4, fontSize: 148, bold: true, color: C.ghost,
  fontFace: F, align: 'right', valign: 'middle', margin: 0,
});
s.addShape('roundRect', {
  x: 0.5, y: 0.62, w: 3.15, h: 0.42, fill: { color: C.panel },
  line: { color: C.accent, width: 1.1 }, rectRadius: 0.21,
});
s.addText('INFORMÁTICA FORENSE', {
  x: 0.5, y: 0.62, w: 3.15, h: 0.42, fontSize: 9.5, bold: true, color: C.accent,
  fontFace: F, align: 'center', valign: 'middle', margin: 0, charSpacing: 1.4,
});
s.addText('NIST SP 800-86', {
  x: 0.5, y: 1.22, w: 6.1, h: 0.9, fontSize: 46, bold: true, color: C.white,
  fontFace: F, valign: 'middle', margin: 0, charSpacing: 0.5,
});
s.addText('Guía para integrar técnicas forenses\nen la respuesta a incidentes', {
  x: 0.5, y: 2.18, w: 5.5, h: 0.8, fontSize: 15, color: C.text,
  fontFace: F, valign: 'top', margin: 0, lineSpacingMultiple: 1.25,
});
s.addText('Guide to Integrating Forensic Techniques into Incident Response', {
  x: 0.5, y: 3.02, w: 5.5, h: 0.3, fontSize: 10, italic: true, color: C.muted,
  fontFace: F, margin: 0,
});

// Mini-mapa de las 4 fases (derecha)
PHASES.forEach((p, i) => {
  const y = 1.22 + i * 0.66;
  s.addShape('ellipse', { x: 6.55, y: y + 0.06, w: 0.44, h: 0.44, fill: { color: p.col } });
  s.addText(p.n, {
    x: 6.55, y: y + 0.06, w: 0.44, h: 0.44, fontSize: 11, bold: true, color: C.white,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(p.es, {
    x: 7.12, y: y + 0.04, w: 2.4, h: 0.26, fontSize: 12.5, bold: true, color: C.white,
    fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(p.en, {
    x: 7.12, y: y + 0.29, w: 2.4, h: 0.24, fontSize: 9.5, italic: true, color: p.col,
    fontFace: F, margin: 0, valign: 'middle',
  });
});

// Pie institucional
const meta = [
  ['MATERIA',    'Informática Forense'],
  ['INSTITUCIÓN','Escuela Militar de Ingeniería'],
  ['GESTIÓN',    'Cochabamba, Bolivia — 2026'],
];
meta.forEach((m, i) => {
  const x = 0.5 + i * 3.05;
  s.addText(m[0], { x, y: 4.42, w: 2.9, h: 0.22, fontSize: 8, bold: true, color: C.accent, fontFace: F, charSpacing: 1.2, margin: 0 });
  s.addText(m[1], { x, y: 4.66, w: 2.9, h: 0.28, fontSize: 11, color: C.text, fontFace: F, margin: 0 });
});
s.addNotes('Presentación sobre la guía NIST SP 800-86. De las seis guías vistas en clase (RFC 3227, SWGDE, ACPO, CP4DF, NIST e ISO) se eligió NIST porque define un proceso de cuatro fases claro, es de acceso libre y se aplica directamente a la respuesta a incidentes reales.');
footer(s, 'Portada');
}

// ── 2. AGENDA ──────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Contenido', 'Agenda de la exposición');
const items = [
  'Objetivos del trabajo',
  '¿Qué es el NIST?',
  'Autoría de la guía SP 800-86',
  'Alcance y ámbito de aplicación',
  'Panorama: las seis guías forenses',
  'El proceso forense de cuatro fases',
  'Contenido detallado de cada etapa',
  'Ejemplo aplicado: caso de ransomware',
  'Recomendaciones y conclusiones',
];
items.forEach((t, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.5 + col * 4.6, y = 1.42 + row * 0.72;
  card(s, x, y, 4.4, 0.6, C.panel);
  s.addShape('ellipse', { x: x + 0.16, y: y + 0.13, w: 0.34, h: 0.34, fill: { color: C.panel2 } });
  s.addText(String(i + 1), {
    x: x + 0.16, y: y + 0.13, w: 0.34, h: 0.34, fontSize: 10.5, bold: true,
    color: C.accent, fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(t, {
    x: x + 0.62, y, w: 3.65, h: 0.6, fontSize: 12, color: C.text,
    fontFace: F, valign: 'middle', margin: 0,
  });
});
s.addNotes('Recorrido de la exposición: primero el contexto (qué es NIST, quién escribe la guía, para quién sirve), luego el núcleo técnico (las cuatro fases y su contenido), después la aplicación práctica y el cierre.');
footer(s, 'Agenda');
}

// ── 3. OBJETIVOS ───────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Propósito del trabajo', 'Objetivos');
card(s, 0.5, 1.35, 9, 1.42, C.panel, C.accent);
s.addText('OBJETIVO GENERAL', {
  x: 0.8, y: 1.5, w: 3, h: 0.24, fontSize: 8.5, bold: true, color: C.accent,
  fontFace: F, charSpacing: 1.3, margin: 0,
});
s.addText('Analizar la guía NIST SP 800-86 para comprender el proceso forense de cuatro fases que propone, el contenido de cada etapa y su aplicación práctica en la investigación de incidentes de seguridad informática.', {
  x: 0.8, y: 1.78, w: 8.4, h: 0.85, fontSize: 14.5, color: C.white,
  fontFace: F, valign: 'top', margin: 0, lineSpacingMultiple: 1.28,
});
s.addText('OBJETIVOS ESPECÍFICOS', {
  x: 0.5, y: 2.95, w: 4, h: 0.26, fontSize: 8.5, bold: true, color: C.muted,
  fontFace: F, charSpacing: 1.3, margin: 0,
});
const objs = [
  ['a', 'Identificar el organismo que elabora la guía, sus autores y el alcance que declara.'],
  ['b', 'Describir las cuatro fases del proceso y el contenido concreto de cada una.'],
  ['c', 'Aplicar el proceso completo a un caso de incidente y extraer recomendaciones.'],
];
objs.forEach((o, i) => {
  const x = 0.5 + i * 3.06;
  card(s, x, 3.26, 2.88, 1.5, C.panel);
  s.addShape('ellipse', { x: x + 0.2, y: 3.44, w: 0.38, h: 0.38, fill: { color: C.panel2 } });
  s.addText(o[0], {
    x: x + 0.2, y: 3.44, w: 0.38, h: 0.38, fontSize: 12, bold: true, color: C.accent,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(o[1], {
    x: x + 0.2, y: 3.94, w: 2.5, h: 0.95, fontSize: 10.5, color: C.text,
    fontFace: F, valign: 'top', margin: 0, lineSpacingMultiple: 1.22,
  });
});
s.addNotes('El objetivo general marca el alcance del trabajo: no se trata de traducir la guía, sino de entender su lógica de proceso y demostrar que funciona sobre un caso concreto.');
footer(s, 'Objetivos');
}

// ── 4. ¿QUÉ ES NIST? ───────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Contexto institucional', '¿Qué es el NIST?');
const cards = [
  ['flag', 'Organismo federal', 'Instituto Nacional de Estándares y Tecnología, del Departamento de Comercio de EE. UU. Produce estándares técnicos, no normas policiales.'],
  ['target', 'Su misión', 'Promover la innovación mediante mediciones, normas y tecnología. En ciberseguridad define marcos que hoy son referencia mundial de facto.'],
  ['book', 'La serie SP 800', 'Special Publications dedicadas a seguridad informática. Más de 200 documentos gratuitos en csrc.nist.gov, entre ellos el SP 800-86.'],
];
cards.forEach((c, i) => {
  const x = 0.5 + i * 3.06;
  card(s, x, 1.35, 2.88, 2.3, C.panel);
  iconCircle(s, c[0], x + 0.22, 1.55, 0.62, C.panel2);
  s.addText(c[1], {
    x: x + 0.22, y: 2.28, w: 2.5, h: 0.3, fontSize: 13, bold: true, color: C.white,
    fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(c[2], {
    x: x + 0.22, y: 2.62, w: 2.5, h: 0.98, fontSize: 9.8, color: C.text,
    fontFace: F, valign: 'top', margin: 0, lineSpacingMultiple: 1.22,
  });
});
// Línea de tiempo
s.addText('HITOS', { x: 0.5, y: 3.82, w: 2, h: 0.24, fontSize: 8.5, bold: true, color: C.muted, fontFace: F, charSpacing: 1.3, margin: 0 });
const hits = [
  ['1901', 'Se funda como National\nBureau of Standards'],
  ['1988', 'Pasa a llamarse NIST y\namplía su mandato'],
  ['1990s', 'Nace la serie SP 800\nde ciberseguridad'],
  ['2006', 'Se publica el\nSP 800-86'],
];
s.addShape('rect', { x: 0.72, y: 4.36, w: 8.1, h: 0.02, fill: { color: C.line } });
hits.forEach((h, i) => {
  const cx = 0.72 + i * 2.7;
  const isLast = i === hits.length - 1;
  s.addShape('ellipse', { x: cx - 0.09, y: 4.27, w: 0.2, h: 0.2, fill: { color: isLast ? C.accent : C.line } });
  s.addText(h[0], {
    x: cx - 0.12, y: 4.06, w: 1.4, h: 0.22, fontSize: 11.5, bold: true,
    color: isLast ? C.accent : C.white, fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(h[1], {
    x: cx - 0.05, y: 4.56, w: 2.35, h: 0.52, fontSize: 9.3, color: C.muted,
    fontFace: F, margin: 0, valign: 'top', lineSpacingMultiple: 1.18,
  });
});
s.addNotes('Aclarar que NIST no impone nada por ley fuera de EE.UU.: su fuerza es técnica. Sus publicaciones son gratuitas, lo que explica por qué se adoptan en todo el mundo, incluida la región.');
footer(s, '¿Qué es el NIST?');
}

// ── 5. QUIÉNES ELABORAN ────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Autoría y publicación', '¿Quiénes elaboran la guía?');
card(s, 0.5, 1.35, 4.45, 3.62, C.panel);
s.addText('ORGANISMO RESPONSABLE', { x: 0.75, y: 1.52, w: 3.9, h: 0.24, fontSize: 8.5, bold: true, color: C.accent, fontFace: F, charSpacing: 1.3, margin: 0 });
const org = [
  ['Institución', 'National Institute of Standards\nand Technology (NIST)'],
  ['Unidad', 'Computer Security Division\nInformation Technology Laboratory'],
  ['Publicación', 'Special Publication 800-86, año 2006'],
  ['Estado', 'Vigente — sigue siendo referencia\ninternacional en forense digital'],
];
let oy = 1.86;
org.forEach((o) => {
  s.addText(o[0].toUpperCase(), { x: 0.75, y: oy, w: 3.9, h: 0.2, fontSize: 8, bold: true, color: C.muted, fontFace: F, charSpacing: 1, margin: 0 });
  s.addText(o[1], { x: 0.75, y: oy + 0.21, w: 3.9, h: 0.5, fontSize: 11, color: C.text, fontFace: F, margin: 0, valign: 'top', lineSpacingMultiple: 1.18 });
  oy += 0.79;
});
card(s, 5.05, 1.35, 4.45, 3.62, C.panel);
s.addText('AUTORES DEL DOCUMENTO', { x: 5.3, y: 1.52, w: 3.9, h: 0.24, fontSize: 8.5, bold: true, color: C.accent, fontFace: F, charSpacing: 1.3, margin: 0 });
const authors = ['Karen Kent', 'Suzanne Chevalier', 'Tim Grance', 'Hung Dang'];
authors.forEach((a, i) => {
  const y = 1.9 + i * 0.6;
  card(s, 5.3, y, 3.95, 0.5, C.panel2);
  s.addText(String(i + 1).padStart(2, '0'), {
    x: 5.42, y, w: 0.42, h: 0.5, fontSize: 11, bold: true, color: C.accent,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(a, { x: 5.9, y, w: 3.2, h: 0.5, fontSize: 12.5, bold: true, color: C.white, fontFace: F, valign: 'middle', margin: 0 });
});
s.addText('Documento de descarga libre y gratuita:\ncsrc.nist.gov  →  Publications  →  SP 800-86', {
  x: 5.3, y: 4.34, w: 3.95, h: 0.5, fontSize: 9.5, color: C.accent, fontFace: F,
  valign: 'top', margin: 0, lineSpacingMultiple: 1.2,
});
s.addNotes('Los cuatro autores son investigadores de la división de seguridad informática del NIST. Vale la pena resaltar que el documento se puede descargar gratis, a diferencia de la ISO 27037 que es de pago: ese detalle pesa mucho en el ámbito académico.');
footer(s, 'Autoría');
}

// ── 6. ALCANCE ─────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Ámbito de aplicación', 'Alcance de la guía');
const aud = [
  ['alert', C.p1, 'Equipos de respuesta a incidentes', 'Personal que atiende un incidente y necesita recolectar y preservar evidencia sin destruirla durante la contención.'],
  ['search', C.p2, 'Investigadores forenses digitales', 'Peritos que analizan discos, memoria, tráfico de red y aplicaciones para sustentar una investigación.'],
  ['server', C.p3, 'Administradores de sistemas y redes', 'Técnicos que operan la infraestructura y deben conservar registros y evidencia ante un evento de seguridad.'],
  ['case', C.p4, 'Organizaciones públicas y privadas', 'Instituciones que necesitan políticas y procedimientos forenses propios antes de que ocurra el incidente.'],
];
aud.forEach((a, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.5 + col * 4.6, y = 1.32 + row * 1.64;
  card(s, x, y, 4.4, 1.5, C.panel);
  iconCircle(s, a[0], x + 0.2, y + 0.2, 0.48, C.panel2);
  s.addText(a[2], {
    x: x + 0.8, y: y + 0.18, w: 3.42, h: 0.5, fontSize: 12, bold: true, color: C.white,
    fontFace: F, valign: 'middle', margin: 0, lineSpacingMultiple: 1.05,
  });
  s.addText(a[3], {
    x: x + 0.2, y: y + 0.76, w: 4, h: 0.65, fontSize: 9.8, color: C.text,
    fontFace: F, valign: 'top', margin: 0, lineSpacingMultiple: 1.2,
  });
});
card(s, 0.5, 4.6, 9, 0.55, C.panel2);
s.addText('Lo que la guía NO pretende ser:  no es asesoría legal, no reemplaza la normativa de cada país y no es un manual de una herramienta específica.', {
  x: 0.75, y: 4.6, w: 8.5, h: 0.55, fontSize: 10, color: C.amber, fontFace: F,
  valign: 'middle', margin: 0,
});
s.addNotes('El alcance es amplio pero tiene límites explícitos. Insistir en el recuadro inferior: NIST aclara que su guía no sustituye el criterio legal de cada jurisdicción, algo clave en Bolivia donde la admisibilidad depende del Código de Procedimiento Penal.');
footer(s, 'Alcance');
}

// ── 7. PANORAMA DE LAS SEIS GUÍAS ──────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Marco comparativo', 'Las seis guías del área forense');
const COLS = [
  { x: 0.5,  w: 1.72, key: 'Guía' },
  { x: 2.3,  w: 1.72, key: 'Origen' },
  { x: 4.1,  w: 4.5,  key: 'Enfoque principal' },
  { x: 8.68, w: 0.82, key: 'Año' },
];
COLS.forEach((c, i) => {
  s.addText(c.key.toUpperCase(), {
    x: c.x + (i === 3 ? 0 : 0.14), y: 1.3, w: c.w - 0.14, h: 0.28, fontSize: 8.5, bold: true,
    color: C.muted, fontFace: F, charSpacing: 1.1, margin: 0, valign: 'middle',
    align: i === 3 ? 'center' : 'left',
  });
});
const data = [
  ['RFC 3227', 'IETF', 'Recolección y archivo; orden de volatilidad', '2002'],
  ['SWGDE', 'Estados Unidos', 'Buenas prácticas y calidad en laboratorios forenses', '1998'],
  ['ACPO', 'Reino Unido', 'Cuatro principios para el ámbito policial', '2012'],
  ['CP4DF', 'Académico', 'Proceso común entre respuesta a incidentes y pericia', '2007'],
  ['NIST SP 800-86', 'NIST — EE. UU.', 'Cuatro fases integradas a la respuesta a incidentes', '2006'],
  ['ISO/IEC 27037', 'Internacional', 'Identificación, recolección, adquisición, preservación', '2012'],
];
data.forEach((r, i) => {
  const y = 1.64 + i * 0.48;
  const sel = r[0].startsWith('NIST');
  card(s, 0.5, y, 9, 0.42, sel ? '17394A' : C.panel, sel ? C.accent : undefined);
  s.addText(r[0], {
    x: COLS[0].x + 0.14, y, w: COLS[0].w - 0.14, h: 0.42, fontSize: 10.5, bold: true,
    color: sel ? C.accent : C.white, fontFace: F, valign: 'middle', margin: 0,
  });
  s.addText(r[1], {
    x: COLS[1].x, y, w: COLS[1].w, h: 0.42, fontSize: 9.8,
    color: C.muted, fontFace: F, valign: 'middle', margin: 0,
  });
  s.addText(r[2], {
    x: COLS[2].x, y, w: COLS[2].w, h: 0.42, fontSize: 9.8,
    color: C.text, fontFace: F, valign: 'middle', margin: 0,
  });
  s.addText(r[3], {
    x: COLS[3].x, y, w: COLS[3].w - 0.14, h: 0.42, fontSize: 9.8, bold: sel,
    color: sel ? C.accent : C.muted, fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
});
card(s, 0.5, 4.58, 9, 0.5, C.panel2);
s.addText('Se eligió el SP 800-86: define fases claras y verificables, es gratuita y permite demostrar un caso completo.', {
  x: 0.75, y: 4.58, w: 8.5, h: 0.5, fontSize: 9.8, color: C.accent, fontFace: F,
  valign: 'middle', margin: 0,
});
s.addNotes('Esta tabla justifica la elección del tema. Señalar que las guías no compiten entre sí: RFC 3227 aporta el orden de volatilidad, ISO 27037 la preservación y ACPO los principios; NIST es la que articula todo en un proceso operativo.');
footer(s, 'Comparativa');
}

// ── 8. PROCESO — VISIÓN GENERAL ────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Núcleo de la guía', 'El proceso forense en cuatro fases');
PHASES.forEach((p, i) => {
  const x = 0.5 + i * 2.3;
  card(s, x, 1.32, 2.1, 2.62, C.panel, p.col);
  iconCircle(s, p.ic, x + 0.78, 1.5, 0.54, p.col);
  s.addText(p.n, {
    x: x + 0.1, y: 2.12, w: 1.9, h: 0.24, fontSize: 9.5, bold: true, color: p.col,
    fontFace: F, align: 'center', margin: 0,
  });
  s.addText(p.es, {
    x: x + 0.1, y: 2.34, w: 1.9, h: 0.3, fontSize: 14, bold: true, color: C.white,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(p.en, {
    x: x + 0.1, y: 2.62, w: 1.9, h: 0.22, fontSize: 9, italic: true, color: C.muted,
    fontFace: F, align: 'center', margin: 0,
  });
  s.addText(p.desc, {
    x: x + 0.15, y: 2.9, w: 1.8, h: 0.95, fontSize: 8.8, color: C.text,
    fontFace: F, align: 'center', valign: 'top', margin: 0, lineSpacingMultiple: 1.18,
  });
  if (i < 3) {
    s.addShape('rightArrow', { x: x + 2.14, y: 2.58, w: 0.12, h: 0.16, fill: { color: C.line } });
  }
});
// Cadena de transformación del dato
s.addText('CADA FASE TRANSFORMA LO QUE RECIBE', {
  x: 0.5, y: 4.05, w: 5, h: 0.24, fontSize: 8.5, bold: true, color: C.muted,
  fontFace: F, charSpacing: 1.3, margin: 0,
});
const chain = ['MEDIOS', 'DATOS', 'INFORMACIÓN', 'EVIDENCIA', 'INFORME'];
chain.forEach((t, i) => {
  const x = 0.5 + i * 1.87;
  const last = i === chain.length - 1;
  s.addShape('roundRect', {
    x, y: 4.36, w: 1.54, h: 0.46, fill: { color: last ? '17394A' : C.panel },
    rectRadius: 0.22, line: last ? { color: C.accent, width: 1 } : undefined,
  });
  s.addText(t, {
    x, y: 4.36, w: 1.54, h: 0.46, fontSize: 9.5, bold: true,
    color: last ? C.accent : C.text, fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  if (i < chain.length - 1) {
    s.addShape('rightArrow', { x: x + 1.62, y: 4.51, w: 0.18, h: 0.16, fill: { color: C.line } });
  }
});
s.addNotes('Esta es la diapositiva central. El aporte propio de NIST es la cadena de abajo: los medios se convierten en datos, los datos en información, la información en evidencia. Si una fase se salta, la siguiente trabaja con material que no puede sostener.');
footer(s, 'Proceso');
}

// ── 9-12. FASES EN DETALLE ─────────────────────────────────────────────────
const detail = [
  {
    p: PHASES[0],
    sub: 'Identificar, adquirir y preservar los datos sin alterar la fuente original',
    blocks: [
      ['Identificación de las fuentes', 'Medios físicos (discos duros, SSD, USB, celulares), memoria RAM volátil, registros del sistema operativo, tráfico de red y datos de aplicaciones. Se prioriza según el orden de volatilidad: lo que se pierde primero se captura primero.'],
      ['Adquisición forense', 'Copia bit a bit del medio mediante bloqueador de escritura. Nunca se trabaja sobre el original. Cada imagen se sella con función hash (MD5 y SHA-256) para poder demostrar después que nada cambió.'],
      ['Cadena de custodia', 'Registro formal e ininterrumpido de quién tuvo la evidencia, cuándo, para qué y bajo qué condiciones de resguardo. Un vacío en este registro puede invalidar toda la investigación ante un tribunal.'],
    ],
    tools: ['dd / dcfldd', 'FTK Imager', 'Bloqueador de escritura', 'Volatility (RAM)'],
    out: 'Imagen forense verificada por hash y formulario de cadena de custodia firmado.',
  },
  {
    p: PHASES[1],
    sub: 'Hacer visible y manejable el volumen de datos recolectado',
    blocks: [
      ['Reducción del volumen', 'Se descartan los archivos conocidos del sistema comparando sus hashes contra listas de referencia (NSRL). De millones de archivos se pasa a un conjunto manejable de candidatos relevantes.'],
      ['Recuperación de datos', 'Extracción de archivos borrados, particiones ocultas, espacio no asignado y slack space. También se descomprime, se descifra cuando se cuenta con la clave y se recuperan archivos por firma (carving).'],
      ['Filtrado y clasificación', 'Búsqueda por palabras clave, tipo de archivo, rango de fechas, usuario propietario o extensión falsificada. El resultado se organiza para que el analista pueda interpretarlo en la fase siguiente.'],
    ],
    tools: ['Autopsy / Sleuth Kit', 'EnCase', 'bulk_extractor', 'PhotoRec'],
    out: 'Conjunto acotado de datos relevantes, extraídos y clasificados, listos para analizar.',
  },
  {
    p: PHASES[2],
    sub: 'Convertir la información en evidencia que responda las preguntas del caso',
    blocks: [
      ['Línea de tiempo', 'Reconstrucción cronológica de accesos, creaciones, modificaciones y borrados a partir de las marcas temporales del sistema de archivos, los registros de eventos y los artefactos de aplicación.'],
      ['Correlación entre fuentes', 'Se cruzan registros de red, del sistema operativo y de aplicaciones. Un solo indicio rara vez prueba algo; la fuerza del análisis está en que varias fuentes independientes cuenten la misma historia.'],
      ['Identificación de artefactos', 'Malware y mecanismos de persistencia, cuentas comprometidas, conexiones no autorizadas, datos exfiltrados y rastros de técnicas antiforenses como el borrado de registros.'],
    ],
    tools: ['log2timeline / Plaso', 'Volatility', 'NetworkMiner', 'YARA'],
    out: 'Hipótesis confirmada o descartada, con línea de tiempo y artefactos que la respaldan.',
  },
  {
    p: PHASES[3],
    sub: 'Documentar de forma reproducible, comprensible y legalmente admisible',
    blocks: [
      ['Informe técnico', 'Metodología, herramientas y versiones utilizadas, comandos ejecutados, hashes y hallazgos. Debe permitir que otro perito repita el procedimiento y llegue al mismo resultado.'],
      ['Informe ejecutivo', 'Resumen sin lenguaje técnico dirigido a la gerencia: qué pasó, cuándo empezó, qué se vio afectado, cuál fue la causa raíz y qué se recomienda hacer. Es la parte que se lee en la toma de decisiones.'],
      ['Soporte legal', 'Cadena de custodia completa, bitácora de cada acción realizada y anexos con los hashes de la evidencia. Es lo que sostiene la admisibilidad del material ante la autoridad competente.'],
    ],
    tools: ['Autopsy Reports', 'CaseNotes', 'Plantillas de custodia', 'PDF firmado'],
    out: 'Informe técnico, informe ejecutivo, cadena de custodia y recomendaciones de remediación.',
  },
];

detail.forEach((d) => {
  const s = pres.addSlide();
  bg(s);
  // Encabezado con badge de fase
  s.addShape('ellipse', { x: 0.5, y: 0.42, w: 0.5, h: 0.5, fill: { color: d.p.col } });
  s.addText(d.p.n, {
    x: 0.5, y: 0.42, w: 0.5, h: 0.5, fontSize: 15, bold: true, color: C.white,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText('FASE ' + d.p.n + '  ·  ' + d.p.en.toUpperCase(), {
    x: 1.12, y: 0.38, w: 8.3, h: 0.24, fontSize: 9, bold: true, color: d.p.col,
    fontFace: F, charSpacing: 1.5, margin: 0, valign: 'middle',
  });
  s.addText(d.p.es, {
    x: 1.12, y: 0.62, w: 8.3, h: 0.36, fontSize: 25, bold: true, color: C.white,
    fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(d.sub, {
    x: 1.12, y: 1.0, w: 8.3, h: 0.24, fontSize: 10.5, italic: true, color: C.muted,
    fontFace: F, margin: 0, valign: 'middle',
  });
  // Bloques de contenido
  d.blocks.forEach((b, i) => {
    const y = 1.4 + i * 1.24;
    card(s, 0.5, y, 6.35, 1.14, C.panel);
    s.addShape('ellipse', { x: 0.72, y: y + 0.19, w: 0.26, h: 0.26, fill: { color: d.p.col } });
    s.addText(b[0], {
      x: 1.1, y: y + 0.14, w: 5.5, h: 0.32, fontSize: 12, bold: true, color: C.white,
      fontFace: F, margin: 0, valign: 'middle',
    });
    s.addText(b[1], {
      x: 0.72, y: y + 0.47, w: 5.92, h: 0.6, fontSize: 9.3, color: C.text,
      fontFace: F, margin: 0, valign: 'top', lineSpacingMultiple: 1.16,
    });
  });
  // Panel lateral
  card(s, 7.0, 1.4, 2.5, 3.62, C.panel);
  s.addText('HERRAMIENTAS TÍPICAS', {
    x: 7.18, y: 1.54, w: 2.2, h: 0.22, fontSize: 8, bold: true, color: d.p.col,
    fontFace: F, charSpacing: 1, margin: 0,
  });
  d.tools.forEach((t, i) => {
    const y = 1.84 + i * 0.46;
    card(s, 7.18, y, 2.14, 0.38, C.panel2);
    s.addText(t, {
      x: 7.18, y, w: 2.14, h: 0.38, fontSize: 9, bold: true, color: C.text,
      fontFace: F, align: 'center', valign: 'middle', margin: 0,
    });
  });
  s.addText('RESULTADO DE LA FASE', {
    x: 7.18, y: 3.78, w: 2.2, h: 0.22, fontSize: 8, bold: true, color: d.p.col,
    fontFace: F, charSpacing: 1, margin: 0,
  });
  s.addText(d.out, {
    x: 7.18, y: 4.04, w: 2.14, h: 0.88, fontSize: 9.2, color: C.text,
    fontFace: F, margin: 0, valign: 'top', lineSpacingMultiple: 1.2,
  });
  s.addNotes('Fase ' + d.p.n + ' — ' + d.p.es + '. ' + d.sub + '. Explicar los tres bloques y cerrar señalando el resultado concreto que esta fase entrega a la siguiente.');
  footer(s, 'Fase ' + d.p.n + ' · ' + d.p.es);
});

// ── 13. CASO PRÁCTICO ──────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Aplicación del proceso', 'Ejemplo: incidente de ransomware', C.amber);
card(s, 0.5, 1.3, 9, 0.66, C.panel, C.amber);
iconCircle(s, 'alert', 0.68, 1.44, 0.38, C.panel2);
s.addText('CASO HIPOTÉTICO:  una empresa amanece con sus archivos cifrados y una nota de rescate. Se sospecha de un ransomware ingresado por correo electrónico en un equipo de administración.', {
  x: 1.2, y: 1.3, w: 8.15, h: 0.66, fontSize: 10.5, color: C.amber, fontFace: F,
  valign: 'middle', margin: 0,
});
const steps = [
  [PHASES[0], ['Aislar el equipo de la red', 'Volcado de memoria RAM', 'Imagen bit a bit del disco', 'Hash SHA-256 y acta de custodia']],
  [PHASES[1], ['Montar la imagen en solo lectura', 'Descartar archivos del sistema', 'Recuperar el adjunto borrado', 'Listar ejecutables recientes']],
  [PHASES[2], ['Timeline del ataque completa', 'Vector: macro en un adjunto', 'Movimiento lateral por SMB', 'Exfiltración previa al cifrado']],
  [PHASES[3], ['Informe técnico reproducible', 'Informe ejecutivo del impacto', 'Anexo legal con los hashes', 'Plan de remediación']],
];
steps.forEach(([p, list], i) => {
  const x = 0.5 + i * 2.3;
  card(s, x, 2.12, 2.1, 2.9, C.panel, p.col);
  s.addShape('roundRect', { x, y: 2.12, w: 2.1, h: 0.46, fill: { color: p.col }, rectRadius: 0.08 });
  s.addShape('rect', { x, y: 2.4, w: 2.1, h: 0.18, fill: { color: p.col } });
  s.addText(p.n + '  ' + p.es, {
    x, y: 2.12, w: 2.1, h: 0.46, fontSize: 11, bold: true, color: C.white,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  list.forEach((t, j) => {
    const y = 2.7 + j * 0.57;
    s.addShape('ellipse', { x: x + 0.16, y: y + 0.19, w: 0.13, h: 0.13, fill: { color: p.col } });
    s.addText(t, {
      x: x + 0.38, y, w: 1.62, h: 0.52, fontSize: 8.8, color: C.text,
      fontFace: F, valign: 'middle', margin: 0, lineSpacingMultiple: 1.14,
    });
  });
});
s.addNotes('El caso es hipotético pero realista. Lo importante es que cada columna corresponde exactamente a una fase de la guía: se ve que el proceso no es teoría, sino la secuencia de acciones que uno realmente ejecuta.');
footer(s, 'Ejemplo aplicado');
}

// ── 14. RESULTADO DEL ANÁLISIS ─────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Resultado de la fase 03', 'Línea de tiempo reconstruida', C.p3);
const heads = [['HORA', 0.5, 0.95, 'center'], ['EVENTO RECONSTRUIDO', 1.6, 4.2, 'left'], ['ARTEFACTO QUE LO PRUEBA', 5.95, 3.55, 'left']];
heads.forEach((h) => {
  s.addText(h[0], {
    x: h[1], y: 1.3, w: h[2], h: 0.28, fontSize: 8.5, bold: true, color: C.muted,
    fontFace: F, charSpacing: 1.1, align: h[3], valign: 'middle', margin: 0,
  });
});
const ev = [
  ['09:14', 'Llega un correo con el adjunto Factura_0725.xlsm', 'Registros del servidor de correo'],
  ['09:22', 'El usuario abre el archivo y habilita las macros', 'Claves TrustRecords del registro'],
  ['09:23', 'Se descarga el ejecutable desde una IP externa', 'Captura de red y registros del proxy'],
  ['09:25', 'Se instala persistencia y una tarea programada', 'Clave Run del registro, carpeta Tasks'],
  ['10:05', 'Movimiento lateral hacia dos servidores por SMB', 'Eventos 4624 y 4672 de Windows'],
  ['11:40', 'Exfiltración de datos hacia un servicio externo', 'NetFlow y registros del cortafuegos'],
  ['12:10', 'Cifrado masivo y creación de la nota de rescate', 'Marcas temporales de la MFT'],
];
ev.forEach((r, i) => {
  const y = 1.63 + i * 0.43;
  card(s, 0.5, y, 9, 0.38, i % 2 ? C.panel : '16283F');
  s.addText(r[0], {
    x: 0.5, y, w: 0.95, h: 0.38, fontSize: 10, bold: true, color: C.p3,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addShape('rect', { x: 1.5, y: y + 0.09, w: 0.02, h: 0.2, fill: { color: C.line } });
  s.addText(r[1], {
    x: 1.6, y, w: 4.2, h: 0.38, fontSize: 9.6, color: C.white,
    fontFace: F, valign: 'middle', margin: 0,
  });
  s.addText(r[2], {
    x: 5.95, y, w: 3.4, h: 0.38, fontSize: 9.6, color: C.muted,
    fontFace: F, valign: 'middle', margin: 0,
  });
});
s.addText('La fuerza probatoria nace de que fuentes independientes —correo, sistema y red— coinciden en la misma secuencia.', {
  x: 0.5, y: 4.72, w: 9, h: 0.42, fontSize: 9.8, color: C.p3, fontFace: F,
  valign: 'middle', margin: 0,
});
s.addNotes('Esta tabla es el entregable estrella del análisis. Recalcar la tercera columna: sin un artefacto que la respalde, una línea de tiempo es una suposición, no evidencia.');
footer(s, 'Línea de tiempo');
}

// ── 15. RECOMENDACIONES ────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Buenas prácticas', 'Recomendaciones');
const recs = [
  ['shield', 'Preparar la capacidad antes', 'NIST insiste en tener políticas, roles y herramientas definidas antes del incidente, no improvisadas durante él.'],
  ['lock', 'No tocar el original', 'Trabajar siempre sobre copias forenses verificadas y usar bloqueador de escritura en la adquisición.'],
  ['hash', 'Verificar la integridad', 'Calcular y comparar hashes al inicio y al final de cada fase. Un hash distinto rompe la cadena de evidencia.'],
  ['edit', 'Documentar cada acción', 'Quién, cuándo, con qué herramienta y con qué parámetros. Lo que no está documentado, no ocurrió.'],
  ['tool', 'Usar herramientas validadas', 'Emplear software forense reconocido y registrar la versión exacta utilizada en el informe.'],
  ['users', 'Capacitar y coordinar', 'Formación continua del equipo y participación del área legal desde el primer minuto del incidente.'],
];
recs.forEach((r, i) => {
  const col = i % 3, row = Math.floor(i / 3);
  const x = 0.5 + col * 3.06, y = 1.35 + row * 1.9;
  card(s, x, y, 2.88, 1.76, C.panel);
  iconCircle(s, r[0], x + 0.2, y + 0.2, 0.46, C.panel2);
  s.addText(r[1], {
    x: x + 0.2, y: y + 0.74, w: 2.5, h: 0.28, fontSize: 11.5, bold: true, color: C.white,
    fontFace: F, margin: 0, valign: 'middle',
  });
  s.addText(r[2], {
    x: x + 0.2, y: y + 1.04, w: 2.5, h: 0.62, fontSize: 9.3, color: C.text,
    fontFace: F, margin: 0, valign: 'top', lineSpacingMultiple: 1.18,
  });
});
s.addNotes('Las tres primeras recomendaciones vienen directamente de la guía; las tres últimas son la lectura práctica del equipo. La más olvidada en la realidad es la primera: casi nadie prepara la capacidad forense antes del incidente.');
footer(s, 'Recomendaciones');
}

// ── 16. CONCLUSIONES ───────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
header(s, 'Cierre del análisis', 'Conclusiones');
const cons = [
  'El SP 800-86 convierte la informática forense en un proceso repetible y auditable de cuatro fases, en lugar de un conjunto de técnicas sueltas.',
  'Su aporte distintivo es integrar la forense dentro de la respuesta a incidentes: la evidencia se preserva mientras se contiene el ataque, no después.',
  'La cadena Medios → Datos → Información → Evidencia hace explícito el valor que agrega cada etapa y evita saltarse pasos por urgencia.',
  'Es complementaria y no excluyente: se apoya en el orden de volatilidad del RFC 3227 y en los criterios de preservación de la ISO/IEC 27037.',
];
cons.forEach((t, i) => {
  const y = 1.35 + i * 0.78;
  card(s, 0.5, y, 9, 0.68, C.panel);
  s.addShape('ellipse', { x: 0.7, y: y + 0.17, w: 0.34, h: 0.34, fill: { color: C.panel2 } });
  s.addText(String(i + 1).padStart(2, '0'), {
    x: 0.7, y: y + 0.17, w: 0.34, h: 0.34, fontSize: 9.5, bold: true, color: C.accent,
    fontFace: F, align: 'center', valign: 'middle', margin: 0,
  });
  s.addText(t, {
    x: 1.18, y, w: 8.1, h: 0.68, fontSize: 10.8, color: C.text, fontFace: F,
    valign: 'middle', margin: 0, lineSpacingMultiple: 1.14,
  });
});
card(s, 0.5, 4.52, 9, 0.62, '17394A', C.accent);
s.addText('Por su claridad, su gratuidad y su aplicabilidad inmediata, el SP 800-86 es la guía más didáctica de las seis para introducirse a la informática forense.', {
  x: 0.75, y: 4.52, w: 8.5, h: 0.62, fontSize: 11, bold: true, color: C.accent,
  fontFace: F, valign: 'middle', margin: 0,
});
s.addNotes('Cerrar con la idea del recuadro: no se afirma que NIST sea superior a las demás guías, sino que es la puerta de entrada más clara y la más fácil de aplicar con recursos limitados.');
footer(s, 'Conclusiones');
}

// ── 17. CIERRE ─────────────────────────────────────────────────────────────
{
const s = pres.addSlide();
bg(s);
s.addText('800-86', {
  x: 2.55, y: 3.05, w: 6.95, h: 2.4, fontSize: 148, bold: true, color: C.ghost,
  fontFace: F, align: 'right', valign: 'middle', margin: 0,
});
s.addText('Gracias por su atención', {
  x: 0.5, y: 1.1, w: 6.5, h: 0.7, fontSize: 36, bold: true, color: C.white,
  fontFace: F, valign: 'middle', margin: 0,
});
s.addText('Espacio para preguntas y comentarios', {
  x: 0.5, y: 1.85, w: 6.5, h: 0.32, fontSize: 13, color: C.accent, fontFace: F, margin: 0,
});
s.addText('REFERENCIAS', {
  x: 0.5, y: 2.6, w: 4, h: 0.24, fontSize: 8.5, bold: true, color: C.muted,
  fontFace: F, charSpacing: 1.3, margin: 0,
});
const refs = [
  'Kent, K., Chevalier, S., Grance, T. y Dang, H. (2006). Guide to Integrating Forensic Techniques into Incident Response (NIST SP 800-86). Gaithersburg: NIST.',
  'Brezinski, D. y Killalea, T. (2002). Guidelines for Evidence Collection and Archiving (RFC 3227). IETF.',
  'ISO/IEC (2012). ISO/IEC 27037: Guidelines for identification, collection, acquisition and preservation of digital evidence.',
  'ACPO (2012). Good Practice Guide for Digital Evidence, versión 5. Reino Unido.',
];
refs.forEach((r, i) => {
  const y = 2.9 + i * 0.44;
  s.addShape('ellipse', { x: 0.53, y: y + 0.11, w: 0.1, h: 0.1, fill: { color: C.line } });
  s.addText(r, {
    x: 0.78, y, w: 8.7, h: 0.4, fontSize: 9.2, color: C.muted, fontFace: F,
    valign: 'middle', margin: 0, lineSpacingMultiple: 1.14,
  });
});
s.addText('Materia: Informática Forense  ·  Escuela Militar de Ingeniería  ·  Cochabamba, 2026', {
  x: 0.5, y: 4.86, w: 9, h: 0.3, fontSize: 9.5, color: C.text, fontFace: F, margin: 0, valign: 'middle',
});
s.addNotes('Agradecer y abrir preguntas. Tener a mano el dato de que el documento se descarga gratis desde csrc.nist.gov por si alguien lo pide.');
footer(s, 'Cierre');
}

await pres.writeFile({ fileName: 'NIST_SP_800-86_Presentacion.pptx' });
console.log('OK — NIST_SP_800-86_Presentacion.pptx (' + pageNo + ' diapositivas)');
}

build().catch((e) => { console.error(e); process.exit(1); });

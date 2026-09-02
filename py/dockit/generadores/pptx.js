#!/usr/bin/env node
/* Generador PPTX nativo a partir del contrato JSON que entrega el adaptador Python.
 *
 * Regla central: las imágenes ilustran; PowerPoint conserva títulos, rótulos,
 * cifras, citas y fuentes como texto/gráficos nativos editables.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
// Los tipos de forma van como literal: pptxgen.ShapeType es estático
// y en pptxgenjs 4 no existe (solo en la instancia).

const W = 13.333;
const H = 7.5;

function fail(message) {
  process.stderr.write(`pptx: ${message}\n`);
  process.exit(2);
}

function cleanColor(value, fallback) {
  const color = String(value || '').replace(/^#/, '').toUpperCase();
  return /^[0-9A-F]{6}$/.test(color) ? color : fallback;
}

function palette(format) {
  const custom = Array.isArray(format.paleta) ? format.paleta : [];
  return {
    ink: cleanColor(custom[0], '182126'),
    primary: cleanColor(custom[1], '0B6B61'),
    accent: cleanColor(custom[2], 'F3B33D'),
    soft: cleanColor(custom[3], 'DCEDE9'),
    paper: 'FFFFFF',
    muted: '5B6970',
    pale: 'F5F8F8',
  };
}

// Las diapositivas se proyectan: por debajo de 24 pt la última fila no lee.
// La escala se fija una vez en generate() y la usan todas las láminas, para no
// tener que pasar el formato por cada firma.
let ESCALA_TEXTO = 1;
let TITULO_TRABAJO = '';

function bodySize(base) {
  return Math.max(20, Math.round(base * ESCALA_TEXTO));
}

function safeFont(format) {
  const requested = String(format.tipografia || '').trim();
  const safe = new Set(['Arial', 'Calibri', 'Cambria', 'Times New Roman', 'Courier New', 'Bookman Old Style', 'Century Schoolbook']);
  return safe.has(requested) ? requested : 'Arial';
}

function textWithCitations(block, inText) {
  let value = String(block.texto || '');
  const keys = Array.isArray(block.citas) ? block.citas : [];
  if (!keys.length) return value;
  const citations = keys.map((key) => {
    if (!Object.prototype.hasOwnProperty.call(inText, key)) {
      throw new Error(`la cita «${key}» no fue verificada`);
    }
    return inText[key];
  }).join(' ');
  value = value.trimEnd();
  const punctuation = /[.!?]$/.test(value);
  if (punctuation) value = value.slice(0, -1).trimEnd();
  return `${value} ${citations}${punctuation ? '.' : ''}`;
}

function sentenceChunks(text, limit = 190) {
  const clean = String(text || '').replace(/\s+/g, ' ').trim();
  if (!clean) return [];
  if (clean.length <= limit) return [clean];
  const sentences = clean.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [clean];
  const chunks = [];
  let current = '';
  for (const sentence of sentences) {
    const part = sentence.trim();
    if (!current && part.length > limit) {
      const words = part.split(/\s+/);
      let line = '';
      for (const word of words) {
        if (line && `${line} ${word}`.length > limit) {
          chunks.push(line);
          line = word;
        } else {
          line = line ? `${line} ${word}` : word;
        }
      }
      if (line) current = line;
    } else if (current && `${current} ${part}`.length > limit) {
      chunks.push(current);
      current = part;
    } else {
      current = current ? `${current} ${part}` : part;
    }
  }
  if (current) chunks.push(current);
  return chunks;
}

// Pie con el título: quien entra a media exposición sabe de qué va.
function addPie(slide, titulo, font, colors) {
  if (!titulo) return;
  slide.addText(String(titulo), {
    x: 0.8, y: H - 0.52, w: W - 2.4, h: 0.3,
    fontFace: font, fontSize: 10, color: colors.muted, margin: 0,
  });
}

function addSlideNumber(slide, number, font, colors) {
  slide.addText(String(number).padStart(2, '0'), {
    x: 12.28, y: 7.02, w: 0.48, h: 0.2,
    fontFace: font, fontSize: 9, color: colors.muted,
    align: 'right', margin: 0, breakLine: false,
  });
}

function addTitle(slide, title, font, colors, continuation = false) {
  const label = continuation ? `${title} · continuación` : title;
  slide.addText(label, {
    x: 0.68, y: 0.5, w: 11.8, h: 0.76,
    fontFace: font, fontSize: bodySize(continuation ? 34 : 40),
    bold: true, color: colors.ink, margin: 0,
    valign: 'mid', breakLine: false, fit: 'shrink',
  });
}

function addMotif(slide, colors, variant = 0) {
  // Motivo funcional: relaciones/nodos que refuerzan la estructura, nunca
  // una barra decorativa ni una línea bajo el título.
  const positions = variant % 2 === 0
    ? [[10.85, 5.05, 0.7], [11.65, 4.35, 0.42], [12.15, 5.6, 0.34]]
    : [[0.6, 5.7, 0.48], [1.25, 5.15, 0.3], [1.68, 5.85, 0.38]];
  for (let i = 0; i < positions.length; i += 1) {
    const [x, y, r] = positions[i];
    slide.addShape('ellipse', {
      x, y, w: r, h: r,
      fill: { color: i === 0 ? colors.primary : colors.soft, transparency: i === 0 ? 4 : 12 },
      line: { color: i === 0 ? colors.primary : colors.muted, transparency: 35, width: 1.2 },
    });
  }
}

function addNotes(slide, title, fullText) {
  const notes = [title, ...fullText].filter(Boolean).join('\n\n');
  slide.addNotes(notes || title);
}

function addCover(pptx, input, colors, font) {
  const slide = pptx.addSlide();
  const p = input.guion.portada || {};
  slide.background = { color: colors.ink };
  slide.addShape('ellipse', {
    x: 8.9, y: -1.15, w: 5.5, h: 5.5,
    fill: { color: colors.primary, transparency: 8 },
    line: { color: colors.primary, transparency: 100 },
  });
  slide.addShape('ellipse', {
    x: 10.3, y: 3.9, w: 2.6, h: 2.6,
    fill: { color: colors.accent, transparency: 5 },
    line: { color: colors.accent, transparency: 100 },
  });

  // Datos académicos arriba: quien entra a la sala sabe de qué defensa es
  const encabezado = [p.institucion, p.carrera].filter(Boolean).join('  ·  ');
  if (encabezado) {
    slide.addText(encabezado.toUpperCase(), {
      x: 0.88, y: 0.62, w: 8.5, h: 0.32,
      fontFace: font, fontSize: 12, bold: true,
      color: colors.accent, margin: 0, charSpacing: 1.4,
    });
  }

  slide.addText(input.guion.titulo, {
    x: 0.88, y: encabezado ? 1.5 : 1.35, w: 8.5, h: 2.1,
    fontFace: font, fontSize: 40, bold: true,
    color: colors.paper, margin: 0, valign: 'mid', fit: 'shrink',
  });

  if (p.materia) {
    slide.addText(p.materia, {
      x: 0.9, y: 3.72, w: 8.0, h: 0.4,
      fontFace: font, fontSize: 17, italic: true,
      color: colors.soft, margin: 0,
    });
  }

  // Bloque de créditos, con la etiqueta en pequeño sobre cada dato
  const creditos = [
    ['Presentado por', p.autor || input.guion.autor],
    ['Docente', p.docente],
  ].filter(([, v]) => v);
  creditos.forEach(([etiqueta, valor], i) => {
    const y = 4.5 + i * 0.78;
    slide.addText(etiqueta.toUpperCase(), {
      // sobre el fondo oscuro de la portada, `muted` no se lee
      x: 0.92, y, w: 4.0, h: 0.24, fontFace: font, fontSize: 10,
      color: colors.accent, margin: 0, charSpacing: 1.2,
    });
    slide.addText(String(valor), {
      x: 0.92, y: y + 0.26, w: 5.4, h: 0.4,
      fontFace: font, fontSize: 16, color: colors.paper, margin: 0,
    });
  });

  const pie = [p.lugar, p.fecha].filter(Boolean).join('  ·  ');
  if (pie) {
    slide.addText(pie, {
      x: 0.92, y: 6.5, w: 7.0, h: 0.3,
      fontFace: font, fontSize: 12, color: colors.soft, margin: 0,
    });
  }
  addNotes(slide, input.guion.titulo, [p.institucion || '', p.autor || '']);
  return slide;
}

// Agenda: el público necesita la estructura antes de que empiece el fondo.
function addAgenda(pptx, secciones, colors, font, number) {
  if (secciones.length < 2) return number;
  const slide = pptx.addSlide();
  slide.background = { color: colors.paper };
  addTitle(slide, 'Contenido', font, colors, false);
  const columnas = secciones.length > 6 ? 2 : 1;
  const porColumna = Math.ceil(secciones.length / columnas);
  secciones.forEach((titulo, i) => {
    const col = Math.floor(i / porColumna);
    const fila = i % porColumna;
    const x = 0.95 + col * 6.3;
    const y = 1.7 + fila * 0.74;
    slide.addText(String(i + 1).padStart(2, '0'), {
      x, y, w: 0.7, h: 0.5, fontFace: font, fontSize: bodySize(22),
      bold: true, color: colors.accent, margin: 0,
    });
    slide.addText(titulo, {
      x: x + 0.75, y, w: (columnas === 1 ? 10.6 : 5.2), h: 0.5,
      fontFace: font, fontSize: bodySize(22), color: colors.ink,
      margin: 0, fit: 'shrink',
    });
  });
  addSlideNumber(slide, number, font, colors);
  addNotes(slide, 'Contenido', secciones);
  return number + 1;
}

// Separador entre partes: marca el cambio de tema y da respiro al público.
function addSeparador(pptx, titulo, indice, colors, font) {
  const slide = pptx.addSlide();
  slide.background = { color: colors.ink };
  slide.addShape('ellipse', {
    x: 9.6, y: 1.4, w: 4.2, h: 4.2,
    fill: { color: colors.primary, transparency: 12 },
    line: { color: colors.primary, transparency: 100 },
  });
  slide.addText(String(indice).padStart(2, '0'), {
    x: 1.0, y: 2.1, w: 2.0, h: 1.0, fontFace: font, fontSize: 60,
    bold: true, color: colors.accent, margin: 0,
  });
  slide.addText(titulo, {
    x: 1.0, y: 3.25, w: 8.4, h: 1.4, fontFace: font, fontSize: 36,
    bold: true, color: colors.paper, margin: 0, valign: 'top', fit: 'shrink',
  });
  addNotes(slide, titulo, []);
  return slide;
}

// Cierre: terminar en la lista de referencias deja la exposición colgando.
function addCierre(pptx, input, colors, font) {
  const slide = pptx.addSlide();
  const p = input.guion.portada || {};
  slide.background = { color: colors.ink };
  slide.addShape('ellipse', {
    x: -1.2, y: 3.6, w: 4.6, h: 4.6,
    fill: { color: colors.primary, transparency: 10 },
    line: { color: colors.primary, transparency: 100 },
  });
  slide.addText('Gracias', {
    x: 1.0, y: 2.5, w: 11.0, h: 1.2, fontFace: font, fontSize: 54,
    bold: true, color: colors.paper, margin: 0, align: 'center',
  });
  slide.addText('¿Preguntas?', {
    x: 1.0, y: 3.8, w: 11.0, h: 0.7, fontFace: font, fontSize: 24,
    color: colors.accent, margin: 0, align: 'center',
  });
  const firma = [p.autor || input.guion.autor, p.materia].filter(Boolean).join('  ·  ');
  if (firma) {
    slide.addText(firma, {
      x: 1.0, y: 5.2, w: 11.0, h: 0.4, fontFace: font, fontSize: 14,
      color: colors.soft, margin: 0, align: 'center',
    });
  }
  addNotes(slide, 'Cierre', []);
  return slide;
}

function addContentSlideConFigura(pptx, section, items, colors, font, number,
                                  continuation, variant, figura) {
  const fs = require('fs');
  const slide = pptx.addSlide();
  slide.background = { color: colors.paper };
  addTitle(slide, section, font, colors, continuation);
  // sin motivo decorativo: con el diagrama a la derecha, los círculos de
  // adorno acababan pisando la última viñeta

  const colW = 5.6;
  let y = 1.6;
  for (const item of items.slice(0, 5)) {
    slide.addShape('ellipse', {
      x: 0.8, y: y + 0.16, w: 0.2, h: 0.2,
      fill: { color: colors.primary }, line: { color: colors.primary },
    });
    slide.addText(item.text, {
      x: 1.15, y, w: colW - 0.5, h: 1.0,
      fontFace: font, fontSize: bodySize(24), color: colors.ink,
      margin: 0, valign: 'top', fit: 'shrink',
    });
    y += 1.12;
  }

  if (figura && figura.ruta && fs.existsSync(figura.ruta)) {
    slide.addImage({
      path: figura.ruta,
      x: colW + 0.7, y: 1.45, w: W - colW - 1.4, h: (W - colW - 1.4) * 0.5625,
      sizing: { type: 'contain', w: W - colW - 1.4, h: (W - colW - 1.4) * 0.5625 },
    });
    if (figura.fuente) {
      slide.addText(`Fuente: ${figura.fuente}`, {
        x: colW + 0.9, y: H - 1.25, w: W - colW - 1.7, h: 0.4,
        fontFace: font, fontSize: 13, italic: true,
        color: colors.muted, margin: 0, align: 'right',
      });
    }
  }
  addPie(slide, TITULO_TRABAJO, font, colors);
  addSlideNumber(slide, number, font, colors);
  addNotes(slide, section, items.map((i) => i.full || i.text));
  return slide;
}

function addContentSlide(pptx, section, items, colors, font, number, continuation, variant, figura) {
  if (figura) {
    return addContentSlideConFigura(pptx, section, items, colors, font, number,
                                    continuation, variant, figura);
  }
  const slide = pptx.addSlide();
  slide.background = { color: colors.paper };
  addTitle(slide, section, font, colors, continuation);
  addMotif(slide, colors, variant);

  const useCards = items.length <= 4 && items.every((item) => item.text.length <= 165);
  if (useCards) {
    const columns = items.length === 1 ? 1 : 2;
    const rows = Math.ceil(items.length / columns);
    const cardW = columns === 1 ? 9.9 : 5.5;
    const cardH = rows === 1 ? 3.7 : 2.25;
    const startX = columns === 1 ? 1.0 : 0.72;
    const startY = rows === 1 ? 1.75 : 1.48;
    for (let i = 0; i < items.length; i += 1) {
      const row = Math.floor(i / columns);
      const col = i % columns;
      const x = startX + col * (cardW + 0.42);
      const y = startY + row * (cardH + 0.34);
      slide.addShape('roundRect', {
        x, y, w: cardW, h: cardH, rectRadius: 0.08,
        fill: { color: i === 0 ? colors.soft : colors.pale },
        line: { color: i === 0 ? colors.primary : 'D7DFE0', width: 1.1 },
        shadow: { type: 'outer', color: '8FA3A6', blur: 1.5, angle: 45, distance: 1, opacity: 0.12 },
      });
      slide.addShape('ellipse', {
        x: x + 0.25, y: y + 0.25, w: 0.42, h: 0.42,
        fill: { color: i === 0 ? colors.primary : colors.accent },
        line: { color: i === 0 ? colors.primary : colors.accent },
      });
      slide.addText(String(i + 1), {
        x: x + 0.25, y: y + 0.275, w: 0.42, h: 0.19,
        align: 'center', fontFace: font, fontSize: 10, bold: true,
        color: i === 0 ? colors.paper : colors.ink, margin: 0,
      });
      slide.addText(items[i].text, {
        x: x + 0.82, y: y + 0.25, w: cardW - 1.08, h: cardH - 0.5,
        fontFace: font, fontSize: bodySize(rows <= 3 ? 28 : 24),
        color: colors.ink, margin: 0.04, valign: 'mid', fit: 'shrink',
        breakLine: false,
      });
    }
  } else {
    const left = items.slice(0, Math.ceil(items.length / 2));
    const right = items.slice(left.length);
    [left, right].forEach((column, columnIndex) => {
      let y = 1.55;
      const x = 0.82 + columnIndex * 6.08;
      column.forEach((item, itemIndex) => {
        slide.addShape('ellipse', {
          x, y: y + 0.07, w: 0.22, h: 0.22,
          fill: { color: itemIndex === 0 ? colors.accent : colors.primary },
          line: { color: itemIndex === 0 ? colors.accent : colors.primary },
        });
        slide.addText(item.text, {
          x: x + 0.42, y, w: 5.25, h: 0.93,
          fontFace: font, fontSize: bodySize(24), color: colors.ink,
          margin: 0, valign: 'top', fit: 'shrink',
        });
        y += 1.16;
      });
    });
  }
  addPie(slide, TITULO_TRABAJO, font, colors);
  addSlideNumber(slide, number, font, colors);
  addNotes(slide, section, items.map((item) => item.full || item.text));
  return slide;
}

function addTableSlide(pptx, block, colors, font, number) {
  const slide = pptx.addSlide();
  slide.background = { color: colors.paper };
  const title = block.leyenda || 'Datos';
  addTitle(slide, title, font, colors, false);
  const rows = [];
  if (Array.isArray(block.cabecera) && block.cabecera.length) rows.push(block.cabecera.map(String));
  for (const row of block.filas || []) rows.push(row.map((value) => String(value)));
  const cols = Math.max(1, rows[0] ? rows[0].length : 1);
  const fontSize = bodySize(cols >= 6 ? 14 : cols >= 4 ? 16 : 18);
  slide.addTable(rows, {
    x: 0.68, y: 1.48, w: 11.95, h: 4.9,
    fontFace: font, fontSize, color: colors.ink,
    border: { type: 'solid', color: 'CAD4D6', width: 1 },
    fill: colors.paper, margin: 0.08, valign: 'mid',
    rowH: 0.46,
    bold: false,
    autoFit: false,
    color: colors.ink,
  });
  if (block.fuente) {
    slide.addText(`Fuente: ${block.fuente}`, {
      x: 0.72, y: 6.62, w: 10.8, h: 0.22,
      fontFace: font, fontSize: 9, italic: true, color: colors.muted, margin: 0,
    });
  }
  addSlideNumber(slide, number, font, colors);
  addNotes(slide, title, [`Tabla con ${rows.length - (block.cabecera?.length ? 1 : 0)} filas.`, block.fuente ? `Fuente: ${block.fuente}` : '']);
}

function addChartSlide(pptx, block, colors, font, number) {
  const slide = pptx.addSlide();
  slide.background = { color: colors.paper };
  const title = block.titulo || block.leyenda || 'Gráfico';
  addTitle(slide, title, font, colors, false);
  const categories = (block.categorias || []).map(String);
  const series = (block.series || []).map((serie) => ({
    name: String(serie.nombre || 'Serie'),
    labels: categories,
    values: (serie.valores || []).map(Number),
  }));
  const typeMap = {
    barras: pptxgen.ChartType.bar,
    columnas: pptxgen.ChartType.column,
    linea: pptxgen.ChartType.line,
    circular: pptxgen.ChartType.pie,
  };
  const chartType = typeMap[block.tipo_grafico] || pptxgen.ChartType.bar;
  slide.addChart(chartType, series, {
    x: 0.78, y: 1.45, w: 11.7, h: 4.95,
    showTitle: true,
    title: block.unidad ? `${title} · ${block.unidad}` : title,
    showLegend: series.length > 1,
    legendPos: 'b',
    showValue: true,
    dataLabelPosition: chartType === pptxgen.ChartType.bar ? 'outEnd' : 'inEnd',
    chartColors: [colors.primary, colors.accent, '4E86A1', '925E78'],
    catAxisLabelColor: colors.muted,
    valAxisLabelColor: colors.muted,
    valGridLine: { color: 'DDE4E5', size: 1 },
    catGridLine: { style: 'none' },
    showCatName: false,
    showSerName: false,
    showPercent: chartType === pptxgen.ChartType.pie,
    border: { color: colors.paper, transparency: 100 },
  });
  slide.addText(`Fuente: ${block.fuente} · Unidad: ${block.unidad || 'conteo'}`, {
    x: 0.8, y: 6.62, w: 11.0, h: 0.22,
    fontFace: font, fontSize: 9, italic: true, color: colors.muted, margin: 0,
  });
  addSlideNumber(slide, number, font, colors);
  addNotes(slide, title, [block.mensaje || '', `Fuente: ${block.fuente}`, `Unidad: ${block.unidad || 'conteo'}`]);
}

function addFigureSlide(pptx, block, colors, font, number) {
  if (!block.ruta || !fs.existsSync(block.ruta)) {
    throw new Error(`no existe la figura declarada: ${block.ruta || '(sin ruta)'}`);
  }
  const slide = pptx.addSlide();
  slide.background = { color: colors.paper };
  const title = block.leyenda || 'Figura';
  addTitle(slide, title, font, colors, false);
  const alt = block.texto_alternativo || block.alt || block.leyenda;
  if (!alt) throw new Error(`la figura ${block.ruta} no tiene texto alternativo`);
  slide.addImage({
    path: block.ruta, x: 0.82, y: 1.45, w: 8.05, h: 4.95,
    sizing: 'contain', altText: alt,
  });
  slide.addShape('roundRect', {
    x: 9.22, y: 1.58, w: 3.25, h: 3.85, rectRadius: 0.08,
    fill: { color: colors.soft }, line: { color: colors.primary, width: 1.1 },
  });
  slide.addText(block.mensaje || block.leyenda || alt, {
    x: 9.55, y: 1.95, w: 2.58, h: 2.65,
    fontFace: font, fontSize: 18, bold: true, color: colors.ink,
    margin: 0, valign: 'mid', fit: 'shrink',
  });
  if (block.fuente) {
    slide.addText(`Fuente: ${block.fuente}`, {
      x: 0.84, y: 6.62, w: 11.0, h: 0.22,
      fontFace: font, fontSize: 9, italic: true, color: colors.muted, margin: 0,
    });
  }
  addSlideNumber(slide, number, font, colors);
  addNotes(slide, title, [block.notas || block.mensaje || alt, block.fuente ? `Fuente: ${block.fuente}` : '']);
}

function addReferences(pptx, bibliography, colors, font, startNumber) {
  const todas = Object.entries(bibliography).sort((a, b) => a[1].localeCompare(b[1], 'es'));
  const perSlide = 5;
  // Proyectadas no las lee nadie: su sitio es el informe. Se muestran las
  // primeras y se dice cuántas quedan, en vez de encadenar veinte láminas.
  const MAX_LAMINAS_REF = 2;
  const tope = perSlide * MAX_LAMINAS_REF;
  const entries = todas.slice(0, tope);
  const restantes = todas.length - entries.length;
  let lastSlide = null;
  let number = startNumber;
  if (!entries.length) {
    const slide = pptx.addSlide();
    slide.background = { color: colors.paper };
    addTitle(slide, 'Referencias', font, colors, false);
    slide.addText('No se declararon referencias para esta presentación.', {
      x: 0.9, y: 2.2, w: 10.8, h: 1.0, fontFace: font,
      fontSize: 20, color: colors.muted, margin: 0,
    });
    addSlideNumber(slide, number, font, colors);
    addNotes(slide, 'Referencias', []);
    return number + 1;
  }
  for (let i = 0; i < entries.length; i += perSlide) {
    const group = entries.slice(i, i + perSlide);
    const slide = pptx.addSlide();
    slide.background = { color: colors.paper };
    addTitle(slide, 'Referencias', font, colors, i > 0);
    let y = 1.42;
    group.forEach(([key, entry]) => {
      slide.addShape('ellipse', {
        x: 0.78, y: y + 0.06, w: 0.18, h: 0.18,
        fill: { color: colors.primary }, line: { color: colors.primary },
      });
      slide.addText(entry, {
        x: 1.08, y, w: 11.35, h: 0.86,
        fontFace: font, fontSize: bodySize(16), color: colors.ink,
        margin: 0, breakLine: false, fit: 'shrink',
      });
      y += 1.05;
    });
    addSlideNumber(slide, number, font, colors);
    addNotes(slide, 'Referencias', group.map(([, entry]) => entry));
    lastSlide = slide;
    number += 1;
  }
  if (restantes > 0 && lastSlide) {
    lastSlide.addText(
      `y ${restantes} referencias más — la lista completa está en el informe.`,
      { x: 0.9, y: H - 1.15, w: W - 1.8, h: 0.5, fontFace: font,
        fontSize: 16, italic: true, color: colors.muted, margin: 0 });
  }
  return number;
}

function sectionsFromGuion(guion, inText) {
  const events = [];
  let section = null;
  let items = [];

  let figura = null;

  function flush() {
    if (!section) return;
    events.push({ kind: 'content', title: section, items, figura });
    section = null;
    items = [];
    figura = null;
  }

  for (const block of guion.bloques || []) {
    switch (block.clase) {
      case 'titulo':
        if ((block.nivel || 1) <= 2) {
          flush();
          section = String(block.texto);
        } else {
          items.push({ text: String(block.texto), full: String(block.texto) });
        }
        break;
      case 'parrafo':
      case 'cita': {
        if (!section) section = guion.titulo;
        const full = textWithCitations(block, inText);
        for (const chunk of sentenceChunks(full)) items.push({ text: chunk, full });
        break;
      }
      case 'lista':
        if (!section) section = guion.titulo;
        for (const item of block.items || []) {
          const full = String(item);
          for (const chunk of sentenceChunks(full, 150)) items.push({ text: chunk, full });
        }
        break;
      case 'tabla':
        flush();
        events.push({ kind: 'table', block });
        break;
      case 'grafico':
        flush();
        events.push({ kind: 'chart', block });
        break;
      case 'figura':
        // Si hay una sección abierta, el diagrama va EN esa lámina, junto a
        // sus viñetas: una imagen en lámina aparte rompe el ritmo y obliga a
        // recordar de qué se hablaba.
        if (section) {
          figura = block;
        } else {
          flush();
          events.push({ kind: 'figure', block });
        }
        break;
      case 'bibliografia':
        flush();
        events.push({ kind: 'references' });
        break;
      case 'salto':
        flush();
        break;
      default:
        break;
    }
  }
  flush();
  return events;
}

async function generate(input) {
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_WIDE';
  pptx.author = input.guion.autor || 'SISIFO';
  pptx.subject = input.guion.titulo;
  pptx.title = input.guion.titulo;
  pptx.company = 'SISIFO';
  pptx.lang = 'es-BO';
  pptx.theme = {
    headFontFace: safeFont(input.formato || {}),
    bodyFontFace: safeFont(input.formato || {}),
    lang: 'es-BO',
  };
  pptx.defineLayout({ name: 'SISIFO_WIDE', width: W, height: H });
  pptx.layout = 'SISIFO_WIDE';

  ESCALA_TEXTO = Number((input.formato || {}).escala_texto) || 1;
  TITULO_TRABAJO = input.guion.titulo || '';
  const colors = palette(input.formato || {});
  const font = safeFont(input.formato || {});
  addCover(pptx, input, colors, font);
  let number = 2;
  let referencesAdded = false;
  const events = sectionsFromGuion(input.guion, input.en_texto || {});
  let variant = 0;

  const secciones = events.filter((e) => e.kind === 'content').map((e) => e.title);
  number = addAgenda(pptx, secciones, colors, font, number);
  // con muchas secciones, un separador cada tres da respiro sin alargar
  const cadaCuantas = secciones.length >= 6 ? 3 : 0;
  let nSeccion = 0;
  for (const event of events) {
    if (event.kind === 'content') {
      nSeccion += 1;
      if (cadaCuantas && nSeccion > 1 && (nSeccion - 1) % cadaCuantas === 0) {
        addSeparador(pptx, event.title, nSeccion, colors, font);
      }
      const sourceItems = event.items.length ? event.items : [{
        text: 'Esta sección organiza la idea principal de la exposición.',
        full: event.title,
      }];
      const groups = [];
      for (let i = 0; i < sourceItems.length; i += 6) groups.push(sourceItems.slice(i, i + 6));
      for (let i = 0; i < groups.length; i += 1) {
        // el diagrama va en la primera lámina de la sección
        addContentSlide(pptx, event.title, groups[i], colors, font, number,
                        i > 0, variant, i === 0 ? event.figura : null);
        number += 1;
        variant += 1;
      }
    } else if (event.kind === 'table') {
      addTableSlide(pptx, event.block, colors, font, number++);
    } else if (event.kind === 'chart') {
      addChartSlide(pptx, event.block, colors, font, number++);
    } else if (event.kind === 'figure') {
      addFigureSlide(pptx, event.block, colors, font, number++);
    } else if (event.kind === 'references') {
      number = addReferences(pptx, input.bibliografia || {}, colors, font, number);
      referencesAdded = true;
    }
  }
  if (!referencesAdded && Object.keys(input.bibliografia || {}).length) {
    number = addReferences(pptx, input.bibliografia || {}, colors, font, number);
  }
  addCierre(pptx, input, colors, font);
  await pptx.writeFile({ fileName: input.destino });
  return { ruta: input.destino, unidades: pptx._slides.length };
}

async function main() {
  const inputPath = process.argv[2];
  if (!inputPath) fail('falta el archivo JSON de solicitud');
  let input;
  try {
    input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  } catch (error) {
    fail(`no pude leer la solicitud: ${error.message}`);
  }
  if (!input.destino || !input.guion) fail('la solicitud necesita destino y guion');
  fs.mkdirSync(path.dirname(input.destino), { recursive: true });
  try {
    const result = await generate(input);
    process.stdout.write(`${JSON.stringify(result)}\n`);
  } catch (error) {
    fail(error.stack || error.message);
  }
}

main();

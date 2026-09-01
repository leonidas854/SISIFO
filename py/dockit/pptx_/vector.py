# -*- coding: utf-8 -*-
"""Genera gráficos vectoriales (SVG->PNG) en la paleta de la plantilla policial."""
import subprocess, os, textwrap

OLIVA  = '#455119'
VERDE  = '#5E672C'
GRIS   = '#838858'
ORO    = '#C9A538'
SUAVE  = '#F4F3EE'
BLANCO = '#FFFFFF'

# --- Iconos: viewBox 0 0 100 100, trazo. {c}=color principal ---
ICONS = {
'escudo_check': '<path d="M50 8 L87 22 V52 c0 22-17 36-37 42-20-6-37-20-37-42 V22 Z" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
                '<path d="M32 50 L45 63 L70 36" fill="none" stroke="{a}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>',
'guante': '<rect x="35" y="14" width="11" height="32" rx="5.5" fill="{c}"/>'
                '<rect x="48" y="8"  width="11" height="38" rx="5.5" fill="{c}"/>'
                '<rect x="61" y="16" width="11" height="30" rx="5.5" fill="{c}"/>'
                '<g transform="rotate(-32 26 56)"><rect x="20" y="40" width="11" height="30" rx="5.5" fill="{c}"/></g>'
                '<path d="M33 40 H74 V70 a14 14 0 0 1 -14 14 H47 a14 14 0 0 1 -14 -14 Z" fill="{c}"/>'
                '<rect x="33" y="80" width="41" height="12" rx="4" fill="{a}"/>',
'etiqueta':     '<path d="M12 22 H60 L88 50 L60 78 H12 Z" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
                '<circle cx="27" cy="50" r="5.5" fill="{c}"/>'
                '<path d="M40 38 V62 M48 38 V62 M56 38 V62" stroke="{a}" stroke-width="5" stroke-linecap="round"/>',
'balanza':      '<path d="M50 16 V84 M34 84 H66" stroke="{c}" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M14 32 H86" stroke="{c}" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M20 32 V42 M80 32 V42" stroke="{c}" stroke-width="4"/>'
                '<circle cx="50" cy="22" r="6" fill="{c}"/>'
                '<path d="M8 42 H32 L20 62 Z" fill="{a}"/><path d="M68 42 H92 L80 62 Z" fill="{a}"/>',
'trazabilidad': '<path d="M12 50 H88" stroke="{c}" stroke-width="6" stroke-linecap="round"/>'
                '<circle cx="16" cy="50" r="9" fill="{c}"/><circle cx="40" cy="50" r="9" fill="{a}"/>'
                '<circle cx="64" cy="50" r="9" fill="{c}"/><circle cx="88" cy="50" r="9" fill="{a}"/>',
'lupa':         '<circle cx="44" cy="42" r="25" fill="none" stroke="{c}" stroke-width="7"/>'
                '<path d="M62 60 L86 84" stroke="{c}" stroke-width="9" stroke-linecap="round"/>'
                '<circle cx="44" cy="42" r="8" fill="{a}"/>',
'caja_precinto':'<path d="M14 34 H86 V86 H14 Z" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
                '<path d="M14 34 L27 14 H73 L86 34" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
                '<rect x="43" y="34" width="14" height="52" fill="{a}"/>',
'bolsa_papel':  '<path d="M24 32 H76 V88 H24 Z" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
                '<path d="M24 32 L34 14 H66 L76 32" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
                '<path d="M36 52 H64 M36 66 H56" stroke="{a}" stroke-width="5" stroke-linecap="round"/>',
'bolsa_zip':    '<rect x="22" y="24" width="56" height="66" rx="5" fill="none" stroke="{c}" stroke-width="6"/>'
                '<path d="M22 40 H78" stroke="{c}" stroke-width="6"/>'
                '<path d="M32 32 h8 M48 32 h8 M64 32 h8" stroke="{a}" stroke-width="5" stroke-linecap="round"/>'
                '<circle cx="50" cy="66" r="12" fill="{a}" opacity="0.55"/>',
'estante':      '<path d="M12 12 V90 M88 12 V90" stroke="{c}" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M12 40 H88 M12 66 H88 M12 90 H88" stroke="{c}" stroke-width="6" stroke-linecap="round"/>'
                '<rect x="20" y="20" width="24" height="18" fill="{a}"/><rect x="52" y="24" width="28" height="14" fill="{c}" opacity="0.45"/>'
                '<rect x="20" y="48" width="30" height="16" fill="{c}" opacity="0.45"/><rect x="58" y="46" width="22" height="18" fill="{a}"/>',
'mazo':         '<path d="M18 88 H82" stroke="{c}" stroke-width="8" stroke-linecap="round"/>'
                '<path d="M26 74 H74" stroke="{a}" stroke-width="9" stroke-linecap="round"/>'
                '<g transform="rotate(-42 58 30)"><rect x="38" y="18" width="42" height="22" rx="4" fill="{c}"/></g>'
                '<path d="M50 40 L28 62" stroke="{c}" stroke-width="9" stroke-linecap="round"/>',
'camion':       '<path d="M8 32 H56 V66 H8 Z" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
                '<path d="M56 42 H72 L86 56 V66 H56 Z" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
                '<circle cx="26" cy="74" r="9" fill="{a}"/><circle cx="70" cy="74" r="9" fill="{a}"/>',
'formulario':   '<path d="M22 8 H60 L80 28 V92 H22 Z" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
                '<path d="M60 8 V28 H80" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
                '<path d="M34 44 H68 M34 58 H68 M34 72 H56" stroke="{a}" stroke-width="5" stroke-linecap="round"/>',
'matraz':       '<path d="M40 12 V40 L18 78 q-5 12 8 12 H74 q13 0 8-12 L60 40 V12" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
                '<path d="M33 12 H67" stroke="{c}" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M27 66 q23 -8 46 0 l9 14 q3 10 -7 10 H25 q-10 0 -7 -10 Z" fill="{a}" opacity="0.75"/>',
'no_mezclar':   '<rect x="6" y="30" width="32" height="52" rx="4" fill="none" stroke="{c}" stroke-width="6"/>'
                '<rect x="62" y="30" width="32" height="52" rx="4" fill="none" stroke="{c}" stroke-width="6"/>'
                '<circle cx="22" cy="58" r="7" fill="{a}"/><circle cx="78" cy="58" r="7" fill="{c}" opacity="0.5"/>'
                '<circle cx="50" cy="56" r="15" fill="#FFFFFF"/>'
                '<circle cx="50" cy="56" r="15" fill="none" stroke="{a}" stroke-width="6"/>'
                '<path d="M40 66 L60 46" stroke="{a}" stroke-width="6" stroke-linecap="round"/>',
'termometro':   '<path d="M42 14 a8 8 0 0 1 16 0 V58 a16 16 0 1 1 -16 0 Z" fill="none" stroke="{c}" stroke-width="6"/>'
                '<circle cx="50" cy="74" r="10" fill="{a}"/><path d="M50 44 V70" stroke="{a}" stroke-width="7" stroke-linecap="round"/>'
                '<path d="M64 26 H76 M64 38 H76 M64 50 H76" stroke="{c}" stroke-width="5" stroke-linecap="round"/>',
'huella':       '<path d="M18 74 V46 a32 32 0 0 1 64 0 V74" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M27 84 V46 a23 23 0 0 1 46 0 V64" fill="none" stroke="{a}" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M36 86 V46 a14 14 0 0 1 28 0 V80" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M45 76 V47 a5 5 0 0 1 10 0 V68" fill="none" stroke="{a}" stroke-width="6" stroke-linecap="round"/>',
'farola': '<path d="M50 92 V38" stroke="{c}" stroke-width="7" stroke-linecap="round"/><path d="M32 92 H68" stroke="{c}" stroke-width="7" stroke-linecap="round"/><path d="M30 34 q20 -20 40 0 Z" fill="{c}"/><path d="M22 22 L34 30 M78 22 L66 30 M50 12 V24" stroke="{a}" stroke-width="6" stroke-linecap="round"/>',
'camara_vig': '<path d="M14 34 L74 20 L80 42 L20 56 Z" fill="{c}"/><path d="M74 30 L92 26 L94 40 L78 44 Z" fill="{a}"/><path d="M34 52 V72 a10 10 0 0 0 10 10 H62" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round"/><circle cx="70" cy="82" r="8" fill="{a}"/>',
'reja': '<path d="M12 26 H88 M12 74 H88" stroke="{c}" stroke-width="7" stroke-linecap="round"/><path d="M24 18 V86 M42 18 V86 M58 18 V86 M76 18 V86" stroke="{c}" stroke-width="7" stroke-linecap="round"/><rect x="40" y="42" width="20" height="16" rx="3" fill="{a}"/>',
'ojo': '<path d="M8 50 q42 -34 84 0 q-42 34 -84 0 Z" fill="none" stroke="{c}" stroke-width="7" stroke-linejoin="round"/><circle cx="50" cy="50" r="15" fill="{a}"/><circle cx="50" cy="50" r="6" fill="{c}"/>',
'comunidad': '<circle cx="26" cy="30" r="12" fill="{c}"/><circle cx="74" cy="30" r="12" fill="{c}"/><circle cx="50" cy="24" r="14" fill="{a}"/><path d="M6 78 q20 -24 40 0 Z" fill="{c}"/><path d="M54 78 q20 -24 40 0 Z" fill="{c}"/><path d="M26 86 q24 -28 48 0 Z" fill="{a}"/>',
'dialogo': '<path d="M8 20 H58 a6 6 0 0 1 6 6 V50 a6 6 0 0 1 -6 6 H30 L16 68 V56 H8 a6 6 0 0 1 -6 -6 V26 a6 6 0 0 1 6 -6 Z" fill="{c}"/><path d="M42 40 H92 a6 6 0 0 1 6 6 V66 a6 6 0 0 1 -6 6 H84 V84 L70 72 H42 a6 6 0 0 1 -6 -6 V46 a6 6 0 0 1 6 -6 Z" fill="{a}"/>',
'oreja': '<path d="M32 88 V64 C18 56 14 40 22 28 C32 12 56 8 70 18 c14 10 16 30 6 42 -6 8 -14 8 -16 16" fill="none" stroke="{c}" stroke-width="7" stroke-linecap="round"/><path d="M40 42 a10 10 0 1 1 16 10" fill="none" stroke="{a}" stroke-width="7" stroke-linecap="round"/>',
'estrella': '<path d="M50 8 L62 38 L94 40 L69 60 L78 92 L50 74 L22 92 L31 60 L6 40 L38 38 Z" fill="{c}"/><path d="M50 26 L57 43 L75 44 L61 55 L66 74 L50 63 L34 74 L39 55 L25 44 L43 43 Z" fill="{a}"/>',
'libro_ley': '<path d="M12 20 H44 a8 8 0 0 1 6 4 a8 8 0 0 1 6 -4 H88 V78 H56 a8 8 0 0 0 -6 4 a8 8 0 0 0 -6 -4 H12 Z" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/><path d="M50 24 V82" stroke="{c}" stroke-width="6"/><path d="M20 36 H40 M20 50 H40 M60 36 H80 M60 50 H80" stroke="{a}" stroke-width="5" stroke-linecap="round"/>',
'columna': '<path d="M8 30 L50 10 L92 30 Z" fill="{c}"/><path d="M22 38 V74 M40 38 V74 M60 38 V74 M78 38 V74" stroke="{c}" stroke-width="9" stroke-linecap="round"/><path d="M8 84 H92" stroke="{a}" stroke-width="10" stroke-linecap="round"/>',
'mundo': '<circle cx="50" cy="50" r="38" fill="none" stroke="{c}" stroke-width="6"/><path d="M12 50 H88" stroke="{c}" stroke-width="5"/><path d="M50 12 c-18 16 -18 60 0 76 c18 -16 18 -60 0 -76" fill="none" stroke="{a}" stroke-width="5"/><path d="M20 30 q30 14 60 0 M20 70 q30 -14 60 0" fill="none" stroke="{a}" stroke-width="5"/>',
'candado': '<rect x="18" y="44" width="64" height="46" rx="8" fill="{c}"/><path d="M32 44 V30 a18 18 0 0 1 36 0 V44" fill="none" stroke="{c}" stroke-width="8"/><circle cx="50" cy="62" r="7" fill="{a}"/><path d="M50 66 V78" stroke="{a}" stroke-width="6" stroke-linecap="round"/>',
'no_fuerza': '<path d="M34 46 V26 a6 6 0 0 1 12 0 v18 M46 44 V20 a6 6 0 0 1 12 0 v24 M58 44 V26 a6 6 0 0 1 12 0 v30" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round"/><path d="M34 46 v18 a22 22 0 0 0 22 22 h4 a10 10 0 0 0 10 -10 V52" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round"/><circle cx="50" cy="50" r="42" fill="none" stroke="{a}" stroke-width="7"/><path d="M22 78 L78 22" stroke="{a}" stroke-width="7" stroke-linecap="round"/>',
'botiquin': '<rect x="10" y="28" width="80" height="58" rx="8" fill="none" stroke="{c}" stroke-width="6"/><path d="M36 28 V20 a6 6 0 0 1 6 -6 h16 a6 6 0 0 1 6 6 v8" fill="none" stroke="{c}" stroke-width="6"/><path d="M50 44 V70 M37 57 H63" stroke="{a}" stroke-width="9" stroke-linecap="round"/>',
'no_soborno': '<circle cx="50" cy="50" r="26" fill="none" stroke="{c}" stroke-width="7"/><path d="M50 32 V68 M40 40 h16 a8 8 0 0 1 0 16 h-12 a8 8 0 0 0 0 16 h16" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round"/><path d="M18 82 L82 18" stroke="{a}" stroke-width="8" stroke-linecap="round"/>',
'camara_foto': '<path d="M8 30 H30 L38 18 H62 L70 30 H92 V84 H8 Z" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/><circle cx="50" cy="56" r="18" fill="none" stroke="{c}" stroke-width="6"/><circle cx="50" cy="56" r="8" fill="{a}"/>',
'croquis': '<rect x="10" y="14" width="80" height="72" rx="4" fill="none" stroke="{c}" stroke-width="6"/><path d="M26 30 H60 V56 H26 Z" fill="none" stroke="{a}" stroke-width="5"/><path d="M60 40 H76 M26 66 H74" stroke="{a}" stroke-width="5" stroke-linecap="round"/><path d="M26 74 H74 M26 70 V78 M74 70 V78" stroke="{c}" stroke-width="4"/>',
'video': '<rect x="8" y="28" width="58" height="44" rx="7" fill="{c}"/><path d="M70 42 L92 30 V70 L70 58 Z" fill="{a}"/><circle cx="26" cy="50" r="8" fill="{a}"/>',
'cinta': '<path d="M4 34 L96 22 L96 44 L4 56 Z" fill="{c}"/><path d="M4 62 L96 50 L96 72 L4 84 Z" fill="{a}"/>',
'reloj': '<circle cx="50" cy="52" r="36" fill="none" stroke="{c}" stroke-width="7"/><path d="M50 30 V54 L68 64" fill="none" stroke="{a}" stroke-width="7" stroke-linecap="round"/><path d="M38 10 H62" stroke="{c}" stroke-width="7" stroke-linecap="round"/>',
'calendario': '<rect x="10" y="20" width="80" height="70" rx="8" fill="none" stroke="{c}" stroke-width="6"/><path d="M10 40 H90" stroke="{c}" stroke-width="6"/><path d="M30 10 V28 M70 10 V28" stroke="{c}" stroke-width="7" stroke-linecap="round"/><rect x="24" y="52" width="14" height="12" rx="2" fill="{a}"/><rect x="44" y="52" width="14" height="12" rx="2" fill="{a}"/><rect x="64" y="70" width="14" height="12" rx="2" fill="{a}"/>',
'carpeta': '<path d="M8 26 H40 L48 36 H92 V82 H8 Z" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/><path d="M20 50 H80 M20 64 H62" stroke="{a}" stroke-width="6" stroke-linecap="round"/>',
'jerarquia': '<rect x="36" y="8" width="28" height="20" rx="4" fill="{c}"/><rect x="6" y="60" width="26" height="20" rx="4" fill="{a}"/><rect x="37" y="60" width="26" height="20" rx="4" fill="{a}"/><rect x="68" y="60" width="26" height="20" rx="4" fill="{a}"/><path d="M50 28 V44 M19 60 V44 H81 V60 M50 44 V60" fill="none" stroke="{c}" stroke-width="5"/>',
'barras': '<path d="M10 88 H92" stroke="{c}" stroke-width="6" stroke-linecap="round"/><rect x="18" y="54" width="16" height="32" fill="{c}"/><rect x="42" y="34" width="16" height="52" fill="{a}"/><rect x="66" y="20" width="16" height="66" fill="{c}"/>',
'alerta': '<path d="M50 10 L94 86 H6 Z" fill="none" stroke="{c}" stroke-width="7" stroke-linejoin="round"/><path d="M50 38 V62" stroke="{a}" stroke-width="9" stroke-linecap="round"/><circle cx="50" cy="74" r="5.5" fill="{a}"/>',
'medalla': '<path d="M28 6 L44 40 M72 6 L56 40" stroke="{c}" stroke-width="8" stroke-linecap="round"/><circle cx="50" cy="64" r="26" fill="none" stroke="{c}" stroke-width="7"/><path d="M50 50 L55 61 L67 62 L58 70 L61 82 L50 75 L39 82 L42 70 L33 62 L45 61 Z" fill="{a}"/>',
'bandera': '<path d="M22 92 V10" stroke="{c}" stroke-width="8" stroke-linecap="round"/><path d="M22 14 H86 L74 34 L86 54 H22 Z" fill="{a}"/><path d="M22 14 H54 L48 34 L54 54 H22 Z" fill="{c}"/>',
'manos_apoyo': '<path d="M50 84 C30 70 10 56 10 38 a18 18 0 0 1 34 -8 a18 18 0 0 1 34 8 c0 18 -20 32 -28 46" fill="{a}"/><path d="M50 88 C28 72 6 58 6 38" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round"/>',
}

def icon(name, c=OLIVA, a=ORO):
    return ICONS[name].format(c=c, a=a)

def esc(s):
    return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def wrap_lines(text, width):
    return textwrap.wrap(text, width=width) or ['']

def svg_open(w, h, bg='none'):
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
    if bg != 'none':
        s += f'<rect width="{w}" height="{h}" rx="14" fill="{bg}"/>'
    return s

def render(svg, out_png, w_px):
    tmp = out_png.replace('.png', '.svg')
    open(tmp, 'w').write(svg)
    subprocess.run(['rsvg-convert', '-w', str(w_px), '-o', out_png, tmp], check=True)
    return out_png

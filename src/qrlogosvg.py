#!/usr/bin/env python3
"""Genera un QR SVG con un logo SVG centrado, sin rasterizar."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import qrcode
from qrcode.image.svg import SvgImage

SVG_NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG_NS)


def generar_ruta_disponible(ruta: Path) -> Path:
    if not ruta.exists():
        return ruta
    numero = 0
    while True:
        candidata = ruta.with_name(f'{ruta.stem}-{numero:04d}{ruta.suffix}')
        if not candidata.exists():
            return candidata
        numero += 1


def generar_qr(logo: Path, enlace: str, salida: Path) -> Path:
    if not logo.is_file() or logo.suffix.lower() != '.svg':
        raise ValueError('El logo debe ser un archivo SVG existente.')
    logo_raiz = ET.parse(logo).getroot()
    if logo_raiz.tag != f'{{{SVG_NS}}}svg':
        raise ValueError('El logo no tiene un elemento raíz SVG válido.')

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=10, border=4)
    qr.add_data(enlace)
    qr.make(fit=True)
    imagen = qr.make_image(image_factory=SvgImage)
    qr_raiz = ET.fromstring(imagen.to_string())

    # SvgImage expresa sus coordenadas en milímetros (1 módulo = 1 mm).
    lado = len(qr.get_matrix())
    # Los rectángulos de SvgImage usan mm; con viewBox deben ser unidades SVG.
    for elemento in qr_raiz.iter():
        for atributo in ('x', 'y', 'width', 'height'):
            valor = elemento.get(atributo)
            if valor is not None and valor.endswith('mm'):
                elemento.set(atributo, valor[:-2])
    qr_raiz.set('viewBox', f'0 0 {lado} {lado}')
    qr_raiz.insert(0, ET.Element(f'{{{SVG_NS}}}rect', {
        'x': '0', 'y': '0', 'width': str(lado), 'height': str(lado), 'fill': 'white'
    }))
    tamano_logo = lado * 0.19
    posicion = (lado - tamano_logo) / 2

    fondo = ET.SubElement(qr_raiz, f'{{{SVG_NS}}}rect', {
        'x': f'{posicion - 0.6:.4f}', 'y': f'{posicion - 0.6:.4f}',
        'width': f'{tamano_logo + 1.2:.4f}',
        'height': f'{tamano_logo + 1.2:.4f}', 'fill': 'white',
    })
    logo_raiz.set('x', f'{posicion:.4f}')
    logo_raiz.set('y', f'{posicion:.4f}')
    logo_raiz.set('width', f'{tamano_logo:.4f}')
    logo_raiz.set('height', f'{tamano_logo:.4f}')
    logo_raiz.set('preserveAspectRatio', 'xMidYMid meet')
    if 'viewBox' not in logo_raiz.attrib:
        raise ValueError('El logo debe tener viewBox para escalar correctamente.')
    qr_raiz.append(logo_raiz)

    salida = generar_ruta_disponible(salida)
    ET.ElementTree(qr_raiz).write(salida, encoding='utf-8', xml_declaration=True)
    return salida


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logo', type=Path)
    parser.add_argument('enlace')
    parser.add_argument('salida', type=Path)
    args = parser.parse_args()
    try:
        salida = generar_qr(args.logo.expanduser(), args.enlace, args.salida.expanduser())
    except (ValueError, ET.ParseError, OSError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(f'QR vectorial generado: {salida}')


if __name__ == '__main__':
    main()

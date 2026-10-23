# xml2altimetria.py
# -*- coding: utf-8 -*-
"""
Genera la altimetría de la etapa en formato SVG a partir del archivo XML.
Proyecto: LaVuelta2026
"""

import xml.etree.ElementTree as ET

class AltimetriaSVG(object):
    """
    Clase para leer el XML de la etapa y generar su perfil altimétrico en SVG.
    """
    def __init__(self, archivo_xml, archivo_svg):
        self.archivo_xml = archivo_xml
        self.archivo_svg = archivo_svg
        self.ns = {'u': 'http://www.uniovi.es'}
        
        # Ampliamos el lienzo para evitar solapamientos horizontales
        self.ancho_svg = 2400
        self.alto_svg = 800
        self.margen_x = 100
        self.margen_y = 250 # Margen superior amplio para nombres largos
        
        self.raiz = ET.Element('svg', {
            'xmlns': "http://www.w3.org/2000/svg",
            'version': "2.0",
            'width': str(self.ancho_svg),
            'height': str(self.alto_svg),
            'style': "background-color: white; font-family: Arial, sans-serif;"
        })

    def addLine(self, x1, y1, x2, y2, stroke, stroke_width):
        ET.SubElement(self.raiz, 'line', {
            'x1': str(x1), 'y1': str(y1),
            'x2': str(x2), 'y2': str(y2),
            'stroke': stroke,
            'stroke-width': str(stroke_width)
        })

    def addPolyline(self, points, stroke, stroke_width, fill):
        ET.SubElement(self.raiz, 'polyline', {
            'points': points,
            'stroke': stroke,
            'stroke-width': str(stroke_width),
            'fill': fill
        })
        
    def addText(self, texto, x, y, font_size, style, transform=""):
        atributos = {
            'x': str(x),
            'y': str(y),
            'font-size': str(font_size),
            'style': style
        }
        # Inyectamos transformaciones de giro si se reciben
        if transform:
            atributos['transform'] = transform
            
        elemento_texto = ET.SubElement(self.raiz, 'text', atributos)
        elemento_texto.text = texto

    def procesar_xml(self):
        try:
            arbol_xml = ET.parse(self.archivo_xml)
        except Exception as e:
            print(f"Error al leer el XML: {e}")
            return
            
        puntos = []
        max_distancia = 0.0
        max_altitud = 0.0
        
        nodos_puntos = arbol_xml.findall('.//u:puntoAnonimo', self.ns)
        
        for nodo in nodos_puntos:
            nodo_nombre = nodo.find('u:nombre', self.ns)
            nombre = nodo_nombre.text.strip() if nodo_nombre is not None else ""
            dist = float(nodo.find('u:distancia', self.ns).text)
            alt = float(nodo.find('u:altitud', self.ns).text)
            
            puntos.append({'nombre': nombre, 'distancia': dist, 'altitud': alt})
            
            if dist > max_distancia:
                max_distancia = dist
            if alt > max_altitud:
                max_altitud = alt

        if not puntos:
            print("No se encontraron puntos para trazar la altimetría.")
            return

        ancho_dibujo = self.ancho_svg - (2 * self.margen_x)
        alto_dibujo = self.alto_svg - (2 * self.margen_y)
        
        escala_x = ancho_dibujo / max_distancia if max_distancia > 0 else 1
        escala_y = alto_dibujo / max_altitud if max_altitud > 0 else 1
        
        y_suelo = self.alto_svg - (self.margen_y - 100) # Ajuste de altura base

        # Eje X horizontal
        self.addLine(self.margen_x, y_suelo, self.ancho_svg - self.margen_x, y_suelo, "black", 2)

        coordenadas_suelo = [f"{self.margen_x},{y_suelo}"]
        
        for index, p in enumerate(puntos):
            px = self.margen_x + (p['distancia'] * escala_x)
            py = y_suelo - (p['altitud'] * escala_y)
            coordenadas_suelo.append(f"{px},{py}")
            
            # Líneas guía verticales
            self.addLine(px, y_suelo, px, py, "#cccccc", 1)
            
            # Escalonamiento de los textos de los Kilómetros en zig-zag para evitar choques
            offset_y = 20 if (index % 2 == 0) else 40
            self.addText(f"{p['distancia']} km", px - 15, y_suelo + offset_y, 11, "fill: #333;")
            
            # Nombres rotados nativamente hacia arriba (ángulo -90)
            texto_vertical = f"{p['nombre']} ({p['altitud']} m)"
            anclaje_x = px + 4
            anclaje_y = py - 10
            rotacion = f"rotate(-90 {anclaje_x},{anclaje_y})"
            self.addText(texto_vertical, anclaje_x, anclaje_y, 14, "fill: black; font-weight: bold;", rotacion)

        # Cierre del polígono
        px_final = self.margen_x + (puntos[-1]['distancia'] * escala_x)
        coordenadas_suelo.append(f"{px_final},{y_suelo}")

        # Trazado
        string_coordenadas = " ".join(coordenadas_suelo)
        self.addPolyline(string_coordenadas, "red", 4, "#ffcccc")

    def escribir(self):
        arbol_svg = ET.ElementTree(self.raiz)
        if hasattr(ET, 'indent'):
            ET.indent(arbol_svg, space="  ", level=0)
        arbol_svg.write(self.archivo_svg, encoding='utf-8', xml_declaration=True)
        print(f"¡Éxito! Altimetría reparada y generada en: {self.archivo_svg}")

def main():
    altimetria = AltimetriaSVG("etapaEsquema.xml", "altimetria.svg")
    altimetria.procesar_xml()
    altimetria.escribir()

if __name__ == "__main__":
    main()
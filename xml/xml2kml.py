# xml2kml.py
# -*- coding: utf-8 -*-
"""
Generación de archivo KML a partir de XML usando XPath y OOP.
Proyecto: LaVuelta2026
"""

import xml.etree.ElementTree as ET

class Kml(object):
    """
    Clase encargada de leer los datos de la etapa en XML y generar 
    su representación planimétrica en un archivo KML.
    """
    def __init__(self, archivo_xml, archivo_kml):
        """
        Inicializa los archivos, el espacio de nombres y el árbol DOM KML base.
        """
        self.archivo_xml = archivo_xml
        self.archivo_kml = archivo_kml
        
        # Espacio de nombres del XML de entrada (imprescindible para usar XPath)
        self.ns = {'u': 'http://www.uniovi.es'}
        
        # Creación del árbol DOM para el archivo KML de salida
        self.raiz = ET.Element('kml', xmlns="http://www.opengis.net/kml/2.2")
        self.doc = ET.SubElement(self.raiz, 'Document')
        
        # Inicializar los estilos visuales obligatorios
        self.crear_estilos()

    def crear_estilos(self):
        """
        Crea los estilos de colores en el prólogo del KML.
        Los colores en KML usan el formato AABBGGRR (Alpha, Blue, Green, Red) en Hexadecimal.
        """
        # Paleta requerida por el enunciado
        estilos = {
            'rojo': 'ff0000ff',      # Salida y Meta
            'verde': 'ff00ff00',     # Puertos de montaña
            'azul': 'ffff0000',      # Sprints intermedios
            'amarillo': 'ff00ffff',  # Puntos anónimos
            'linea_ruta': 'ff0000ff' # Línea de la ruta (Roja)
        }
        
        for id_estilo, color_hex in estilos.items():
            estilo = ET.SubElement(self.doc, 'Style', id=id_estilo)
            
            if id_estilo == 'linea_ruta':
                line_style = ET.SubElement(estilo, 'LineStyle')
                ET.SubElement(line_style, 'color').text = color_hex
                ET.SubElement(line_style, 'width').text = "5"
            else:
                icon_style = ET.SubElement(estilo, 'IconStyle')
                ET.SubElement(icon_style, 'color').text = color_hex
                # Se escala el icono para que se vea mejor en Google Earth
                ET.SubElement(icon_style, 'scale').text = "1.2"
                
                # AÑADIDO: Forzamos a que el icono base sea blanco para que los colores no se mezclen mal
                icon = ET.SubElement(icon_style, 'Icon')
                ET.SubElement(icon, 'href').text = "http://maps.google.com/mapfiles/kml/pushpin/wht-pushpin.png"

    def _extraer_coordenadas(self, elemento_padre):
        """
        Método auxiliar para extraer la longitud, latitud y altitud 
        de cualquier nodo XML utilizando XPath.
        """
        lon = elemento_padre.find('u:longitud', self.ns).text.strip()
        lat = elemento_padre.find('u:latitud', self.ns).text.strip()
        alt = elemento_padre.find('u:altitud', self.ns).text.strip()
        return lon, lat, alt

    def add_placemark(self, nombre, descripcion, lon, lat, alt, id_estilo):
        """
        Añade un marcador (Point) al documento KML asociado a un color.
        """
        pm = ET.SubElement(self.doc, 'Placemark')
        ET.SubElement(pm, 'name').text = nombre
        ET.SubElement(pm, 'description').text = descripcion
        ET.SubElement(pm, 'styleUrl').text = f"#{id_estilo}"
        
        punto = ET.SubElement(pm, 'Point')
        ET.SubElement(punto, 'coordinates').text = f"{lon},{lat},{alt}"
        ET.SubElement(punto, 'altitudeMode').text = "relativeToGround"

    def procesar_etapa(self):
        """
        Lee el XML, extrae los datos mediante XPath y genera la ruta completa.
        El orden es clave: pintamos primero lo amarillo para que los hitos
        especiales (rojo, verde, azul) queden dibujados por encima en el mapa.
        """
        try:
            arbol_xml = ET.parse(self.archivo_xml)
        except Exception as e:
            print(f"Error al abrir el XML: {e}")
            return

        # 1. PUNTOS ANÓNIMOS PRIMERO (Capa base - Amarillo)
        coordenadas_ruta = []
        for punto in arbol_xml.findall('.//u:puntoAnonimo', self.ns):
            nodo_nombre = punto.find('u:nombre', self.ns)
            nombre = nodo_nombre.text.strip() if nodo_nombre is not None else "Punto Anónimo"
            
            lon, lat, alt = self._extraer_coordenadas(punto)
            self.add_placemark(nombre, "Hito de ruta", lon, lat, alt, "amarillo")
            
            # Recopilamos las coordenadas en orden para la línea continua
            coordenadas_ruta.append(f"{lon},{lat},{alt}")

        # 2. SALIDA Y META (Se pintan encima - Rojo)
        salida = arbol_xml.find('.//u:salida', self.ns)
        if salida is not None:
            lon, lat, alt = self._extraer_coordenadas(salida)
            self.add_placemark("Salida de etapa", "Inicio", lon, lat, alt, "rojo")

        meta = arbol_xml.find('.//u:meta', self.ns)
        if meta is not None:
            lon, lat, alt = self._extraer_coordenadas(meta)
            self.add_placemark("Meta de etapa", "Final", lon, lat, alt, "rojo")

        # 3. PUERTOS DE MONTAÑA (Se pintan encima - Verde)
        for puerto in arbol_xml.findall('.//u:puerto', self.ns):
            nombre = puerto.find('u:nombre', self.ns).text.strip()
            lon, lat, alt = self._extraer_coordenadas(puerto)
            self.add_placemark(nombre, "Puerto de Montaña", lon, lat, alt, "verde")

        # 4. SPRINTS INTERMEDIOS (Se pintan encima - Azul)
        for sprint in arbol_xml.findall('.//u:sprint', self.ns):
            nombre = sprint.find('u:nombre', self.ns).text.strip()
            lon, lat, alt = self._extraer_coordenadas(sprint)
            self.add_placemark(nombre, "Sprint Intermedio", lon, lat, alt, "azul")

        # 5. TRAZADO DE LA LÍNEA
        if coordenadas_ruta:
            pm_linea = ET.SubElement(self.doc, 'Placemark')
            ET.SubElement(pm_linea, 'name').text = "Ruta de la etapa"
            ET.SubElement(pm_linea, 'styleUrl').text = "#linea_ruta"
            
            ls = ET.SubElement(pm_linea, 'LineString')
            ET.SubElement(ls, 'extrude').text = "1"
            ET.SubElement(ls, 'tessellation').text = "1"
            ET.SubElement(ls, 'altitudeMode').text = "relativeToGround"
            ET.SubElement(ls, 'coordinates').text = "\n".join(coordenadas_ruta)

    def generar(self):
        """
        Escribe el árbol KML generado en un archivo físico.
        """
        arbol_kml = ET.ElementTree(self.raiz)
        
        # Formatear el XML de salida para que sea legible
        if hasattr(ET, 'indent'):
            ET.indent(arbol_kml, space="  ", level=0)
            
        arbol_kml.write(self.archivo_kml, encoding='utf-8', xml_declaration=True)
        print(f"¡Éxito! Planimetría generada en: {self.archivo_kml}")


def main():
    print(">>> Iniciando generador KML (LaVuelta2026)...")
    
    # 1. Creo una instacia de la clase kml
    generador = Kml("etapaEsquema.xml", "etapa.kml")
    
    # 2. Procesamos el XML y construimos el árbol DOM de KML
    generador.procesar_etapa()
    
    # 3. Guardamos el archivo 
    generador.generar()

if __name__ == "__main__":
    main()
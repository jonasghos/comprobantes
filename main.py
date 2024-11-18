import os
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import json
import re

# Configurar la ruta de Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\JonasGho\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Rutas
carpeta_archivos = 'procesar_imagenes'
carpeta_comprobantes = 'comprobantes'

# Crear la carpeta de comprobantes si no existe
os.makedirs(carpeta_comprobantes, exist_ok=True)



def transformar_texto_a_objeto(texto):
    # Dividir el texto en líneas y filtrar las líneas vacías
    lineas = [linea.strip() for linea in texto.strip().splitlines() if linea.strip()]
    
    # Crear un diccionario donde cada línea es una entrada
    resultado = {f"linea_{i + 1}": linea for i, linea in enumerate(lineas)}
    
    return resultado


def obtener_numero_decimal(resultado):
    # Definir un patrón para buscar números decimales
    patron_decimal = re.compile(r'\d+\.\d+')

    # Recorrer cada línea en el resultado
    for clave, linea in resultado.items():
        # Buscar el número decimal en la línea
        coincidencia = patron_decimal.search(linea)
        if coincidencia:
            numero_decimal = coincidencia.group()  # Obtener el número decimal encontrado
            print(f"La línea '{clave}' contiene un número decimal: {numero_decimal}")
            return numero_decimal 

def obtener_fecha(resultado):
    # Definir un patrón para buscar fechas en varios formatos
    patron_fecha = re.compile(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2} de \w+ de \d{4}|\d{1,2}/[A-Z]{3}/\d{4})\b')

    # Recorrer cada línea en el resultado
    for clave, linea in resultado.items():
        # Buscar la fecha en la línea
        coincidencia = patron_fecha.search(linea)
        if coincidencia:
            fecha_encontrada = coincidencia.group()  # Obtener la fecha encontrada
            print(f"La línea '{clave}' contiene una fecha: {fecha_encontrada}")
            return fecha_encontrada  # Retornar la fecha encontrada
    
    print("No se encontraron fechas en las líneas.")
    return None

def obtener_hora(resultado):
    # Definir un patrón para buscar horas en varios formatos
    patron_hora = re.compile(r'\b([01]?[0-9]|2[0-3]):[0-5][0-9]\s*(am|pm|AM|PM|hs|h)?\b')

    # Recorrer cada línea en el resultado
    for clave, linea in resultado.items():
        # Buscar la hora en la línea
        coincidencia = patron_hora.search(linea)
        if coincidencia:
            hora_encontrada = coincidencia.group(0)  # Obtener la hora encontrada
            # Extraer solo la parte de la hora (sin letras)
            hora_sin_letras = hora_encontrada.split()[0]  # Tomar solo la parte numérica
            print(f"La línea '{clave}' contiene una hora: {hora_sin_letras}")
            return hora_sin_letras  # Retornar solo la hora encontrada
    
    print("No se encontraron horas en las líneas.")
    return None 

datos = {
    "Origen" : None,
    "Destino" : None,
    "Monto" : None,
    "Fecha" : None,
    "Hora" : None,
    "Número de operación" : None
}




# Procesar archivos en la carpeta
for archivo in os.listdir(carpeta_archivos):
    ruta_archivo = os.path.join(carpeta_archivos, archivo)
    texto_extraido = ""

    if archivo.endswith(('.png', '.jpg', '.jpeg')):
        # Procesar imágenes
        imagen_pil = Image.open(ruta_archivo)
        texto_extraido = pytesseract.image_to_string(imagen_pil)

    elif archivo.endswith('.pdf'):
        # Procesar PDFs
        with fitz.open(ruta_archivo) as pdf:
            for num_pagina, pagina in enumerate(pdf, start=1):
                # Extraer texto directamente
                texto = pagina.get_text()
                if not texto.strip():  # Si la página está vacía de texto
                    # Convertir la página a imagen y usar OCR
                    pix = pagina.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    texto = pytesseract.image_to_string(img)
                texto_extraido += f"\n--- Página {num_pagina} ---\n{texto}\n"

    # Crear un archivo JSON para el texto extraído
    if texto_extraido.strip():  # Verificar que haya texto
        # Procesar el texto para obtener los pares clave-valor deseados
        datos_extraidos = transformar_texto_a_objeto(texto_extraido)

        datos["Monto"] = obtener_numero_decimal(datos_extraidos)
        datos["Fecha"] = obtener_fecha(datos_extraidos)
        datos["Hora"] = obtener_hora(datos_extraidos)


        # Incluir el nombre del archivo en los datos
        datos_extraidos["archivo"] = archivo  # Añadir el nombre del archivo

        # Agregar el texto completo procesado
        json_data = {
            "datos": datos_extraidos,  # Almacenar como objeto con los valores extraídos
            "texto": texto_extraido.strip(),
            "objeto": datos  # Incluir el contenido del texto procesado
        }
        
        # Nombre del archivo JSON
        nombre_json = os.path.splitext(archivo)[0] + ".json"
        ruta_json = os.path.join(carpeta_comprobantes, nombre_json)

        # Guardar el JSON
        with open(ruta_json, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

print(f"Archivos JSON generados en la carpeta '{carpeta_comprobantes}'")

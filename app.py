
from flask import Flask, request, jsonify, render_template, send_from_directory
import logging
from logging.handlers import RotatingFileHandler
import os
import shutil
import asyncio
import uuid
from pathlib import Path

# Importar las funciones de la lógica de negocio
from backend_logic import (
    extract_text_from_pdf, anonymize_text, redact_keywords,
    get_llm_response, create_text_pdf, merge_pdfs_temp, KEYWORD_REDACTION_LIST
)

app = Flask(__name__)
# Directorios para almacenar archivos temporales y de salida

APP_DATA_DIR_NAME = "EstudioIAClaroData" 
USER_HOME_DIR = Path.home() 
APP_DATA_ROOT = USER_HOME_DIR / APP_DATA_DIR_NAME

UPLOAD_FOLDER = APP_DATA_ROOT  / "Informes Clásicos"
OUTPUT_FOLDER = APP_DATA_ROOT  / "Informes Simplificados"

# Crear directorios si no existen
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Logging
log_dir = APP_DATA_ROOT / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "app_activity.log"
app.logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024 * 10, backupCount=5) 
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(file_handler)



@app.route('/')
def index():
   
    return render_template('index.html')

@app.route('/upload_pdf', methods=['POST'])
async def upload_pdf():
   
    if 'pdf_file' not in request.files:
        return jsonify({"error": "No se encontró el archivo PDF."}), 400
    
    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo."}), 400
    
    if file and file.filename.endswith('.pdf'):
        # Generar un ID único para esta sesión de procesamiento
        session_id = str(uuid.uuid4())
        session_dir = UPLOAD_FOLDER / session_id
        session_dir.mkdir(exist_ok=True)

        original_pdf_path = session_dir / file.filename
        file.save(original_pdf_path)

        try:
            # Extraer texto
            original_text = extract_text_from_pdf(original_pdf_path)
            if not original_text.strip():
                return jsonify({"error": "El PDF está vacío o no contiene texto extraíble."}), 400

            # Anonimizar
            anonymized_text = anonymize_text(original_text)
            anonymized_text = redact_keywords(anonymized_text, KEYWORD_REDACTION_LIST)

            #Crear PDF de vista previa
            preview_filename = f"ANONIMIZADO_vista_previa_{session_id}.pdf"
            preview_pdf_path = OUTPUT_FOLDER / preview_filename
            create_text_pdf(anonymized_text, preview_pdf_path, "Texto Anonimizado (Vista Previa)")

            # Retornar la URL del PDF de vista previa y el ID de sesión
            return jsonify({
                "message": "PDF cargado y anonimizado. Revise la vista previa.",
                "preview_url": f"/download/{preview_filename}",
                "session_id": session_id,
                "original_pdf_name": file.filename 
            }), 200
        except Exception as e:
            # Limpiar directorio de sesión en caso de error
            shutil.rmtree(session_dir, ignore_errors=True)
            return jsonify({"error": f"Error durante la carga y anonimización: {str(e)}"}), 500
    else:
        return jsonify({"error": "Formato de archivo no soportado. Por favor, suba un PDF."}), 400

@app.route('/confirm_and_process', methods=['POST'])
async def confirm_and_process():

    data = request.get_json()
    session_id = data.get('session_id')
    original_pdf_name = data.get('original_pdf_name')
    output_filename_base = data.get('output_filename')
    
    if not session_id or not original_pdf_name:
        return jsonify({"error": "Datos de sesión incompletos."}), 400

    session_dir = UPLOAD_FOLDER / session_id
    original_pdf_path = session_dir / original_pdf_name

    if not original_pdf_path.exists():
            # Limpiar directorio de sesión si el archivo original no se encuentra
            shutil.rmtree(session_dir, ignore_errors=True)
            return jsonify({"error": "Archivo original no encontrado para esta sesión."}), 404

    try:
        # Re-extraer texto si es necesario o cargar el anonimizado si se guardó
        original_text = extract_text_from_pdf(original_pdf_path)
        anonymized_text = anonymize_text(original_text)
        anonymized_text = redact_keywords(anonymized_text, KEYWORD_REDACTION_LIST)

        #Enviar a la IA para análisis
        ia_response = await get_llm_response(anonymized_text)

        # Crear PDF con la respuesta de la IA
        response_pdf_filename = f"analisis_ia_temp_{session_id}.pdf" # Nombre temporal para el PDF de la IA
        # El PDF de respuesta de la IA se guarda temporalmente en la carpeta de sesión
        response_pdf_path = session_dir / response_pdf_filename 
        create_text_pdf(ia_response, response_pdf_path, "Análisis Generado por IA")

        # Fusionar documentos: Usar el nombre proporcionado por el usuario
        final_merged_filename = f"{output_filename_base}.pdf" if not output_filename_base.lower().endswith('.pdf') else output_filename_base
        final_merged_pdf_path = OUTPUT_FOLDER / final_merged_filename # El PDF final fusionado se guarda en OUTPUT_FOLDER
        
        merge_pdfs_temp(original_pdf_path, response_pdf_path, final_merged_pdf_path)

        # Limpiar directorio de sesión temporal después de la fusión
        shutil.rmtree(session_dir, ignore_errors=True)

        return jsonify({
            "message": "Proceso completado con éxito.",
            "final_pdf_url": f"/download/{final_merged_filename}"
        }), 200
    except Exception as e:
        # Limpiar directorio de sesión en caso de error
        shutil.rmtree(session_dir, ignore_errors=True)
        return jsonify({"error": f"Error durante el procesamiento: {str(e)}"}), 500
   
        

@app.route('/download/<filename>')
def download_file(filename):

    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=5000)


@app.route('/upload_pdf', methods=['POST'])
async def upload_pdf():
    app.logger.info("Solicitud de carga de PDF recibida.")  
    if 'pdf_file' not in request.files:
        app.logger.warning("No se encontró el archivo PDF en la solicitud.")  
        return jsonify({"error": "No se encontró el archivo PDF."}), 400

    try:

        app.logger.info(f"PDF original guardado: {original_pdf_path}")  
        original_text = extract_text_from_pdf(original_pdf_path)
        app.logger.info("Texto extraído del PDF.")  
        anonymized_text = anonymize_text(original_text)
        app.logger.info("Texto anonimizado.")  

        app.logger.info(f"Vista previa PDF creada: {preview_pdf_path}")  
        return jsonify({
            "message": "PDF cargado y anonimizado. Revise la vista previa.",
            "preview_url": f"/download/{preview_filename}",
            "session_id": session_id,
            "original_pdf_name": file.filename
        }), 200
    except Exception as e:
        app.logger.exception(f"Error durante la carga y anonimización: {e}") 
        shutil.rmtree(session_dir, ignore_errors=True)
        return jsonify({"error": f"Error durante la carga y anonimización: {str(e)}"}), 500


@app.route('/confirm_and_process', methods=['POST'])
async def confirm_and_process():
    data = request.get_json()
    session_id = data.get('session_id')
    original_pdf_name = data.get('original_pdf_name')
    output_filename_base = data.get('output_filename')

    app.logger.info(f"Solicitud de procesamiento recibida para sesión: {session_id}")  

    if not session_id or not original_pdf_name:
        app.logger.warning("Datos de sesión incompletos para procesamiento.")  
        return jsonify({"error": "Datos de sesión incompletos."}), 400

    try:

        app.logger.info("Enviando texto a la IA (Gemini).")  
        ia_response = await get_llm_response(anonymized_text)
        app.logger.info("Respuesta de la IA recibida.") 
  
        app.logger.info(f"Fusionando PDF final: {final_merged_pdf_path}")  
        merge_pdfs_temp(original_pdf_path, response_pdf_path, final_merged_pdf_path)
        app.logger.info("Proceso completado con éxito.")  

    except Exception as e:
        app.logger.exception(f"Error durante el procesamiento final: {e}")  
        shutil.rmtree(session_dir, ignore_errors=True)
        return jsonify({"error": f"Error durante el procesamiento: {str(e)}"}), 500

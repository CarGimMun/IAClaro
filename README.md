#  IAClaro: Generador de Informes de Alta Centrado en el Paciente

IAClaro es una aplicación web desarrollada como parte demi Trabajo de Fin de Grado, estudiante de Ingeniería Biomédica en la Universidad Autónoma de Madrid.

El proyecto propone una herramienta basada en **Inteligencia Artificial (IA)** capaz de **adaptar los informes de alta hospitalaria** a un lenguaje más accesible para el paciente, manteniendo la fidelidad clínica y respetando los principios éticos y de protección de datos.

---

## Objetivo del Proyecto

El objetivo principal de IAClaro es **mejorar la comprensión del informe de alta hospitalaria** mediante el uso de modelos de lenguaje (LLMs) como *Gemini 2.5*, aplicados de forma **segura y local** dentro del entorno hospitalario. Para integrarlo en el flujo de trabajo normativo, se optó por desarollar una app web que permitiera al clínico interactuar con una interfaz sencilla y amigable. 

La herramienta realiza tres pasos fundamentales:

1. **Anonimización automática** del informe en PDF (basada en *Microsoft Presidio* y *spaCy*).  
2. **Simplificación del lenguaje clínico** usando un modelo LLM configurable.  
3. **Generación de un nuevo PDF** que combina el informe original con una versión adaptada al paciente.

---

## Arquitectura y Tecnologías

- **Backend:** Python 3.10, Flask  
- **Frontend:** HTML5, CSS, Bootstrap  
- **Procesamiento NLP:** spaCy, Presidio, Gemini / OpenAI API  
- **PDF Handling:** PyPDF2, ReportLab  
- **Despliegue local:** entorno virtual (venv)  

---

##  Instalación y Ejecución

### Clonar el repositorio

```bash
git clone https://github.com/tuusuario/IAClaro.git
cd IAClaro


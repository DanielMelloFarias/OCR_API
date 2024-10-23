from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from PIL import Image
import io
import base64
import requests
import google.generativeai as genai
import time

# Configure Google Generative AI
genai.configure(api_key="AIzaSyD9XWKW-zJa05wr6r3SFCX8EllUDl-w4C8")
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

class URLRequest(BaseModel):
    url: str

class Base64Request(BaseModel):
    base64: str

def gemini_pro_vision_api(image, prompt="Descreva a img e extraia a informação de texto (caso necessário, complete o texto da forma q achar necessário), responta em pt-br."):
    response = model.generate_content([prompt, image])
    return response.text

# Função para processar PDF
def process_pdf(pdf_file: UploadFile):
    name = pdf_file.filename
    path = f"/tmp/{name}"  # Salvar o arquivo temporariamente
    
    with open(path, "wb") as f:
        f.write(pdf_file.file.read())
    
    try:
        pdfFile = genai.get_file(f"files/{name}")
    except:
        pdfFile = genai.upload_file(path=path, name=name, resumable=True)

    # Espera o arquivo ser processado
    while pdfFile.state.name == "PROCESSING":
        time.sleep(10)
        pdfFile = genai.get_file(pdfFile.name)

    if pdfFile.state.name == "FAILED":
        raise ValueError("Falha no processamento do arquivo PDF.")
    
    # Geração do conteúdo transcrito
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        system_instruction=[
            "You are a helpful transcriber that can accurately transcribe text from images and PDFs.",
            "Your mission is to transcribe text from the provided PDF file.",
        ],
    )
    prompt = "Please transcribe the text in this PDF document."
    response = model.generate_content([pdfFile, prompt], request_options={"timeout": 600})

    return response.text

@app.get("/")
async def read_root():
    return {"message": "OI"}

@app.post("/api/url")
async def analyze_image_url(request: URLRequest):
    response = requests.get(request.url)
    image = Image.open(io.BytesIO(response.content))
    return {"description": gemini_pro_vision_api(image)}

@app.post("/api/base64")
async def analyze_image_base64(request: Base64Request):
    image_data = base64.b64decode(request.base64)
    image = Image.open(io.BytesIO(image_data))
    return {"description": gemini_pro_vision_api(image)}

@app.post("/api/upload")
async def analyze_uploaded_image(file: UploadFile = File(...)):
    image = Image.open(file.file)
    return {"description": gemini_pro_vision_api(image)}

# Nova rota para upload de PDF
@app.post("/api/upload_pdf")
async def analyze_uploaded_pdf(file: UploadFile = File(...)):
    try:
        transcription = process_pdf(file)
        return {"transcription": transcription}
    except Exception as e:
        return {"error": str(e)}

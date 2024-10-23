from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from PIL import Image
import io
import base64
import requests
import google.generativeai as genai
import time
import re

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
    # Convertendo o nome do arquivo para minúsculas e substituindo espaços por traços
    name = pdf_file.filename.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)  # Substituindo caracteres inválidos
    name = name.strip('-')  # Removendo traços no início ou final
    
    path = f"/tmp/{name}"  # Salvar o arquivo temporariamente
    
    # Salvar o PDF no caminho temporário
    with open(path, "wb") as f:
        f.write(pdf_file.file.read())
    
    try:
        # Tenta obter o arquivo, caso já esteja carregado
        pdfFile = genai.get_file(f"files/{name}")
    except:
        # Define o tipo MIME corretamente
        mime_type = "application/pdf"
        print(f"Uploading file with mime_type: {mime_type}")
        
        # Realiza o upload com o mime_type definido
        pdfFile = genai.upload_file(path=path, name=name, mime_type=mime_type, resumable=True)
        print(f"Completed upload: {pdfFile.uri}")

    # Espera o arquivo ser processado
    while pdfFile.state.name == "PROCESSING":
        #time.sleep(10)
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
    

@app.post("/api/upload_pdf_base64")
async def analyze_pdf_base64(request: Base64Request):
    try:
        # Decodificando o Base64 para binário
        pdf_data = base64.b64decode(request.base64)
        
        # Definindo um nome temporário para o arquivo PDF
        name = "uploaded_pdf_base64.pdf"
        path = f"/tmp/{name}"

        # Escrevendo o PDF no sistema de arquivos temporariamente
        with open(path, "wb") as f:
            f.write(pdf_data)
        
        # Criando um objeto UploadFile para reutilizar a função `process_pdf`
        class TempFile:
            filename = name
            file = open(path, "rb")
        
        # Chamando a função de processamento do PDF com o arquivo temporário
        transcription = process_pdf(TempFile)
        
        # Fechar o arquivo temporário
        TempFile.file.close()

        return {"transcription": transcription}
    except Exception as e:
        return {"error": str(e)}


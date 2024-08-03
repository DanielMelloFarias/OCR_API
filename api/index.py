from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
from vercel_storage import blob


app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utilizando variáveis de ambiente do Vercel
# Utilizando variáveis de ambiente do Vercel
BLOB_READ_WRITE_TOKEN = os.environ.get('BLOB_READ_WRITE_TOKEN')
GROQ_API_KEY = os.environ.get('API_GROQ')

# Lista de extensões de arquivo permitidas
ALLOWED_EXTENSIONS = {".txt", ".csv", ".doc", ".docx", ".pdf"}

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Upload File</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f9;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    text-align: center;
                }
                h1 {
                    color: #333;
                }
                form {
                    margin-top: 20px;
                }
                input[type="file"] {
                    display: none;
                }
                label {
                    background-color: #007bff;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                }
                button {
                    background-color: #28a745;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-top: 20px;
                }
                button:hover, label:hover {
                    opacity: 0.9;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Upload File</h1>
                <form action="/uploadfile" method="post" enctype="multipart/form-data">
                    <label for="file">Choose a file</label>
                    <input type="file" id="file" name="file">
                    <button type="submit">Upload</button>
                </form>
            </div>
        </body>
    </html>
    """

@app.post("/uploadfile")
async def upload_form(file: UploadFile = File(...)):
    # Verifica se a extensão do arquivo é permitida
    _, file_extension = os.path.splitext(file.filename)
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tipo de Arquivo não Permitido. Tipos de Arquivos permitidos: .txt, .csv, .doc, .docx, .pdf")

    try:
        my_file = file.filename
        file_content = await file.read()

        resp = blob.put(
            pathname=my_file,
            body=file_content,
            options={'token': BLOB_READ_WRITE_TOKEN}
        )

        return {"message": "File uploaded successfully", "data": resp}
    except Exception as e:
        return {"message": "Failed to upload file", "error": str(e)}

@app.get("/files")
async def list_files():
    try:
        resp = blob.list(options={'token': BLOB_READ_WRITE_TOKEN})
        return {"files": resp}
    except Exception as e:
        return {"message": "Failed to list files", "error": str(e)}

@app.post("/deletefile")
async def delete_file(url: dict = Body(...)):
    try:
        url_to_delete = url.get("url")
        resp = blob.delete(
            [url_to_delete],
            options={'token': BLOB_READ_WRITE_TOKEN}
        )
        return {"message": "File deleted successfully", "data": resp}
    except Exception as e:
        return {"message": "Failed to delete file", "error": str(e)}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

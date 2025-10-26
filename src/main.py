# src/main.py
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd

app = FastAPI()

# Montar carpeta static y templates
app.mount("/static", StaticFiles(directory="../static"), name="static")
templates = Jinja2Templates(directory="../templates")

@app.get("/", response_class=HTMLResponse)
def form_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    # Leer archivo subido con pandas
    df = pd.read_csv(file.file)
    # Información básica
    info = {
        "num_filas": len(df),
        "num_columnas": len(df.columns),
        "columnas": list(df.columns),
        "primeras_filas": df.head().to_html()
    }
    return templates.TemplateResponse("index.html", {"request": request, "info": info})

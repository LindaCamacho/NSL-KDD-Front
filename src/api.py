from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
import io
from pathlib import Path

# Crear instancia FastAPI
app = FastAPI()

# Base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Montar carpeta de archivos estáticos
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Templates
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Guardar CSV cargado temporalmente
uploaded_dfs = {}

# ===========================
# Rutas
# ===========================

@app.get("/", response_class=HTMLResponse)
def formulario(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "columns": []})


@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...)):
    # Intentar leer CSV con distintos encodings y separadores
    try:
        df = pd.read_csv(file.file)
    except UnicodeDecodeError:
        file.file.seek(0)
        df = pd.read_csv(file.file, encoding="latin1")
    except pd.errors.ParserError:
        file.file.seek(0)
        df = pd.read_csv(file.file, sep=";")
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "columns": [],
            "error": f"Error al leer CSV: {e}"
        })

    uploaded_dfs["current"] = df
    columns = list(df.columns)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "columns": columns,
        "filename": file.filename
    })


@app.post("/process", response_class=HTMLResponse)
async def process(request: Request, selected_columns: list[str] = Form(...), limit: int = Form(5)):
    df = uploaded_dfs.get("current")
    if df is None:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "columns": [],
            "result": "<tr><td colspan='2'>No hay CSV cargado</td></tr>"
        })

    result_html = ""
    summary_df = pd.DataFrame(columns=["Columna", "Valores Únicos"])

    for col in selected_columns:
        unique_vals = df[col].unique()[:limit]
        more_flag = " ... (+ más)" if len(df[col].unique()) > limit else ""
        result_html += f"<tr><td>{col}</td><td>{', '.join(map(str, unique_vals))}{more_flag}</td></tr>"
        summary_df = pd.concat([summary_df, pd.DataFrame({"Columna":[col], "Valores Únicos":[', '.join(map(str, unique_vals)) + more_flag]})])

    # Guardar CSV en memoria
    buffer = io.StringIO()
    summary_df.to_csv(buffer, index=False)
    buffer.seek(0)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "columns": list(df.columns),
        "result": result_html,
        "download_csv": buffer.getvalue()
    })


@app.post("/download")
async def download(csv_data: str = Form(...)):
    buffer = io.StringIO(csv_data)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=resultados.csv"}
    )

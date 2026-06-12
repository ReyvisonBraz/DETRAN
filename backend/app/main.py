"""API do DETRAN-PA Consultas.

Endpoints:
  GET  /api/consultas              -> catalogo (o frontend monta a tela)
  POST /api/jobs                   -> dispara 1+ consultas (lote)
  GET  /api/jobs/{job_id}          -> status + resultados (polling)
  GET  /api/documentos/{nome}      -> download de PDF/boleto gerado
  GET  /healthz                    -> healthcheck
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app import catalog, settings
from app.jobs import gerenciador
from app.schemas import CriarJobRequest, CriarJobResponse, Job

app = FastAPI(
    title="DETRAN-PA Consultas API",
    version="0.1.0",
    description="Motor de consultas DETRAN-PA com execucao assincrona.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/consultas")
def listar_consultas():
    """Catalogo completo: o frontend usa para montar a selecao e os formularios."""
    return {"consultas": [c.to_dict() for c in catalog.listar()]}


@app.post("/api/jobs", response_model=CriarJobResponse)
def criar_job(req: CriarJobRequest):
    if not req.consultas:
        raise HTTPException(400, "Selecione ao menos uma consulta.")
    for sel in req.consultas:
        if not catalog.obter(sel.slug):
            raise HTTPException(400, f"Consulta invalida: {sel.slug}")

    job = gerenciador.criar(req.consultas, req.parametros)
    return CriarJobResponse(job_id=job.job_id, status=job.status, total=len(job.itens))


@app.get("/api/jobs/{job_id}", response_model=Job)
def status_job(job_id: str):
    job = gerenciador.obter(job_id)
    if not job:
        raise HTTPException(404, "Job nao encontrado.")
    return job


@app.get("/api/documentos/{nome}")
def baixar_documento(nome: str):
    # Impede path traversal
    nome_seguro = os.path.basename(nome)
    caminho = os.path.join(settings.STORAGE_DIR, nome_seguro)
    if not os.path.exists(caminho):
        raise HTTPException(404, "Documento nao encontrado ou expirado.")
    return FileResponse(caminho, media_type="application/pdf", filename=nome_seguro)

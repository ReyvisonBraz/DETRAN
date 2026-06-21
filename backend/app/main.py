import os

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app import catalog, settings
from app.auth import get_current_user
from app.creditos import (
    obter_saldo,
    obter_historico,
    deduzir_creditos,
    CUSTO_POR_CONSULTA,
    tem_creditos_suficientes,
)
from app.jobs import gerenciador
from app.schemas import CriarJobRequest, CriarJobResponse, Job

app = FastAPI(
    title="DETRAN-PA Consultas API",
    version="0.2.0",
    description="Motor de consultas DETRAN-PA com autenticacao e creditos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/consultas")
def listar_consultas():
    return {"consultas": [c.to_dict() for c in catalog.listar()]}


@app.post("/api/jobs", response_model=CriarJobResponse)
def criar_job(req: CriarJobRequest, user: dict = Depends(get_current_user)):
    if not req.consultas:
        raise HTTPException(400, "Selecione ao menos uma consulta.")
    for sel in req.consultas:
        if not catalog.obter(sel.slug):
            raise HTTPException(400, f"Consulta invalida: {sel.slug}")

    uid = user["uid"]
    custo_total = len(req.consultas) * CUSTO_POR_CONSULTA
    if not tem_creditos_suficientes(uid, custo_total):
        saldo = obter_saldo(uid)
        raise HTTPException(
            402,
            f"Creditos insuficientes. Saldo: {saldo}, necessario: {custo_total}.",
        )

    deduzir_creditos(uid, custo_total, descricao=f"{len(req.consultas)} consulta(s)")

    job = gerenciador.criar(req.consultas, req.parametros, uid=uid)
    return CriarJobResponse(job_id=job.job_id, status=job.status, total=len(job.itens))


@app.get("/api/jobs/{job_id}", response_model=Job)
def status_job(job_id: str, user: dict = Depends(get_current_user)):
    job = gerenciador.obter(job_id)
    if not job:
        raise HTTPException(404, "Job nao encontrado.")
    if job.uid != user["uid"]:
        raise HTTPException(403, "Acesso negado a este job.")
    return job


@app.get("/api/documentos/{nome}")
def baixar_documento(nome: str, user: dict = Depends(get_current_user)):
    nome_seguro = os.path.basename(nome)
    caminho = os.path.join(settings.STORAGE_DIR, nome_seguro)
    if not os.path.exists(caminho):
        raise HTTPException(404, "Documento nao encontrado ou expirado.")
    return FileResponse(caminho, media_type="application/pdf", filename=nome_seguro)


@app.get("/api/creditos/saldo")
def saldo_creditos(user: dict = Depends(get_current_user)):
    saldo = obter_saldo(user["uid"])
    historico = obter_historico(user["uid"], limite=20)
    return {"saldo": saldo, "custo_por_consulta": CUSTO_POR_CONSULTA, "historico": historico}


@app.get("/api/creditos/historico")
def historico_creditos(user: dict = Depends(get_current_user)):
    transacoes = obter_historico(user["uid"])
    return {"transacoes": transacoes}
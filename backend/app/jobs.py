"""Gerenciador de jobs com persistencia no Firestore.

Um job agrupa uma ou varias consultas marcadas pelo cliente. Cada job roda
numa thread, processando as consultas em sequencia e atualizando o status.

Estado do job e persistido em `jobs/{jobId}` no Firestore e tambem na subcolecao
`users/{uid}/consultas/{jobId}`. Um cache em memoria garante leitura rapida
para o polling do frontend. Se o processo reiniciar, o cache volta a ser
preenchido sob demanda a partir do Firestore.

Projetado para ser trocado por Redis/RQ/Celery sem mudar a API: basta
reimplementar `criar`, `obter` e o disparo de `_processar`.
"""

import threading
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app import runner, settings
from app.catalog import obter as obter_consulta
from app.schemas import (
    Job, ItemJob, StatusJob, StatusItem, StatusResultado, ConsultaSelecionada,
)

logger = logging.getLogger(__name__)


def _db():
    from app.firebase_admin import init_firebase
    from firebase_admin import firestore
    init_firebase()
    return firestore.client()


def _now():
    return datetime.now(timezone.utc)


class GerenciadorJobs:
    def __init__(self, max_workers: int = 2):
        self._cache: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=max_workers)

    def criar(self, consultas: list[ConsultaSelecionada], parametros: dict, uid: str = "") -> Job:
        job_id = uuid.uuid4().hex
        itens = []
        for sel in consultas:
            c = obter_consulta(sel.slug)
            itens.append(ItemJob(
                slug=sel.slug,
                titulo=c.titulo if c else sel.slug,
            ))
        job = Job(
            job_id=job_id,
            uid=uid,
            itens=itens,
            parametros=parametros,
            criado_em=_now(),
            atualizado_em=_now(),
        )

        with self._lock:
            self._cache[job_id] = job

        self._persistir(job)

        self._pool.submit(self._processar, job_id, consultas, parametros)
        return job

    def obter(self, job_id: str) -> Job | None:
        with self._lock:
            if job_id in self._cache:
                return self._cache[job_id]

        # Se nao estiver no cache, tenta carregar do Firestore
        job = self._carregar_do_firestore(job_id)
        if job:
            with self._lock:
                self._cache[job_id] = job
        return job

    def _atualizar(self, job_id: str):
        with self._lock:
            job = self._cache.get(job_id)
            if job:
                job.atualizado_em = _now()

    def _processar(self, job_id: str, consultas: list[ConsultaSelecionada], globais: dict):
        job = self.obter(job_id)
        if not job:
            return

        job.status = StatusJob.PROCESSANDO
        self._atualizar(job_id)
        self._persistir(job)

        for item, sel in zip(job.itens, consultas):
            item.status = StatusItem.PROCESSANDO
            self._atualizar(job_id)
            self._persistir(job)

            params = {**globais, **sel.parametros}
            resultado = runner.executar(sel.slug, params)

            item.resultado = resultado
            item.status = (
                StatusItem.ERRO
                if resultado.status == StatusResultado.ERRO
                else StatusItem.OK
            )
            self._atualizar(job_id)
            self._persistir(job)

        houve_ok = any(i.status == StatusItem.OK for i in job.itens)
        houve_erro = any(i.status == StatusItem.ERRO for i in job.itens)
        if houve_ok and houve_erro:
            job.status = StatusJob.CONCLUIDO_PARCIAL
        elif houve_ok:
            job.status = StatusJob.CONCLUIDO
        else:
            job.status = StatusJob.ERRO
        self._atualizar(job_id)
        self._persistir(job)

    def _persistir(self, job: Job):
        try:
            db = _db()
            data = self._job_to_dict(job)

            db.collection("jobs").document(job.job_id).set(data)

            if job.uid:
                db.collection("users").document(job.uid).collection("consultas").document(job.job_id).set({
                    "slug": ",".join(item.slug for item in job.itens),
                    "titulo": ",".join(item.titulo for item in job.itens),
                    "status": job.status.value,
                    "totalItens": len(job.itens),
                    "parametros": job.parametros,
                    "createdAt": job.criado_em,
                    "updatedAt": job.atualizado_em,
                })
        except Exception as e:
            logger.warning(f"[jobs] Falha ao persistir job {job.job_id}: {e}")

    def _carregar_do_firestore(self, job_id: str) -> Job | None:
        try:
            db = _db()
            doc = db.collection("jobs").document(job_id).get()
            if not doc.exists:
                return None
            return self._dict_to_job(doc.id, doc.to_dict())
        except Exception as e:
            logger.warning(f"[jobs] Falha ao carregar job {job_id}: {e}")
            return None

    @staticmethod
    def _job_to_dict(job: Job) -> dict:
        return {
            "jobId": job.job_id,
            "uid": job.uid,
            "status": job.status.value,
            "itens": [item.model_dump(mode="json") for item in job.itens],
            "parametros": job.parametros,
            "criadoEm": job.criado_em,
            "atualizadoEm": job.atualizado_em,
        }

    @staticmethod
    def _dict_to_job(job_id: str, data: dict) -> Job:
        itens = [ItemJob(**item) for item in data.get("itens", [])]
        return Job(
            job_id=job_id,
            uid=data.get("uid", ""),
            status=StatusJob(data.get("status", "fila")),
            criado_em=data.get("criadoEm", _now()),
            atualizado_em=data.get("atualizadoEm", _now()),
            itens=itens,
            parametros=data.get("parametros", {}),
        )


gerenciador = GerenciadorJobs(max_workers=settings.MAX_WORKERS)
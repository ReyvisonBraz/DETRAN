"""Gerenciador de jobs em memoria.

Um job agrupa uma ou varias consultas marcadas pelo cliente. Cada job roda
numa thread, processando as consultas em sequencia e atualizando o status.
O frontend cria o job, recebe o job_id e faz polling do status.

Projetado para ser trocado por Redis/RQ/Celery sem mudar a API: basta
reimplementar `criar`, `obter` e o disparo de `_processar`.
"""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from app import runner, settings
from app.catalog import obter as obter_consulta
from app.schemas import (
    Job, ItemJob, StatusJob, StatusItem, StatusResultado, ConsultaSelecionada,
)


class GerenciadorJobs:
    def __init__(self, max_workers: int = 2):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=max_workers)

    def criar(self, consultas: list[ConsultaSelecionada], parametros: dict) -> Job:
        job_id = uuid.uuid4().hex
        itens = []
        for sel in consultas:
            c = obter_consulta(sel.slug)
            itens.append(ItemJob(
                slug=sel.slug,
                titulo=c.titulo if c else sel.slug,
            ))
        job = Job(job_id=job_id, itens=itens, parametros=parametros)
        with self._lock:
            self._jobs[job_id] = job
        self._pool.submit(self._processar, job_id, consultas, parametros)
        return job

    def obter(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _atualizar(self, job_id: str):
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.atualizado_em = datetime.utcnow()

    def _processar(self, job_id: str, consultas: list[ConsultaSelecionada], globais: dict):
        job = self.obter(job_id)
        if not job:
            return
        job.status = StatusJob.PROCESSANDO
        self._atualizar(job_id)

        for item, sel in zip(job.itens, consultas):
            item.status = StatusItem.PROCESSANDO
            self._atualizar(job_id)

            # Parametros do item sobrescrevem os globais do job
            params = {**globais, **sel.parametros}
            resultado = runner.executar(sel.slug, params)

            item.resultado = resultado
            item.status = (
                StatusItem.ERRO
                if resultado.status == StatusResultado.ERRO
                else StatusItem.OK
            )
            self._atualizar(job_id)

        # Status final do job
        houve_ok = any(i.status == StatusItem.OK for i in job.itens)
        houve_erro = any(i.status == StatusItem.ERRO for i in job.itens)
        if houve_ok and houve_erro:
            job.status = StatusJob.CONCLUIDO_PARCIAL
        elif houve_ok:
            job.status = StatusJob.CONCLUIDO
        else:
            job.status = StatusJob.ERRO
        self._atualizar(job_id)


gerenciador = GerenciadorJobs(max_workers=settings.MAX_WORKERS)

# DETRAN-PA Consultas — Backend (API)

Motor de consultas do DETRAN-PA exposto como API HTTP, com execucao
**assincrona** (jobs) para suportar consultas em lote sem estourar limite de
tempo. Reaproveita 100% do motor de scraping em `../detran-pa-consultas`.

## Por que um backend separado (e nao tudo no Vercel)

As consultas resolvem CAPTCHA via 2Captcha (20–60s) e mantem sessao JSF
persistente. Isso estoura o limite de tempo das funcoes serverless do Vercel.
Solucao profissional:

- **Frontend (Next.js)** -> Vercel (gratis).
- **Este backend (FastAPI)** -> servico sempre-ligado (Render / Fly.io / Koyeb
  / Oracle Cloud Always Free / VPS). Docker puro, sem amarras de plataforma.
- Cliente cria um **job**, recebe `job_id`, e o painel faz *polling* do status.

## Arquitetura

```
Catalogo (catalog.py) ── descreve cada consulta p/ o frontend e o runner
   │
Frontend ──POST /api/jobs──► Jobs (jobs.py) ──► Runner (runner.py) ──► Motor
   ▲                              │                    │             (detran-pa-consultas)
   └────GET /api/jobs/{id}────────┘            normaliza p/ ResultadoConsulta
        (polling de status)                    (schemas.py): dados, PDF, erro
```

## Endpoints

| Metodo | Rota | Funcao |
|--------|------|--------|
| GET | `/api/consultas` | Catalogo: o frontend monta a selecao e os formularios |
| POST | `/api/jobs` | Dispara 1+ consultas (lote). Retorna `job_id` |
| GET | `/api/jobs/{job_id}` | Status + resultados (polling) |
| GET | `/api/documentos/{nome}` | Download do PDF/boleto gerado |
| GET | `/healthz` | Healthcheck |

### Exemplo: criar job em lote

```json
POST /api/jobs
{
  "parametros": { "placa": "OFS3J55", "renavam": "00477026001" },
  "consultas": [
    { "slug": "veiculo_detalhada" },
    { "slug": "infracoes" },
    { "slug": "licenciamento_atual" }
  ]
}
```

Os `parametros` do job sao comuns a todas; cada item pode sobrescrever com
`parametros` proprios.

### Envelope de resultado (sempre o mesmo formato)

Toda consulta — com sucesso ou erro — volta como `ResultadoConsulta`:
`status` (ok/parcial/sem_dados/erro), `dados`, `secoes`, `tabelas`,
`documentos` (PDFs) e `erro` (tipo + mensagem amigavel + se e retentavel).
Isso permite ao frontend renderizar resultado completo, parcial ou erro de
forma unica.

## Rodar localmente

```bash
cd backend
pip install -r requirements.txt
export TWOCAPTCHA_API_KEY=sua_chave   # Windows: $env:TWOCAPTCHA_API_KEY="..."
uvicorn app.main:app --reload --port 8000
```

Docs interativas: http://localhost:8000/docs

## Variaveis de ambiente

Veja `.env.example`. A principal e `TWOCAPTCHA_API_KEY` (sem ela, as consultas
falham com erro de CAPTCHA — comportamento ja testado e tratado).

## Deploy (Docker)

O `Dockerfile` esta na raiz do backend e copia tambem o motor. Build a partir
da **raiz do repositorio**:

```bash
docker build -f backend/Dockerfile -t detran-api .
docker run -p 8000:8000 -e TWOCAPTCHA_API_KEY=xxx detran-api
```

Em Render/Fly/Koyeb: aponte para `backend/Dockerfile`, defina
`TWOCAPTCHA_API_KEY` e `CORS_ORIGINS` (URL do painel no Vercel).

## Status atual / proximos passos

- [x] Catalogo de 9 consultas com metadados (descricao, campos, PDF, creditos)
- [x] Execucao assincrona em lote com status por item
- [x] Envelope normalizado de resultado + classificacao de erros
- [x] Download de PDF/boleto
- [ ] Persistencia de jobs (hoje em memoria; trocar por Redis/banco)
- [ ] Frontend Next.js (painel do cliente)
- [ ] Login + creditos (fase futura)
```

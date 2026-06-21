# Notas do Codex GPT-5 sobre o projeto DETRAN

Data da anotacao: 2026-06-21
IA usada: Codex, baseado em GPT-5

## Visao geral

Este repositorio parece ser uma plataforma de consultas DETRAN-PA em formato
monorepo. A ideia central e oferecer um painel web onde o usuario seleciona
consultas, informa dados como placa, Renavam, chassi ou CPF, e acompanha a
execucao assincrona dessas consultas.

O sistema esta dividido em tres partes principais:

- `frontend/`: painel web em Next.js 14, React e TypeScript.
- `backend/`: API em FastAPI responsavel por catalogo, jobs e documentos.
- `detran-pa-consultas/`: motor de scraping/automacao usado pelo backend.

Tambem existem documentacao, configuracao de deploy e uma pasta `DETRAN/` que
parece conter uma copia parcial ou antiga de arquivos do projeto.

## Frontend

O frontend fica em `frontend/`.

Tecnologias identificadas:

- Next.js 14 com App Router.
- React 18.
- TypeScript.
- Firebase no client.
- Manifest/PWA e service worker.

Rotas/paginas observadas:

- `/`: selecao de consultas.
- `/resultado/[jobId]`: acompanhamento do resultado de um job.
- Rotas de autenticacao em `app/(auth)`.
- Rotas autenticadas em `app/(app)`, incluindo dashboard, consultas,
  historico, creditos, perfil e suporte.

O frontend monta a tela de consultas a partir de `GET /api/consultas`, ou seja,
o catalogo do backend e a fonte principal para titulos, descricoes, campos,
creditos e indicacao de PDF/boleto.

## Backend

O backend fica em `backend/`.

Tecnologias identificadas:

- FastAPI.
- Uvicorn.
- Pydantic.
- Requests, BeautifulSoup e lxml.
- 2Captcha.
- fpdf2.

Endpoints principais identificados:

- `GET /healthz`: healthcheck.
- `GET /api/consultas`: lista o catalogo de consultas.
- `POST /api/jobs`: cria um job com uma ou mais consultas.
- `GET /api/jobs/{job_id}`: retorna status e resultados do job.
- `GET /api/documentos/{nome}`: baixa PDF/boleto gerado.

O gerenciador de jobs atual usa memoria local e `ThreadPoolExecutor`. Isso
significa que os jobs nao persistem se o processo reiniciar. A propria
documentacao aponta Redis, banco ou fila como evolucao futura.

## Catalogo de consultas

O arquivo `backend/app/catalog.py` e a fonte unica de verdade do produto.

Consultas encontradas:

- `veiculo_detalhada`: consulta detalhada de veiculo.
- `infracoes`: multas/infracoes.
- `licenciamento_atual`: boleto de licenciamento do ano atual.
- `licenciamento_anterior`: boleto de licenciamento de anos anteriores.
- `boleto_infracao`: boleto para pagamento de multa.
- `gravame`: consulta de gravame por chassi.
- `crlv_e`: emissao de CRLV-e.
- `acompanha_documento`: acompanhamento de documento/processo.
- `cnh_pontuacao`: pontuacao de CNH por CPF.

Cada consulta define slug, titulo, descricao, categoria, sistema, handler,
campos de entrada, se gera PDF/boleto, creditos e tempo estimado.

## Motor de consultas

O motor fica em `detran-pa-consultas/`.

Arquivos/pacotes relevantes:

- `services/sistransito.py`
- `services/renach.py`
- `services/jsf_session.py`
- `services/captcha_solver.py`
- `parsers/sistransito_parser.py`
- `parsers/renach_parser.py`
- `main.py`
- `config.py`

Esse motor parece lidar com sessao JSF, scraping dos sistemas do DETRAN-PA e
resolucao de CAPTCHA via 2Captcha.

## Documentacao e direcao planejada

O arquivo `docs/ARQUITETURA.md` descreve uma evolucao para SaaS com:

- Firebase Auth.
- Firestore.
- Perfil de usuario.
- Historico de consultas.
- Sistema de creditos.
- Recarga via Mercado Pago, incluindo PIX.
- Painel admin.
- Webhook de pagamento.
- Regras de seguranca Firestore.

Modelo planejado no Firestore:

- `users/{uid}`
- `transacoes/{tid}`
- `jobs/{jobId}`
- `pagamentos/{pid}`
- `admin_config/{configId}`

## Deploy

Existe `render.yaml` na raiz configurando deploy do backend no Render:

- Servico web chamado `detran-api`.
- Runtime Docker.
- Dockerfile em `./backend/Dockerfile`.
- Contexto Docker na raiz do repositorio.
- Healthcheck em `/healthz`.
- Variaveis esperadas:
  - `TWOCAPTCHA_API_KEY`
  - `CORS_ORIGINS`
  - `MAX_WORKERS`

O README do backend sugere frontend no Vercel e backend em Render, Fly.io,
Koyeb, Oracle Cloud Always Free ou VPS.

## Estado observado do repositorio

No momento da inspecao:

- Branch git: `main`, rastreando `origin/main`.
- Havia uma alteracao local em
  `detran-pa-consultas/services/captcha_solver.py`.
- Nao foram executados testes.
- Nao foram feitas alteracoes no codigo existente durante a inspecao inicial.

## Pontos de atencao

- A pasta `DETRAN/` dentro da raiz parece conter arquivos duplicados ou uma
  versao parcial do projeto. Vale confirmar se ela ainda e necessaria.
- O backend ainda usa jobs em memoria; isso e simples para MVP, mas fragil em
  producao.
- A autenticacao, historico, creditos, pagamentos e painel admin parecem estar
  documentados/planejados, mas devem ser conferidos no codigo antes de assumir
  que estao completos.
- Consultas dependem de CAPTCHA e servicos externos, entao testes reais podem
  depender de `TWOCAPTCHA_API_KEY` e disponibilidade dos sistemas do DETRAN-PA.

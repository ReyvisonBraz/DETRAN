# DETRAN-PA — Conhecimento do Projeto (visão da IA)

> **Autor:** Claude Code · **IA usada:** Claude Opus 4.8 (`claude-opus-4-8`)
> Documento gerado em 2026-06-21. Resumo do que se sabe sobre o projeto, sua
> arquitetura, estado e detalhes técnicos não óbvios. Verifique contra o código
> atual antes de tratar qualquer item como verdade definitiva.

## O que é

SaaS web de **consultas veiculares do DETRAN-PA** (sistemas SISTRANSITO/RENACH).
Transforma o motor de scraping `detran-pa-consultas/` (Python: `requests` +
`BeautifulSoup` + `2Captcha`) num produto web com login, créditos e histórico.

## Arquitetura (decidida em jun/2026)

- **Frontend** (`frontend/`) — Next.js (App Router), hospedado no Vercel.
  PWA instalável (manifest + service worker + ícones).
- **Backend** (`backend/`) — FastAPI separado, em serviço sempre-ligado
  (Render/Fly/Koyeb/Oracle Always Free/VPS).
  - **Por quê separado:** resolver reCAPTCHA (20–60s) + sessão JSF estoura o
    timeout serverless do Vercel. Separar também mantém IP estável (evita
    bloqueio do DETRAN).
  - Execução **assíncrona via jobs com polling**.
- **Motor de scraping** (`detran-pa-consultas/`) — scraper original reaproveitado
  pelo backend via `backend/app/engine_bridge.py`.
- **Auth e dados:** Firebase — login Google, Firestore (`firestore.rules`),
  Storage para PDFs.

## Componentes principais

### Backend (`backend/app/`)
- `main.py` — app FastAPI.
- `catalog.py` — catálogo de consultas disponíveis.
- `jobs.py` — gestão de jobs assíncronos.
- `runner.py` — execução das consultas.
- `engine_bridge.py` — ponte para o motor `detran-pa-consultas/`.
- `pdf_generator.py` — gera comprovante PDF (fpdf2) para consultas sem PDF nativo.
- `schemas.py`, `settings.py`, `firebase_storage.py`.

### Motor (`detran-pa-consultas/`)
- `services/jsf_session.py` — sessão JSF (stateful).
- `services/sistransito.py`, `services/renach.py` — fluxos de consulta.
- `services/captcha_solver.py` — resolução de captcha (mCaptcha/2Captcha).
- `parsers/sistransito_parser.py`, `parsers/renach_parser.py`.

### Frontend (`frontend/app/`)
- Rotas: dashboard, consultas, créditos, histórico, perfil, suporte, login,
  completar cadastro, resultado/[jobId].
- Componentes: Onboarding, FeedbackWidget, Toast.
- `lib/`: api, auth, firebase, types. `middleware.ts` para proteção de rotas.

## Funcionalidades já implementadas

Login Google, créditos, onboarding, histórico, feedback, estorno automático,
perfil, regras Firestore, Firebase Storage de PDFs, validação de captcha (mCaptcha).

## Status de testes reais (chave 2Captcha validada)

- ✅ `veiculo_detalhada` — OK (38 campos reais).
- ✅ `infracoes` — OK (parser precisa polir rótulos colando).
- ✅ `licenciamento_atual` — OK com PDF REAL de boleto (~434KB).
- ⚠️ `cnh_pontuacao` — retorna "Aguarde...Processando" → RENACH precisa de etapa
  de follow-up (igual o boleto precisou).

> A chave 2Captcha **não** é guardada — pedir ao usuário quando for testar.

## Descobertas técnicas não óbvias (já corrigidas)

1. **Encoding:** páginas são UTF-8 (NÃO latin-1); `requests` às vezes erra →
   forçar `resp.encoding='utf-8'`. Acentos vêm como bytes UTF-8 e/ou entidades
   HTML (`&iacute;`).
2. **Títulos de seção** têm glifos material-icons colados → `decompose` em
   `i.material-icons` no soup.
3. **Form de licenciamento** usa campos SEM prefixo (`placa1`/`renavam`/`confirma`),
   diferente do veículo (`indexRenavam:placa1`).
4. **Boleto de licenciamento** = fluxo de 4 POSTs:
   GET → placa+renavam+captcha (orçamento/Total) → `:segundaVia` (Linha Digitável)
   → `:gerarBoleto` "Salvar Boleto" (PDF real).
5. **Consultas sem PDF nativo** ganham comprovante via fpdf2
   (`backend/app/pdf_generator.py`); fpdf2 2.8 exige `multi_cell` com largura
   explícita + `XPos`/`YPos`.

## Infra / arquivos de deploy

- `render.yaml` — deploy do backend.
- `firebase.json`, `firestore.rules`, `firestore.indexes.json`.
- `backend/Dockerfile`, `backend/.env.example`, `frontend/.env.example`.

## Pontos de atenção

- Existe uma pasta **`DETRAN/` aninhada** na raiz com arquivos duplicados/parciais
  (`DETRAN/frontend/...`, `DETRAN/backend/...`). Pode ser commit acidental —
  verificar se é lixo a remover.
- Arquivo modificado não commitado no último snapshot:
  `detran-pa-consultas/services/captcha_solver.py`.

## Documentação relacionada no repo

- `DETRAN-PA-ANALISE.md`
- `docs/ARQUITETURA.md`
- `backend/README.md`, `frontend/README.md`

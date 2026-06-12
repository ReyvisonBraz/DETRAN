# DETRAN-PA Consultas — Painel (Frontend)

Painel do cliente em Next.js (App Router). Consome a API do `../backend`.
Deploy no **Vercel** (gratis).

## Telas

- **/** — selecao de consultas: cards do catalogo agrupados por categoria,
  multi-selecao (lote) e formulario dinamico (so pede os campos que as
  consultas marcadas exigem). Mostra creditos e quais geram PDF.
- **/resultado/[jobId]** — acompanha o job em tempo real (polling): cada
  consulta aparece como fila → processando → concluido/erro, com dados,
  tabelas, PDFs para download e erros amigaveis.

## Rodar localmente

```bash
cd frontend
npm install
cp .env.example .env.local   # ajuste NEXT_PUBLIC_API_URL
npm run dev
```

Abra http://localhost:3000 (com o backend rodando em :8000).

## Deploy no Vercel

1. Importe a pasta `frontend/` como projeto no Vercel.
2. Defina a env `NEXT_PUBLIC_API_URL` = URL publica do backend.
3. No backend, inclua o dominio do Vercel em `CORS_ORIGINS`.

## Como o frontend e dirigido pelo catalogo

Nada de consulta fica hardcoded aqui: a tela e montada a partir de
`GET /api/consultas`. Para adicionar/editar uma consulta, mexa so no
`backend/app/catalog.py` — o painel se ajusta sozinho (titulo, descricao,
campos do formulario, badge de PDF, creditos).

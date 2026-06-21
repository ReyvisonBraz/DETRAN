# PLANO DE EXECUÇÃO — DETRAN-PA Consultas

> Ultima atualizacao: 21/06/2026
> Autor: GLM-5.1 (sintese das 3 IAs)
> Status: APOS LIMPEZA DO REPO — pronto para executar

---

## Estado Atual (pos-limpeza)

### O que FUNCIONA
- Motor de scraping: 9 consultas (8 SISTRANSITO + 1 RENACH)
- Backend FastAPI: endpoints protegidos (auth Firebase, deducao de creditos)
- Frontend: login Google, completar perfil, dashboard, consultas, resultado
- Sistema de creditos: deducao atomica via Firestore Transaction
- Auth backend: Firebase ID Token middleware (Depends(get_current_user))
- API client: envia Bearer token do Firebase Auth
- Firebase Auth + Firestore: login, perfil, historico, feedbacks, refund, transacoes
- PWA: manifest, service worker, icones
- PDFs: geracao local (fpdf2) + upload Firebase Storage (fallback local)
- Componentes: Onboarding, FeedbackWidget, Toast

### O que NAO EXISTE (precisa implementar)
- Testar as 9 consultas com 2Captcha key valida
- Persistencia de jobs em Firestore (atual: em memoria)
- Integracao Mercado Pago (PIX + cartao)
- Pagina de pagamento com QR Code
- Pagina de suporte (stub)
- Painel admin (nao existe)

### O que foi LIMPO
- [x] Pasta `DETRAN/` duplicada removida (arquivos uteis mesclados para o root)
- [x] Arquivos de decisao duplicados removidos (mantido so DECISAO-DEFINITIVA.md)
- [x] `.env` com API key exposta removido do motor
- [x] `__pycache__/` e `.next/` cache removidos
- [x] PDFs de teste do storage removidos

---

## FASE 1 — Estabilizar o que existe (SEM auth/creditos) ✅ CONCLUÍDA

- [x] 1.1 `.env` do motor recriado (sem key)
- [x] 1.2 CAPTCHA identificado (mCaptcha local, Image via 2Captcha, reCAPTCHA v2 removido)
- [x] 1.3 JSP IDs dinamicos (fallback hardcoded)
- [x] 1.4 Encoding UTF-8 forçado, material-icons removidos, fluxo 4-POSTs

> **Nota:** Testar as 9 consultas com 2Captcha key ainda pendente (FASE 1.2 parcial)

---

## FASE 2 — Auth e protecao ✅ CONCLUÍDA

- [x] 2.1 Backend: `auth.py` com `get_current_user` (Firebase ID Token)
- [x] 2.2 Backend: `firebase_admin.py` centralizado (auth + storage)
- [x] 2.3 Frontend: `api.ts` envia `Authorization: Bearer <token>` automaticamente
- [x] 2.4 Rotas protegidas: `/api/jobs`, `/api/creditos/*`, `/api/documentos/*`
- [x] 2.5 Rota publica: `/api/consultas`, `/healthz`

---

## FASE 3 — Sistema de creditos ✅ CONCLUÍDA

- [x] 3.1 Backend: `creditos.py` com `deduzir_creditos`, `adicionar_creditos` (Firestore Transaction)
- [x] 3.2 Backend: `POST /api/jobs` verifica saldo e deduz atomicamente (HTTP 402 se insuficiente)
- [x] 3.3 Backend: `GET /api/creditos/saldo` e `GET /api/creditos/historico`
- [x] 3.4 Frontend: `api.ts` com `obterSaldo()` e `obterHistoricoCreditos()`
- [x] 3.5 Firestore rules: `transacoes` collection (user so le, service account escreve)
- [x] 3.6 Firestore indexes: `transacoes` por `uid ASC + createdAt DESC`

---

## FASE 4 — Pagamentos (Mercado Pago)

Objetivo: Usuarios podem comprar creditos via PIX.

### 4.1 Backend: integracao Mercado Pago
- Criar `backend/app/pagamentos.py`
- `POST /api/creditos/recarga`: cria cobranca PIX via SDK do Mercado Pago
- `GET /api/creditos/recarga/{pid}/status`: polling de status
- `POST /api/creditos/webhook/mercado-pago`: webhook de confirmacao
- Adicionar `mercadopago` ao requirements.txt

### 4.2 Frontend: pagina de pagamento
- `creditos/recarga/[pid]/page.tsx`: exibe QR Code PIX + copia e cola
- Polling a cada 3s para verificar confirmacao
- Apos confirmacao: redirecionar para dashboard com toast de sucesso

### 4.3 Backend: webhook de confirmacao
- Validar assinatura do webhook
- Em transaction: atualizar pagamento para "pago", creditar creditos no user, criar transacao
- Idempotencia via `gatewayId` do Mercado Pago

---

## FASE 5 — Painel Admin

Objetivo: Admin pode ver metricas, gerenciar usuarios e creditos.

### 5.1 Backend: rotas admin
- Criar `backend/app/admin_routes.py`
- `GET /api/admin/dashboard`: metricas gerais
- `GET /api/admin/users`: lista usuarios
- `POST /api/admin/users/{uid}/creditos`: creditar/descontar manualmente
- `PATCH /api/admin/users/{uid}/role`: promover/rebaixar role
- Todas protegidas por `role == "admin"`

### 5.2 Frontend: layout admin
- `(admin)/layout.tsx`: layout dedicado com sidebar de admin
- `(admin)/dashboard/page.tsx`: metricas (usuarios, consultas, receita)
- `(admin)/users/page.tsx`: lista de usuarios com filtros
- `(admin)/users/[uid]/page.tsx`: detalhes do usuario + acoes

### 5.3 Firestore security rules
- Ja temos `firestore.rules` basico (users so leem/escrevem o proprio doc)
- Expandir para incluir `transacoes`, `pagamentos`, `admin_config`
- Deploy via `firebase deploy --only firestore`

---

## FASE 6 — Polish + Deploy

### 6.1 Rate limiting
- Rate limiting por usuario: max 3 consultas/minuto (configuravel em admin_config)
- Implementar no backend com middleware

### 6.2 Variaveis de ambiente
- Documentar todas as env vars em `.env.example` (frontend e backend)
- Configurar no Render (backend) e Vercel (frontend)

### 6.3 Deploy
- **Frontend:** Vercel (conectado ao repo, `cd frontend && npm run build`)
- **Backend:** Render (Docker, `render.yaml` ja existe)
- **Firebase:** `firebase deploy --only firestore`

### 6.4 Monitoramento
- Logs do backend no Render
- Firebase Auth + Firestore no console Firebase
- Error tracking basico (console.error com contexto)

---

## Sobre o uso de IA com navegador para o scraper

### Por que precisamos
O scraper faz POSTs em sistemas JSF do DETRAN-PA. Para validar que tudo funciona, precisamos:
1. Fazer GET na pagina de consulta → capturar JSESSIONID + ViewState
2. Resolver CAPTCHA (mCaptcha é local, reCAPTCHA/Image CAPTCHA via 2Captcha)
3. Fazer POST com os dados → parsear resultado HTML

### O que a IA com navegador faria
- Abrir cada URL de consulta no navegador
- Confirmar que a pagina carrega e tem os campos esperados
- Validar o fluxo JSF (campos, ViewState, form action)
- Se um scraper falhar, investigar com inspecao visual do HTML retornado
- Testar edge cases: placa invalida, renavam invalido, sessao expirada

### 2Captcha
- **mCaptcha:** Resolvido localmente (Proof-of-Work), sem custo
- **Image CAPTCHA (RENACH):** Resolvido via 2Captcha (~5-15s, ~$0.001/imagem)
- **Custo estimado:** ~$0.001 por consulta (mCaptcha gratis) + ~$0.001 (image CAPTCHA para CNH)
- **reCAPTCHA v2:** REMOVIDO do site (sitekey morto), nao e mais necessario
- **API key:** Substituir no `.env` do motor antes de testar

### Ordem de teste recomendada
1. Rodar o motor standalone (`python main.py`) com uma chave 2Captcha valida
2. Testar cada consulta em ordem (veiculo_detalhada primeiro)
3. Se falhar, usar IA com navegador para investigar o HTML retornado
4. Ajustar parser ou fluxo JSF conforme necessario
5. Repetir ate todas as 9 consultas passarem

---

## Checklist resumido

- [x] FASE 1.1: `.env` do motor recriado sem key exposta
- [ ] FASE 1.2: Testar todas as 9 consultas com 2Captcha key
- [ ] FASE 1.3: Persistir jobs em Firestore
- [x] FASE 1.4: Bugs do motor corrigidos (encoding, JSF IDs dinamicos, mCaptcha)
- [x] FASE 2.1: Middleware auth no backend (Firebase ID Token)
- [x] FASE 2.2: API client com Bearer token
- [x] FASE 2.3: Rotas protegidas (jobs, creditos, documentos)
- [ ] FASE 2.4: Pagina de suporte (stub com WhatsApp)
- [x] FASE 3.1: Deducao de creditos ao criar job (Firestore Transaction)
- [x] FASE 3.2: Endpoints de saldo e historico
- [x] FASE 3.3: API client conectada (obterSaldo, obterHistoricoCreditos)
- [x] FASE 3.4: Bonus de cadastro (2 creditos, confirmado)
- [ ] FASE 4.1: Integracao Mercado Pago (PIX)
- [ ] FASE 4.2: Pagina de pagamento com QR Code
- [ ] FASE 4.3: Webhook de confirmacao
- [ ] FASE 5.1: Rotas admin no backend
- [ ] FASE 5.2: Layout e paginas admin no frontend
- [ ] FASE 5.3: Firestore security rules completas (ja temos: users, transacoes, feedbacks, refunds)
- [ ] FASE 6.1: Rate limiting
- [ ] FASE 6.2: Documentar variaveis de ambiente
- [ ] FASE 6.3: Deploy (Vercel + Render + Firebase)
- [ ] FASE 6.4: Monitoramento basico
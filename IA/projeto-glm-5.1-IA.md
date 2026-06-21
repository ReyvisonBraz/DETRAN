# DETRAN-PA Consultas — Documento de Contexto da IA

> Última atualização: 21/06/2026

---

## 1. Visão Geral

Plataforma SaaS para consultas veiculares e de CNH do DETRAN-PA, transformando o sistema atual (aberto, sem auth, sem persistência) numa plataforma paga com créditos e autenticação.

**Objetivo:** Permitir que usuários comprem créditos e realizem consultas automatizadas nos sistemas do DETRAN-PA (que exigem resolução de CAPTCHA e navegação JSF).

---

## 2. Arquitetura

```
[ Frontend Next.js 14 (Vercel) ]
        │
        │  API REST (JSON)
        ▼
[ Backend FastAPI (Render/Fly/Koyeb) ]
        │
        ├── Motor de scraping (detran-pa-consultas)
        │     ├── Resolve CAPTCHA via 2Captcha API
        │     └── Navega JSF (JSESSIONID + ViewState)
        │
        └── Firebase Admin SDK
              ├── Auth (valida ID Token)
              └── Firestore (users, jobs, transações, pagamentos)
```

---

## 3. Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Firebase SDK |
| Backend | FastAPI (Python 3.11), Uvicorn |
| Banco de dados | Firestore (Firebase) |
| Autenticação | Firebase Auth (Google) |
| Pagamentos | Mercado Pago (PIX + cartão) |
| CAPTCHA | 2Captcha API |
| Deploy Frontend | Vercel |
| Deploy Backend | Docker (Render/Fly/Koyeb) |

---

## 4. Backend — Estrutura

```
backend/
├── app/
│   ├── main.py            # FastAPI app, CORS, rotas
│   ├── catalog.py          # Catálogo de 9 consultas com metadados
│   ├── engine_bridge.py    # Ponte para o motor detran-pa-consultas
│   ├── jobs.py             # Criação e gerenciamento de jobs
│   ├── runner.py           # Execução assíncrona de consultas
│   ├── schemas.py          # Modelos Pydantic (ResultadoConsulta, etc.)
│   ├── pdf_generator.py    # Geração de PDFs/boletos
│   ├── settings.py         # Configurações via env vars
│   ├── auth.py             # (PLANEJADO) Validação Firebase ID Token
│   ├── deps.py             # (PLANEJADO) get_current_user dependency
│   ├── creditos.py         # (PLANEJADO) Saldo, extrato, desconto
│   ├── pagamentos.py       # (PLANEJADO) Integração Mercado Pago
│   └── admin_routes.py     # (PLANEJADO) Rotas admin
├── storage/                # PDFs gerados
├── Dockerfile
├── requirements.txt
└── README.md
```

### Endpoints Atuais

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/api/consultas` | — | Catálogo de consultas |
| POST | `/api/jobs` | — | Criar job (lote de consultas) |
| GET | `/api/jobs/{job_id}` | — | Status + resultados |
| GET | `/api/documentos/{nome}` | — | Download PDF/boleto |
| GET | `/healthz` | — | Healthcheck |

### Endpoints Planejados

- Auth: `/api/auth/google`, `/api/auth/completar-perfil`, `/api/auth/me`
- Créditos: `/api/creditos/saldo`, `/api/creditos/extrato`, `/api/creditos/recarga`
- Admin: `/api/admin/dashboard`, `/api/admin/users`, etc.

---

## 5. Frontend — Estrutura

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx       # Login Google
│   │   ├── completar/page.tsx    # Completar nome/sobrenome
│   │   └── layout.tsx            # Layout sem sidebar
│   ├── resultado/
│   │   └── [jobId]/page.tsx      # Resultado da consulta
│   ├── page.tsx                  # Página principal (consulta)
│   ├── layout.tsx                # Layout raiz
│   ├── globals.css
│   └── register-sw.tsx           # Service Worker (PWA)
├── lib/
│   ├── firebase.ts              # Firebase client config
│   ├── auth.tsx                  # AuthContext + hooks
│   ├── api.ts                    # API client
│   └── types.ts                  # Tipos TypeScript
├── public/
│   ├── manifest.webmanifest      # PWA manifest
│   ├── sw.js                     # Service Worker
│   ├── icon-192.png
│   └── icon-512.png
└── package.json
```

### Páginas Planejadas (não implementadas)

```
app/
├── (app)/
│   ├── dashboard/page.tsx
│   ├── consultas/page.tsx
│   ├── consultas/[jobId]/page.tsx
│   ├── historico/page.tsx
│   ├── creditos/page.tsx
│   ├── creditos/recarga/[pid]/page.tsx
│   ├── perfil/page.tsx
│   └── suporte/page.tsx
├── (admin)/
│   ├── dashboard/page.tsx
│   ├── users/page.tsx
│   ├── users/[uid]/page.tsx
│   ├── transacoes/page.tsx
│   └── config/page.tsx
```

---

## 6. Modelo de Dados — Firestore

### users/{uid}
```typescript
{
  id: string                    // Firebase Auth UID
  email: string                 // Google email
  nome: string                  // Primeiro nome
  sobrenome: string             // Sobrenome
  telefone: string | null       // WhatsApp
  fotoURL: string | null        // Google photo URL
  role: "cliente" | "admin"
  saldoCreditos: number         // Créditos disponíveis
  totalConsultas: number
  createdAt: Timestamp
  updatedAt: Timestamp
  deletedAt: Timestamp | null
  lastLoginAt: Timestamp | null
}
```

### transacoes/{tid}
```typescript
{
  id: string
  uid: string
  tipo: "recarga" | "consumo" | "reembolso" | "bonus"
  creditos: number
  valorReais: number | null
  descricao: string
  metodoPagamento: "pix" | "cartao_credito" | "cartao_debito" | "mercado_pago" | "bonus" | "admin"
  status: "pendente" | "confirmado" | "cancelado" | "estornado"
  pagamentoId: string | null
  jobId: string | null
  createdAt: Timestamp
  confirmedAt: Timestamp | null
}
```

### jobs/{jobId}
```typescript
{
  id: string
  uid: string
  status: "fila" | "processando" | "concluido" | "parcial" | "erro"
  parametros: Record<string, string>
  creditosDescontados: number
  itens: Array<{
    slug: string
    titulo: string
    status: string
    creditos: number
  }>
  createdAt: Timestamp
  updatedAt: Timestamp
  concluidoEm: Timestamp | null
}
```

### pagamentos/{pid}
```typescript
{
  id: string
  uid: string
  gateway: "mercado_pago"
  gatewayId: string
  tipo: "pix" | "cartao_credito" | "cartao_debito"
  valor: number
  creditos: number
  status: "aguardando" | "pago" | "cancelado" | "estornado"
  pixQrCode: string | null
  pixCopiaCola: string | null
  pixExpiracao: Timestamp | null
  cartaoBrand: string | null
  cartaoFinal: string | null
  createdAt: Timestamp
  pagoEm: Timestamp | null
}
```

### admin_config/{configId}
```typescript
// "pricing"
{
  id: "pricing"
  pacotes: [
    { id: "inicial", creditos: 5, preco: 9.90, titulo: "Inicial" },
    { id: "popular", creditos: 15, preco: 27.90, titulo: "Popular" },
    { id: "profissional", creditos: 50, preco: 89.90, titulo: "Profissional" }
  ]
  creditosBonusCadastro: 2
}

// "system"
{
  id: "system"
  manutencao: boolean
  whatsappNumero: "5591987654321"
  maxConsultasPorMinuto: 3
}
```

---

## 7. Sistema de Créditos

### Preços
| Pacote | Créditos | Preço (R$) | Por crédito |
|--------|----------|------------|-------------|
| Inicial | 5 | R$ 9,90 | R$ 1,98 |
| Popular | 15 | R$ 27,90 | R$ 1,86 |
| Profissional | 50 | R$ 89,90 | R$ 1,80 |

### Custo por consulta
| Consulta | Créditos | Equivalente R$ |
|----------|----------|----------------|
| Boleto Licenciamento | 1 | R$ 1,80–1,98 |
| Acompanhar Documento | 1 | R$ 1,80–1,98 |
| Veículo Detalhada | 2 | R$ 3,60–3,96 |
| Infrações/Multas | 2 | R$ 3,60–3,96 |
| Gravame | 2 | R$ 3,60–3,96 |
| CRLV-e | 2 | R$ 3,60–3,96 |
| CNH Pontuação | 2 | R$ 3,60–3,96 |

**Bônus de cadastro:** 2 créditos grátis (~R$ 4,00).

---

## 8. Fluxo de Consulta com Créditos

```
1. Usuário seleciona consultas (ex: Veículo Detalhada = 2cr + Infrações = 2cr = 4cr total)
2. Frontend verifica saldo local: se insuficiente, redireciona para /creditos
3. POST /api/jobs { consultas, parametros } + Authorization: Bearer <firebase-id-token>
4. Backend:
   a. Valida Firebase ID Token → obtém uid
   b. Lê user do Firestore
   c. Transaction Firestore:
      - Verifica saldo >= total créditos
      - Se não: retorna 402 "Saldo insuficiente"
      - Desconta: user.saldoCreditos -= total
      - Cria transacao tipo="consumo"
   d. Cria job no Firestore
   e. Executa consultas (thread pool)
   f. Atualiza job com resultados
5. Frontend polling
```

---

## 9. Fluxo de Recarga via PIX (Mercado Pago)

```
1. Usuário escolhe pacote (ex: 15 créditos = R$ 27,90)
2. Frontend chama POST /api/creditos/recarga { pacoteId: "popular" }
3. Backend:
   a. Lê pacote de admin_config/pricing
   b. Cria cobrança no Mercado Pago (PIX)
   c. Retorna { pid, pixQrCode, pixCopiaCola, expiracao }
4. Frontend exibe QR Code
5. Frontend polling GET /api/creditos/recarga/{pid}/status a cada 3s
6. Usuário paga PIX
7. Mercado Pago webhook POST /api/creditos/webhook/mercado-pago
8. Backend valida, credita créditos, atualiza pagamento
9. Frontend detecta status="pago", exibe confirmação
```

---

## 10. Consultas Disponíveis (Motor de Scraping)

O motor `detran-pa-consultas` automatiza as consultas nos sistemas JSF do DETRAN-PA:

### SISTRANSITO (mCaptcha — Proof-of-Work local)
| Slug | Consulta | Campos | Créditos |
|------|----------|--------|----------|
| `veiculo_detalhada` | Veículo Detalhada | placa, renavam | 2 |
| `infracoes` | Infrações/Multas | placa, renavam | 2 |
| `licenciamento_atual` | Boleto Licenciamento Atual | placa, renavam | 1 |
| `licenciamento_anterior` | Boleto Licenciamento Anterior | placa, renavam | 1 |
| `gravame` | Gravame | chassi | 2 |
| `crlv_e` | CRLV-e (emissão) | cpfCnpj, placa, renavam | 2 |
| `acompanha_documento` | Acompanhar Documento | renavam (ou chassi) | 1 |

### RENACH (Image CAPTCHA)
| Slug | Consulta | Campos | Créditos |
|------|----------|--------|----------|
| `cnh_pontuacao` | CNH Pontuação | cpf | 2 |

### Fluxo JSF Genérico
1. GET na página → capturar JSESSIONID + javax.faces.ViewState
2. Resolver CAPTCHA (mCaptcha local ou 2Captcha: Image)
3. POST com form fields + ViewState + CAPTCHA response
4. Parsear HTML de resposta

---

## 11. Regras Firestore

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    function isAuthenticated() { return request.auth != null; }
    function isOwner(uid) { return isAuthenticated() && request.auth.uid == uid; }
    function getUserRole() {
      return get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role;
    }
    function isAdmin() { return isAuthenticated() && getUserRole() == 'admin'; }

    match /users/{userId} {
      allow read: if isOwner(userId) || isAdmin();
      allow create: if isOwner(userId);
      allow update: if isOwner(userId) || isAdmin();
      allow delete: if isAdmin();
    }
    match /transacoes/{tid} {
      allow read: if isOwner(resource.data.uid) || isAdmin();
      allow create: if isAuthenticated() && request.resource.data.uid == request.auth.uid;
      allow update: if isAdmin();
    }
    match /jobs/{jobId} {
      allow read: if isOwner(resource.data.uid) || isAdmin();
      allow create: if isAuthenticated() && request.resource.data.uid == request.auth.uid;
      allow update: if isAdmin();
    }
    match /pagamentos/{pid} {
      allow read: if isOwner(resource.data.uid) || isAdmin();
      allow create: if isAuthenticated() && request.resource.data.uid == request.auth.uid;
      allow update: if isAdmin();
    }
    match /admin_config/{configId} {
      allow read: if isAuthenticated();
      allow write: if isAdmin();
    }
  }
}
```

---

## 12. Estado Atual (Checklist)

### Concluído ✅
- [x] Motor de scraping (detran-pa-consultas) com 9 consultas
- [x] Backend FastAPI com jobs assíncronos
- [x] Catálogo de consultas com metadados
- [x] Envelope normalizado de resultado
- [x] Download de PDF/boleto
- [x] Frontend: página de login Google
- [x] Frontend: página completar perfil
- [x] Frontend: página principal (consulta)
- [x] Frontend: página de resultado
- [x] PWA (manifest + service worker)
- [x] Firebase Auth configurado
- [x] Modelo de dados Firestore definido

### Em Progresso 🔧
- [ ] Persistência de jobs (atualmente em memória)

### Planejado 📋
- [ ] Middleware auth no backend (auth.py, deps.py)
- [ ] Sistema de créditos (creditos.py)
- [ ] Integração Mercado Pago (pagamentos.py)
- [ ] Webhook de confirmação de pagamento
- [ ] Tela de créditos + pacotes
- [ ] Tela de pagamento com QR Code PIX
- [ ] Dashboard do usuário
- [ ] Histórico de consultas
- [ ] Perfil editável
- [ ] Painel admin completo
- [ ] Firestore security rules
- [ ] Rate limiting
- [ ] Testes E2E
- [ ] Deploy produção

---

## 13. Dados de Teste

- **Placa:** OFS3J55
- **Renavam:** 00477026001
- **CPF:** 05532667217
- **Chassi:** 9C6KG0450B0010630

---

## 14. Detalhes Técnicos do Scraping

### CAPTCHAs
- **SISTRANSITO:** mCaptcha (Proof-of-Work local, sitekey: `pLmK1r0kfDWi26GT845rxZBaqdFo168p`). O fallback reCAPTCHA v2 foi removido do site.
- **RENACH:** Imagem CAPTCHA (5 caracteres alfanuméricos, servida com JSESSIONID, resolvido via 2Captcha)

### JSF Specifics
- Sempre fazer GET primeiro para obter JSESSIONID e ViewState
- ViewState muda a cada request — sempre extrair novo valor
- Form action URLs contêm jsessionid
- Alguns serviços são multi-etapas (Boleto Infração, Certidão Negativa, Edital Notificação)
- RENACH usa RichFaces (antigo), SISTRANSITO usa PrimeFaces (moderno)

### Sistemas DETRAN-PA
| Sistema | Domínio | Tecnologia |
|---------|---------|------------|
| Portal Principal | www.detran.pa.gov.br | Vue.js/Vite |
| SISTRANSITO | sistemas-renavam.detran.pa.gov.br | JSF (PrimeFaces) |
| RENACH | sistemas-renach.detran.pa.gov.br | JSF (RichFaces) |
| Portal Cidadão | cidadao.detran.pa.gov.br | HTML/Bootstrap |
| Serviços Cidadão | servicos-cidadao.detran.pa.gov.br | Angular SPA |

---

## 15. Variáveis de Ambiente

### Backend (.env.example)
- `TWOCAPTCHA_API_KEY` — Chave da API 2Captcha (obrigatória)
- `CORS_ORIGINS` — URLs permitidas de CORS

### Frontend (.env.example)
- `NEXT_PUBLIC_FIREBASE_API_KEY`
- `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
- `NEXT_PUBLIC_FIREBASE_PROJECT_ID`
- `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`
- `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`
- `NEXT_PUBLIC_FIREBASE_APP_ID`
- `NEXT_PUBLIC_API_URL` — URL do backend

---

## 16. Deploy

### Frontend (Vercel)
```bash
cd frontend && npm run build
# Deploy automático via Vercel CLI ou GitHub integration
```

### Backend (Docker)
```bash
docker build -f backend/Dockerfile -t detran-api .
docker run -p 8000:8000 -e TWOCAPTCHA_API_KEY=xxx detran-api
```

### render.yaml
Arquivo de configuração do Render presente na raiz do projeto.
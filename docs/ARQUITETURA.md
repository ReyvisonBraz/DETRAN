# DETRAN-PA Consultas — Arquitetura Completa

## Visão Geral

Transformar o sistema atual (aberto, sem auth, sem persistência) numa plataforma SaaS com:
- Autenticação Google (Firebase Auth)
- Painel do usuário (perfil, histórico, créditos)
- Sistema de créditos com recarga (PIX via Mercado Pago)
- Painel admin com controle total
- WhatsApp para suporte
- Firestore como banco de dados
- Cloud Functions para lógica de crédito e pagamentos

---

## Preços — Pacotes de Créditos

Cada crédito equivale a ~R$ 2,00. Consultas de 1 crédito = R$2,00, de 2 créditos = R$4,00.

| Pacote | Créditos | Preço (R$) | Por crédito | Economia |
|--------|----------|-------------|-------------|----------|
| Inicial | 5 | R$ 9,90 | R$ 1,98 | — |
| Popular | 15 | R$ 27,90 | R$ 1,86 | 6% |
| Profissional | 50 | R$ 89,90 | R$ 1,80 | 9% |

**Custo por tipo de consulta:**
| Consulta | Créditos | Equivalente R$ |
|----------|----------|----------------|
| Boleto Licenciamento | 1 | R$ 1,80–1,98 |
| Acompanhar Documento | 1 | R$ 1,80–1,98 |
| Veículo Detalhada | 2 | R$ 3,60–3,96 |
| Infrações/Multas | 2 | R$ 3,60–3,96 |
| Gravame | 2 | R$ 3,60–3,96 |
| CRLV-e | 2 | R$ 3,60–3,96 |
| CNH Pontuação | 2 | R$ 3,60–3,96 |

**Bônus de cadastro:** 2 créditos grátis (R$ ~4,00) para o usuário testar.

**Gateway de pagamento:** Mercado Pago (PIX + cartão).

---

## Modelo de Dados — Firestore

### users/{uid}
```typescript
{
  id: string                    // Firebase Auth UID
  email: string                 // Google email
  nome: string                  // Primeiro nome
  sobrenome: string             // Sobrenome
  telefone: string | null       // WhatsApp (opcional)
  fotoURL: string | null        // Google photo URL
  role: "cliente" | "admin"     // Role do sistema
  saldoCreditos: number         // Créditos disponíveis (denormalizado)
  totalConsultas: number         // Contador de consultas realizadas
  createdAt: Timestamp
  updatedAt: Timestamp
  deletedAt: Timestamp | null   // Soft delete
  lastLoginAt: Timestamp | null
}
```

### transacoes/{tid}
```typescript
{
  id: string
  uid: string                   // user ID
  tipo: "recarga" | "consumo" | "reembolso" | "bonus"
  creditos: number              // Quantidade (+ ou -)
  valorReais: number | null     // Valor em Reais (recarga)
  descricao: string             // Ex: "Recarga 15 créditos", "Consulta Veículo Detalhada"
  metodoPagamento: "pix" | "cartao_credito" | "cartao_debito" | "mercado_pago" | "bonus" | "admin"
  status: "pendente" | "confirmado" | "cancelado" | "estornado"
  pagamentoId: string | null    // ID do pagamento no Mercado Pago
  jobId: string | null          // Job que consumiu (tipo=consumo)
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
  parametros: Record<string, string>  // { placa, renavam, cpf, etc }
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
  gatewayId: string             // ID no Mercado Pago
  tipo: "pix" | "cartao_credito" | "cartao_debito"
  valor: number                 // Em Reais
  creditos: number              // Créditos que serão creditados
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
// configId = "pricing"
{
  id: "pricing"
  pacotes: [
    { id: "inicial", creditos: 5, preco: 9.90, titulo: "Inicial" },
    { id: "popular", creditos: 15, preco: 27.90, titulo: "Popular" },
    { id: "profissional", creditos: 50, preco: 89.90, titulo: "Profissional" }
  ]
  creditosBonusCadastro: 2
}

// configId = "system"
{
  id: "system"
  manutencao: boolean
  whatsappNumero: "5591987654321"
  maxConsultasPorMinuto: 3
}
```

---

## Regras Firestore

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

## API Endpoints

### Auth
| Método | Caminho | Auth | Descrição |
|--------|---------|------|-----------|
| POST | /api/auth/google | — | Login/registro com Google ID Token |
| POST | /api/auth/completar-perfil | user | Completar nome/sobrenome |
| GET | /api/auth/me | user | Dados do usuário logado |

### Consultas (existentes, atualizados)
| Método | Caminho | Auth | Descrição |
|--------|---------|------|-----------|
| GET | /api/consultas | — | Catálogo (sem auth) |
| POST | /api/jobs | user | Criar job (desconta créditos) |
| GET | /api/jobs/{jobId} | user | Status + resultado |
| GET | /api/jobs | user | Listar jobs do usuário |
| GET | /api/documentos/{nome} | user | Download PDF |

### Créditos e Pagamentos
| Método | Caminho | Auth | Descrição |
|--------|---------|------|-----------|
| GET | /api/creditos/saldo | user | Saldo atual |
| GET | /api/creditos/extrato | user | Histórico de transações |
| POST | /api/creditos/recarga | user | Iniciar recarga (PIX ou cartão) |
| GET | /api/creditos/recarga/{pid}/status | user | Status do pagamento |
| POST | /api/creditos/webhook/mercado-pago | — | Webhook Mercado Pago |

### Admin
| Método | Caminho | Auth | Descrição |
|--------|---------|------|-----------|
| GET | /api/admin/dashboard | admin | Métricas gerais |
| GET | /api/admin/users | admin | Listar usuários |
| GET | /api/admin/users/{uid} | admin | Detalhes do usuário |
| POST | /api/admin/users/{uid}/creditos | admin | Creditar/descontar manualmente |
| PATCH | /api/admin/users/{uid}/role | admin | Promover/rebaixar role |
| GET | /api/admin/jobs | admin | Todos os jobs |
| GET | /api/admin/transacoes | admin | Todas as transações |
| GET/PUT | /api/admin/config | admin | Configurações do sistema |

---

## Fluxo de Recarga via PIX (Mercado Pago)

```
1. Usuário escolhe pacote (ex: 15 créditos = R$ 27,90)
2. Frontend chama POST /api/creditos/recarga { pacoteId: "popular" }
3. Cloud Function / backend:
   a. Lê pacote de admin_config/pricing
   b. Cria cobrança no Mercado Pago: POST /v1/payments
      - payment_type_id: "pix"
      - transaction_amount: 27.90
      - description: "Recarga DETRAN-PA - 15 créditos"
   c. Mercado Pago retorna: qr_code_base64 + qr_code (copia e cola) + date_of_expiration
   d. Salva em /pagamentos/{pid}
   e. Retorna { pid, pixQrCode, pixCopiaCola, expiracao }
4. Frontend exibe QR Code para pagamento
5. Frontend polling GET /api/creditos/recarga/{pid}/status a cada 3s
6. Usuário paga PIX no app do banco
7. Mercado Pago envia webhook POST /api/creditos/webhook/mercado-pago
8. Cloud Function / backend:
   a. Valida assinatura/x-signature do webhook
   b. Verifica status = "approved"
   c. Em transação Firestore:
      - Cria transação tipo="recarga" creditos=15
      - Atualiza user.saldoCreditos += 15
      - Atualiza pagamento status="pago"
9. Frontend detecta status="pago", exibe confirmação
```

---

## Estrutura de Pastas — Projeto Final

```
detran-pa-app/
├── frontend/                        # Next.js 14 (App Router)
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx           # Login Google
│   │   │   ├── completar/page.tsx        # Completar nome/sobrenome
│   │   │   └── layout.tsx                # Layout sem sidebar
│   │   ├── (app)/
│   │   │   ├── layout.tsx               # Layout com sidebar
│   │   │   ├── dashboard/page.tsx       # Dashboard
│   │   │   ├── consultas/page.tsx       # Nova consulta
│   │   │   ├── consultas/[jobId]/page.tsx  # Resultado
│   │   │   ├── historico/page.tsx        # Histórico
│   │   │   ├── creditos/page.tsx        # Saldo + extrato + pacotes
│   │   │   ├── creditos/recarga/[pid]/page.tsx  # Pagamento
│   │   │   ├── perfil/page.tsx          # Perfil
│   │   │   └── suporte/page.tsx         # WhatsApp + FAQ
│   │   ├── (admin)/
│   │   │   ├── layout.tsx
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── users/page.tsx
│   │   │   ├── users/[uid]/page.tsx
│   │   │   ├── transacoes/page.tsx
│   │   │   └── config/page.tsx
│   │   ├── globals.css
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ui/                           # Button, Input, Card, Badge...
│   │   ├── layout/                       # Sidebar, Header, Footer
│   │   └── domain/                       # ConsultaCard, RecargaPacote...
│   ├── lib/
│   │   ├── firebase.ts                   # Firebase client config
│   │   ├── auth.ts                        # Auth context + hooks
│   │   ├── api.ts                         # API client
│   │   ├── types.ts                       # Tipos
│   │   └── utils.ts                       # Helpers
│   └── hooks/
│       ├── useAuth.ts
│       ├── useCreditos.ts
│       └── useJobs.ts
│
├── backend/                         # FastAPI (existente, atualizado)
│   └── app/
│       ├── main.py                       # + CORS atualizado
│       ├── auth.py                       # NOVO: Validar Firebase ID Token
│       ├── deps.py                      # NOVO: get_current_user dependency
│       ├── creditos.py                  # NOVO: Saldo, extrato, recarga
│       ├── pagamentos.py                # NOVO: Mercado Pago integration
│       ├── admin_routes.py              # NOVO: Rotas admin
│       ├── jobs.py                      # ATUALIZADO: Desconta créditos
│       ├── schemas.py                   # ATUALIZADO: + User, Transacao, Pagamento
│       └── ...                          # (restante mantido)
│
└── firebase/                        # Firebase project config
    ├── firebase.json
    ├── .firebaserc
    ├── firestore.indexes.json
    └── firestore.rules
```

---

## Fluxo de Consulta com Créditos

```
1. Usuário seleciona consultas (ex: Veículo Detalhada = 2cr + Infrações = 2cr = 4cr total)
2. Frontend verifica saldo local: se insuficiente, redireciona para /creditos
3. POST /api/jobs { consultas, parametros } + Header: Authorization: Bearer <firebase-id-token>
4. Backend:
   a. Valida Firebase ID Token → obtém uid
   b. Lê user do Firestore
   c. Transaction Firestore:
      - Verifica saldo >= total creditos
      - Se não: retorna 402 "Saldo insuficiente. Você tem X créditos, precisa de Y."
      - Desconta: user.saldoCreditos -= total
      - Cria transacao tipo="consumo"
   d. Cria job no Firestore
   e. Executa consultas (thread pool, igual atual)
   f. Atualiza job com resultados
5. Frontend polling como hoje
```

---

## Implementação — Ordem

### Fase 1: Fundação (Firebase + Auth)
1. Configurar projeto Firebase (Auth + Firestore)
2.firebase.ts — Configuração SDK client
3. auth.ts — AuthContext, useAuth hook
4. (auth)/login — Tela de login Google
5. (auth)/completar — Completar perfil
6. (app)/layout — Layout com sidebar
7. Middleware Next.js para proteger rotas
8. Auth trigger: criar perfil no Firestore

### Fase 2: Perfil e Dashboard
9. Dashboard com saldo e atalhos
10. Perfil editável
11. Refatorar consulta para rota autenticada
12. Histórico de consultas

### Fase 3: Créditos e Mercado Pago
13. auth.py — Middleware FastAPI
14. creditos.py — Saldo, extrato, desconto
15. Tela de créditos + pacotes
16. Integração Mercado Pago PIX
17. Webhook de confirmação
18. Tela de pagamento com QR Code

### Fase 4: Painel Admin
19. Layout admin
20. Dashboard métricas
21. CRUD usuários
22. Transações e configurações

### Fase 5: Polish
23. Firestore security rules
24. Rate limiting
25. Testes E2E
26. Deploy
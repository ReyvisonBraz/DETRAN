# CONFIGURACAO FIREBASE — DETRAN-PA Consultas

Estado **real** da configuracao Firebase deste projeto. Atualizado apos a sessao em
que a parte CLI foi executada de fato.

> **Projeto Firebase:** `detran-pa` — **Project ID:** `detran-pa-8e4ad` (Project Number `374085668939`)
> **App Web:** `detran-web` — **App ID:** `1:374085668939:web:d6b1841affcd010a8abdce`
> **Conta logada no CLI:** littlefigther50@gmail.com
>
> O projeto, o app web, o Firestore `(default)` e o bucket de Storage **JA EXISTEM**.
> Nao e preciso criar nada do zero — o doc antigo apontava para um `detran-pa-consultas`
> ficticio que nunca existiu nesta conta.

---

## 0. RESUMO — o que ja esta feito vs o que falta

### Feito via Firebase CLI (nesta pasta)
- [x] `.firebaserc` vinculado a `detran-pa-8e4ad`
- [x] `frontend/.env.local` com as 6 variaveis `NEXT_PUBLIC_FIREBASE_*` reais (+ `NEXT_PUBLIC_API_URL`)
- [x] `storage.rules` criado e deployado
- [x] `firebase.json` com bloco `storage`
- [x] `firestore.rules` deployado
- [x] Indice composto `transacoes (uid ASC + createdAt DESC)` deployado

### Falta (SO no Console — o CLI nao faz)
- [ ] **Ativar Google Sign-In** (Authentication)
- [ ] **Gerar Service Account** (chave privada JSON) e preencher `backend/.env`

---

## 1. CONFIG REAL DO APP WEB (ja aplicada)

Valores ja gravados em `frontend/.env.local` (obtidos via
`firebase apps:sdkconfig WEB <appId>`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyBqCbTdlOD9xFGBP-kBxWn9LEi5YlO0HIc
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=detran-pa-8e4ad.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=detran-pa-8e4ad
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=detran-pa-8e4ad.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=374085668939
NEXT_PUBLIC_FIREBASE_APP_ID=1:374085668939:web:d6b1841affcd010a8abdce
```

> A `API_KEY` de um app web Firebase **nao e secreta** — vai no bundle do cliente.
> A seguranca vem das regras do Firestore/Storage e do Authentication, nao de esconder a key.

---

## 2. PENDENTE NO CONSOLE — Google Sign-In

O Firebase CLI **nao tem comando** para habilitar provedores de Auth. Faca no Console:

1. https://console.firebase.google.com/project/detran-pa-8e4ad/authentication/providers
2. **Authentication** -> **Sign-in method** -> **Google** -> **Enable**
3. Em "Support email", selecione um e-mail valido
4. **Salvar**

Sem isso, o login Google do frontend nao funciona.

---

## 3. PENDENTE NO CONSOLE — Service Account (backend)

Usada pelo backend (Python/FastAPI) para verificar ID Tokens, ler/escrever Firestore
(creditos, transacoes) e subir PDFs ao Storage. So o Console gera a private key.

1. https://console.firebase.google.com/project/detran-pa-8e4ad/settings/serviceaccounts/adminsdk
2. **Gerar nova chave privada** -> salve o JSON em local seguro
3. **NUNCA** commite o JSON. Confirme que esta no `.gitignore`
4. Preencha `backend/.env` com os campos do JSON:

```env
# Firebase Admin (conta de servico)
FIREBASE_PROJECT_ID=detran-pa-8e4ad
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@detran-pa-8e4ad.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n"
FIREBASE_PRIVATE_KEY_ID=xxxxxxxxxxxx
FIREBASE_STORAGE_BUCKET=detran-pa-8e4ad.firebasestorage.app

# Scraper
TWOCAPTCHA_API_KEY=

# Config
CORS_ORIGINS=http://localhost:3000
MAX_WORKERS=2
```

> **FIREBASE_PRIVATE_KEY**: use aspas duplas e mantenha os `\n` como literais
> (exatamente como vem no campo `private_key` do JSON).

---

## 4. DEPLOY VIA CLI (referencia)

Ja executado nesta sessao. Para repetir apos editar regras/indices:

```bash
# regras + indices + storage de uma vez
firebase deploy --only firestore:rules,firestore:indexes,storage

# ou individualmente
firebase deploy --only firestore:rules
firebase deploy --only firestore:indexes
firebase deploy --only storage
```

O projeto default ja vem do `.firebaserc` (`detran-pa-8e4ad`), nao precisa `--project`.

### Nota sobre indices de campo unico
Os indices `users -> codigoIndicacao` e `consultas -> createdAt` foram **removidos** do
`firestore.indexes.json`: sao de **campo unico**, que o Firestore cria automaticamente
(inclusive em collection group). Tentar declara-los como composto gera erro HTTP 400
"this index is not necessary". So o `transacoes (uid + createdAt)` e composto de verdade.

### storage.rules atual
```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /pdfs/{allPaths=**} {
      allow read: if true;    // URLs assinadas, sem necessidade de auth
      allow write: if false;  // apenas a service account (backend) escreve
    }
    match /{allPaths=**} {
      allow read, write: if false;
    }
  }
}
```

---

## 5. VERIFICACAO MANUAL (Console)

### 5a. Authentication
- https://console.firebase.google.com/project/detran-pa-8e4ad/authentication/users
- Faca login pelo frontend e verifique se o usuario aparece

### 5b. Firestore
- Login pelo frontend cria `users/{uid}` com `saldoCreditos: 2`
- Indices: o composto `transacoes (uid ASC, createdAt DESC)` deve estar **Enabled**

### 5c. Storage
- A pasta `pdfs/` e criada automaticamente apos o primeiro upload

### 5d. Fluxo completo
1. Backend: `cd backend && uvicorn app.main:app --reload`
2. Frontend: `cd frontend && npm run dev`
3. Login com Google -> doc `users/{uid}` criado com `saldoCreditos: 2`
4. Criar job via `/api/jobs` -> deduz credito e cria doc em `transacoes`
5. Upload de PDF para Storage funciona (URL assinada)

---

## 6. ESTRUTURA DO FIRESTORE

### Colecao: `users/{uid}`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| uid | string | Firebase Auth UID |
| email | string | E-mail do Google |
| nome | string | Primeiro nome |
| sobrenome | string | Restante do nome |
| telefone | string\|null | Telefone (preenchido no perfil) |
| fotoURL | string\|null | Avatar do Google |
| role | string | "cliente" (futuro: "admin") |
| saldoCreditos | number | Saldo de creditos (inicia com 2) |
| totalConsultas | number | Total de consultas realizadas |
| codigoIndicacao | string | Codigo unico de 6 chars para indicacao |
| indicadoPor | string\|undefined | UID de quem indicou |
| perfilCompleto | boolean | Se completou o onboarding |
| onboardingCompleto | boolean | Se finalizou o onboarding |
| createdAt | timestamp | Data de criacao |
| updatedAt | timestamp | Ultima atualizacao |

### Colecao: `transacoes/{transacaoId}`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| uid | string | UID do usuario |
| tipo | string | "consumo", "recarga", "bonus", "reembolso" |
| quantidade | number | Positivo (recarga/bonus) ou negativo (consumo) |
| descricao | string | Ex: "1 consulta(s)", "Recarga", "Bonus indicacao" |
| saldoApos | number | Saldo apos a transacao |
| createdAt | timestamp | Data/hora da transacao |

### Colecao: `feedbacks/{uid}_{jobId}`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| uid | string | UID do autor |
| texto | string | Conteudo do feedback |
| nota | number | Avaliacao (1-5) |
| jobId | string | Job relacionado |
| createdAt | timestamp | Immutavel |

### Colecao: `refunds/{uid}_{jobId}`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| uid | string | UID do solicitante |
| jobId | string | Job com erro |
| motivo | string | Motivo do estorno |
| creditosDevolvidos | number | Quantidade de creditos devolvidos |
| createdAt | timestamp | Immutavel |

### Subcolecao: `users/{uid}/consultas/{jobId}`

| Campo | Tipo | Descricao |
|-------|------|-----------|
| slug | string | Tipo de consulta (ex: "veiculo_detalhada") |
| titulo | string | Nome legivel |
| status | string | "processando", "ok", "erro" |
| resultado | object | Resultado completo |
| createdAt | timestamp | Data da consulta |

---

## 7. CHECKLIST FINAL

- [x] Projeto Firebase (`detran-pa-8e4ad`) — ja existia
- [x] Firestore `(default)` em modo nativo — ja existia
- [x] Storage bucket `detran-pa-8e4ad.firebasestorage.app` — ja existia
- [x] App Web `detran-web` registrado — ja existia
- [x] `.firebaserc` vinculado
- [x] `frontend/.env.local` com as 6 variaveis `NEXT_PUBLIC_FIREBASE_*`
- [x] `firestore.rules` deployado
- [x] `storage.rules` criado e deployado
- [x] Indice composto `transacoes` deployado
- [ ] **Google Sign-In ativado no Console**
- [ ] **Service Account gerada e `backend/.env` preenchido**
- [ ] Login via frontend cria `users/{uid}` com `saldoCreditos: 2`
- [ ] Criacao de job deduz creditos e cria doc em `transacoes`
- [ ] Upload de PDF para Storage funciona

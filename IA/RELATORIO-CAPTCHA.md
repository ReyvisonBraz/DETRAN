# RELATÓRIO — Reconhecimento do CAPTCHA do DETRAN-PA

> **Gerado por:** Claude Code (Opus 4.8)
> **Data:** 21/06/2026
> **Método:** Coleta direta do HTML server-side via `curl` (GET, sem submeter forms).
> As páginas são JSF renderizadas no servidor, então o HTML retornado já contém
> form, widget de CAPTCHA e ViewState — suficiente para identificar o tipo de CAPTCHA.

## ⚠️ Nota sobre screenshots

Este ambiente **não tem navegador (Playwright/Puppeteer) disponível**, então não foi
possível gerar screenshots em pixels. Em vez disso, o **HTML cru de cada página foi salvo**
em `IA/html/{slug}.html` — essa é a fonte de verdade para a identificação do CAPTCHA e dos
forms (mais confiável que um print, inclusive). Os 9 fetches retornaram **HTTP 200**, sem
bloqueio de IP nem redirecionamentos.

---

# RESUMO EXECUTIVO

| Sistema | CAPTCHA atual | Mudou? |
|---|---|---|
| **SISTRANSITO** | **mCaptcha** (Proof-of-Work, widget em `mcaptcha.detran.pa.gov.br`) | ❌ Não mudou o tipo, mas **o fallback reCAPTCHA v2 sumiu do HTML** |
| **RENACH** | **Image CAPTCHA** (5 caracteres, imagem em `/renach/renach-web/imagem`) | ❌ Nenhuma mudança |

**Resposta direta:**
- **SISTRANSITO usa mCaptcha** — sitekey **`pLmK1r0kfDWi26GT845rxZBaqdFo168p`** (inalterado).
  Em todas as páginas de consulta o widget é um `<iframe src="https://mcaptcha.detran.pa.gov.br/widget?sitekey=...">`
  e o token chega via `window.postMessage` (origin `https://mcaptcha.detran.pa.gov.br`) para o
  hidden `mcaptcha__token`. **Não há mais nenhum `g-recaptcha` / `grecaptcha` / `data-sitekey` no HTML** — o fallback reCAPTCHA v2 foi removido.
- **RENACH usa Image CAPTCHA** — imagem em `../../imagem` (= `/renach/renach-web/imagem`), campo de resposta `formJSF:senha` (maxlength 5). Inalterado.

Todas as páginas SISTRANSITO trazem o comentário de versão no HTML:
`versao : 07abcd3 - 17/06/2026-00:23:54 - novo captcha` — ou seja, a troca para mCaptcha foi um deploy recente, e é a versão que já estávamos suportando.

---

# RELATÓRIOS POR URL

## veiculo_detalhada — Consulta de Veículo Detalhada

**URL visitada:** `.../servicos/veiculos/indexRenavam.jsf`
**URL final:** mesma · **Status HTTP:** 200
**CAPTCHA tipo:** mCaptcha
**CAPTCHA sitekey:** `pLmK1r0kfDWi26GT845rxZBaqdFo168p`
**CAPTCHA campo de resposta:** `mcaptcha__token` (hidden)

### Form HTML
- **Forms:** dois — `frmFlag` (controle) e **`indexRenavam`** (consulta)
- **Form action:** `/sistransito/detran-web/servicos/veiculos/indexRenavam.jsf;jsessionid=...`
- **Campos visíveis:**
  - `indexRenavam:placa1` (text, maxlength 7) — "Placa do Veículo *"
  - `indexRenavam:renavam` (text, maxlength 11) — "Número do Renavam *"
- **Campos hidden:** `indexRenavam`=indexRenavam · `mcaptcha__token` · `javax.faces.ViewState` = `3626085249823816489:-666515...`
- **Botão submit:** `indexRenavam:confirma` = "Consultar Veículo" (`onclick="return validarRecaptcha();"`)

### Mudanças
- Nenhuma estrutural. Botão submit qualificado com prefixo `indexRenavam:` (manter no scraper).

---

## infracoes — Consulta de Infrações

**URL:** `.../servicos/infracao/indexConsultaInfracao.jsf` · **Status:** 200
**CAPTCHA tipo:** mCaptcha · **sitekey:** `pLmK1r0kfDWi26GT845rxZBaqdFo168p` · **campo:** `mcaptcha__token`

### Form HTML
- **Form ID:** `indexForm`
- **Campos visíveis (sem prefixo de form!):**
  - `placa` (text, maxlength 7) — "Placa"
  - `renavam` (text, maxlength 11) — "Renavam"
- **Hidden:** `indexForm`=indexForm · `mcaptcha__token` · `javax.faces.ViewState`
- **Botão submit:** `confirma` = "Confirmar" · botão limpar: `j_idt23` = "Limpar"

### Mudanças
- ⚠️ Campos **`placa`/`renavam` sem prefixo** e submit **`confirma`** (sem prefixo). Difere das outras páginas.

---

## licenciamento_atual — Licenciamento Atual (Boleto)

**URL:** `.../servicos/b/indexBLicencAnoAtual.jsf` · **Status:** 200
**CAPTCHA tipo:** mCaptcha · **sitekey:** `pLmK1r0kfDWi26GT845rxZBaqdFo168p` · **campo:** `mcaptcha__token`

### Form HTML
- **Forms:** `frmFlag` + **`indexBoletoAnoAtual`**
- **Campos visíveis (sem prefixo):**
  - `placa1` (text, maxlength 7) — "Placa *"
  - `renavam` (text, maxlength 11) — "Renavam *"
- **Hidden:** `mcaptcha__token` · `javax.faces.ViewState`
- **Botão submit:** `confirma` = "Consultar Orçamento"

### Mudanças
- Campo placa é **`placa1`** (não `placa`) e sem prefixo; submit `confirma` sem prefixo.

---

## licenciamento_anterior — Licenciamento Anterior (Boleto)

**URL:** `.../servicos/b/indexBLicencAnoAnterior.jsf` · **Status:** 200
**CAPTCHA tipo:** mCaptcha · **sitekey:** `pLmK1r0kfDWi26GT845rxZBaqdFo168p` · **campo:** `mcaptcha__token`

### Form HTML
- **Forms:** `frmFlag` + **`indexBoletoAnoAnterior`**
- **Campos visíveis (COM prefixo):**
  - `indexBoletoAnoAnterior:placa1` (text, maxlength 7) — "Placa *"
  - `indexBoletoAnoAnterior:renavam` (text, maxlength 11) — "Renavam *"
- **Botão submit:** `indexBoletoAnoAnterior:confirma` = "Consultar Orçamento" · limpar `indexBoletoAnoAnterior:j_idt23`

### Mudanças
- ⚠️ Mesma função do "ano atual", mas aqui os campos **vêm com prefixo** `indexBoletoAnoAnterior:`. Inconsistência entre as duas páginas de licenciamento — tratar separadamente no scraper.

---

## boleto_infracao — Boleto Infração

**URL:** `.../servicos/b/indexBInfracao.jsf` · **Status:** 200
**CAPTCHA tipo:** **Nenhum** (página seletora, sem CAPTCHA)
**sitekey:** N/A · **campo:** N/A

### Form HTML
- **Form ID:** `indexBoletoInfracao`
- **Campos visíveis:** radio group **`indexBoletoInfracao:j_idt21`**
  - opção `veiculosPara` (id `...:j_idt21:0`) — "Veículos do Pará"
  - opção `veiculosOutroEstado` (id `...:j_idt21:1`) — "Veículos de outro Estado"
- **Botão submit:** `indexBoletoInfracao:confirma` = "Continuar"

### Mudanças
- Esta é uma **página de seleção em 2 etapas** — escolhe-se o tipo de veículo e só na próxima tela aparece o form com placa/renavam + mCaptcha. O radio ainda é o auto-gerado **`j_idt21`** (igual ao registrado nas notas antigas), mas IDs `j_idt*` são instáveis — derive o `name` do radio via parse, não hardcode.

---

## gravame — Gravame (SNG)

**URL:** `.../servicos/veiculos/indexSNG.jsf` · **Status:** 200
**CAPTCHA tipo:** mCaptcha · **sitekey:** `pLmK1r0kfDWi26GT845rxZBaqdFo168p` · **campo:** `mcaptcha__token`

### Form HTML
- **Forms:** `frmFlag` + **`indexGravame`**
- **Campos visíveis (COM prefixo):**
  - `indexGravame:chassi` (text, maxlength 21) — "Número Chassi *"
- **Botão submit:** `indexGravame:confirma` = "Consultar SNG"

### Mudanças
- Nenhuma. Consulta é **por chassi** (não placa/renavam).

---

## crlv_e — CRLV-e

**URL:** `.../servicos/crlv/indexCRLVe.jsf` · **Status:** 200
**CAPTCHA tipo:** mCaptcha · **sitekey:** `pLmK1r0kfDWi26GT845rxZBaqdFo168p` · **campo:** `mcaptcha__token`

### Form HTML
- **Form ID:** `indexCRLVe`
- **Campos visíveis (COM prefixo):**
  - `indexCRLVe:placa` (text, maxlength 7) — "Placa do Veículo *"
  - `indexCRLVe:renavam` (text, maxlength 11) — "Número do Renavam *"
  - `indexCRLVe:cpfCnpj` (text, maxlength 14) — "CPF / CNPJ do Proprietário *"
- **Botão submit:** link `<a id="indexCRLVe:confirma">` usando `jsf.util.chain(...)` + `mojarra.jsfcljs(...)`

### Mudanças
- ⚠️ O submit **não é `<input type=submit>`**, e sim um **link `<a>` que dispara `mojarra.jsfcljs`** (POST via JS). O scraper precisa enviar o par `indexCRLVe:confirma=indexCRLVe:confirma` no POST manualmente. Exige **3 campos** (placa, renavam, CPF/CNPJ).

---

## acompanha_documento — Acompanha Documento

**URL:** `.../servicos/veiculos/indexAcompanhaDocumento.jsf` · **Status:** 200
**CAPTCHA tipo:** mCaptcha · **sitekey:** `pLmK1r0kfDWi26GT845rxZBaqdFo168p` · **campo:** `mcaptcha__token`

### Form HTML
- **Forms:** `frmFlag` + **`indexAcompanhaDocumento`**
- **Campos visíveis (sem prefixo):**
  - radio `opcao` — `OpPlaca` (value `P`) / `OpChassi` (value `C`)
  - `renavam` (text, maxlength 11) — "Número Renavam *"
  - `chassi` (text, maxlength 21) — "Número Chassi *"
  - `noBoleto` (text, maxlength 15) — "Número do Boleto"
- **Botão submit:** `confirma` = "Confirmar" · limpar `j_idt27`

### Mudanças
- Form mais complexo: radio `opcao` (P/C) + renavam/chassi/noBoleto. Campos sem prefixo, submit `confirma`.

---

## cnh_pontuacao — CNH Pontuação (RENACH)

**URL:** `.../renach/renach-web/servicos/consultaPontuacao/indexConsultaPontuacao.jsf` · **Status:** 200
**CAPTCHA tipo:** **Image CAPTCHA**
**sitekey:** N/A · **campo de resposta:** `formJSF:senha`

### Form HTML
- **Form ID:** `formJSF`
- **Campos visíveis:**
  - `formJSF:cpf` (text, maxlength 11) — "CPF"
  - `formJSF:senha` (text, maxlength 5) — "Digite a sequencia de caracteres" (resposta do CAPTCHA)
- **Imagem do CAPTCHA:** `<img src="../../imagem">` → resolve para `/renach/renach-web/imagem` (200x100px)
- **Botão atualizar imagem:** link com `jsfcljs(...,{'formJSF:j_id_jsp_1697595030_6':...})`
- **Botão submit:** `formJSF:j_id_jsp_1697595030_8` = "Confirmar" · limpar `formJSF:j_id_jsp_1697595030_9`
- **Hidden:** `javax.faces.ViewState` **id=`javax.faces.ViewState` value=`_id28042`** (formato antigo RichFaces/Mojarra, diferente do SISTRANSITO)

### Mudanças
- Nenhuma mudança. **Os IDs JSP auto-gerados continuam idênticos** aos das notas antigas:
  submit ainda é **`formJSF:j_id_jsp_1697595030_8`**. Mesmo assim, prefira localizar o submit por `value="Confirmar"` para robustez.

---

# DIFERENÇAS DE ViewState ENTRE OS DOIS SISTEMAS

- **SISTRANSITO (Mojarra novo):** `javax.faces.ViewState` com **id `j_id1:javax.faces.ViewState:0`** e valor no formato `numero:numero` (stateless-ish, dois inteiros). Aparece **2x** quando há dois forms (`:0` e `:1`).
- **RENACH (JSF/RichFaces antigo):** `javax.faces.ViewState` com **id `javax.faces.ViewState`** e valor curto tipo `_id28042`.

O scraper deve extrair o ViewState **do form correto** em cada caso.

---

# COOKIES / SESSÃO

- **SISTRANSITO:** `JSESSIONID=...renavam-web-...` (path `/sistransito/detran-web`) + `INGRESSCOOKIE=...` (ingress nginx, sticky session — **importante manter** para o POST cair no mesmo pod). O `jsessionid` também vem embutido no `action` da URL (`;jsessionid=...`).
- **RENACH:** `JSESSIONID=...renach-web-...` (path `/renach/renach-web`), também embutido na URL da imagem e do action.
- Servidor: `nginx/1.8.1`. Sem Cloudflare/WAF detectável no header.

---

# MUDANÇAS QUE EXIGEM REFATORAÇÃO DO SCRAPER

1. **Remover o caminho de fallback reCAPTCHA v2 do SISTRANSITO.** Não existe mais `g-recaptcha`/`data-sitekey`/`grecaptcha` em nenhuma página. O sitekey antigo `6LfDIwMtAAAAAKL8RPTzJd_fDTfWCOzXDv79aJhK` está morto. Só mCaptcha.
2. **mCaptcha permanece** com sitekey `pLmK1r0kfDWi26GT845rxZBaqdFo168p`. Fluxo: resolver PoW contra `https://mcaptcha.detran.pa.gov.br` e preencher hidden `mcaptcha__token`. (Confirmar se o solver PoW local atual ainda bate com a config do widget.)
3. **Padronizar a leitura de nomes de campo por página** — há 3 padrões coexistindo:
   - Sem prefixo: `infracoes` (`placa`/`renavam`/`confirma`), `licenciamento_atual` (`placa1`/`renavam`/`confirma`), `acompanha_documento`.
   - Com prefixo `<form>:`: `veiculo_detalhada`, `licenciamento_anterior`, `gravame`, `crlv_e`.
   Não hardcode — derive os `name`s do HTML por página.
4. **`crlv_e`: submit é link `mojarra.jsfcljs`, não input submit.** Enviar `indexCRLVe:confirma=indexCRLVe:confirma` no POST. Exige 3º campo `cpfCnpj`.
5. **`boleto_infracao` é fluxo de 2 etapas** (radio `j_idt21` → próxima página com captcha). Tratar como navegação encadeada.
6. **`gravame` consulta por chassi** (`indexGravame:chassi`), não placa/renavam.
7. **RENACH inalterado** — Image CAPTCHA via `/renach/renach-web/imagem`, campo `formJSF:senha`, submit `formJSF:j_id_jsp_1697595030_8`. Manter 2Captcha.
8. **IDs `j_idt*` e `j_id_jsp_*` são auto-gerados e instáveis** — preferir localizar botões por `value`/texto em vez de hardcode (mesmo que hoje coincidam com as notas antigas).

---

# RECOMENDAÇÃO DE SERVIÇO DE RESOLUÇÃO POR TIPO

| Sistema | CAPTCHA | Serviço recomendado |
|---|---|---|
| **SISTRANSITO** | mCaptcha (Proof-of-Work) | **Solver PoW local** (não precisa de 2Captcha — o mCaptcha é PoW computacional do lado do cliente). Manter a implementação local atual; se o solver local falhar, o 2Captcha **suporta mCaptcha** como método pago de backup. |
| **RENACH** | Image CAPTCHA (5 chars alfanum.) | **2Captcha** (endpoint de imagem/OCR normal). Baixar `/renach/renach-web/imagem` com o JSESSIONID e enviar para resolução. Continua exigindo a chave 2Captcha — ver memória sobre a falta dessa chave. |

> ⚠️ Lembrete (memória do projeto): há bloqueio E2E e **falta de chave 2Captcha** registrados — o RENACH não roda fim-a-fim sem essa chave.

---

# ARQUIVOS GERADOS

- `IA/html/{slug}.html` — HTML cru das 9 páginas (fonte de verdade).
- `IA/html/cookies_sistransito.txt` — cookie jar do primeiro fetch.
- `IA/screenshots/` — **vazio** (sem navegador disponível neste ambiente; ver nota no topo).

### Como gerar os screenshots (se necessário depois)
Com Playwright instalado no ambiente:
```bash
npx playwright screenshot --full-page \
  "https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexRenavam.jsf" \
  IA/screenshots/veiculo_detalhada.png
```
(repetir para os 9 slugs).

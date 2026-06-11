# DETRAN-PA - Analise Completa dos Servicos e Endpoints

## 1. Arquitetura dos Sistemas

| Sistema | Dominio | Tecnologia | Funcao |
|---------|---------|------------|--------|
| Portal Principal | www.detran.pa.gov.br | Vue.js/Vite SPA | Portal informativo |
| Sistema Restrito | restrito.detran.pa.gov.br | Laravel | Admin/CMS + API REST |
| SISTRANSITO (Veiculos/Infracoes) | sistemas-renavam.detran.pa.gov.br | JavaServer Faces (JSF) | Consultas de veiculo e multas |
| RENACH (Habilitacao) | sistemas-renach.detran.pa.gov.br | JavaServer Faces (JSF antigo) | Consultas de CNH e habilitacao |
| Portal do Cidadao (Venus) | cidadao.detran.pa.gov.br | HTML/Bootstrap | Defesa e recursos |
| Servicos do Cidadao | servicos-cidadao.detran.pa.gov.br | Angular SPA | Login cidadao |
| Dashboard CNH | dashboard-cnh.detran.pa.gov.br | R Shiny | Estatisticas CNH |
| Dashboard Infracoes | dashboard-infracao.detran.pa.gov.br | R Shiny | Estatisticas infracoes |
| Dashboard Frota | dashboard-frota.detran.pa.gov.br | R Shiny | Estatisticas frota |
| CFC | sistemas.detran.pa.gov.br/cfc-web | JSF | Auto escolas |
| PAE | pae-consulta-publica.sistemas.pa.gov.br | Next.js | Processo administrativo |
| API REST | restrito.detran.pa.gov.br/api | REST JSON | Dados para o portal |

---

## 2. Tipos de CAPTCHA

### 2.1 Google reCAPTCHA v2
- **Site Key:** `6LfDIwMtAAAAAKL8RPTzJd_fDTfWCOZXDv79aJhK`
- **Usado em:** Todas as consultas do SISTRANSITO (sistemas-renavam)
- **Integracao 2Captcha:** Tipo `recaptcha`, enviar sitekey + pageurl
- **Parametro de resposta:** `g-recaptcha-response`

### 2.2 JSF Image CAPTCHA
- **URL da imagem:** `../../imagem` (relativo a pagina JSF, ex: `https://sistemas-renach.detran.pa.gov.br/renach/renach-web/servicos/consultaPontuacao/imagem`)
- **Usado em:** Todas as consultas do RENACH (sistemas-renach)
- **Integracao 2Captcha:** Tipo `image`, enviar screenshot/base64 da imagem CAPTCHA
- **Parametro de resposta:** `formJSF:senha` (campo texto, max 5 caracteres)
- **Botao atualizar:** Ha um botao de refresh ao lado da imagem para gerar novo CAPTCHA

---

## 3. Fluxo de Submissao JSF (TODAS as consultas)

Todas as paginas usam JavaServer Faces (JSF) que exige um fluxo especifico:

```
1. GET na pagina de consulta
   -> Capturar: Cookie JSESSIONID, campo oculto javax.faces.ViewState, CAPTCHA (reCAPTCHA ou imagem)

2. Resolver CAPTCHA via 2Captcha API
   -> reCAPTCHA v2: Enviar sitekey + pageurl, receber token
   -> Image CAPTCHA: Enviar imagem base64, receber texto

3. POST no form action URL (inclui jsessionid no path)
   -> Headers: Cookie: JSESSIONID=xxx
   -> Body: form fields + javax.faces.ViewState + captcha response
   -> Content-Type: application/x-www-form-urlencoded

4. Parsear resposta HTML
   -> O resultado vem na mesma pagina apos o POST
```

---

## 4. Consultas Principais - Detalhes Completos

### 4.1 CONSULTA VEICULO DETALHADA
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexRenavam.jsf`
- **CAPTCHA:** Google reCAPTCHA v2
- **Form:** `indexRenavam`
- **Campos:**
  - `indexRenavam:placa1` - Placa do veiculo (7 caracteres)
  - `indexRenavam:renavam` - Numero do RENAVAM (11 digitos)
  - `g-recaptcha-response` - Token do reCAPTCHA
  - `javax.faces.ViewState` - Hidden field
  - `indexRenavam` - Hidden field (value="indexRenavam")
- **Botao submit:** `indexRenavam:confirma`
- **Retorno:** Dados administrativos, judiciais e caracteristicas do veiculo

### 4.2 CONSULTA DE INFRACOES
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/infracao/indexConsultaInfracao.jsf`
- **CAPTCHA:** Google reCAPTCHA v2
- **Form:** `indexForm`
- **Campos:**
  - `placa` - Placa do veiculo (7 caracteres)
  - `renavam` - Numero do RENAVAM (11 digitos)
  - `g-recaptcha-response` - Token do reCAPTCHA
  - `javax.faces.ViewState` - Hidden field
  - `indexForm` - Hidden field (value="indexForm")
- **Botao submit:** `confirma`

### 4.3 BOLETO LICENCIAMENTO ANO ATUAL
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/b/indexBLicencAnoAtual.jsf`
- **CAPTCHA:** Google reCAPTCHA v2
- **Form:** `indexBoletoAnoAtual`
- **Campos:**
  - `placa1` - Placa do veiculo (7 caracteres)
  - `renavam` - Numero do RENAVAM (11 digitos)
  - `g-recaptcha-response` - Token do reCAPTCHA
  - `javax.faces.ViewState` - Hidden field
  - `frmFlag:hidFlag` - Hidden field (value padrão "0", setado para "1" no submit)
- **Form auxiliar:** `frmFlag` (form separado para controle de flag)
- **Botao submit:** `confirma`

### 4.4 BOLETO LICENCIAMENTO ANO ANTERIOR
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/b/indexBLicencAnoAnterior.jsf`
- **CAPTCHA:** Google reCAPTCHA v2
- **Form:** `indexBoletoAnoAnterior`
- **Campos:**
  - `indexBoletoAnoAnterior:placa1` - Placa do veiculo (7 caracteres)
  - `indexBoletoAnoAnterior:renavam` - Numero do RENAVAM (11 digitos)
  - `g-recaptcha-response` - Token do reCAPTCHA
  - `javax.faces.ViewState` - Hidden field
- **Botao submit:** `indexBoletoAnoAnterior:confirma`

### 4.5 BOLETO INFRACAO (1a etapa - selecao)
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/b/indexBInfracao.jsf`
- **CAPTCHA:** Nenhum (1a etapa e apenas selecao)
- **Form:** `indexBoletoInfracao`
- **Campos:**
  - `indexBoletoInfracao:j_idt21` - Radio: `veiculosPara` (PA) ou `veiculosOutroEstado` (outro estado)
  - `javax.faces.ViewState` - Hidden field
- **Botao submit:** `indexBoletoInfracao:confirma`
- **Nota:** Apos a selecao, e redirecionado para uma 2a etapa com campos e CAPTCHA

### 4.6 CONSULTA GRAVAME
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexSNG.jsf`
- **CAPTCHA:** Google reCAPTCHA v2
- **Form:** `indexGravame`
- **Campos:**
  - `indexGravame:chassi` - Numero do chassi
  - `g-recaptcha-response` - Token do reCAPTCHA
  - `javax.faces.ViewState` - Hidden field

### 4.7 EMISSAO CRLV-e
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/crlv/indexCRLVe.jsf`
- **CAPTCHA:** Google reCAPTCHA v2
- **Form:** `indexCRLVe`
- **Campos:**
  - `indexCRLVe:cpfCnpj` - CPF ou CNPJ
  - `indexCRLVe:placa` - Placa do veiculo
  - `indexCRLVe:renavam` - Numero do RENAVAM
  - `g-recaptcha-response` - Token do reCAPTCHA
  - `javax.faces.ViewState` - Hidden field

### 4.8 CONSULTA PONTUACAO CNH
- **URL:** `https://sistemas-renach.detran.pa.gov.br/renach/renach-web/servicos/consultaPontuacao/indexConsultaPontuacao.jsf`
- **CAPTCHA:** JSF Image CAPTCHA (imagem gerada no servidor)
- **Form:** `formJSF`
- **Campos:**
  - `formJSF:cpf` - CPF do condutor (11 digitos)
  - `formJSF:senha` - Caracteres da imagem CAPTCHA (5 caracteres)
  - `javax.faces.ViewState` - Hidden field
  - `formJSF` - Hidden field (value="formJSF")
- **Botao submit:** `formJSF:j_id_jsp_1697595030_8` (Confirmar)
- **CAPTCHA Image URL:** Relative `../../imagem` -> `https://sistemas-renach.detran.pa.gov.br/renach/renach-web/servicos/consultaPontuacao/imagem`
- **Atualizar CAPTCHA:** Botao com JSF action `formJSF:j_id_jsp_1697595030_6`

### 4.9 PORTAL CONDUTOR (Boletos CNH)
- **URL:** `https://sistemas-renach.detran.pa.gov.br/renach/renach-web/servicos/portalCondutor/indexPortalCondutor.jsf`
- **CAPTCHA:** JSF Image CAPTCHA
- **Form:** `formJSF`
- **Campos:**
  - `formJSF:cpf` - CPF do condutor
  - `formJSF:registro` - Registro CNH
  - `formJSF:senha` - Caracteres da imagem CAPTCHA (5 caracteres)
  - `javax.faces.ViewState` - Hidden field

### 4.10 CERTIDAO NEGATIVA (1a etapa - selecao)
- **URL:** `https://sistemas-renach.detran.pa.gov.br/renach/renach-web/servicos/certidaoNegativa/indexCertidaoNegativa.jsf`
- **CAPTCHA:** Nenhum (1a etapa e apenas selecao)
- **Form:** `formJSF`
- **Campos:**
  - `formJSF:j_id_jsp_1898215000_4` - Radio: `0` (Emitir) ou `1` (Validar)
  - `javax.faces.ViewState` - Hidden field
- **Botao submit:** `formJSF:j_id_jsp_1898215000_7` (Confirmar)

### 4.11 CONSULTA EDITAL NOTIFICACAO INFRACAO
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexEdital.jsf`
- **CAPTCHA:** Provavelmente reCAPTCHA v2

### 4.12 ACOMPANHE SEU PROCESSO (Veiculo)
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexAcompanhaDocumento.jsf`

### 4.13 CONSULTA COMUNICACAO DE VENDA
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexAvisoTransf.jsf`

### 4.14 BOLETO LICENC. TRANSFER/JURISDICAO
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/b/indexBLicencTransf.jsf`

### 4.15 BOLETO PARCELAMENTO TAXAS
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/b/indexParcelamento.jsf`

### 4.16 AUTORIZACAO DE ESTAMPAGEM
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexEmiteAutorizacaoEstampagem.jsf`

### 4.17 CONSULTA VALIDA TRANSFERENCIA/JURISDICAO
- **URL:** `https://sistemas-renavam.detran.pa.gov.br/sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexValidaTransfJurisdicao.jsf`

### 4.18 RENACH - Outros servicos
- **Agendamento:** `/renach/renach-web/servicos/agendaExame/indexAgendaExame.jsf`
- **Acompanhamento PA:** `/renach/renach-web/servicos/acompanhamentoPA/indexAcompanhamentoPA.jsf`
- **Distribuicao Agenda:** `/renach/renach-web/servicos/distribuicaoAgenda/indexConsultaDistribuicaoAgenda.jsf`
- **Boleto Junta Medica/Reteste:** `/renach/renach-web/servicos/reExame/indexReExame.jsf`
- **Passaporte Biometrico:** `/renach/renach-web/servicos/biometria/indexPassaporteBiometrico.jsf`
- **Primeira Habilitacao:** `/renach/renach-web/servicos/primeiraHabilitacao/indexPrimeiraHabilitacao.jsf`

---

## 5. API REST do Portal (restrito.detran.pa.gov.br/api)

Endpoints disponiveis (sem autenticacao):

| Endpoint | Descricao |
|----------|-----------|
| GET `/api/banners` | Banners do portal |
| GET `/api/popups` | Popups do portal |
| GET `/api/menus` | Menu completo com links |
| GET `/api/perguntas` | FAQ |
| GET `/api/rede-atendimento` | Postos de atendimento |
| GET `/api/cfcs` | Auto escolas |
| GET `/api/clinicas` | Clinicas |
| GET `/api/estampadoras` | Estampadoras |
| GET `/api/editais` | Editais |
| GET `/api/editais/anos` | Anos dos editais |
| GET `/api/exames-toxicologicos` | Exames toxicologicos |
| GET `/api/locais` | Locais |
| GET `/api/vistorias` | Vistorias |
| GET `/api/radares` | Radares |
| GET `/api/news` | Noticias |
| GET `/api/links` | Links externos |
| GET `/api/agrupamento-links` | Grupos de links |

---

## 6. Resumo para Integracao 2Captcha

### reCAPTCHA v2 (SISTRANSITO)
```json
{
  "task_type": "RecaptchaV2TaskProxyless",
  "websiteURL": "https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexRenavam.jsf",
  "websiteKey": "6LfDIwMtAAAAAKL8RPTzJd_fDTfWCOZXDv79aJhK"
}
```

### Image CAPTCHA (RENACH)
```json
{
  "task_type": "ImageTask",
  "body": "<base64 da imagem CAPTCHA>"
}
```
- A imagem CAPTCHA e servida com cookie de sessao (JSESSIONID)
- Eh preciso fazer download da imagem usando a mesma sessao que sera usada para o submit

### Fluxo Completo de Consulta (Exemplo: Veiculo)

```
1. GET https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexRenavam.jsf
   -> Salvar cookie JSESSIONID
   -> Extrair javax.faces.ViewState do HTML
   -> Extrair action URL do form (se diferente)

2. Enviar reCAPTCHA v2 para 2Captcha
   -> websiteKey: 6LfDIwMtAAAAAKL8RPTzJd_fDTfWCOZXDv79aJhK
   -> websiteURL: (url da pagina)
   -> Aguardar resolucao (~20-60s)

3. POST para action URL com:
   Headers:
     Cookie: JSESSIONID=xxx
     Content-Type: application/x-www-form-urlencoded
   Body:
     indexRenavam=indexRenavam
     indexRenavam:placa1=ABC1234
     indexRenavam:renavam=12345678901
     g-recaptcha-response=<token_do_2captcha>
     javax.faces.ViewState=<valor_extraido>
     indexRenavam:confirma=Consultar Veiculo

4. Parsear HTML de resposta para extrair dados do veiculo
```

### Fluxo Completo de Consulta (Exemplo: Pontuacao CNH)

```
1. GET https://sistemas-renach.detran.pa.gov.br/renach/renach-web/servicos/consultaPontuacao/indexConsultaPontuacao.jsf
   -> Salvar cookie JSESSIONID
   -> Extrair javax.faces.ViewState do HTML

2. GET https://sistemas-renach.detran.pa.gov.br/renach/renach-web/servicos/consultaPontuacao/imagem
   Headers: Cookie: JSESSIONID=xxx
   -> Receber imagem CAPTCHA em base64

3. Enviar imagem CAPTCHA para 2Captcha
   -> Aguardar resolucao (~5-15s)

4. POST para action URL com:
   Headers:
     Cookie: JSESSIONID=xxx
     Content-Type: application/x-www-form-urlencoded
   Body:
     formJSF=formJSF
     formJSF:cpf=12345678901
     formJSF:senha=<texto_resolvido_2captcha>
     javax.faces.ViewState=<valor_extraido>
     formJSF:j_id_jsp_1697595030_8=Confirmar

5. Parsear HTML de resposta para extrair pontuacao
```

---

## 7. Sistemas Adicionais (Dashboards Publicos - Sem Login)

| Dashboard | URL | Tipo de dados |
|-----------|-----|---------------|
| Dashboard CNH | https://dashboard-cnh.detran.pa.gov.br/ | Estatisticas de CNH por municipio |
| Dashboard Infracoes | https://dashboard-infracao.detran.pa.gov.br/ | Estatisticas de infracoes |
| Dashboard Frota | https://dashboard-frota.detran.pa.gov.br/ | Estatisticas de frota veicular |

Estes dashboards sao Shiny (R) e possuem dados abertos com filtros interativos.

---

## 8. Portal do Cidadao (Venus)

- **URL Login:** https://servicos-cidadao.detran.pa.gov.br/
- **URL Home:** https://cidadao.detran.pa.gov.br/
- **Funcao:** Defesa de autucacao e Recurso de multa 100% online
- **Tecnologia:** Angular SPA (servicos-cidadao) + HTML/Bootstrap (cidadao)
- **Requer cadastro/login de cidadao**

---

## 9. Formularios Detalhados com Dados de Teste

### Dados de Teste Fornecidos
- **Placa:** OFS3J55
- **Renavam:** 00477026001
- **CPF:** 05532667217
- **Chassi:** 9C6KG0450B0010630

### 9.1 Boleto Infracao - Fluxo Multi-Etapas

**ETAPA 1:** Selecao de tipo de veiculo (SEM CAPTCHA)
- URL: `/sistransito/detran-web/servicos/b/indexBInfracao.jsf`
- Form: `indexBoletoInfracao`
- Campos:
  - `indexBoletoInfracao:j_idt21` - Radio: `veiculosPara` (PA) ou `veiculosOutroEstado`
- Submit: `indexBoletoInfracao:confirma` = "Continuar"

**ETAPA 2A (Veiculos do Para):** Redireciona para `indexBInfracaoPara.jsf`
- CAPTCHA: Google reCAPTCHA v2
- Campos:
  - `indexBoletoInfracao:placa1` - Placa (7 chars)
  - `indexBoletoInfracao:renavam` - Renavam (11 digitos)
  - `g-recaptcha-response`
- Submit: `indexBoletoInfracao:confirma`

**ETAPA 2B (Veiculos de Outro Estado):** Redireciona para `indexBInfracaoOutroEstado.jsf`
- CAPTCHA: Google reCAPTCHA v2
- Campos:
  - `indexBoletoInfracao:placa1` - Placa
  - `indexBoletoInfracao:renavam` - Renavam
  - `indexBoletoInfracao:cpfCnpj` - CPF/CNPJ
  - `indexBoletoInfracao:nomeCompleto` - Nome completo
  - `g-recaptcha-response`
- Submit: `indexBoletoInfracao:confirma`

### 9.2 Acompanhe seu Documento - Dois Modos

- URL: `/sistransito/detran-web/servicos/veiculos/indexAcompanhaDocumento.jsf`
- CAPTCHA: Google reCAPTCHA v2
- **Modo Renavam** (padrao):
  - `opcao` = `P` (radio, default checked)
  - `renavam` - Numero Renavam (11 digitos, obrigatorio)
  - `noBoleto` - Numero do Boleto (opcional, 15 digitos)
- **Modo Chassi:**
  - `opcao` = `C` (radio)
  - `chassi` - Numero Chassi (21 chars, obrigatorio)
  - `noBoleto` - Numero do Boleto (opcional)
- Form: `indexAcompanhaDocumento`
- Form auxiliar: `frmFlag` com `frmFlag:hidFlag`

### 9.3 Consulta Edital de Notificacao de Infracao

- URL: `/sistransito/detran-web/servicos/veiculos/indexEdital.jsf`
- CAPTCHA: Google reCAPTCHA v2
- Form: `formJSF`
- **ETAPA 1:** Selecao do tipo de busca (3 opcoes):
  - `j_idt22` = `1` - Consulta por CPF/CNPJ
  - `j_idt22` = `2` - Consulta por Placa/Renavam
  - `j_idt22` = `3` - Consulta por Chassi
- Submit: `confirma`
- **ETAPA 2:** Formulario com campos especificos do tipo selecionado

### 9.4 Certidao Negativa - Fluxo Multi-Etapas

**ETAPA 1** (SEM CAPTCHA): Selecione Emitir ou Validar
- `formJSF:j_id_jsp_1898215000_4` = `0` (Emitir) ou `1` (Validar)
- Submit: `formJSF:j_id_jsp_1898215000_7` = "Confirmar"

**ETAPA 2** (apos "Emitir"): Pedira CPF e CAPTCHA imagem
- Campos: CPF + caracteres da imagem CAPTCHA (5 chars)

### 9.5 Pagina de Erro (SISTRANSITO)

Quando o reCAPTCHA falha, o sistema redireciona para `/sistransito/detran-web/servicos/veiculos/erro.jsf` com:
- Titulo: "Ops! Ocorreu um Erro"
- Subtitulo: "Nao foi possivel concluir a solicitacao."
- Estrutura HTML:
  ```html
  <div class="error-alert">
    <div class="alert-content">
      <p class="alert-title">Atencao!!</p>
      <ul><li> Verificacao reCAPTCHA invalida. Tente novamente.</li></ul>
    </div>
  </div>
  <a href="../veiculos/indexRenavam.jsf" class="btn-back">
    <i class="material-icons">arrow_back</i> Voltar
  </a>
  ```
- Form de erro: `erroPadrao:frmErro` com action `/sistransito/detran-web/servicos/veiculos/erro.jsf`

---

## 10. Regras de Submissao JSF (CRITICAL)

### Sessao e ViewState
1. **Sempre faca GET primeiro** para obter `JSESSIONID` (cookie) e `javax.faces.ViewState` (hidden field)
2. O `JSESSIONID` aparece tanto no cookie quanto na URL do form action (`;jsessionid=xxx`)
3. Use sempre o URL completo do form action (com jsessionid)
4. Op `javax.faces.ViewState` muda a cada request - SEMPRE extraia o novo valor

### Cookies
- `JSESSIONID` - Sessao do servidor JSF (obrigatorio)
- `INGRESSCOOKIE` - Cookie de balanceamento (retornado automaticamente)

### Multi-Etapas
- Boleto Infracao: Etapa 1 (selecao) -> Etapa 2 (dados + captcha)
- Certidao Negativa: Etapa 1 (selecao) -> Etapa 2 (dados + captcha)
- Edit Notificacao: Etapa 1 (tipo de busca) -> Etapa 2 (dados + captcha)
- Cada etapa gera novo ViewState que deve ser usado na proxima

### Renach vs Sistransito (Diferencas Importantes)

| Aspecto | SISTRANSITO | RENACH |
|---------|-------------|--------|
| Framework | JSF moderno (PrimeFaces) | JSF antigo (RichFaces) |
| CAPTCHA | Google reCAPTCHA v2 | Imagem gerada no servidor |
| ViewState | Formato longo (`-123:456`) | Formato curto (`_id52910`) |
| CSS | Material Design customizado | Bootstrap Material Kit |
| URL Imagem CAPTCHA | N/A | `/renach/renach-web/imagem` (com cookie JSESSIONID) |
| Campo CAPTCHA | `g-recaptcha-response` | `formJSF:senha` (5 caracteres) |
| Botao Atualizar CAPTCHA | N/A | `formJSF:j_id_jsp_1697595030_6` |
| Erro Page | Pagina formal com CSS | Alert JavaScript inline |

---

## 11. Notas Importantes para Implementacao

1. **JSESSIONID e essencial** - Todos os sistemas JSF mantem estado de sessao. Sempre inclua o cookie.
2. **javax.faces.ViewState** - Deve ser extraido do HTML da pagina inicial e enviado no POST.
3. **Form action URLs** contem jsessionid - Sempre use a URL completa do action do form.
4. **Os sistemas RENACH e SISTRANSITO usam frameworks JSF diferentes** - O RENACH e mais antigo (RichFaces) e o SISTRANSITO e mais recente (PrimeFaces/Material Design).
5. **reCAPTCHA v2** usa callback JavaScript `validarRecaptcha()` que chama `grecaptcha.getResponse()`.
6. **Image CAPTCHA** do RENACH serve a imagem em `/renach/renach-web/imagem` com o mesmo JSESSIONID.
7. **Alguns servicos tem multi-etapas** (ex: Boleto Infracao, Certidao Negativa, Edital Notificacao) - primeiro selecione opcao, depois preencha dados.
8. **Os campos `autoTab` e `nn_KeyWeb`** sao validacoes JavaScript do lado cliente - nao afetam a submissao server-side.
9. **Campos obrigatorios** marcados com `*` nos placeholders (ex: "Placa *", "Renavam *")
10. **A funcao `padRenavam()` no CRLV-e** adiciona zero a esquerda se o renavam tiver 10 digitos.
11. **Campo `frmFlag:hidFlag`** em alguns forms controla refresh de pagina apos voltar (valor 0 ou 1).
12. **Pagina de erro** do SISTRANSITO redireciona para `erro.jsf` com CSS design-system e mensagem de erro especifica.
13. **Placa no SISTRANSITO** usa `toUpperCase()` no blur para maiusculas automaticas.
14. **A funcao `nn_KeyWeb()`** permite apenas numeros nos campos renavam e CPF.

---

## 12. Integracao 2Captcha - Configuracoes Especificas

### reCAPTCHA v2 (SISTRANSITO)
```
POST https://2captcha.com/in.php
- method: userrecaptcha
- googlekey: 6LfDIwMtAAAAAKL8RPTzJd_fDTfWCOZXDv79aJhK
- pageurl: https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexRenavam.jsf
- Retorno: g-recaptcha-response token (valido por ~2 minutos)
```

### Image CAPTCHA (RENACH)
```
1. Fazer GET na pagina JSF para obter JSESSIONID
2. Fazer GET em https://sistemas-renach.detran.pa.gov.br/renach/renach-web/imagem
   com Cookie: JSESSIONID=xxx
   -> Retorna imagem JPEG (~4KB)
3. Converter imagem para base64
4. POST https://2captcha.com/in.php
   - method: base64
   - body: <imagem_base64>
   - maxlen: 5
   - numeric: 0  (pode conter letras)
5. Resolver e enviar no campo formJSF:senha
```

### Fluxo Completo de Automacao (Pseudocodigo)

```python
# Exemplo: Consulta Veiculo Detalhada
1. session = requests.Session()
2. r = session.get("https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web/servicos/veiculos/indexRenavam.jsf")
3. viewstate = extrair_viewstate(r.text)
4. captcha_token = resolver_recaptcha_v2(API_KEY, "6LfDIwMtAAAAAKL8RPTzJd_fDTfWCOZXDv79aJhK", r.url)
5. data = {
     "indexRenavam": "indexRenavam",
     "indexRenavam:placa1": "OFS3J55",
     "indexRenavam:renavam": "00477026001",
     "g-recaptcha-response": captcha_token,
     "javax.faces.ViewState": viewstate,
     "indexRenavam:confirma": "Consultar Veiculo"
   }
6. r = session.post(action_url, data=data)
7. resultado = parsear_html_veiculo(r.text)
```

```python
# Exemplo: Consulta Pontuacao CNH
1. session = requests.Session()
2. r = session.get("https://sistemas-renach.detran.pa.gov.br/renach/renach-web/servicos/consultaPontuacao/indexConsultaPontuacao.jsf")
3. viewstate = extrair_viewstate(r.text)
4. r_captcha = session.get("https://sistemas-renach.detran.pa.gov.br/renach/renach-web/imagem")
5. captcha_text = resolver_imagem_captcha(API_KEY, base64(r_captcha.content), maxlen=5)
6. data = {
     "formJSF": "formJSF",
     "formJSF:cpf": "05532667217",
     "formJSF:senha": captcha_text,
     "javax.faces.ViewState": viewstate,
     "formJSF:j_id_jsp_1697595030_8": "Confirmar"
   }
7. r = session.post(action_url, data=data)
8. resultado = parsear_html_pontuacao(r.text)
```
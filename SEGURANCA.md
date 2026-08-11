# Segurança do Dashboard AON 26

Este documento descreve como o painel é protegido, o que está pendente e o passo a passo da migração para login real.

---

## Situação atual (antes da migração)

| Camada | Estado | Vale como proteção? |
|---|---|---|
| Senha na tela (`jdc123`) | Ativa | **Não.** Está escrita no código-fonte da página; qualquer visitante lê em dois cliques |
| `robots.txt` + `noindex` | Ativo | Parcialmente. Reduz indexação, mas é um pedido — não impede acesso |
| Repositório GitHub | Público | **Não.** Expõe o código e as URLs das planilhas |
| Planilhas Google | "Qualquer pessoa com o link" | **Não.** Quem tem a URL lê nome, e-mail e telefone de todos os leads |

**Conclusão:** hoje o painel não tem controle de acesso. Quem tiver o link entra.

---

## Por que o GitHub Pages não resolve

Duas limitações de plataforma, verificadas:

1. **Pages a partir de repositório privado exige GitHub Pro** (pago). No plano free, só repositório público publica.
2. **Mesmo no Pro, o site continua público.** Publicar um site do Pages de forma privada só existe no GitHub Enterprise Cloud.

Ou seja: não há combinação de GitHub Pages que entregue repositório privado + login, sem plano corporativo.

---

## Arquitetura escolhida (gratuita)

```
GitHub (repo PRIVADO)
        ↓ push
Cloudflare Pages          ← deploy automático, grátis
        ↓
Cloudflare Access         ← login obrigatório, grátis até 50 usuários
        ↓
  Dashboard (.pages.dev)
```

- **Repositório privado**: gratuito e ilimitado no GitHub.
- **Cloudflare Pages**: conecta no repositório privado e republica a cada push, como o GitHub Pages fazia.
- **Cloudflare Access**: portal de login antes da página. Lista de e-mails autorizados; quem entra recebe um código de uso único por e-mail (ou entra pela conta Google). Plano Zero Trust free cobre até 50 usuários.

O que muda na prática: a URL deixa de ser `*.github.io` e passa a ser `*.pages.dev`.

---

## Passo a passo

### 1. Tornar o repositório privado

GitHub → repositório → **Settings** → role até **Danger Zone** → **Change repository visibility** → **Make private**.

> Isso desativa o GitHub Pages atual. É esperado — o Cloudflare Pages assume no passo 3.

### 2. Criar conta no Cloudflare

[dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up) — gratuita, não pede cartão e não exige domínio próprio.

### 3. Publicar pelo Cloudflare Pages

1. No painel do Cloudflare: **Compute (Workers & Pages)** → **Create** → aba **Pages** → **Connect to Git**
2. Autorize o GitHub e escolha o repositório `thegreatdashboard`
3. Configuração de build:
   - **Framework preset:** `None`
   - **Build command:** deixe **vazio**
   - **Build output directory:** `/`
4. **Save and Deploy**

Em cerca de um minuto o painel estará em `https://<nome-do-projeto>.pages.dev`. Cada `git push` na `main` republica sozinho.

### 4. Ligar o login (Cloudflare Access)

1. No painel do Cloudflare: **Zero Trust** → na primeira vez, escolha o plano **Free** (até 50 usuários)
2. **Access** → **Applications** → **Add an application** → **Self-hosted**
3. Configure:
   - **Application name:** `Dashboard AON 26`
   - **Session duration:** `24 hours` (com que frequência pede login de novo)
   - **Subdomain:** `*`  ·  **Domain:** `pages.dev`  ·  **Path:** vazio

   > O `*` é o que protege também a URL de produção, não só as prévias.
4. **Next** → crie a política:
   - **Policy name:** `Time autorizado`
   - **Action:** `Allow`
   - **Include:** `Emails` → adicione os e-mails autorizados, um por linha
5. Em métodos de login, deixe ativo **One-time PIN** (código por e-mail) e, se quiser, **Google**
6. **Save**

### 5. Conferir

- Abrir a URL em uma **janela anônima** → deve aparecer a tela de login do Cloudflare, não o dashboard
- Entrar com um e-mail autorizado → recebe o código e acessa
- Tentar com um e-mail fora da lista → acesso negado

### 6. Remover a senha da tela

Depois que o passo 5 estiver confirmado, a senha em JavaScript vira só atrito: quem passou pelo Access já está autenticado de verdade. Peça a remoção do bloco de autenticação do `index.html`.

---

## Pendência importante: as planilhas

O login acima protege o **painel**. Ele não protege as **planilhas**, que continuam compartilhadas como "qualquer pessoa com o link".

E há um agravante: **o repositório foi público até agora**, com as URLs das planilhas no código. Quem já clonou ou leu o histórico tem essas URLs para sempre — tornar o repositório privado agora não desfaz isso.

Para fechar de verdade:

1. No Google Drive, mudar cada planilha de "qualquer pessoa com o link" para **pessoas específicas**
2. Publicar um **Google Apps Script** como Web App na conta dona das planilhas, que as lê pelo servidor (`SpreadsheetApp.openById`) e devolve os dados já filtrados
3. Apontar o dashboard para esse Web App em vez das URLs diretas

Isso elimina de uma vez a exposição das planilhas **e** os proxies públicos de terceiros (`corsproxy.io`, `allorigins.win`, `codetabs.com`), por onde hoje passam os dados de todos os leads.

Enquanto esse passo não acontece, o risco fica assim: painel protegido, planilhas acessíveis a quem tiver as URLs antigas.

---

## Camadas já ativas no repositório

- **`robots.txt`** — `Disallow: /` geral mais blocos nomeados para crawlers de IA, indexadores e raspadores
- **Meta `noindex`** — em `index.html` e `testes.html`, para crawlers que ignoram o `robots.txt`
- **`_headers`** — cabeçalhos aplicados pelo Cloudflare Pages: `X-Robots-Tag` no servidor, `frame-ancestors 'none'` (anti-clickjacking), `nosniff`, `no-referrer`, HSTS e `no-store` para os dados não ficarem em cache de intermediários
- **`.gitignore`** — impede que planilhas e exportações voltem ao versionamento

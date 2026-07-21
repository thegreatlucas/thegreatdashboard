# Dashboard AON 26 — John Deere Construção

Dashboard 100% client-side para acompanhamento de leads das campanhas AON 26 (Brasil, Argentina, México). Não tem backend, banco de dados nem build step — é um único `index.html`.

---

## Arquitetura Geral

```
Google Sheets (por dealer)
        ↓  export?format=csv  (via proxy CORS)
  parseLeadsFromCSV()         — detecção dinâmica de colunas
        ↓
  applyFilter()               — filtragem por campanha + data + país
        ↓
  renderDealerCards()         — cards por dealer            [aba Visão Geral]
  renderNegRadar()            — radar de negociações abertas [aba Visão Geral]
  renderObsAnalysis()         — análise de observações       [aba Visão Geral]
  renderSales()               — vendas efetuadas             [aba Visão Geral]
  renderAnalytics()           — funil, timeline, produtos    [aba Visão Geral]
  renderAdvancedAnalytics()   — mídia, geo, SLA, perfil,
                                perdas, higiene, semanal     [aba Análises Avançadas]
```

Tudo roda no browser. O dado persiste em `localStorage` como cache de emergência (se os proxies falharem, lê o cache mais recente).

---

## Autenticação

- Senha: `jdc123` (case-insensitive)
- Armazenada em `sessionStorage` como flag `jd_auth`
- Persiste durante a sessão; some ao fechar o browser

---

## Fetching de Dados

### Proxy Rotation (`fetchWithProxyFallback`)

Google Sheets bloqueia CORS direto. O dashboard tenta 3 proxies em paralelo com `Promise.any()` — o primeiro que responder vence:

1. `corsproxy.io`
2. `allorigins.win`
3. `codetabs.com`

Timeout por proxy: **8 segundos** (AbortController). Se todos falharem, cai no cache local.

### Cache localStorage

- Chave: `cache_{DEALER_NAME}` e `cache_General_{COUNTRY}`
- Salvo a cada fetch bem-sucedido
- Lido automaticamente se proxy falhar

---

## DEALERS_CONFIG

Cada dealer é uma entrada no objeto `DEALERS_CONFIG`:

```js
"Nome do Dealer": {
  country: "BR" | "AR" | "MX",
  sheetUrl: "https://docs.google.com/spreadsheets/d/...",
  statusCol: "Nome exato da coluna de status",
  postStatusCol: "Nome exato da coluna de pós-status"
}
```

- **country**: Controla qual planilha geral AON é usada para cross-reference de emails
- **statusCol / postStatusCol**: Matching é case-insensitive e tolera variações de hífen/espaço

Dealers ativos: 11 BR, 4 AR, 3 MX + 1 entrada virtual (Expoagro AR).

---

## Parsing de CSV (`parseLeadsFromCSV`)

### Detecção de Colunas

As planilhas dos dealers não têm cabeçalho padronizado. O parser usa normalização + matching fuzzy:

```js
normalizeString(str)
  → trim → lowercase → remove acentos → underscore vira espaço
```

| Campo | Como detecta |
|---|---|
| **Máquina** | Varre as primeiras 30 linhas procurando valores como `retroescava`, `escavadeira`, `cargadora`, `tractor` etc. Coluna com >2 hits vence. Fallback: header com `tipo de maquina` |
| **Status** | Match no nome do header via `config.statusCol` |
| **AON?** | Match exato: `key.trim() === 'AON?'` |
| **Nome** | Header com `nome`, `nombre`, `name`, `razao social`, `razon social` |
| **Email** | Header contendo `mail` ou `correo` |
| **Telefone** | Header contendo `tele`, `phone` ou igual a `whatsapp` |
| **Data** | Match exato em `data`, `fecha`, `data do lead` |
| **Frota** | Header com `ja tem maquina`, `tem maquinaria`, `frota`, `equipamento`, `actualmente`, `cuentas con` |
| **Setor/Negócio** | Header com `aplica`, `setor`, `negocio`, `ramo`, `principal` |
| **Prazo** | Header com `planeja`, `prazo`, `cuando`, `renovar` |
| **Pagamento** | Header com `pagamento` ou `pago` |
| **Condição** | Header com `nova` ou `nueva` |

### Campos Extraídos por Lead

```js
{
  status, postStatus,           // colunas de qualificação
  aonRaw, hasAonCol,            // coluna AON? (preservada sem normalizar)
  dateRaw,                      // data combinada (fórmula + valor)
  nameRaw,                      // nome (sem normalizar)
  email, phone,                 // normalizados
  machineRaw, lossRaw,          // normalizados
  fleetRaw, conditionRaw,       // normalizados
  applicationRaw, timeframeRaw, // normalizados
  paymentRaw,                   // normalizado
  rawAll                        // concatenação de todas as células (para busca livre)
}
```

### Deduplicação

Dentro da mesma planilha, leads com mesmo email são deduplicados. Fica o de maior prioridade de status:

```
venda efetuada (isSaleLead)      → 4
qualificado / calificado        → 3
negociac / propuesta / cotizando → 2
aguardando / contactado          → 1
outros                           → 0
```

Leads sem email nunca são deduplicados.

### Filtro de Linhas Fantasma

Linhas onde nenhuma célula tem conteúdo real são descartadas (`skipEmptyLines: 'greedy'` + check de `hasContent`). Isso resolve o problema de planilhas com Google Sheets Tables que exportam linhas de formatação.

---

## Parsear Datas (`parseDateAny`)

Suporta 3 formatos + fallback nativo:

```
Date(2026, 2, 19)   → mês 0-indexed (formato Google Sheets)
19/03/2026          → DD/MM/YYYY (separador qualquer)
2026-03-19          → ISO YYYY-MM-DD
qualquer outra coisa → new Date(str) nativo
```

Retorna `Date` ou `null`.

---

## Filtros de Campanha

Todos os filtros são inclusivos com lógica **OR**: um lead passa se satisfizer qualquer filtro ativo.

### AON 26 (`aon`)

Cross-reference de email com a planilha geral AON de cada país.

```
lead.email ∈ GENERAL_AON_EMAILS[país]
```

**Fallback para AR/MX** (sem coluna de email confiável):
```
!lead.email AND data >= DATA_INÍCIO_AON[país]
```

Datas de início AON: BR `20/11/2025`, AR `19/11/2025`, MX `21/11/2025`

### ExpertConnect (`expertconnect`)

```
(nameRaw OU phone preenchido)          ← não é linha fantasma
AND applicationRaw vazio               ← sem setor/negócio
AND fleetRaw vazio                     ← sem pergunta de frota
AND (data >= 01/12/2025 OU sem data)   ← janela temporal EC
AND !isConexpo(lead)                   ← não é lead Conexpo
```

**Racional:** leads do Meta sempre têm setor e frota preenchidos (campos do formulário). EC usa formulário diferente — não tem essas perguntas. A combinação de ambos vazios + janela de data é o identificador.

### OLX (`olx`)

```
'olx' ∈ lead.rawAll
```

Busca simples na concatenação de todas as células do lead.

### Conexpo (`conexpo`)

```
dateRaw normalizado ∈ ['19/03', 'date(2026,2,19)']
```

Evento Conexpo-CONSTRÓI: 19/03/2026.

### Expoagro (`expoagro`)

Leads cujo email ou telefone está na lista `EXPOAGRO_EMAILS` / `EXPOAGRO_PHONES`, populada a partir da planilha geral AR com `campaign_name` contendo `expo`.

Deduplicação: se o mesmo lead aparecer em dealer AR e em Expoagro, o dealer AR tem prioridade.

### 2025 (`2025`)

```
YEAR(dateRaw) <= 2025
```

Leads legados da campanha AON 2025.

### Geral (`all`)

Sem filtro — mostra tudo. Exclusivo: ativar `all` desativa os outros.

---

## Algoritmo de Calor (`calcNegHeat`)

Score de 0 a 10 para cada negociação aberta. Fórmula:

```
SCORE = MIN(10, MAX(0, BASE + DIAS_MOD + PRAZO_BONUS))
```

### BASE (0–6) — qualidade do comentário

Scan do campo `lossRaw` (observação/comentário do vendedor):

| Score | Condição |
|---|---|
| **0** | Palavra de descarte: `desistiu`, `cancelou`, `sem interesse`, `sin interes`, `nao quer`, `no quiere`, `perdemos`, `parou` |
| **6** | Urgência: `urgente`, `urgencia`, `imediato`, `essa semana`, `lo antes posible`, `vai fechar`, `vamos fechar`, `fecha`, `quer fechar`, `quiero cerrar` |
| **4** | Interesse claro: `interessado`, `interesado`, `proposta`, `propuesta`, `avancando`, `acordo`, `positivo`, `confirmado`, `reuniao agendada`, `visita agendada` |
| **2** | Atividade: `gostou`, `reuniao`, `demo`, `visita`, `ligamos`, `retorno` |
| **1** | Incerto: `talvez`, `quizas`, `ver se`, `avaliar`, `pensar`, `aguardando decisao` |
| **2** | Qualquer comentário com >5 chars sem keyword |
| **0** | Sem comentário |

Palavras de descarte aplicam **override imediato** (score = 0, ignora resto).

### DIAS_MOD — recência do lead

```
sem data              →  0
≤ 30 dias             → +4   (lead fresco)
31–90 dias            → +1   (ciclo normal de máquinas)
> 90 dias             → −3   (negociação estagnada)
```

Benchmark: ciclo de venda de equipamentos de construção = 60–120 dias.

### PRAZO_BONUS (+1)

Se `timeframeRaw` contém: `imediato`, `imediata`, `esse mes`, `este mes`, `30 dias`, `curto prazo`.

### Classificação Final

| Score | Label | Cor |
|---|---|---|
| ≥ 7 | 🔥 Quente | Vermelho `#FF453A` |
| 4–6 | ⚡ Morno | Laranja `#FF9500` |
| < 4 | ❄️ Frio | Azul `#64D2FF` |
| sem dados | — | Cinza |

---

## Radar de Negociações

Exibe todas as negociações em aberto (status contendo `negocia`, `se envia propuesta`, `venta sujeta a obra`, `cotizando obra`). Leads detectados como venda efetuada (`isSaleLead`) são excluídos do radar — venda fechada não é negociação em aberto.

- Ordenação: score DESC, data ASC
- Default: top 5, expansível para ver todos
- Colunas: Distribuidor · Lead · Máquina · Temperatura · Score · Data · Dias em Aberto · Observação · Detalhes
- **Dias em Aberto**: verde ≤7d, laranja ≤30d, vermelho >30d
- Modal fullscreen com navegação prev/next entre negociações

---

## Exportação XLSX (`exportNegXLSX`)

Gera `negociacoes_aon26_YYYYMMDD.xlsx` com layout John Deere:

- **Linha 1**: Título mergeado, fundo JD Yellow `#FFD100`
- **Linha 2**: Subtítulo com timestamp, contagem de negociações e breakdown de temperatura
- **Linha 3**: Divisor amarelo
- **Linha 4**: Headers (fundo preto, texto JD Yellow)
- **Linhas 5+**: Dados, rows alternadas em dois tons escuros
- **Linhas 5+ formatação condicional**:
  - Distribuidor: bold amarelo
  - Temperatura: cor de acordo com calor (vermelho/laranja/azul)
  - Score: fundo tintado por calor
  - Dias em Aberto: verde/laranja/vermelho
- **Primeiras 4 linhas congeladas** (freeze panes)

Biblioteca: ExcelJS v4.4.0 (CDN).

---

## Analytics (`renderAnalytics`)

### Funil de Conversão
```
Brutos (100%)
→ Atendidos (X%)
→ Qualificados (Y% dos atendidos)
→ Negociando (Z% dos qualificados)
→ Vendas (verde, share do total)
```

### Timeline (Chart.js)
Linha de leads por data. Cor JD Yellow, fill semi-transparente, curva suave (tension 0.4).

### Top Produtos
Top 10 tipos de máquina por frequência.

### Motivos de Perda
Agrupamento semântico de comentários de perda:

| Grupo | Palavras-chave |
|---|---|
| PREÇO / VALOR EXTREMO | `preco`, `caro`, `valor` |
| PERDA PARA CONCORRÊNCIA | `concorren*`, `caterpillar`, `komatsu` |
| LEAD CURIOSO / ESPECULADOR | `curio*`, `so queria saber` |
| ESTUDANTE / TRABALHO ACADÊMICO | `estudan*`, `escola`, `tcc` |
| REPROVAÇÃO DE CRÉDITO | `credito`, `financia*`, `reprov*`, `banco` |
| BUSCANDO PEÇAS / SERVIÇO | `peca`, `mecanic*`, `oficina` |
| BUSCANDO USADOS | `usad*`, `seminov` |
| OUTROS MOTIVOS MISTOS | comentário >25 chars sem keyword |

---

## Abas de Visualização

O dashboard tem duas abas (`switchView`): **Visão Geral** (KPIs, países, funil, radar, observações, vendas, dealers) e **Análises Avançadas**. Ambas respeitam os filtros globais de campanha, país e período.

### Aba Análises Avançadas (`renderAdvancedAnalytics`)

| Análise | Fonte | Descrição |
|---|---|---|
| **Performance de Mídia** | Planilha geral (`ad_name`, `platform`, `is_organic`) × status do dealer via e-mail | Top anúncios com tx de qualificação e neg+vendas; split Instagram/Facebook/orgânico |
| **Geografia** | `Região`/`Cidade` do dealer, fallback `state`/`city` da geral | Top estados com % qual; top cidades |
| **SLA** | Coluna `Data do início da negociação` | Dias lead→negociação por dealer (média) + distribuição em buckets |
| **Perfil × Conversão** | `timeframeRaw` × `paymentRaw` | Matriz com % que avançou (neg/venda); segmentos de frota (conquest) |
| **Perdas Detalhadas** | Coluna `Porque não prosseguiu com a compra` | Motivos agrupados, perdas por máquina, concorrentes citados |
| **Higiene de Dados** | Todas as colunas | Score de completude por dealer (status, data, observações, data de negociação) |
| **Tendência Semanal** | `dateRaw` | Chart.js: leads e qualificados por semana (segunda-feira como âncora) |

Helpers centrais: `leadOutcome()` (desfecho canônico: sale > neg > qual > desq > other), `rankedBarsHtml()` (barras rankeadas reutilizáveis), `groupLossReason()` (agrupamento semântico de perdas — keywords sem acento, pois os textos passam por `normalizeString`).

---

## Efeitos Visuais

- **Parallax**: 3 orbs desfocados fixos ao fundo (`.parallax-layer`) que se movem em velocidades diferentes no scroll (rAF-throttled).
- **Scroll reveal**: seções com classe `.reveal` aparecem com fade/slide via IntersectionObserver.
- **Contadores animados**: KPIs principais fazem tween numérico (`setKpi`, 600ms ease-out).
- Todos os efeitos são desativados com `prefers-reduced-motion: reduce`.

---

## Alertas de Novas Vendas

- **Auto-sync**: com o dashboard aberto, as planilhas são re-buscadas a cada 10 min em modo silencioso (sem overlay de loading).
- **Detecção**: snapshot acumulativo das vendas conhecidas em `localStorage` (`jd_known_sales_v1`), chave = `dealer|email→phone→nome`. Falha temporária de planilha não gera re-alerta (snapshot é união, nunca encolhe). Primeira execução registra o histórico sem alertar.
- **Toast**: card verde no canto inferior direito para cada venda nova (máx. 4 + resumo), auto-dismiss em 12s.
- **Notificação do navegador**: opt-in pelo botão 🔔 Alertas no header (pede permissão via Notification API); funciona com a aba em segundo plano.
- **Preferência** (`jd_sale_alerts`): `on` = toast + notificação · não definido = só toast · `off` = silêncio total.

---

## Vendas Efetuadas (`isSaleLead` / `renderSales`)

Um lead é venda quando `status + postStatus` (normalizados) contêm `vend`, `venta`, `faturad` ou `facturad` **e não** contêm nenhum termo da blacklist:

```
sujeta (venta sujeta a obra = negociação), perdid, cancel,
vendedor, revenda, "sem ", "sin ", "nao ", "no "
```

- KPI "Vendas Efetuadas" no grid principal (verde)
- Contador "Vendas" no card de cada dealer
- Etapa "Vendas" no funil de conversão
- Seção "Vendas Efetuadas": chips (total, por país, top dealer, % conversão sobre negociações+vendas) + tabela (Distribuidor · Cliente · Máquina · Status · Data · Pagamento · Observação · Detalhes)
- Modal de detalhe compartilhado com o radar (`openSaleDetail`)
- Na deduplicação por e-mail, o registro de venda tem prioridade máxima

---

## Análise de Observações (`renderObsAnalysis`)

Classifica o campo Observações (`lossRaw`) dos leads **em negociação** em 7 temas, reutilizando as listas de palavras do `calcNegHeat`:

| Tema | Fonte | Cor |
|---|---|---|
| Urgência / Fechamento | HOT_WORDS | vermelho |
| Interesse Claro | WARM_WORDS | laranja |
| Atividade / Follow-up | MILD_WORDS | amarelo |
| Indecisão | NEG_WORDS | azul |
| Risco de Perda | DEAD_WORDS (precedência máxima) | rosa |
| Outros Comentários | comentário >5 chars sem keyword | cinza |
| Sem Observação | vazio/nan/≤5 chars | cinza escuro |

Componentes:
- Barras por tema (clicáveis — abrem drill-down com os comentários do tema)
- Diagnóstico: % com observação, sinais de compra (quente+morno), negociações >30d abertas, média de palavras por observação
- Alertas: negociações sem observação e negociações com linguagem de desistência

---

## Normalização de Máquinas (`normalizeMachine`)

Padroniza variações PT/ES para nome canônico:

| Entrada | Saída |
|---|---|
| RETROESCAV* | RETROESCAVADEIRA |
| MINI ESC* | MINIESCAVADEIRA |
| ESCAV* | ESCAVADEIRA |
| MINI CAR* | MINICARREGADEIRA |
| PA CARREG* / CARGADOR* | PÁ-CARREGADEIRA |
| MOTONI* / NIVELA* | MOTONIVELADORA |
| TRATOR* / TRACTOR* | TRATOR DE ESTEIRA |
| ROLO* / COMPACTA* | ROLO COMPACTADOR |
| <3 chars / INDEFINIDO | — |

---

## Filtro de Data e País

- **Filtro de data**: range inclusivo [início 00:00, fim 23:59]. Afeta leads dos dealers e leads órfãos.
- **Filtro de país**: só afeta a grade de cards de dealers. Métricas globais sempre mostram todos os países.

---

## Hierarquia de Identidade do Lead (`leadIdent`)

```
1. nameRaw  (se preenchido)
2. email    (se não for 'nan')
3. phone    (se não for 'nan')
4. '—'      (fallback)
```

---

## Notas para Futuras Sessões

- **Adicionar dealer**: inserir entrada em `DEALERS_CONFIG` com `country`, `sheetUrl`, `statusCol`, `postStatusCol`.
- **Ajustar critério EC**: função `isExpertConnect()` — modificar campos checados ou janela de data.
- **Ajustar calor**: função `calcNegHeat()` — arrays de keywords e valores de `daysMod` são os principais alvos.
- **Novo filtro de campanha**: adicionar botão no HTML + case no `passesFilter()` + lógica de detecção própria.
- **Colunas novas no XLSX**: array `columns` em `exportNegXLSX()` + campo correspondente extraído em `parseLeadsFromCSV()`.
- **Planilha geral (cross-reference AON)**: `loadGeneralSheets()` — uma por país, popula `GENERAL_AON_EMAILS` e `EXPOAGRO_EMAILS/PHONES`.
- **Critério de venda**: função `isSaleLead()` — palavras-chave e blacklist.
- **Temas de observação**: array `OBS_THEMES` + `classifyObsTheme()`.
- **Fonte**: Uni Sans (via fonts.cdnfonts.com) com fallback Montserrat/Inter/Bebas Neue.
- **Segurança de render**: todo conteúdo vindo das planilhas deve passar por `escapeHtml()` antes de entrar em `innerHTML`.
- **Categoria de máquina**: `machineCategory()` é a fonte única para analytics/modal; `normalizeMachine()` é a variante de exibição (retorna `—`).
- **Nova análise avançada**: adicionar card no HTML da aba `#view-advanced` + função `renderAdv*()` chamada em `renderAdvancedAnalytics()`.
- **Colunas novas do dealer**: extrair em `parseLeadsFromCSV` (já extrai `regionRaw`, `cityRaw`, `negStartRaw`, `noBuyRaw`).
- **Campos novos da geral**: `loadGeneralSheets()` já captura `campaign`, `ad`, `platform`, `organic`, `state`, `city`.

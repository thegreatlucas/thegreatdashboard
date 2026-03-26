# 📖 LEIA-ME: Documentação Técnica Completa do Dashboard AON 26

Este documento detalha o funcionamento, as lógicas vitais, e as opções de hospedagem e evolução do sistema entregue.

---

## Arquitetura (Design & Fluxo)

A aplicação foi desenhada de forma **100% Client-Side**. Isso significa que **não exige nenhum tipo de servidor backend** (Node.js, PHP, etc) nem Banco de Dados. Todo o processamento e a junção dos dados ocorrem diretamente no navegador do usuário através do arquivo final HTML entregue.

A lógica contínua do dashboard executa os seguintes passos rotineiros:
1. **Extração Dinâmica de URL**
   - O objeto JS `DEALERS_CONFIG` gerencia as URLs. Internamente o regex tira o Sheet ID e formata a pesquisa.
2. **Fetch API Endpoint**
   - Utilizamos o Endpoint de Visualização Pública do Google (`/gviz/tq`), que tem menos limite de "throttle/timeout" que as URLs de Export usuais de CSV/Excel da plataforma.
3. **Processamento Paralelo**
   - Realização das 16 leituras usando `Promise.all()`. Isso evita a demora sequencial, de forma que o Dashboard pode varrer 16 planilhas geralmente sob ~1-2 segundos de resposta.
4. **Transformação Dinâmica (Agnóstica a Índices)**
   - Algumas planilhas tem a coluna `"Status"` na N e outras na M. O algoritmo resolve indexações aleatórias escaneando dinamincamente o `table.cols` pelo nome sem prender-se a colunas estáticas como `A, B, C...`.
5. **DOM Dinâmico**
   - Atualização completa do Painel Visual na injeção dos dados já compilados.

## A lógica GVIZ do Google Sheets

A API Pública do endpoint `tqx=out:json` do Google **não entrega um JSON puro**, mas encapsula isso em uma declaração Javascript: 
```javascript
google.visualization.Query.setResponse({...});
```
Nós utilizamos expressões regulares (RegEx) puras no nosso script `fetchGoogleSheetData` para extrair este conteúdo e depois interpretá-lo via pacote nativo `JSON.parse()`.

---

## Adicionando Novos (e novos) Dealers
Graças ao uso do _CSS Grid_, a plataforma se ajusta para 16, 20 ou até infinitos Dealers de forma orgânica. 
Se você fechar uma parceria de um novo dealer no Brasil ano que vem, tudo o que precisa ser feito é abrir o arquivo `dashboard-aon26.html` e adicionar mais 1 linha nova na variável principal:
```javascript
// Exemplo ilustrativo da alteração de código:
const DEALERS_CONFIG = {
    // ... planilhas existentes ...
    "Dimanor": { country: "MX", sheetUrl: "SUA_URL_AQUI", statusCol: "Status", postStatusCol: "Post-calificación" },
    
    // -> Basta adicionar isso:
    "Meu Novo Dealer BR": { country: "BR", sheetUrl: "URL_GERADA_DA_PLANILHA_AQUI", statusCol: "Status", postStatusCol: "Fase pós qualificação" }
}
```

---

## Tipos de Hospedagem

Você tem 3 opções de uso:
1. **Desktop/Local:** Simplesmente dando 2 preenchimentos via Python, crie seu "configurado" e abra usando "Dois Cliques" localmente. Todos da sua rede da empresa podem fazer isso offline.
2. **GitHub Pages (Grátis):** Crie um repositório no Github, ponha o `dashboard-aon26-configurado.html` nomeado como `index.html` e habilite a tab de Settings > Pages. Ele ficará na nuvem por conta da Github - totalmente gratuito.
3. **Vercel / Netlify (Grátis):** Opção de "Drag and Drop". Arraste direto essa pasta finalizada no painel destas plataformas e você receberá uma URL real acessível via Celular globalmente!

---

## FAQ de Regras de Negócio e Tratativa de Erros

**Q: Clico em atualizar, e se 15 dealers lerem direito e 1 ficar falhando em erro interno? Ele quebra TUDO?**
> **R:** NÃO! Esta foi uma restrição solicitada e cumprida à risca. Caso 1 falhe, a somatória será em cima dos 15 bem sucedidos e o card do falhado mostrará em letras vermelhas o erro, evitando interromper a operação global.

**Q: Qual a rigidez das comparações do Status (ex. Maiúsculas ou espaços sobrando)?**
> **R:** O código usa função auxiliar `normalizeString` que reverte as variáveis da planilha para `.toLowerCase` e `.trim()`. 
> Ex: Um usuário digitalizar `" QuaLIFICADO "` nas planilhas, ou `"Sem intenção de COMPRA"`, resultará na contabilização devida e sem interferência visual.

**Q: Quais as Features Extensíveis documentadas (Porém aguardando escopo para serem feitas no futuro)?**
- **Chart.js:** Pode ser configurada a instalação de um gráfico de pizza para a distribuição de propensão de vendas.
- **Histórico:** Salvamento via `localStorage` gerando comparativo de semana passada vs hoje.
- **Toggle Theming:** Mudança no root do CSS variando dark mode entre Light mode.

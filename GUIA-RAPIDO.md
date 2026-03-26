# ⚡ GUIA RÁPIDO: Configuração do Dashboard AON 26

Este guia fornece os passos rápidos e práticos para rodar o Dashboard integrado às suas 16 planilhas (Brasil, Argentina e México).

## Passo 1: Preparar as Planilhas (IMPORTANTE)
Antes de começar, certifique-se de que cada uma das 16 planilhas esteja:
1. Com uma aba chamada exatamente `"Página1"` (com P maiúsculo e acento).
2. Tendo as colunas corretas em qualquer ordem (ex: "Status" e "Fase pós qualificação" ou "Post-calificación").
3. **Pública para leitura:**
   - No Google Sheets, clique no botão azul "Compartilhar" (canto superior direito).
   - Mude de "Restrito" para `"Qualquer pessoa com o link"`.
   - Pode deixar a permissão como "Leitor".
   - Clique em "Concluído" e copie o link gerado.

## Passo 2: O Script de Instalação Rápida
Certifique-se de que o Python 3.x está instalado na sua máquina.
1. Abra um terminal/Prompt de Comando na pasta onde estes arquivos foram salvos.
2. Execute o comando interativo:
   ```bash
   python configurar_dashboard.py
   ```
3. O script listará os 16 dealers, um por vez.
4. Cole o link do Google Sheets correspondente a cada um. Se quiser manter o "Modo Demonstração" (dados falsos) para algum, basta apenas apertar `Enter`.

## Passo 3: Utilizando o Dashboard
O script criará um arquivo pronto chamado **`dashboard-aon26-configurado.html`**.
- Dê um duplo-clique neste arquivo.
- Ele abrirá no seu navegador de preferência.
- Clique no pequeno botão verde `"Atualizar Dados"` logo no topo para forçar as planilhas a serem lidas sob demanda.

## Checklist Rápido de Links
Para facilitar o preenchimento, separe aqui antes de rodar o programa:

**🇧🇷 Brasil:**
- [ ] Veneza Sul
- [ ] Veneza NE
- [ ] INOVA
- [ ] RZK
- [ ] Terraverde
- [ ] SLC
- [ ] Nissey
- [ ] Iguaçu
- [ ] Agro Baggio

**🇦🇷 Argentina:**
- [ ] Diesel Lange
- [ ] Patagonia
- [ ] Agronorte
- [ ] Cia Mercantil

**🇲🇽 México:**
- [ ] Maqro
- [ ] Dimasur
- [ ] Dimanor

## Erros Comuns (Troubleshooting)
- **Mando Atualizar e um Card Fica Vermelho "A planilha não é pública"** -> Verifique o Passo 1 deste guia. Um documento estava configurado como "Restrito".
- **Cartão de um Dealer fica todo zerado (0)** -> Os nomes das colunas de qualificação podem estar ligeiramente diferentes do padrão ("Status" ou "Fase pós qualificação"). A busca do código ignora maiúsculas, mas exige os textos corretos.
- **Quero visualizar os dados estáticos antes** -> Abra o arquivo secundário `dashboard-aon26-demo.html`.

Para dúvidas profundas de documentação técnica, acesse o arquivo `LEIA-ME.md` incluso no pacote.

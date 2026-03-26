import sys
import re
import json
import os

class C:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

DEALERS = [
    "Veneza Sul", "Veneza NE", "INOVA", "RZK", "Terraverde", "SLC", 
    "Nissey", "Iguaçu", "Agro Baggio", "Diesel Lange", "Patagonia", 
    "Agronorte", "Cia Mercantil", "Maqro", "Dimasur", "Dimanor"
]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_screen()
    print(f"{C.BOLD}{C.GREEN}=============================================={C.END}")
    print(f"{C.BOLD}{C.GREEN}   CONFIGURADOR DE DASHBOARD AON 26 {C.END}")
    print(f"{C.BOLD}{C.GREEN}=============================================={C.END}\n")
    print("Por favor, cole a URL completa de cada planilha do Google Sheets.")
    print("Certifique-se de que a planilha tem acesso configurado para 'Qualquer pessoa com o link'.")
    print(f"Pressione Enter sem digitar nada para manter {C.YELLOW}'SUA_URL_AQUI'{C.END} (Modo Demo).\n")
    
    urls = {}
    for i, dealer in enumerate(DEALERS, 1):
        url = input(f"[{i}/16] {C.CYAN}{dealer}{C.END} URL: ").strip()
        
        if not url:
            url = "SUA_URL_AQUI"
        elif "docs.google.com/spreadsheets/d/" not in url:
            print(f"  {C.YELLOW}Aviso:{C.END} A URL fornecida não parece ser uma planilha válida do Google.")
            
        urls[dealer] = url

    print(f"\n{C.YELLOW}Processando configurações...{C.END}")
    
    # Salvar backup
    with open("urls_backup.json", "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=4, ensure_ascii=False)
    print(f"  ✓ Backup das URLs salvo em {C.CYAN}urls_backup.json{C.END}")

    template_path = "dashboard-aon26.html"
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        print(f"\n{C.RED}Erro Fatal:{C.END} O arquivo '{template_path}' não foi encontrado.")
        print("Execute este script no mesmo diretório em que o arquivo HTML está salvo.")
        sys.exit(1)

    # Substituição usando Regex
    configurado = template
    for dealer, url in urls.items():
        # Busca a chave "Nome Dealer" e recua até o "SUA_URL_AQUI" para garantir replace isolado
        pattern = fr'("{dealer}":\s*{{[^}}]*?sheetUrl:\s*)"SUA_URL_AQUI"'
        replacement = fr'\g<1>"{url}"'
        configurado = re.sub(pattern, replacement, configurado)

    output_path = "dashboard-aon26-configurado.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(configurado)

    print(f"  ✓ Dashboard finalizado salvo como {C.GREEN}{output_path}{C.END}\n")
    
    print(f"{C.BOLD}SUCESSO!{C.END} Dê dois cliques em {C.CYAN}{output_path}{C.END} para abrir no navegador.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{C.RED}Configuração cancelada pelo usuário.{C.END}")
        sys.exit(0)

import csv
import time
import pandas as pd
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=False) # Roda com navegador visível para você acompanhar
    context = browser.new_context(viewport={'width': 1280, 'height': 720})
    page = context.new_page()

    # Ler dados de entrada
    buscas = []
    try:
        with open('busca.csv', mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                buscas.append({
                    'Nome': row['Nome'].strip(), 
                    'Orgao': row.get('Orgao', '').strip() if row.get('Orgao') else ''
                })
    except FileNotFoundError:
        print("Arquivo 'busca.csv' não encontrado. Crie o arquivo antes de rodar.")
        return

    dados_extraidos = []

    print("Acessando o Portal da Transparência...")
    page.goto("https://www.transparencia.ms.gov.br/#/Servidores")

    # Lidar com o botão "Continuar" do modal inicial, se houver
    try:
        page.wait_for_selector('text="Continuar"', timeout=10000)
        page.click('text="Continuar"')
        print("Aviso inicial fechado.")
        time.sleep(1)
    except Exception as e:
        print("Botão 'Continuar' não encontrado ou já clicado.")

    for busca in buscas:
        nome_busca = busca['Nome']
        orgao_busca = busca['Orgao']
        print(f"\nBuscando por: {nome_busca} (Filtro Órgão: {orgao_busca if orgao_busca else 'Nenhum'})")

        # Limpar o órgão se estiver preenchido de buscas anteriores
        try:
            page.click('abbr.select2-search-choice-close', timeout=1000)
        except:
            pass

        # Selecionar o Órgão no dropdown
        if orgao_busca:
            try:
                page.click('div#s2id_Orgao .select2-choice')
                time.sleep(0.5) # Aguardar a animação do dropdown
                # O Select2 move o input ativo para o final do HTML, então pegamos o visível
                page.locator('.select2-drop-active .select2-input, input.select2-input:visible').first.fill(orgao_busca)
                # Espera as opções aparecerem e clica na que contém a sigla
                page.wait_for_selector(f'.select2-result-label:has-text("{orgao_busca}")', timeout=5000)
                page.locator(f'.select2-result-label:has-text("{orgao_busca}")').first.click()
                time.sleep(0.5)
            except Exception as e:
                print(f"  -> Aviso: Não foi possível selecionar o órgão '{orgao_busca}'. {e}")

        # Limpar e preencher o campo Nome
        page.fill('input#Nome', '')
        page.fill('input#Nome', nome_busca)
        
        # Clicar em Consultar
        page.click('.btnConsultar')
        
        # Aguardar tabela carregar
        try:
            # Esperar que a tabela atualize (podemos checar o overlay de carregamento ou dar um sleep)
            time.sleep(3) 
            
            # Avaliar a tabela e pegar as linhas
            rows = page.query_selector_all('table tbody tr')
            
            encontrou = False
            for row in rows:
                cols = row.query_selector_all('td')
                if len(cols) >= 8:
                    orgao = cols[2].inner_text().strip()
                    nome = cols[3].inner_text().strip()
                    cargo = cols[4].inner_text().strip()
                    rem_fixa = cols[5].inner_text().strip()
                    rem_eventual = cols[6].inner_text().strip()
                    rem_liquida = cols[7].inner_text().strip()
                    
                    # Filtrar pelo órgão, se especificado
                    if orgao_busca and orgao_busca.upper() not in orgao.upper():
                        continue
                    
                    encontrou = True
                    dados_extraidos.append({
                        'Nome Buscado': nome_busca,
                        'Órgão Buscado': orgao_busca,
                        'Órgão Encontrado': orgao,
                        'Nome Encontrado': nome,
                        'Cargo': cargo,
                        'Remuneração Fixa': rem_fixa,
                        'Remunerações Eventuais': rem_eventual,
                        'Remuneração Líquida': rem_liquida
                    })
            if not encontrou:
                 print(f"  -> Nenhum resultado correspondente para {nome_busca} no órgão '{orgao_busca}'.")
            else:
                 print(f"  -> Dados capturados para {nome_busca}!")
                 
        except Exception as e:
            print(f"  -> Nenhum resultado encontrado ou tempo excedido para {nome_busca}.")

    # Salvar em CSV
    if dados_extraidos:
        df = pd.DataFrame(dados_extraidos)
        df.to_csv('dados_extraidos.csv', index=False, encoding='utf-8-sig')
        print(f"\nSucesso! Extraídos {len(dados_extraidos)} registros em 'dados_extraidos.csv'.")
    else:
        print("\nNenhum dado extraído.")

    context.close()
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)

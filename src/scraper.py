import asyncio
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
from playwright.async_api import async_playwright

ROOT = Path(__file__).parent.parent
BUSCA_CSV = ROOT / "busca.csv"
OUTPUT_DIR = ROOT / "output"
OUTPUT_CSV = OUTPUT_DIR / "dados_extraidos.csv"


def ler_buscas():
    try:
        with open(BUSCA_CSV, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            return [
                {
                    "Nome": row["Nome"].strip(),
                    "Orgao": row.get("Orgao", "").strip() if row.get("Orgao") else "",
                }
                for row in reader
            ]
    except FileNotFoundError:
        print(f"Arquivo '{BUSCA_CSV}' não encontrado.")
        return []


def agrupar_por_orgao(buscas):
    grupos = defaultdict(list)
    for item in buscas:
        grupos[item["Orgao"]].append(item)
    return grupos


async def selecionar_orgao_se_necessario(page, orgao, last_organ):
    if orgao == last_organ:
        print(f"  [CACHE] Órgão '{orgao}' já selecionado, pulando Select2.")
        return last_organ

    # Limpar seleção anterior
    try:
        await page.click("abbr.select2-search-choice-close", timeout=1000)
        await page.wait_for_timeout(300)
    except Exception:
        pass

    if orgao:
        try:
            await page.click("div#s2id_Orgao .select2-choice")
            await page.wait_for_timeout(500)
            await page.locator(
                ".select2-drop-active .select2-input, input.select2-input:visible"
            ).first.fill(orgao)
            await page.wait_for_selector(
                f'.select2-result-label:has-text("{orgao}")', timeout=8000
            )
            await page.locator(
                f'.select2-result-label:has-text("{orgao}")'
            ).first.click()
            await page.wait_for_timeout(500)
        except Exception as e:
            print(f"  -> Aviso: Não foi possível selecionar o órgão '{orgao}'. {e}")

    return orgao


async def worker(browser, orgao, itens):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] Worker iniciado para órgão: '{orgao}' ({len(itens)} busca(s))")

    context = await browser.new_context(viewport={"width": 1280, "height": 720})
    page = await context.new_page()
    resultados = []

    await page.goto("https://www.transparencia.ms.gov.br/#/Servidores")

    try:
        await page.wait_for_selector('text="Continuar"', timeout=10000)
        await page.click('text="Continuar"')
        await page.wait_for_timeout(1000)
    except Exception:
        pass

    last_organ = None

    for busca in itens:
        nome_busca = busca["Nome"]
        orgao_busca = busca["Orgao"]
        print(f"\n  Buscando: {nome_busca} (Órgão: {orgao_busca or 'Nenhum'})")

        last_organ = await selecionar_orgao_se_necessario(page, orgao_busca, last_organ)

        await page.fill("input#Nome", "")
        await page.fill("input#Nome", nome_busca)
        await page.click(".btnConsultar")

        try:
            await page.wait_for_timeout(3000)
            rows = page.query_selector_all("table tbody tr")
            rows = await rows

            encontrou = False
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) >= 8:
                    orgao_enc = (await cols[2].inner_text()).strip()
                    nome_enc = (await cols[3].inner_text()).strip()
                    cargo = (await cols[4].inner_text()).strip()
                    rem_fixa = (await cols[5].inner_text()).strip()
                    rem_eventual = (await cols[6].inner_text()).strip()
                    rem_liquida = (await cols[7].inner_text()).strip()

                    if orgao_busca and orgao_busca.upper() not in orgao_enc.upper():
                        continue

                    encontrou = True
                    resultados.append(
                        {
                            "Nome Buscado": nome_busca,
                            "Órgão Buscado": orgao_busca,
                            "Órgão Encontrado": orgao_enc,
                            "Nome Encontrado": nome_enc,
                            "Cargo": cargo,
                            "Remuneração Fixa": rem_fixa,
                            "Remunerações Eventuais": rem_eventual,
                            "Remuneração Líquida": rem_liquida,
                        }
                    )

            if not encontrou:
                print(
                    f"  -> Nenhum resultado para {nome_busca} no órgão '{orgao_busca}'."
                )
            else:
                print(f"  -> Dados capturados para {nome_busca}!")

        except Exception as e:
            print(f"  -> Erro ao buscar {nome_busca}: {e}")

    await context.close()
    return resultados


async def run():
    buscas = ler_buscas()
    if not buscas:
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    grupos = agrupar_por_orgao(buscas)
    print(f"Rodando em modo headless com {len(grupos)} worker(s) paralelo(s)...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        tasks = [worker(browser, orgao, itens) for orgao, itens in grupos.items()]
        resultados_por_grupo = await asyncio.gather(*tasks)
        await browser.close()

    dados = [row for grupo in resultados_por_grupo for row in grupo]

    if dados:
        df = pd.DataFrame(dados)
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        print(f"\nSucesso! {len(dados)} registro(s) salvos em '{OUTPUT_CSV}'.")
    else:
        print("\nNenhum dado extraído.")


if __name__ == "__main__":
    asyncio.run(run())

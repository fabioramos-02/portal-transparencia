# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Portal Transparência MS — Servidor Extrator** automates extraction and analysis of public servant remuneration data from the Mato Grosso do Sul State Transparency Portal (`transparencia.ms.gov.br`). It has two independent stages: scraping and report generation.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

## Running

```bash
# Stage 1: Extract data from the portal → output/dados_extraidos.csv
python src/scraper.py

# Stage 2: Generate interactive HTML dashboard → output/relatorio_stakeholders.html
python src/gerar_relatorio.py
```

No test or lint commands exist in this project.

## Architecture

**Data flow:**

1. User populates `busca.csv` (columns: `Nome`, `Orgao`) with server names and optional agency acronym (e.g., SEGOV, SED)
2. `scraper.py` reads the CSV, groups entries by agency, then launches parallel async Playwright workers via `asyncio.gather()`
3. Each worker opens a headless Chromium browser, optionally filters by agency via Select2 dropdown, searches by name, and scrapes the results table
4. Extracted rows are saved to `output/dados_extraidos.csv` (UTF-8 BOM)
5. `gerar_relatorio.py` reads the CSV, computes KPIs and discount tiers, builds 4 Plotly charts, and writes a self-contained `output/relatorio_stakeholders.html`

**Key design decisions:**
- Org selection caching: `selecionar_orgao_se_necessario()` tracks which agency is currently selected in the Select2 dropdown and skips re-selection when consecutive searches share the same agency — avoids redundant UI interactions
- All browser work is async; `worker()` is the unit of parallelism, one per agency group
- The HTML report is fully self-contained (Plotly loaded from CDN); no build step required
- CSV encoding is always UTF-8 with BOM to handle Portuguese characters correctly

**Fragility note:** The scraper is tightly coupled to the portal's HTML structure. If the portal changes its DOM (table selectors, dropdown IDs), `scraper.py` will need to be updated.

## Key Files

| File | Purpose |
|------|---------|
| `busca.csv` | Input: list of server names and optional agencies to search |
| `src/scraper.py` | Async Playwright scraper — reads `busca.csv`, writes `output/dados_extraidos.csv` |
| `src/gerar_relatorio.py` | Report builder — reads CSV, generates `output/relatorio_stakeholders.html` |
| `output/dados_extraidos.csv` | Intermediate data (git-ignored) |
| `output/relatorio_stakeholders.html` | Final deliverable dashboard (git-ignored) |

## CSV Format

**Input `busca.csv`:** `Nome` (server name), `Orgao` (agency acronym, optional)

**Output `dados_extraidos.csv`:** `Nome Buscado`, `Órgão Buscado`, `Órgão Encontrado`, `Nome Encontrado`, `Cargo`, `Remuneração Fixa`, `Remunerações Eventuais`, `Remuneração Líquida`

Currency values use Brazilian format (`R$ 1.234,56`). `clean_currency()` in `gerar_relatorio.py` parses them to float; `fmt_brl()` formats them back.

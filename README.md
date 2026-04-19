# Portal Transparência MS — Extrator de Servidores

Ferramenta de automação para consulta de remunerações de servidores públicos no [Portal da Transparência do Mato Grosso do Sul](https://www.transparencia.ms.gov.br/#/Servidores), com geração de relatório interativo.

---

## Requisitos

- Python 3.9+
- Dependências listadas em `requirements.txt`
- Chromium (instalado via Playwright)

---

## Instalação

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## Como Usar

### 1. Edite o arquivo de entrada

Abra `busca.csv` na raiz do projeto e preencha os servidores que deseja consultar:

```csv
Nome,Orgao
MARIA EDUARDA,SEGOV
EDUARDO RIEDEL,
JOAO DA SILVA,SED
```

- **Nome**: nome completo (ou parte) do servidor
- **Orgao**: sigla do órgão para filtrar (deixe vazio para buscar em todos)

### 2. Execute o scraper

```bash
python src/scraper.py
```

O script roda em modo headless (sem abrir o navegador). Os resultados são salvos em `output/dados_extraidos.csv`.

### 3. Gere o relatório

```bash
python src/gerar_relatorio.py
```

O relatório interativo é gerado em `output/relatorio_stakeholders.html`. Abra no navegador para visualizar.

---

## Estrutura de Arquivos

```
portal-transparencia/
├── src/
│   ├── scraper.py          # Extração de dados (Playwright async)
│   └── gerar_relatorio.py  # Geração do relatório (Plotly)
├── output/                 # Gerado automaticamente
│   ├── dados_extraidos.csv
│   └── relatorio_stakeholders.html
├── busca.csv               # Lista de servidores para consultar
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Colunas do CSV de Saída (`dados_extraidos.csv`)

| Coluna | Descrição |
|--------|-----------|
| Nome Buscado | Nome informado no `busca.csv` |
| Órgão Buscado | Órgão informado no `busca.csv` |
| Órgão Encontrado | Órgão retornado pelo portal |
| Nome Encontrado | Nome completo retornado pelo portal |
| Cargo | Cargo/função do servidor |
| Remuneração Fixa | Salário bruto fixo (formato R$) |
| Remunerações Eventuais | Verbas eventuais (formato R$) |
| Remuneração Líquida | Salário líquido recebido (formato R$) |

---

## Relatório Interativo

O relatório HTML contém:

- **KPIs**: total de servidores e média de remuneração líquida
- **Tabela completa**: todos os dados com desconto calculado por servidor
- **Barras agrupadas**: comparativo entre remuneração fixa e líquida
- **Donut**: distribuição da remuneração líquida por órgão
- **Ranking de descontos**: quanto cada servidor perde em descontos (R$ e %)

---

## Notas Técnicas

- **Headless**: o navegador Chromium roda em background, sem janela visível
- **Cache de órgão**: quando múltiplos servidores pertencem ao mesmo órgão, o filtro Select2 é selecionado apenas uma vez, evitando interações redundantes
- **Paralelismo**: as buscas são agrupadas por órgão e cada grupo roda em um worker independente via `asyncio.gather`, reduzindo o tempo total de extração

from datetime import date
from pathlib import Path

from report.builder import build_html
from report.data import load_and_prepare

ROOT        = Path(__file__).parent.parent
INPUT_CSV   = ROOT / "output" / "dados_extraidos.csv"
OUTPUT_HTML = ROOT / "output" / "relatorio_stakeholders.html"


def main() -> None:
    records, orgaos = load_and_prepare(INPUT_CSV)
    if records is None:
        return

    hoje = date.today().strftime("%d/%m/%Y")
    html = build_html(records, orgaos, hoje, len(records))

    OUTPUT_HTML.parent.mkdir(exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Relatório gerado com sucesso em '{OUTPUT_HTML}'!")


if __name__ == "__main__":
    main()

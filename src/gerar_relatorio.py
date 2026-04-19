from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).parent.parent
INPUT_CSV = ROOT / "output" / "dados_extraidos.csv"
OUTPUT_HTML = ROOT / "output" / "relatorio_stakeholders.html"


def clean_currency(val):
    if pd.isna(val):
        return 0.0
    val = str(val).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(val)
    except Exception:
        return 0.0


def fmt_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    try:
        df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"Arquivo '{INPUT_CSV}' não encontrado. Execute o scraper primeiro.")
        return

    if df.empty:
        print("O arquivo de dados está vazio.")
        return

    df["Remuneração Líquida Num"] = df["Remuneração Líquida"].apply(clean_currency)
    df["Remuneração Fixa Num"] = df["Remuneração Fixa"].apply(clean_currency)
    df["Eventuais Num"] = df["Remunerações Eventuais"].apply(clean_currency)
    df["Desconto"] = (df["Remuneração Fixa Num"] - df["Remuneração Líquida Num"]).clip(lower=0)
    df["% Desconto"] = (
        (df["Desconto"] / df["Remuneração Fixa Num"].replace(0, float("nan"))) * 100
    ).round(1).fillna(0)

    df = df.sort_values("Remuneração Líquida Num", ascending=False).reset_index(drop=True)

    # KPIs
    total = len(df)
    maior = df["Remuneração Líquida Num"].max()
    menor = df["Remuneração Líquida Num"].min()
    media = df["Remuneração Líquida Num"].mean()

    # Layout: 1 linha de KPIs, tabela, barras agrupadas + donut, barras horizontais
    fig = make_subplots(
        rows=4,
        cols=2,
        row_heights=[0.08, 0.28, 0.34, 0.30],
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}],
            [{"type": "table", "colspan": 2}, None],
            [{"type": "bar"}, {"type": "pie"}],
            [{"type": "bar", "colspan": 2}, None],
        ],
        subplot_titles=(
            "", "",
            "Tabela de Servidores",
            "",
            "Remuneração Fixa vs Líquida por Servidor",
            "Distribuição da Rem. Líquida por Órgão",
            "Ranking de Descontos (Rem. Fixa − Líquida)",
        ),
        vertical_spacing=0.06,
        horizontal_spacing=0.06,
    )

    # KPI cards
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=total,
            title={"text": "Total de Servidores", "font": {"size": 14}},
            number={"font": {"size": 28, "color": "#2c3e50"}},
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=media,
            title={"text": "Média da Rem. Líquida", "font": {"size": 14}},
            number={"prefix": "R$ ", "valueformat": ",.2f", "font": {"size": 28, "color": "#27ae60"}},
        ),
        row=1, col=2,
    )

    # Cores alternadas para as linhas da tabela
    row_colors = [
        ["#ecf0f1" if i % 2 == 0 else "white" for i in range(len(df))]
    ]

    # Tabela
    fig.add_trace(
        go.Table(
            header=dict(
                values=["Nome", "Órgão", "Cargo", "Rem. Fixa", "Eventuais", "Rem. Líquida", "Desconto", "% Desconto"],
                fill_color="#2c3e50",
                font=dict(size=12, color="white"),
                align="left",
                height=32,
            ),
            cells=dict(
                values=[
                    df["Nome Encontrado"],
                    df["Órgão Encontrado"],
                    df["Cargo"],
                    df["Remuneração Fixa"],
                    df["Remunerações Eventuais"],
                    df["Remuneração Líquida"],
                    df["Desconto"].apply(fmt_brl),
                    df["% Desconto"].apply(lambda x: f"{x}%"),
                ],
                fill_color=row_colors,
                font=dict(size=11, color="#2c3e50"),
                align="left",
                height=26,
            ),
        ),
        row=2, col=1,
    )

    nomes = df["Nome Encontrado"]

    # Barras agrupadas: fixa vs líquida
    fig.add_trace(
        go.Bar(
            name="Rem. Fixa",
            x=nomes,
            y=df["Remuneração Fixa Num"],
            marker_color="#2980b9",
            hovertemplate="%{x}<br>Fixa: R$ %{y:,.2f}<extra></extra>",
        ),
        row=3, col=1,
    )
    fig.add_trace(
        go.Bar(
            name="Rem. Líquida",
            x=nomes,
            y=df["Remuneração Líquida Num"],
            marker_color="#e74c3c",
            hovertemplate="%{x}<br>Líquida: R$ %{y:,.2f}<extra></extra>",
        ),
        row=3, col=1,
    )

    # Donut por órgão
    organ_totais = df.groupby("Órgão Encontrado")["Remuneração Líquida Num"].sum().reset_index()
    fig.add_trace(
        go.Pie(
            labels=organ_totais["Órgão Encontrado"],
            values=organ_totais["Remuneração Líquida Num"],
            hole=0.45,
            hovertemplate="%{label}<br>Total: R$ %{value:,.2f}<br>%{percent}<extra></extra>",
            textinfo="label+percent",
            showlegend=False,
        ),
        row=3, col=2,
    )

    # Ranking de descontos (horizontal, do menor para o maior)
    df_desc = df.sort_values("Desconto", ascending=True)
    fig.add_trace(
        go.Bar(
            x=df_desc["Desconto"],
            y=df_desc["Nome Encontrado"],
            orientation="h",
            marker_color="#e67e22",
            text=df_desc["% Desconto"].apply(lambda x: f"{x}%"),
            textposition="outside",
            hovertemplate="%{y}<br>Desconto: R$ %{x:,.2f} (%{text})<extra></extra>",
            showlegend=False,
        ),
        row=4, col=1,
    )

    fig.update_layout(
        title_text=(
            f"Relatório Executivo de Servidores — Portal Transparência MS"
            f"<br><sup>Maior: {fmt_brl(maior)}  |  Menor: {fmt_brl(menor)}  |  Média: {fmt_brl(media)}</sup>"
        ),
        title_font=dict(size=20, family="Arial Black"),
        height=1700,
        template="plotly_white",
        paper_bgcolor="#f8f9fa",
        plot_bgcolor="white",
        font=dict(family="Arial", size=12),
        margin=dict(l=50, r=50, t=100, b=50),
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
    )

    fig.update_yaxes(tickprefix="R$ ", row=3, col=1)
    fig.update_xaxes(tickangle=-30, row=3, col=1)
    fig.update_xaxes(tickprefix="R$ ", row=4, col=1)

    fig.write_html(str(OUTPUT_HTML))
    print(f"Relatório gerado com sucesso em '{OUTPUT_HTML}'!")


if __name__ == "__main__":
    main()

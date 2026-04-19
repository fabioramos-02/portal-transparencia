from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).parent.parent
INPUT_CSV = ROOT / "output" / "dados_extraidos.csv"
OUTPUT_HTML = ROOT / "output" / "relatorio_stakeholders.html"

# Paleta dark
BG = "#0d1117"
SURFACE = "#161b22"
SURFACE2 = "#21262d"
BORDER = "#30363d"
TEXT = "#e6edf3"
TEXT_MUTED = "#8b949e"
ACCENT_BLUE = "#58a6ff"
ACCENT_GREEN = "#3fb950"
ACCENT_ORANGE = "#d29922"
ACCENT_RED = "#f85149"
ACCENT_PURPLE = "#bc8cff"


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

    df["Líquida"] = df["Remuneração Líquida"].apply(clean_currency)
    df["Fixa"] = df["Remuneração Fixa"].apply(clean_currency)
    df["Eventuais"] = df["Remunerações Eventuais"].apply(clean_currency)
    df["Desconto"] = (df["Fixa"] - df["Líquida"]).clip(lower=0)
    df["PctDesc"] = (
        (df["Desconto"] / df["Fixa"].replace(0, float("nan"))) * 100
    ).round(1).fillna(0)

    df = df.sort_values("Líquida", ascending=False).reset_index(drop=True)

    total = len(df)
    maior = df["Líquida"].max()
    menor = df["Líquida"].min()
    media = df["Líquida"].mean()
    total_folha = df["Líquida"].sum()

    fig = make_subplots(
        rows=4,
        cols=4,
        row_heights=[0.10, 0.26, 0.34, 0.30],
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
            [{"type": "table", "colspan": 4}, None, None, None],
            [{"type": "bar", "colspan": 3}, None, None, {"type": "pie"}],
            [{"type": "bar", "colspan": 4}, None, None, None],
        ],
        subplot_titles=(
            "", "", "", "",
            "Servidores",
            "",
            "Remuneração Fixa vs Líquida",
            "Distribuição por Órgão",
            "Ranking de Descontos",
        ),
        vertical_spacing=0.05,
        horizontal_spacing=0.03,
    )

    # --- KPI Indicators ---
    kpis = [
        ("Total de Servidores", total, "", ",.0f", ACCENT_BLUE),
        ("Folha Total Líquida", total_folha, "R$ ", ",.2f", ACCENT_GREEN),
        ("Maior Remuneração", maior, "R$ ", ",.2f", ACCENT_ORANGE),
        ("Média Líquida", media, "R$ ", ",.2f", ACCENT_PURPLE),
    ]
    for i, (titulo, valor, prefix, fmt, cor) in enumerate(kpis, start=1):
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=valor,
                title={"text": titulo, "font": {"size": 12, "color": TEXT_MUTED}},
                number={"prefix": prefix, "valueformat": fmt, "font": {"size": 24, "color": cor}},
            ),
            row=1, col=i,
        )

    # --- Tabela ---
    row_fill = [SURFACE if i % 2 == 0 else SURFACE2 for i in range(len(df))]
    fig.add_trace(
        go.Table(
            header=dict(
                values=["<b>Nome</b>", "<b>Órgão</b>", "<b>Cargo</b>",
                        "<b>Rem. Fixa</b>", "<b>Eventuais</b>",
                        "<b>Rem. Líquida</b>", "<b>Desconto</b>", "<b>% Desc.</b>"],
                fill_color=SURFACE2,
                font=dict(size=12, color=ACCENT_BLUE),
                align="left",
                height=34,
                line_color=BORDER,
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
                    df["PctDesc"].apply(lambda x: f"{x}%"),
                ],
                fill_color=[row_fill] * 8,
                font=dict(size=11, color=TEXT),
                align="left",
                height=28,
                line_color=BORDER,
            ),
        ),
        row=2, col=1,
    )

    nomes = df["Nome Encontrado"]

    # --- Barras agrupadas ---
    fig.add_trace(
        go.Bar(
            name="Rem. Fixa",
            x=nomes,
            y=df["Fixa"],
            marker_color=ACCENT_BLUE,
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Fixa: R$ %{y:,.2f}<extra></extra>",
        ),
        row=3, col=1,
    )
    fig.add_trace(
        go.Bar(
            name="Rem. Líquida",
            x=nomes,
            y=df["Líquida"],
            marker_color=ACCENT_GREEN,
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Líquida: R$ %{y:,.2f}<extra></extra>",
        ),
        row=3, col=1,
    )

    # --- Donut por órgão ---
    organ_totais = df.groupby("Órgão Encontrado")["Líquida"].sum().reset_index()
    palette = [ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_PURPLE, ACCENT_RED, "#79c0ff", "#56d364"]
    fig.add_trace(
        go.Pie(
            labels=organ_totais["Órgão Encontrado"],
            values=organ_totais["Líquida"],
            hole=0.5,
            marker=dict(colors=palette[:len(organ_totais)], line=dict(color=BG, width=2)),
            hovertemplate="<b>%{label}</b><br>Total: R$ %{value:,.2f}<br>%{percent}<extra></extra>",
            textinfo="label+percent",
            textfont=dict(color=TEXT, size=11),
            showlegend=False,
        ),
        row=3, col=4,
    )

    # --- Ranking de descontos ---
    df_desc = df.sort_values("Desconto", ascending=True)
    bar_colors = [ACCENT_RED if p >= 30 else ACCENT_ORANGE if p >= 20 else ACCENT_GREEN
                  for p in df_desc["PctDesc"]]
    fig.add_trace(
        go.Bar(
            x=df_desc["Desconto"],
            y=df_desc["Nome Encontrado"],
            orientation="h",
            marker_color=bar_colors,
            marker_line_width=0,
            text=df_desc["PctDesc"].apply(lambda x: f"  {x}%"),
            textposition="outside",
            textfont=dict(color=TEXT, size=11),
            hovertemplate="<b>%{y}</b><br>Desconto: R$ %{x:,.2f} (%{text})<extra></extra>",
            showlegend=False,
        ),
        row=4, col=1,
    )

    # Anotação de legenda de cores no ranking
    fig.add_annotation(
        text="<span style='color:#f85149'>■</span> ≥30%  "
             "<span style='color:#d29922'>■</span> ≥20%  "
             "<span style='color:#3fb950'>■</span> <20%",
        xref="paper", yref="paper",
        x=0.99, y=0.005,
        showarrow=False,
        font=dict(size=11, color=TEXT_MUTED),
        align="right",
    )

    # --- Layout global ---
    fig.update_layout(
        title=dict(
            text=(
                "RELATÓRIO EXECUTIVO DE SERVIDORES"
                f"<br><sup style='color:{TEXT_MUTED}'>Portal da Transparência — Mato Grosso do Sul  ·  "
                f"Menor: {fmt_brl(menor)}  ·  Maior: {fmt_brl(maior)}  ·  Total da folha: {fmt_brl(total_folha)}</sup>"
            ),
            font=dict(size=20, color=TEXT, family="Arial Black"),
            x=0.01,
        ),
        height=1750,
        paper_bgcolor=BG,
        plot_bgcolor=SURFACE,
        font=dict(family="Arial", size=12, color=TEXT),
        margin=dict(l=50, r=50, t=90, b=50),
        barmode="group",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.01,
            xanchor="right", x=1,
            font=dict(color=TEXT),
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    # Eixos dos gráficos de barras
    axis_style = dict(
        gridcolor=BORDER,
        linecolor=BORDER,
        tickcolor=BORDER,
        tickfont=dict(color=TEXT_MUTED),
        zerolinecolor=BORDER,
    )
    fig.update_xaxes(**axis_style)
    fig.update_yaxes(**axis_style)
    fig.update_yaxes(tickprefix="R$ ", row=3, col=1)
    fig.update_xaxes(tickangle=-35, row=3, col=1)
    fig.update_xaxes(tickprefix="R$ ", row=4, col=1)

    # Subplot titles color
    for annotation in fig.layout.annotations:
        annotation.font.color = TEXT_MUTED
        annotation.font.size = 13

    fig.write_html(str(OUTPUT_HTML))
    print(f"Relatório gerado com sucesso em '{OUTPUT_HTML}'!")


if __name__ == "__main__":
    main()

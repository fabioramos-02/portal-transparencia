from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

ROOT = Path(__file__).parent.parent
INPUT_CSV = ROOT / "output" / "dados_extraidos.csv"
OUTPUT_HTML = ROOT / "output" / "relatorio_stakeholders.html"

# Paleta
BLUE = "#2563EB"
BLUE_LIGHT = "#EFF6FF"
GRAY = "#64748B"
GRAY_LIGHT = "#F8FAFC"
BORDER = "#E2E8F0"
TEXT = "#0F172A"
TEXT_MUTED = "#64748B"
GREEN = "#059669"
AMBER = "#D97706"
RED = "#DC2626"


def clean_currency(val):
    if pd.isna(val):
        return 0.0
    val = str(val).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(val)
    except Exception:
        return 0.0


def fmt_brl(valor):
    s = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def chart_div(fig, height="100%"):
    return pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
        div_id=None,
        default_width="100%",
        default_height=height,
    )


def make_bar_liquida(df):
    colors = [BLUE if i == 0 else "#93C5FD" for i in range(len(df))]
    fig = go.Figure(
        go.Bar(
            x=df["Líquida"],
            y=df["Nome Curto"],
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            text=df["Líquida"].apply(lambda v: fmt_brl(v)),
            textposition="outside",
            textfont=dict(size=11, color=TEXT_MUTED),
            hovertemplate="<b>%{y}</b><br>Rem. Líquida: R$ %{x:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=80, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(
            tickprefix="R$ ",
            gridcolor=BORDER,
            zeroline=False,
            tickfont=dict(color=TEXT_MUTED, size=10),
        ),
        yaxis=dict(
            gridcolor=BORDER,
            tickfont=dict(color=TEXT, size=11),
            autorange="reversed",
        ),
        font=dict(family="Inter, Arial, sans-serif"),
        height=320,
    )
    return fig


def make_grouped_bar(df):
    df_s = df.sort_values("Líquida", ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Rem. Fixa",
        x=df_s["Nome Curto"],
        y=df_s["Fixa"],
        marker_color="#93C5FD",
        marker_line_width=0,
        text=df_s["Fixa"].apply(lambda v: f"R${v/1000:.1f}k"),
        textposition="outside",
        textfont=dict(size=9, color=TEXT_MUTED),
        hovertemplate="<b>%{x}</b><br>Fixa: R$ %{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Rem. Líquida",
        x=df_s["Nome Curto"],
        y=df_s["Líquida"],
        marker_color=BLUE,
        marker_line_width=0,
        text=df_s["Líquida"].apply(lambda v: f"R${v/1000:.1f}k"),
        textposition="outside",
        textfont=dict(size=9, color=TEXT_MUTED),
        hovertemplate="<b>%{x}</b><br>Líquida: R$ %{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.05,
        margin=dict(l=10, r=10, t=30, b=60),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=11, color=TEXT_MUTED),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            tickangle=-30,
            tickfont=dict(color=TEXT, size=10),
            gridcolor=BORDER,
        ),
        yaxis=dict(
            tickprefix="R$ ",
            gridcolor=BORDER,
            zeroline=False,
            tickfont=dict(color=TEXT_MUTED, size=10),
        ),
        font=dict(family="Inter, Arial, sans-serif"),
        height=320,
    )
    return fig


def make_donut(df):
    organ_totais = df.groupby("Órgão Encontrado")["Líquida"].sum().reset_index()
    palette = [BLUE, "#0EA5E9", GREEN, AMBER, RED, "#7C3AED", "#0891B2"]
    fig = go.Figure(go.Pie(
        labels=organ_totais["Órgão Encontrado"],
        values=organ_totais["Líquida"],
        hole=0.55,
        marker=dict(
            colors=palette[:len(organ_totais)],
            line=dict(color="white", width=3),
        ),
        hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
        textinfo="label+percent",
        textfont=dict(size=11, color=TEXT),
        showlegend=False,
        direction="clockwise",
        sort=True,
    ))
    total = organ_totais["Líquida"].sum()
    fig.add_annotation(
        text=f"<b>{fmt_brl(total)}</b><br><span style='font-size:11px'>Total</span>",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=13, color=TEXT),
        align="center",
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        font=dict(family="Inter, Arial, sans-serif"),
        height=300,
    )
    return fig


def make_desconto_bar(df):
    df_s = df.sort_values("PctDesc", ascending=True)
    bar_colors = [
        RED if p >= 30 else AMBER if p >= 20 else GREEN
        for p in df_s["PctDesc"]
    ]
    fig = go.Figure(go.Bar(
        x=df_s["PctDesc"],
        y=df_s["Nome Curto"],
        orientation="h",
        marker_color=bar_colors,
        marker_line_width=0,
        text=df_s["PctDesc"].apply(lambda x: f"{x}%"),
        textposition="outside",
        textfont=dict(size=11, color=TEXT_MUTED),
        hovertemplate="<b>%{y}</b><br>Desconto: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=10, r=60, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(
            ticksuffix="%",
            gridcolor=BORDER,
            zeroline=False,
            tickfont=dict(color=TEXT_MUTED, size=10),
            range=[0, df_s["PctDesc"].max() * 1.25],
        ),
        yaxis=dict(
            gridcolor=BORDER,
            tickfont=dict(color=TEXT, size=11),
            autorange="reversed",
        ),
        font=dict(family="Inter, Arial, sans-serif"),
        height=320,
    )
    return fig


CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
  background: #F1F5F9;
  color: #0F172A;
  min-height: 100vh;
}
.topbar {
  background: white;
  border-bottom: 1px solid #E2E8F0;
  padding: 0 32px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}
.topbar-title { font-size: 16px; font-weight: 700; color: #0F172A; }
.topbar-sub { font-size: 12px; color: #64748B; margin-left: 12px; }
.badge {
  background: #EFF6FF;
  color: #2563EB;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  border: 1px solid #BFDBFE;
}
.main { max-width: 1300px; margin: 0 auto; padding: 28px 24px 48px; }
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 28px 0 12px;
}
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.kpi-card {
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.kpi-label { font-size: 12px; color: #64748B; font-weight: 500; }
.kpi-value { font-size: 26px; font-weight: 700; color: #0F172A; }
.kpi-sub { font-size: 11px; color: #64748B; }
.kpi-accent-blue .kpi-value { color: #2563EB; }
.kpi-accent-green .kpi-value { color: #059669; }
.kpi-accent-amber .kpi-value { color: #D97706; }
.card {
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 20px 22px;
  margin-bottom: 16px;
}
.card-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 16px;
}
.card-title { font-size: 14px; font-weight: 600; color: #0F172A; }
.card-hint { font-size: 11px; color: #94A3B8; }
.two-col { display: grid; grid-template-columns: 1.8fr 1fr; gap: 16px; }
.chart-wrap { min-height: 200px; }
table.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
table.data-table thead th {
  background: #F8FAFC;
  color: #64748B;
  font-weight: 600;
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid #E2E8F0;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
table.data-table tbody tr { border-bottom: 1px solid #F1F5F9; }
table.data-table tbody tr:hover { background: #F8FAFC; }
table.data-table tbody td { padding: 9px 12px; color: #0F172A; vertical-align: middle; }
.pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 600;
}
.pill-red { background: #FEF2F2; color: #DC2626; }
.pill-amber { background: #FFFBEB; color: #D97706; }
.pill-green { background: #ECFDF5; color: #059669; }
.orgao-tag {
  background: #EFF6FF;
  color: #2563EB;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
}
.footer {
  text-align: center;
  font-size: 11px;
  color: #94A3B8;
  padding: 24px 0 8px;
}
@media (max-width: 900px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
}
"""


def build_html(df, charts):
    total = len(df)
    maior = df["Líquida"].max()
    menor = df["Líquida"].min()
    media = df["Líquida"].mean()
    total_folha = df["Líquida"].sum()
    hoje = date.today().strftime("%d/%m/%Y")

    table_rows = ""
    for _, row in df.iterrows():
        pct = row["PctDesc"]
        if pct >= 30:
            pill = f'<span class="pill pill-red">{pct:.1f}%</span>'
        elif pct >= 20:
            pill = f'<span class="pill pill-amber">{pct:.1f}%</span>'
        else:
            pill = f'<span class="pill pill-green">{pct:.1f}%</span>'

        table_rows += f"""
        <tr>
          <td><strong>{row['Nome Encontrado']}</strong></td>
          <td><span class="orgao-tag">{row['Órgão Encontrado']}</span></td>
          <td style="color:#64748B;font-size:11px">{row['Cargo'][:45]}{'…' if len(str(row['Cargo'])) > 45 else ''}</td>
          <td>{row['Remuneração Fixa']}</td>
          <td>{row['Remunerações Eventuais']}</td>
          <td><strong style="color:#2563EB">{row['Remuneração Líquida']}</strong></td>
          <td>{fmt_brl(row['Desconto'])}</td>
          <td>{pill}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Relatório de Servidores — Transparência MS</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>

<div class="topbar">
  <div style="display:flex;align-items:center;gap:8px">
    <span class="topbar-title">Portal Transparência MS</span>
    <span class="topbar-sub">Relatório Executivo de Servidores</span>
  </div>
  <div style="display:flex;align-items:center;gap:12px">
    <span style="font-size:11px;color:#94A3B8">Gerado em {hoje}</span>
    <span class="badge">{total} servidores</span>
  </div>
</div>

<div class="main">

  <p class="section-title">Visão Geral</p>
  <div class="kpi-row">
    <div class="kpi-card">
      <span class="kpi-label">Total de Servidores</span>
      <span class="kpi-value">{total}</span>
      <span class="kpi-sub">Consulta realizada em {hoje}</span>
    </div>
    <div class="kpi-card kpi-accent-blue">
      <span class="kpi-label">Folha Total Líquida</span>
      <span class="kpi-value">{fmt_brl(total_folha)}</span>
      <span class="kpi-sub">Soma das remunerações líquidas</span>
    </div>
    <div class="kpi-card kpi-accent-green">
      <span class="kpi-label">Média Líquida</span>
      <span class="kpi-value">{fmt_brl(media)}</span>
      <span class="kpi-sub">Variação: {fmt_brl(menor)} – {fmt_brl(maior)}</span>
    </div>
    <div class="kpi-card kpi-accent-amber">
      <span class="kpi-label">Maior Remuneração</span>
      <span class="kpi-value">{fmt_brl(maior)}</span>
      <span class="kpi-sub">Menor: {fmt_brl(menor)}</span>
    </div>
  </div>

  <p class="section-title">Detalhamento</p>
  <div class="card">
    <div class="card-header">
      <span class="card-title">Servidores Encontrados</span>
      <span class="card-hint">Ordenado por remuneração líquida decrescente</span>
    </div>
    <table class="data-table">
      <thead>
        <tr>
          <th>Nome</th>
          <th>Órgão</th>
          <th>Cargo</th>
          <th>Rem. Fixa</th>
          <th>Eventuais</th>
          <th>Rem. Líquida</th>
          <th>Desconto</th>
          <th>% Desc.</th>
        </tr>
      </thead>
      <tbody>{table_rows}</tbody>
    </table>
  </div>

  <p class="section-title">Análise de Remuneração</p>
  <div class="two-col">
    <div class="card">
      <div class="card-header">
        <span class="card-title">Ranking por Remuneração Líquida</span>
      </div>
      <div class="chart-wrap">{charts['bar_liquida']}</div>
    </div>
    <div class="card">
      <div class="card-header">
        <span class="card-title">Distribuição por Órgão</span>
      </div>
      <div class="chart-wrap">{charts['donut']}</div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="card-title">Remuneração Fixa vs Líquida por Servidor</span>
      <span class="card-hint">Barras agrupadas</span>
    </div>
    <div class="chart-wrap">{charts['grouped']}</div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="card-title">Ranking de Descontos</span>
      <span class="card-hint">
        <span style="color:#059669">■</span> &lt;20%&nbsp;&nbsp;
        <span style="color:#D97706">■</span> 20–30%&nbsp;&nbsp;
        <span style="color:#DC2626">■</span> ≥30%
      </span>
    </div>
    <div class="chart-wrap">{charts['desconto']}</div>
  </div>

</div>

<div class="footer">
  Dados extraídos do <strong>Portal da Transparência do Mato Grosso do Sul</strong> — transparencia.ms.gov.br
</div>

</body>
</html>"""


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
    df["Nome Curto"] = df["Nome Encontrado"].apply(
        lambda n: " ".join(n.split()[:2]) if len(n.split()) > 2 else n
    )

    charts = {
        "bar_liquida": chart_div(make_bar_liquida(df), "340px"),
        "donut": chart_div(make_donut(df), "320px"),
        "grouped": chart_div(make_grouped_bar(df), "360px"),
        "desconto": chart_div(make_desconto_bar(df), "340px"),
    }

    html = build_html(df, charts)
    OUTPUT_HTML.parent.mkdir(exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Relatório gerado com sucesso em '{OUTPUT_HTML}'!")


if __name__ == "__main__":
    main()

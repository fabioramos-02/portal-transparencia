import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def clean_currency(val):
    if pd.isna(val):
        return 0.0
    val = str(val).replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(val)
    except:
        return 0.0

def main():
    try:
        df = pd.read_csv('dados_extraidos.csv', encoding='utf-8-sig')
    except FileNotFoundError:
        print("Arquivo 'dados_extraidos.csv' não encontrado. Execute o scraper primeiro.")
        return

    if df.empty:
        print("O arquivo de dados está vazio.")
        return

    # Limpar as colunas de remuneração para números calculáveis
    df['Remuneração Líquida Num'] = df['Remuneração Líquida'].apply(clean_currency)
    df['Remuneração Fixa Num'] = df['Remuneração Fixa'].apply(clean_currency)

    # Ordenar por Remuneração Líquida (do maior para o menor)
    df = df.sort_values('Remuneração Líquida Num', ascending=False)

    # Criar Dashboard
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.4, 0.6],
        specs=[[{"type": "table"}],
               [{"type": "bar"}]],
        subplot_titles=("Tabela de Servidores Encontrados", "Comparativo de Remuneração Líquida (R$)")
    )

    # Tabela
    fig.add_trace(
        go.Table(
            header=dict(
                values=["Nome", "Órgão", "Cargo", "Rem. Líquida"],
                fill_color='paleturquoise',
                align='left',
                font=dict(size=14, color='black')
            ),
            cells=dict(
                values=[df['Nome Encontrado'], df['Órgão Encontrado'], df['Cargo'], df['Remuneração Líquida']],
                fill_color='lavender',
                align='left',
                font=dict(size=12, color='black')
            )
        ),
        row=1, col=1
    )

    # Gráfico de Barras
    fig.add_trace(
        go.Bar(
            x=df['Nome Encontrado'],
            y=df['Remuneração Líquida Num'],
            text=df['Remuneração Líquida'],
            textposition='auto',
            marker_color='indianred',
            hoverinfo='text+x',
            hovertemplate='<b>%{x}</b><br>Remuneração Líquida: R$ %{y:,.2f}<extra></extra>'
        ),
        row=2, col=1
    )

    fig.update_layout(
        title_text="Relatório Executivo de Servidores - Transparência MS",
        height=800,
        showlegend=False,
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    # Configurar eixo Y para moeda
    fig.update_yaxes(tickprefix="R$ ", row=2, col=1)

    # Salvar
    fig.write_html("relatorio_stakeholders.html")
    print("Relatório gerado com sucesso em 'relatorio_stakeholders.html'!")

if __name__ == "__main__":
    main()

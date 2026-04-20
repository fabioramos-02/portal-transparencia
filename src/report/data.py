from pathlib import Path

import pandas as pd


def clean_currency(val) -> float:
    if pd.isna(val):
        return 0.0
    val = str(val).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(val)
    except Exception:
        return 0.0


def fmt_brl(valor: float) -> str:
    s = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def load_and_prepare(csv_path: Path) -> tuple[list[dict], list[str]] | tuple[None, None]:
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"Arquivo '{csv_path}' não encontrado. Execute o scraper primeiro.")
        return None, None

    if df.empty:
        print("O arquivo de dados está vazio.")
        return None, None

    df["Líquida"]   = df["Remuneração Líquida"].apply(clean_currency)
    df["Fixa"]      = df["Remuneração Fixa"].apply(clean_currency)
    df["Eventuais"] = df["Remunerações Eventuais"].apply(clean_currency)
    df["Desconto"]  = (df["Fixa"] - df["Líquida"]).clip(lower=0)
    df["PctDesc"]   = (
        (df["Desconto"] / df["Fixa"].replace(0, float("nan"))) * 100
    ).round(1).fillna(0)
    df = df.sort_values("Líquida", ascending=False).reset_index(drop=True)

    records = []
    for _, row in df.iterrows():
        nome  = str(row["Nome Encontrado"])
        parts = nome.split()
        records.append({
            "nome":         nome,
            "nomeCurto":    " ".join(parts[:2]) if len(parts) > 2 else nome,
            "orgao":        row["Órgão Encontrado"],
            "cargo":        str(row["Cargo"]),
            "fixa":         row["Fixa"],
            "eventuais":    row["Eventuais"],
            "liquida":      row["Líquida"],
            "desconto":     row["Desconto"],
            "pctDesc":      row["PctDesc"],
            "fixaFmt":      row["Remuneração Fixa"],
            "eventuaisFmt": row["Remunerações Eventuais"],
            "liquidaFmt":   row["Remuneração Líquida"],
        })

    orgaos = sorted(df["Órgão Encontrado"].dropna().unique().tolist())
    return records, orgaos

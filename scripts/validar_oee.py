"""Calcula o OEE pela composição em tempo e confere as identidades do memorial.

Reproduz em Python as mesmas contas das medidas DAX (dax/medidas-oee.dax) e
mostra, com a base sintética, os três pontos que mais geram número errado:

1. OEE = F / B fecha por construção com Disponibilidade x Desempenho x Qualidade.
2. Qualidade em peça (boas / produzidas) não é a qualidade do OEE: o refugo
   precisa entrar em TEMPO, porque molde de ciclo lento gasta mais tempo por peça.
3. Média de índices por máquina não é o índice da planta: agregar pela forma
   aditiva (soma dos tempos) dispensa escolher peso e não distorce.

Uso:
    python scripts/validar_oee.py
"""
from pathlib import Path

import pandas as pd

PASTA_DADOS = Path(__file__).resolve().parents[1] / "dados"


def componentes(df: pd.DataFrame) -> pd.Series:
    """Agregados de tempo do memorial, em horas."""
    c = df["Horas_Trab"].sum()                                    # C trabalhadas
    a1 = df["Horas_Paradas"].sum()                                # A1 paradas
    b = c + a1                                                    # B disponíveis
    teorico = df["Hrs_Teorico"].sum()
    cav_isolada = (df["Hrs_Teorico"] * (1 - df["Cav_Ativas"] / df["Cav_Total"])).sum()
    e = teorico - cav_isolada                                     # E total produzido
    refugo_tempo = (df["Horas_Trab"] * df["Pecas_Ref"] / df["Pecas_Prod"].where(df["Pecas_Prod"] > 0)).sum()
    f = e - refugo_tempo                                          # F produtivas
    return pd.Series(
        {
            "B": b, "C": c, "A1": a1, "Teorico": teorico, "CavIsolada": cav_isolada,
            "E": e, "RefugoTempo": refugo_tempo, "F": f,
            "Disponibilidade": c / b,
            "Desempenho": e / c,
            "Qualidade": f / e,
            "OEE": f / b,
            "Qualidade_peca": 1 - df["Pecas_Ref"].sum() / df["Pecas_Prod"].sum(),
        }
    )


def main():
    df = pd.read_csv(PASTA_DADOS / "fInjet_Consolidado.csv", parse_dates=["Data"])
    df["Mes"] = df["Data"].dt.to_period("M")

    por_planta = df.groupby("Filial").apply(componentes, include_groups=False)

    print("\n1) OEE = F/B  x  Disponibilidade x Desempenho x Qualidade")
    produto = por_planta["Disponibilidade"] * por_planta["Desempenho"] * por_planta["Qualidade"]
    tabela = pd.DataFrame(
        {
            "Disponib.": por_planta["Disponibilidade"],
            "Desemp.": por_planta["Desempenho"],
            "Qualid.": por_planta["Qualidade"],
            "OEE (F/B)": por_planta["OEE"],
            "D x P x Q": produto,
            "Diferença (pp)": (por_planta["OEE"] - produto) * 100,
        }
    )
    print((tabela * [100, 100, 100, 100, 100, 1]).round(4).to_string())
    assert (tabela["Diferença (pp)"].abs() < 1e-9).all(), "identidade não fechou"

    print("\n2) Qualidade em peça x qualidade em tempo")
    q = pd.DataFrame(
        {
            "Em peça %": por_planta["Qualidade_peca"] * 100,
            "Em tempo % (OEE)": por_planta["Qualidade"] * 100,
        }
    )
    q["Diferença (pp)"] = q["Em peça %"] - q["Em tempo % (OEE)"]
    print(q.round(2).to_string())

    print("\n3) Média simples dos OEE por máquina x OEE aditivo da planta")
    por_maquina = df.groupby(["Filial", "Maquina"]).apply(componentes, include_groups=False)
    media_simples = por_maquina.groupby("Filial")["OEE"].mean()
    m = pd.DataFrame(
        {
            "Média das máquinas %": media_simples * 100,
            "Aditivo (F/B) %": por_planta["OEE"] * 100,
        }
    )
    m["Distorção (pp)"] = m["Média das máquinas %"] - m["Aditivo (F/B) %"]
    print(m.round(2).to_string())

    print("\n4) OEE mensal por planta (%)")
    mensal = df.groupby(["Filial", "Mes"]).apply(componentes, include_groups=False)["OEE"].unstack(0) * 100
    print(mensal.round(1).to_string())

    print("\n5) Desempenho acima de 100%: máquina rodando mais rápido que o ciclo padrão")
    print((por_planta[["Desempenho"]] * 100).round(2).to_string())


if __name__ == "__main__":
    main()

"""Gera a base sintética usada neste repositório.

Os dados imitam o grão e o comportamento de um MES de injeção plástica
(apontamento por turno x máquina x molde), mas são 100% fictícios: nomes de
produto, máquinas, volumes e índices foram sorteados. Nenhum número aqui vem
de uma empresa real.

Uso:
    python scripts/gerar_dados_sinteticos.py

Gera em dados/:
    fInjet_Consolidado.csv  grão: data x turno x planta x máquina x molde
    fInjet_Paradas.csv      grão: data x turno x máquina x motivo de parada
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEMENTE = 42
INICIO, FIM = "2026-01-01", "2026-06-30"
TURNOS = ["1º Turno", "2º Turno", "3º Turno"]
HORAS_TURNO = 8.0

PLANTAS = {
    # planta: (qtd máquinas, ritmo médio, prob. cavidade bloqueada, refugo médio)
    "Planta A": (18, 1.010, 0.18, 0.016),
    "Planta B": (14, 1.018, 0.04, 0.012),
}
TONELAGENS = [80, 100, 150, 220, 250, 300, 380, 450, 600]

MOTIVOS = [
    # (código, motivo, área, peso)
    ("P01", "Troca de molde", "Setup", 0.22),
    ("P02", "Ajuste de processo", "Processo", 0.18),
    ("P03", "Manutenção corretiva", "Manutenção", 0.17),
    ("P04", "Falta de matéria-prima", "PCP", 0.12),
    ("P05", "Limpeza de molde", "Ferramentaria", 0.10),
    ("P06", "Falta de operador", "Produção", 0.08),
    ("P07", "Aguardando qualidade", "Qualidade", 0.07),
    ("P08", "Falta de energia", "Utilidades", 0.06),
]

PASTA_DADOS = Path(__file__).resolve().parents[1] / "dados"


def montar_parque(rng):
    """Máquinas e moldes de cada planta. O código da máquina traz a tonelagem."""
    parque = []
    n_produto = 1
    for planta, (qtd, *_rest) in PLANTAS.items():
        prefixo = "A" if planta == "Planta A" else "B"
        for i in range(qtd):
            ton = rng.choice(TONELAGENS)
            maquina = f"{ton}/{i + 1:02d}{prefixo}"
            for _ in range(rng.integers(2, 5)):  # moldes que rodam na máquina
                cav = int(rng.choice([1, 2, 4, 8, 16], p=[0.25, 0.3, 0.25, 0.15, 0.05]))
                parque.append(
                    {
                        "Filial": planta,
                        "Maquina": maquina,
                        "Molde": f"MD{n_produto:04d}",
                        "Produto": f"PRD-{n_produto:04d}",
                        "Cav_Total": cav,
                        "Ciclo_Padrao_s": round(float(rng.uniform(14, 70)), 1),
                        "Peso_Liquido_Medio": round(float(rng.uniform(8, 450)), 1),
                    }
                )
                n_produto += 1
    return pd.DataFrame(parque)


def gerar(rng):
    parque = montar_parque(rng)
    datas = pd.date_range(INICIO, FIM, freq="D")
    linhas, paradas = [], []

    for maquina, moldes in parque.groupby("Maquina"):
        planta = moldes["Filial"].iloc[0]
        _, ritmo_medio, p_bloqueio, refugo_medio = PLANTAS[planta]
        molde_atual = moldes.sample(1, random_state=int(rng.integers(1e9))).iloc[0]
        # cada máquina tem a própria taxa de escala e de parada: máquina pouco
        # escalada costuma ser a que mais para, e é ela que distorce a média simples
        escala = float(rng.uniform(0.25, 1.0))
        beta_parada = 6 + 20 * escala

        for data in datas:
            if data.weekday() == 6 and rng.random() < 0.7:  # domingo quase sempre parado
                continue
            if rng.random() < 0.04:  # troca de molde
                molde_atual = moldes.sample(1, random_state=int(rng.integers(1e9))).iloc[0]

            for turno in TURNOS:
                if rng.random() > escala:  # turno sem escala
                    continue
                frac_parada = float(np.clip(rng.beta(1.3, beta_parada), 0, 0.9))
                horas_paradas = HORAS_TURNO * frac_parada
                horas_trab = HORAS_TURNO - horas_paradas

                cav_total = int(molde_atual["Cav_Total"])
                cav_ativas = cav_total
                if cav_total > 1 and rng.random() < p_bloqueio:
                    cav_ativas = int(cav_total - rng.integers(1, max(2, cav_total // 2 + 1)))

                ritmo = float(rng.normal(ritmo_medio, 0.03))
                ciclo_padrao = float(molde_atual["Ciclo_Padrao_s"])
                injecoes = int(horas_trab * 3600 / (ciclo_padrao / ritmo))
                hrs_teorico = injecoes * ciclo_padrao / 3600
                pecas_prod = injecoes * cav_ativas
                # moldes de ciclo lento refugam um pouco mais: é isso que separa
                # a qualidade em peça da qualidade em tempo
                fator_ciclo = ciclo_padrao / 40
                pecas_ref = int(rng.binomial(pecas_prod, min(0.2, refugo_medio * fator_ciclo)))

                linhas.append(
                    {
                        "Data": data.date(),
                        "Turno": turno,
                        "Filial": planta,
                        "Produto": molde_atual["Produto"],
                        "Molde": molde_atual["Molde"],
                        "Maquina": maquina,
                        "Cav_Total": cav_total,
                        "Cav_Ativas": cav_ativas,
                        "Ind_Cav": round(cav_ativas / cav_total, 4),
                        "Ciclo_Padrao_s": ciclo_padrao,
                        "Peso_Liquido_Medio": molde_atual["Peso_Liquido_Medio"],
                        "Horas_Trab": round(horas_trab, 4),
                        "Horas_Paradas": round(horas_paradas, 4),
                        "Hrs_Teorico": round(hrs_teorico, 4),
                        "Pecas_Prod": pecas_prod,
                        "Pecas_Ref": pecas_ref,
                        "Pecas_Boas": pecas_prod - pecas_ref,
                    }
                )

                # Paradas apontadas pelo operador. Somam mais que Horas_Paradas porque
                # incluem parada fora do tempo ativo (como acontece no MES real).
                minutos_restantes = horas_paradas * 60 * rng.uniform(2.5, 3.3)
                pesos = np.array([m[3] for m in MOTIVOS])
                while minutos_restantes > 5:
                    cod, motivo, area, _ = MOTIVOS[rng.choice(len(MOTIVOS), p=pesos / pesos.sum())]
                    duracao = int(min(minutos_restantes, rng.gamma(2, 25)))
                    if duracao < 1:
                        break
                    paradas.append(
                        {
                            "Data_Turno": data.date(),
                            "Turno": turno,
                            "Maquina": maquina,
                            "Molde": molde_atual["Molde"],
                            "Produto": molde_atual["Produto"],
                            "Cod_Parada": cod,
                            "Motivo": motivo,
                            "Area": area,
                            "Eventos": 1,
                            "Duracao_Min": duracao,
                            "Filial": planta,
                        }
                    )
                    minutos_restantes -= duracao

    # mesmo grão do MES: um registro por turno x máquina x motivo
    chaves = ["Data_Turno", "Turno", "Maquina", "Molde", "Produto", "Cod_Parada", "Motivo", "Area", "Filial"]
    paradas = pd.DataFrame(paradas).groupby(chaves, as_index=False)[["Eventos", "Duracao_Min"]].sum()
    return pd.DataFrame(linhas), paradas


def main():
    rng = np.random.default_rng(SEMENTE)
    consolidado, paradas = gerar(rng)
    PASTA_DADOS.mkdir(exist_ok=True)
    consolidado.to_csv(PASTA_DADOS / "fInjet_Consolidado.csv", index=False)
    paradas.to_csv(PASTA_DADOS / "fInjet_Paradas.csv", index=False)
    print(f"fInjet_Consolidado.csv: {len(consolidado):,} linhas")
    print(f"fInjet_Paradas.csv:     {len(paradas):,} linhas")


if __name__ == "__main__":
    main()

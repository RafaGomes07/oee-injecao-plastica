"""Desenha a cascata de perdas do OEE (B -> F) com a base sintética.

Uso:
    python scripts/grafico_cascata.py

Gera docs/cascata-perdas.svg (SVG escrito direto, sem biblioteca de gráfico).
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
W, H, ESQ, TOPO, BASE = 720, 340, 30, 50, 290


def br(v, casas=0, sinal=False):
    s = f"{v:+,.{casas}f}" if sinal else f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    df = pd.read_csv(RAIZ / "dados" / "fInjet_Consolidado.csv")
    c = df["Horas_Trab"].sum()
    a1 = df["Horas_Paradas"].sum()
    b = c + a1
    teorico = df["Hrs_Teorico"].sum()
    cav = (df["Hrs_Teorico"] * (1 - df["Cav_Ativas"] / df["Cav_Total"])).sum()
    ref = (df["Horas_Trab"] * df["Pecas_Ref"] / df["Pecas_Prod"].where(df["Pecas_Prod"] > 0)).sum()
    f = teorico - cav - ref

    etapas = [("Disponível", "(B)"), ("Parada", "(A1)"), ("Ritmo acima", "do padrão"),
              ("Cavidade", "isolada"), ("Refugo", "em tempo"), ("Produtivo", "(F)")]
    deltas = [b, -a1, teorico - c, -cav, -ref, f]

    # o eixo não começa em zero, para dar leitura às perdas
    y_min, y_max = b * 0.85, b * 1.01
    def y(v):
        return BASE - (v - y_min) / (y_max - y_min) * (BASE - TOPO)

    passo = (W - ESQ - 10) / len(etapas)
    larg = passo * 0.6
    el = [
        f'<rect width="{W}" height="{H}" fill="#fff"/>',
        f'<text x="{ESQ}" y="28" font-size="15">Cascata de perdas do OEE, base sintética '
        f'(OEE = F/B = {br(f / b * 100, 1)}%)</text>',
        f'<line x1="{ESQ}" y1="{BASE}" x2="{W - 10}" y2="{BASE}" stroke="#333"/>',
    ]
    nivel = 0
    for i, ((l1, l2), d) in enumerate(zip(etapas, deltas)):
        x = ESQ + passo * i + (passo - larg) / 2
        cx = x + larg / 2
        if i in (0, len(etapas) - 1):
            topo, fundo, cor, nivel = d, y_min, "#2f5d8a", d
            rotulo = br(d) + " h"
        else:
            topo, fundo = (nivel + d, nivel) if d >= 0 else (nivel, nivel + d)
            cor = "#3f9c6e" if d >= 0 else "#c8553d"
            nivel += d
            rotulo = br(d, sinal=True) + " h"
        el.append(f'<rect x="{x:.0f}" y="{y(topo):.0f}" width="{larg:.0f}" height="{y(fundo) - y(topo):.0f}" fill="{cor}"/>')
        el.append(f'<text x="{cx:.0f}" y="{y(topo) - 7:.0f}" text-anchor="middle">{rotulo}</text>')
        el.append(f'<text x="{cx:.0f}" y="{BASE + 18}" text-anchor="middle">{l1}</text>')
        el.append(f'<text x="{cx:.0f}" y="{BASE + 33}" text-anchor="middle">{l2}</text>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="12" fill="#222">\n'
           + "\n".join(el) + "\n</svg>\n")
    (RAIZ / "docs" / "cascata-perdas.svg").write_text(svg, encoding="utf-8")
    print("docs/cascata-perdas.svg")


if __name__ == "__main__":
    main()

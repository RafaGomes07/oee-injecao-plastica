# OEE de injeção plástica conciliado ao MES

Modelo de OEE para uma planta de injeção plástica, construído em Power BI, que reproduz o cálculo do MES de chão de fábrica e fecha com o relatório oficial da fábrica.

> Os dados deste repositório são **sintéticos**, gerados por `scripts/gerar_dados_sinteticos.py`. A lógica, as medidas DAX e o modelo vêm de um projeto real, com nomes, volumes e índices trocados.

![Cascata de perdas do OEE](docs/cascata-perdas.png)

## O problema

O OEE do painel de BI não batia com o OEE do relatório do MES, e cada área tinha a sua explicação para a diferença. Com dois números para o mesmo indicador, a discussão de produção começava por "qual dos dois está certo?".

## O que descobri

**O MES calcula tudo em tempo, não em peças.** Disponibilidade, desempenho e qualidade são razões entre agregados de horas. Reconstruir o índice a partir de peças boas e produzidas nunca fecha, e foi o que travou as primeiras tentativas.

A partir disso, três erros do modelo antigo apareceram:

1. **Cavidade bloqueada estava na qualidade.** Ela é perda de desempenho (tempo teórico que o molde deixou de produzir). Somar cavidade ao refugo descontava a mesma perda duas vezes.
2. **Refugo entrava em peça.** Molde de ciclo lento gasta mais tempo por peça refugada, então a qualidade em peça fica acima da qualidade em tempo.
3. **Índices eram agregados por média.** Máquina pouco escalada pesava igual a máquina que rodou o mês todo. A forma aditiva (soma dos tempos) resolve sem precisar escolher peso.

O detalhamento está no [memorial de cálculo](docs/memorial-de-calculo.md).

## Resultado

Conferido mês a mês contra o relatório oficial, em duas plantas:

- Disponibilidade e Qualidade: **exatas**
- OEE: **erro médio de 0,07 pp** em 6 meses (pior mês, 0,16 pp)
- O resíduo vem de um único componente, investigado e documentado, sem ajuste artificial para "fazer bater"

## Como o OEE é montado

```
B  Disponíveis   = horas trabalhadas + paradas
C  Trabalhadas   = tempo de ciclo apontado
E  Produzido     = teórico - cavidade isolada
F  Produtivas    = E - refugo em tempo

Disponibilidade = C / B      Desempenho = E / C      Qualidade = F / E

OEE = F / B = (C/B) x (E/C) x (F/E)
```

## Estrutura

```
dados/      criado por scripts/gerar_dados_sinteticos.py (semente fixa: a base é sempre a mesma)
dax/        medidas do modelo (OEE, cascata, Pareto, MTBF/MTTR, diagnóstico por máquina)
docs/       memorial de cálculo e modelo de dados
scripts/    geração da base, validação das identidades e gráfico da cascata
```

## Rodando

```bash
pip install -r requirements.txt
python scripts/gerar_dados_sinteticos.py   # cria os CSVs em dados/
python scripts/validar_oee.py              # confere as identidades e mostra as distorções
python scripts/grafico_cascata.py          # gera docs/cascata-perdas.png
```

Saída da validação na base sintética:

| Verificação | Planta A | Planta B |
|---|---:|---:|
| OEE (F/B) | 87,1% | 93,3% |
| F/B menos Disponib. x Desemp. x Qualid. | 0,00 pp | 0,00 pp |
| Qualidade em peça menos qualidade em tempo | +0,39 pp | +0,12 pp |
| Média simples por máquina menos OEE aditivo | -0,26 pp | -0,78 pp |

## Modelo de dados

Esquema estrela, 100% Import, sem relacionamento bidirecional. Dimensões ponte de máquina e turno ligam a fato de produção à fato de paradas. Mais em [modelo de dados](docs/modelo-de-dados.md).

**Stack:** Power BI (PBIP/TMDL) · DAX · Power Query · SQL Server · Python (pandas)

---

Rafael Gomes · [LinkedIn](https://www.linkedin.com/in/rafael-gomes-analista-de-dados) · [Portfólio](https://app.xperiun.com/in/rafagomes)

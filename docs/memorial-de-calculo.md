# Memorial de cálculo do OEE

Como o MES de injeção monta os índices do relatório oficial de situação da fábrica, e como o modelo reproduz essa conta.

A descoberta central: **o MES calcula tudo em unidade de tempo** (horas), não em peças. As quantidades em peças que aparecem no relatório são derivadas depois. Reconstruir os índices a partir de peças não fecha, e foi isso que travou a conciliação por várias iterações.

## Componentes de tempo

| Código | Nome | O que é |
|---|---|---|
| `D` | Ciclos produtivos | tempo de ciclo normal apontado |
| `A1` | Paradas | parada **dentro** do tempo ativo |
| `A2` | Não disponíveis | tempo de calendário fora da escala |
| `A4` | Refugos | refugo convertido em tempo |
| `A5` | Ritmo | ganho ou perda por ciclo fora do padrão |
| - | Cavidade isolada | tempo teórico perdido por cavidade bloqueada no molde |

`A5` é **negativo quando a máquina roda mais rápido que o ciclo padrão**, o caso mais comum. Por isso o Desempenho passa de 100%.

## Agregados

```
C  Trabalhadas      = D
B  Disponíveis      = C + A1
A  Totais           = B + A2
E  Total produzido  = D - Cavidade isolada - A5
F  Produtivas       = E - A4
```

## Índices

```
Disponibilidade  = C / B
Desempenho       = E / C
Qualidade        = F / E
OEE              = F / B
```

O OEE fecha por construção com `Disponibilidade x Desempenho x Qualidade`, porque os termos intermediários se cancelam:

```
C/B  x  E/C  x  F/E  =  F/B
```

## Derivação no grão do apontamento (turno x máquina x molde)

```
Hrs_Teorico   = injeções x ciclo padrão
Cav_Isolada   = Hrs_Teorico x (1 - cavidades ativas / cavidades totais)
Hrs_Refugo    = Horas_Trab x (peças refugadas / peças produzidas)
```

## O que aprendi conciliando com o relatório oficial

**1. A Qualidade é em tempo, e cavidade não entra nela.** Cavidade bloqueada é perda de Desempenho (tempo teórico que o molde deixou de produzir). A versão anterior somava cavidade ao refugo e descontava a mesma perda duas vezes.

**2. Qualidade em peça não é qualidade de OEE.** `boas / produzidas` supera a qualidade em tempo, porque molde de ciclo lento gasta mais tempo por peça refugada. Na base sintética a diferença é de 0,4 pp na Planta A (veja `scripts/validar_oee.py`).

**3. Desempenho e eficiência de ciclo são grandezas diferentes.** Eficiência de ciclo é teórico / trabalhado, sem desconto de cavidade. Desempenho é ela descontada da cavidade isolada.

**4. Peso de agregação importa.** Média de índices por máquina distorce o índice da planta, porque máquina pouco escalada pesa igual a máquina que rodou o mês todo. A forma aditiva resolve sem precisar escolher peso:

```
Disponibilidade = SUM(Horas_Trab) / (SUM(Horas_Trab) + SUM(Horas_Paradas))
Desempenho      = (SUM(Hrs_Teorico) - SUM(Cav_Isolada)) / SUM(Horas_Trab)
Qualidade       = F / E
OEE             = F / B
```

Na base sintética, a média simples subestima o OEE em 0,3 pp na Planta A e 0,8 pp na Planta B.

**5. Parada apontada não é parada do OEE.** A duração que o operador aponta por motivo soma cerca de 3 vezes a parada `A1`, porque inclui máquina parada fora do turno apontado. Ela serve para Pareto, MTBF, MTTR e setup, nunca para o índice. No modelo, ela entra só como proporção para ratear a `A1` oficial por área.

**6. Injeções fora do ciclo normal ficam de fora.** Injeções durante parada têm ciclo muito maior que o normal e derrubam o Desempenho em vários pontos se forem incluídas. O relatório oficial também as exclui.

## Resultado da conciliação

O modelo foi conferido mês a mês contra o relatório oficial do MES, em duas plantas:

| Índice | Resultado |
|---|---|
| Disponibilidade | exata |
| Qualidade | exata |
| Desempenho | diferença na segunda casa decimal |
| OEE | erro médio de 0,07 pp em 6 meses, pior mês 0,16 pp |

O resíduo vem de um único componente, a cavidade isolada. Três hipóteses foram testadas e descartadas (cadastro de cavidades instável, tratamento especial de bloqueio severo e relação dose-resposta com a fração inativa). Um teto ajustado na fração inativa fecharia a conta, mas seria um parâmetro livre calibrado em poucos pontos, sem explicação física, e por isso **não foi implementado**.

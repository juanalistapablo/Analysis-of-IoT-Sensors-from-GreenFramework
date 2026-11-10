import calendar
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


def preparar_dados_temporais(df, coluna_tempo="timestamp_leitura_anterior"):
    """Trata os dados temporais: converte para datetime, remove nulos,

    adiciona o dia da semana e transforma o tempo no índice.
    """
    df_plot = df.copy()

    if coluna_tempo in df_plot.columns:
        df_plot[coluna_tempo] = pd.to_datetime(
            df_plot[coluna_tempo], errors="coerce"
        )
        df_plot = df_plot.dropna(subset=[coluna_tempo])

        dias_pt = {
            "Monday": "Segunda-feira",
            "Tuesday": "Terça-feira",
            "Wednesday": "Quarta-feira",
            "Thursday": "Quinta-feira",
            "Friday": "Sexta-feira",
            "Saturday": "Sábado",
            "Sunday": "Domingo",
        }

        df_plot["dia_da_semana"] = (
            df_plot[coluna_tempo].dt.day_name().map(dias_pt)
        )
        df_plot = df_plot.set_index(coluna_tempo)

        print(
            "✅ Dados temporais tratados. Coluna 'dia_da_semana' adicionada e índice configurado."
        )
        return df_plot
    else:
        print(f"❌ Erro: Coluna '{coluna_tempo}' não encontrada.")
        return df

def plotar_calendario_mensal(df, ano, mes, coluna):
    """Gera uma grade de gráficos (calendário) e retorna o objeto da figura."""
    filtro_mes = f"{ano}-{mes:02d}"
    try:
        df_mes = df.loc[filtro_mes]
    except KeyError:
        print(f"❌ Erro: Nenhum dado de {filtro_mes} encontrado.")
        return None

    cal = calendar.monthcalendar(ano, mes)
    semanas = len(cal)
    nomes_dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    fig, axes = plt.subplots(
        nrows=semanas, ncols=7, figsize=(20, 3 * semanas), sharey=True
    )
    if semanas == 1:
        axes = [axes]

    fig.suptitle(
        f"Curva de Carga (Calendário): {coluna} - {mes:02d}/{ano}",
        fontsize=18,
        y=1.02,
        fontweight="bold",
    )

    for semana_idx, semana in enumerate(cal):
        for dia_semana_idx, dia in enumerate(semana):
            ax = axes[semana_idx][dia_semana_idx]

            if dia == 0:
                ax.axis("off")
                continue

            data_str = f"{ano}-{mes:02d}-{dia:02d}"
            try:
                df_dia = df_mes.loc[data_str]
            except KeyError:
                df_dia = pd.DataFrame()

            if df_dia.empty or df_dia[coluna].dropna().empty:
                ax.text(
                    0.5,
                    0.5,
                    "Sem\ndados",
                    ha="center",
                    va="center",
                    alpha=0.3,
                    fontsize=12,
                )
                ax.set_title(
                    f"{dia} - {nomes_dias[dia_semana_idx]}", fontsize=11
                )
                ax.set_xticks([])
                ax.set_yticks([])
                continue

            ax.plot(df_dia.index, df_dia[coluna], color="#2ca02c", linewidth=2)
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Hh"))

            ax.set_title(
                f"{dia} - {nomes_dias[dia_semana_idx]}",
                fontsize=11,
                fontweight="bold",
            )
            ax.grid(True, linestyle="--", alpha=0.4)
            ax.tick_params(axis="x", rotation=0, labelsize=9)
            ax.tick_params(axis="y", labelsize=9)

            if dia_semana_idx >= 5:
                ax.set_facecolor("#f4f4f4")

    plt.tight_layout()

    # Retorna o objeto da figura em vez de dar plt.show()
    return fig    

def plotar_dias_sequenciais(df, ano, mes, coluna):

    """Gera gráficos diários empilhados verticalmente (um embaixo do outro).

    O eixo X pula de 2 em 2 horas fixando das 00:00 às 23:59.
    """
    filtro_mes = f"{ano}-{mes:02d}"
    try:
        df_mes = df.loc[filtro_mes]
    except KeyError:
        print(f"❌ Erro: Nenhum dado de {filtro_mes} encontrado.")
        return

    # Gera o intervalo contínuo de dias para o mês (inclui dias sem dado na base)
    dias_do_mes = pd.date_range(
        start=f"{ano}-{mes:02d}-01",
        end=f"{ano}-{mes:02d}-{calendar.monthrange(ano, mes)[1]}",
        freq="D",
    )
    num_dias = len(dias_do_mes)

    fig, axes = plt.subplots(
        nrows=num_dias, ncols=1, figsize=(15, 3.5 * num_dias), sharey=True
    )
    if num_dias == 1:
        axes = [axes]

    fig.suptitle(
        f"Curva de Carga Sequencial: {coluna} - {mes:02d}/{ano}",
        fontsize=18,
        y=1.005,
        fontweight="bold",
    )

    dias_pt = [
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo",
    ]

    for idx, dia in enumerate(dias_do_mes):
        ax = axes[idx]
        data_str = dia.strftime("%Y-%m-%d")

        inicio_dia = pd.Timestamp(f"{data_str} 00:00:00")
        fim_dia = pd.Timestamp(f"{data_str} 23:59:59")

        nome_dia = dias_pt[dia.weekday()]

        try:
            df_dia = df_mes.loc[data_str]
        except KeyError:
            df_dia = pd.DataFrame()

        ax.set_title(
            f"Dia {dia.day:02d} - {nome_dia}",
            fontsize=12,
            fontweight="bold",
            loc="left",
        )

        # Fixa obrigatoriamente os limites do dia completo
        ax.set_xlim([inicio_dia, fim_dia])
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Hh"))

        if df_dia.empty or df_dia[coluna].dropna().empty:
            ax.text(
                0.5,
                0.5,
                "Sem dados disponíveis",
                ha="center",
                va="center",
                alpha=0.5,
                fontsize=12,
                transform=ax.transAxes,
            )
            ax.grid(True, linestyle="--", alpha=0.5)
            ax.set_ylabel("Potência (kW)")
            continue

        # Ordena temporalmente
        df_dia = df_dia.sort_index()

        ax.plot(df_dia.index, df_dia[coluna], color="#2ca02c", linewidth=2)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.set_ylabel("Potência (kW)")
        ax.tick_params(axis="x", rotation=0, labelsize=10)
        ax.tick_params(axis="y", labelsize=10)

        if nome_dia in ["Sábado", "Domingo"]:
            ax.set_facecolor("#f4f4f4")

    plt.tight_layout()
    plt.show()

import os
import gc
import calendar
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

# ... (a sua função preparar_dados_temporais continua aqui no topo normalmente) ...

def plotar_calendario_mensal(df, colunas, pasta_base="graficos_mensais", nome_medidor="medidor"):
    """
    Gera calendários com Eixo Y Duplo (Tensão e Corrente no mesmo dia).
    Mantém as regras de cores (Azul/Amarelo) e estilos de linha (Contínua/Tracejada/Pontilhada).
    """
    import os
    import gc
    import calendar
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import pandas as pd

    if not hasattr(df.index, "year"):
        print("❌ Erro: O índice do DataFrame não é temporal.")
        return

    colunas_lista = [colunas] if isinstance(colunas, str) else colunas
    
    # Nome genérico para a análise combinada
    nome_pasta_var = "tensao_e_corrente"
    titulo_grafico = "Tensão (Azul) e Corrente (Amarelo) - 3 Fases"

    pasta_destino = os.path.join(pasta_base, f"analise_{nome_pasta_var}")
    os.makedirs(pasta_destino, exist_ok=True)

    periodos = df.index.to_period("M").unique()
    print(f"📊 Iniciando lote ({len(periodos)} meses) para '{titulo_grafico}'...")

    for periodo in periodos:
        ano = periodo.year
        mes = periodo.month
        
        filtro_mes = f"{ano}-{mes:02d}"
        try:
            df_mes = df.loc[filtro_mes]
        except KeyError:
            continue
            
        if df_mes.empty:
            continue

        print(f"  -> Renderizando calendário: {mes:02d}/{ano}")

        cal = calendar.monthcalendar(ano, mes)
        semanas = len(cal)
        nomes_dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

        fig, axes = plt.subplots(nrows=semanas, ncols=7, figsize=(20, 3 * semanas), sharey=True)
        if semanas == 1: axes = [axes]

        fig.suptitle(f"{titulo_grafico} - Medidor {nome_medidor} ({mes:02d}/{ano})", fontsize=18, y=1.03, fontweight="bold")

        # Variáveis para capturar uma única legenda limpa no topo
        linhas_legenda = []
        labels_legenda = []

        for semana_idx, semana in enumerate(cal):
            for dia_semana_idx, dia in enumerate(semana):
                ax = axes[semana_idx][dia_semana_idx]

                if dia == 0:
                    ax.axis("off")
                    continue

                data_str = f"{ano}-{mes:02d}-{dia:02d}"
                try:
                    df_dia = df_mes.loc[data_str].sort_index()
                except KeyError:
                    df_dia = pd.DataFrame()

                tem_dados = any(col in df_dia.columns and not df_dia[col].dropna().empty for col in colunas_lista)

                if not tem_dados:
                    ax.text(0.5, 0.5, "Sem\ndados", ha="center", va="center", alpha=0.3, fontsize=12)
                    ax.set_title(f"{dia} - {nomes_dias[dia_semana_idx]}", fontsize=11)
                    ax.set_xticks([])
                    ax.set_yticks([])
                    continue
                
                # ax2 será o nosso eixo Y secundário (lado direito)
                ax2 = None
                
                # REGRAS DINÂMICAS DE CORES, ESTILOS E EIXOS
                for col in colunas_lista:
                    if col in df_dia.columns:
                        
                        # Define a cor e em qual eixo plotar
                        if 'voltage' in col.lower():
                            cor = '#1f77b4'  # Azul
                            eixo = ax
                        elif 'current' in col.lower():
                            cor = '#d4ac0d'  # Amarelo Ouro
                            if ax2 is None:
                                ax2 = ax.twinx() # Cria o eixo Y direito na primeira vez que achar corrente
                            eixo = ax2
                        else:
                            cor = '#2ca02c'  # Verde
                            eixo = ax

                        # Define o estilo da linha
                        if '.a' in col.lower(): estilo = '-'      # Contínua
                        elif '.b' in col.lower(): estilo = '--'   # Tracejada
                        elif '.c' in col.lower(): estilo = ':'    # Pontilhada
                        else: estilo = '-'

                        linha = eixo.plot(df_dia.index, df_dia[col], color=cor, linestyle=estilo, linewidth=1.5, label=col)
                        
                        # Salva a referência da linha para a legenda mestre
                        if col not in labels_legenda:
                            linhas_legenda.append(linha[0])
                            labels_legenda.append(col)
                
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%Hh"))
                ax.set_title(f"{dia} - {nomes_dias[dia_semana_idx]}", fontsize=11, fontweight="bold")
                ax.grid(True, linestyle="--", alpha=0.4)
                ax.tick_params(axis="x", rotation=0, labelsize=9)
                ax.tick_params(axis="y", labelsize=9)
                
                # Tratamento do Eixo Secundário (para não sobrepor números no meio do calendário)
                if ax2 is not None:
                    if dia_semana_idx < 6:
                        ax2.set_yticks([]) # Oculta os números da corrente nos dias do meio
                    else:
                        ax2.tick_params(axis="y", labelsize=9) # Mostra os números apenas no Domingo (coluna final)

                if dia_semana_idx >= 5: ax.set_facecolor("#f4f4f4")

        # Adiciona a legenda unificada no topo
        if linhas_legenda:
            fig.legend(linhas_legenda, labels_legenda, loc='upper center', bbox_to_anchor=(0.5, 1.00), ncol=len(colunas_lista), fontsize=13, frameon=False)

        plt.tight_layout()

        nome_arquivo = f"{pasta_destino}/{nome_medidor}_{ano}_{mes:02d}_calendario.png"
        fig.savefig(nome_arquivo, bbox_inches="tight", dpi=150)
        fig.clf()
        plt.close(fig)
        del fig
        gc.collect()
# ==============================================================================

def processar_todos_medidores(lista_caminhos, colunas, funcao_transformacao=None):
    """
    Função Mestra Flexível. Recebe lista de caminhos CSV, e a 'colunas'
    (que pode ser string única ou lista de strings) e orquestra tudo com defesa de RAM.
    """
    import os
    import gc
    import pandas as pd
    
    for caminho_arquivo in lista_caminhos:
        nome_medidor = os.path.basename(caminho_arquivo).replace(".csv", "")
        print(f"\n{'='*50}")
        print(f"🚀 Processando: {nome_medidor} | Alvo: {colunas}")
        print(f"{'='*50}")

        try:
            df = pd.read_csv(caminho_arquivo, low_memory=False)

            if funcao_transformacao is not None:
                df = funcao_transformacao(df)

            df = preparar_dados_temporais(df, coluna_tempo="timestamp_leitura_anterior")
            plotar_calendario_mensal(df, colunas=colunas, nome_medidor=nome_medidor)
            
        except Exception as e:
            print(f"❌ Erro ao processar {nome_medidor}: {e}")

        finally:
            if 'df' in locals():
                del df
            gc.collect()
            print(f"🧹 Memória de {nome_medidor} liberada.")
            
    print("\n✅ LOTE FINALIZADO!")
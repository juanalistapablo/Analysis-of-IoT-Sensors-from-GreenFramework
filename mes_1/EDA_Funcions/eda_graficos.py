import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import calendar

def preparar_dados_temporais(df, coluna_tempo='timestamp_leitura_anterior'):
    """
    Trata os dados temporais: converte para datetime, remove nulos, 
    adiciona o dia da semana e transforma o tempo no índice.
    """
    df_plot = df.copy()
    
    if coluna_tempo in df_plot.columns:
        df_plot[coluna_tempo] = pd.to_datetime(df_plot[coluna_tempo], errors='coerce')
        df_plot = df_plot.dropna(subset=[coluna_tempo])
        
        dias_pt = {
            'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 
            'Wednesday': 'Quarta-feira', 'Thursday': 'Quinta-feira',
            'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        
        df_plot['dia_da_semana'] = df_plot[coluna_tempo].dt.day_name().map(dias_pt)
        df_plot = df_plot.set_index(coluna_tempo)
        
        print("✅ Dados temporais tratados. Coluna 'dia_da_semana' adicionada e índice configurado.")
        return df_plot
    else:
        print(f"❌ Erro: Coluna '{coluna_tempo}' não encontrada.")
        return df

def plotar_calendario_mensal(df, ano, mes, coluna):
    """
    Gera uma grade de gráficos (calendário) diretamente no Notebook.
    """
    filtro_mes = f"{ano}-{mes:02d}"
    try:
        df_mes = df.loc[filtro_mes]
    except KeyError:
        print(f"❌ Erro: Nenhum dado de {filtro_mes} encontrado.")
        return

    cal = calendar.monthcalendar(ano, mes)
    semanas = len(cal)
    nomes_dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

    fig, axes = plt.subplots(nrows=semanas, ncols=7, figsize=(20, 3 * semanas), sharey=True)
    if semanas == 1: axes = [axes]
        
    fig.suptitle(f"Curva de Carga (Calendário): {coluna} - {mes:02d}/{ano}", fontsize=18, y=1.02, fontweight='bold')

    for semana_idx, semana in enumerate(cal):
        for dia_semana_idx, dia in enumerate(semana):
            ax = axes[semana_idx][dia_semana_idx]
            
            if dia == 0:
                ax.axis('off')
                continue
                
            data_str = f"{ano}-{mes:02d}-{dia:02d}"
            try:
                df_dia = df_mes.loc[data_str]
            except KeyError:
                df_dia = pd.DataFrame()
                
            if df_dia.empty or df_dia[coluna].dropna().empty:
                ax.text(0.5, 0.5, 'Sem\ndados', ha='center', va='center', alpha=0.3, fontsize=12)
                ax.set_title(f"{dia} - {nomes_dias[dia_semana_idx]}", fontsize=11)
                ax.set_xticks([])
                ax.set_yticks([])
                continue

            ax.plot(df_dia.index, df_dia[coluna], color='#2ca02c', linewidth=2)
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh'))
            
            ax.set_title(f"{dia} - {nomes_dias[dia_semana_idx]}", fontsize=11, fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.4)
            ax.tick_params(axis='x', rotation=0, labelsize=9)
            ax.tick_params(axis='y', labelsize=9)
            
            if dia_semana_idx >= 5:
                ax.set_facecolor('#f4f4f4')

    plt.tight_layout()
    plt.show()

def plotar_dias_sequenciais(df, ano, mes, coluna):
    """
    Gera gráficos diários empilhados verticalmente (um embaixo do outro).
    O eixo X pula de 2 em 2 horas.
    """
    filtro_mes = f"{ano}-{mes:02d}"
    try:
        df_mes = df.loc[filtro_mes]
    except KeyError:
        print(f"❌ Erro: Nenhum dado de {filtro_mes} encontrado.")
        return

    dias_unicos = df_mes.index.normalize().unique()
    num_dias = len(dias_unicos)

    fig, axes = plt.subplots(nrows=num_dias, ncols=1, figsize=(15, 3.5 * num_dias))
    if num_dias == 1: axes = [axes]

    fig.suptitle(f"Curva de Carga Sequencial: {coluna} - {mes:02d}/{ano}", fontsize=18, y=1.01, fontweight='bold')

    for idx, dia in enumerate(dias_unicos):
        ax = axes[idx]
        data_str = dia.strftime('%Y-%m-%d')
        df_dia = df_mes.loc[data_str]
        
        nome_dia = df_dia['dia_da_semana'].iloc[0] if 'dia_da_semana' in df_dia.columns else ''
        
        if df_dia.empty or df_dia[coluna].dropna().empty:
            ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', alpha=0.5, fontsize=14)
            ax.set_title(f"Dia {dia.day:02d} - {nome_dia}", fontsize=12)
            continue

        ax.plot(df_dia.index, df_dia[coluna], color='#2ca02c', linewidth=2)
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh'))
        
        ax.set_title(f"Dia {dia.day:02d} - {nome_dia}", fontsize=12, fontweight='bold', loc='left')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_ylabel("Potência (kW)")
        ax.tick_params(axis='x', rotation=0, labelsize=10)
        ax.tick_params(axis='y', labelsize=10)
        
        if nome_dia in ['Sábado', 'Domingo']:
            ax.set_facecolor('#f4f4f4')

    plt.tight_layout()
    plt.show()
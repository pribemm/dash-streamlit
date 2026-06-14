import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
    

def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return valor


def formatar_percentual(valor):
    try:
        return f"{float(valor):.2f}%".replace(".", ",")
    except Exception:
        return valor

def formatar_peso(valor):
    try:
        return f"{float(valor):,.2f} Kg".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return valor

def formatar_decimal(valor):
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return valor



def exibir_dataframe(df, altura=None):
    """
    Exibe dataframe com configuração padrão para o dashboard.
    """
    st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        height=altura
    )

def calcular_grandezas_periodo(start_date: datetime, end_date: datetime) -> dict:
    """
    Calcula o total de dias, semanas e meses entre duas datas.
    Retorna os valores totais absolutos e também a visão proporcional (ex: 1 mês, 2 semanas e 3 dias).
    """
    if not start_date or not end_date:
        return {"dias_totais": 0, "semanas_totais": 0, "meses_totais": 0}
    
    # Garante que estamos lidando apenas com a data (sem olhar horas, se houver)
    inicio = pd.to_datetime(start_date).date()
    fim = pd.to_datetime(end_date).date()
    
    # Dias Totais
    diferenca_dias = (fim - inicio).days + 1 # +1 para incluir o próprio dia inicial na contagem do período
    
    # Semanas Totais (com casas decimais)
    semanas_totais = diferenca_dias / 7
    
    # Meses Totais (Aproximação comercial padrão por 30.44 dias)
    anos_dif = fim.year - inicio.year
    meses_dif = fim.month - inicio.month
    meses_totais = (anos_dif * 12) + meses_dif
    
    # Ajuste fino decimal para dias remanescentes no mês
    dia_remanescente_inicio = inicio.day
    dia_remanescente_fim = fim.day
    
    # Adiciona a fração do mês atual baseado em um mês comercial de 30 dias
    meses_totais += (dia_remanescente_fim - dia_remanescente_inicio) / 30.0
    if meses_totais < 0:
        meses_totais = 0
        
    meses_inteiros = int(diferenca_dias // 30.44)
    dias_restantes_mes = int(diferenca_dias % 30.44)
    semanas_inteiras = dias_restantes_mes // 7
    dias_finais = dias_restantes_mes % 7

    return {
        "dias_totais": max(1, diferenca_dias),
        "semanas_totais": round(max(0.1, semanas_totais), 1),
        "semanas_inteiras": semanas_inteiras,
        "meses_totais": round(max(0.1, meses_totais), 1),
        "meses_inteiros": meses_inteiros,
    }

def agrupar_por_granularidade(df: pd.DataFrame, coluna_data: str, coluna_valor: str, granularidade: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Auxiliar para agrupar o DataFrame de acordo com a granularidade temporal,
    garantindo que períodos sem vendas também apareçam preenchidos com zero.
    """
    df = df.copy()
    df[coluna_data] = pd.to_datetime(df[coluna_data])
    
    # Se o usuário não escolheu datas extremas no filtro, usamos os limites dos dados
    if not start_date:
        start_date = df[coluna_data].min()
    if not end_date:
        end_date = df[coluna_data].max()
        
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    if granularidade.lower() == 'diaria':
        df['Tempo'] = df[coluna_data].dt.date
        df_agrupado = df.groupby('Tempo')[coluna_valor].sum().reset_index()
        
        # Cria a sequência completa de todos os dias do período
        sequencia_completa = pd.date_range(start=start_date, end=end_date, freq='D').date
        df_completo = pd.DataFrame({'Tempo': sequencia_completa})
        
        # Junta os dados reais com o calendário completo e preenche os vazios com 0
        df_final = pd.merge(df_completo, df_agrupado, on='Tempo', how='left').fillna(0)

    elif granularidade.lower() == 'semanal':
        # Começo da semana (Segunda-feira)
        df['Tempo'] = df[coluna_data].dt.to_period('W').apply(lambda r: r.start_time.date())
        df_agrupado = df.groupby('Tempo')[coluna_valor].sum().reset_index()
        
        # sequência de todas as semanas do período (freq='W-MON' garante início na segunda)
        sequencia_completa = pd.date_range(start=start_date, end=end_date, freq='W-MON').date
        df_completo = pd.DataFrame({'Tempo': sequencia_completa})
        
        df_final = pd.merge(df_completo, df_agrupado, on='Tempo', how='left').fillna(0)

    elif granularidade.lower() == 'mensal':
        df['Tempo'] = df[coluna_data].dt.to_period('M').astype(str)
        df_agrupado = df.groupby('Tempo')[coluna_valor].sum().reset_index()
        
        # sequência de todos os meses do período
        sequencia_completa = pd.date_range(start=start_date, end=end_date, freq='MS').strftime('%Y-%m')
        df_completo = pd.DataFrame({'Tempo': sequencia_completa})
        df_final = pd.merge(df_completo, df_agrupado, on='Tempo', how='left').fillna(0)
        
    else:
        raise ValueError("Granularidade inválida. Escolha entre 'diária', 'semanal' ou 'mensal'.")
        
    return df_final.sort_values(by='Tempo')

def gerar_grafico(titulo: str,
                descricao: str,
                granularidade: str, 
                dataframe: pd.DataFrame, 
                start_date: datetime = None, 
                end_date: datetime = None,
                colunas: list = None, 
                tipo_grafico: str = 'barras_empilhadas',
                coluna_data: str = 'sold_at',
                cores: dict = None):
    """
    Renderiza gráfico flexível com múltiplas opções de visualização.
    
    Parâmetros:
    -----------
    titulo : str
        Título do gráfico
    descricao : str
        Descrição do gráfico (subtítulo)
    granularidade : str
        'Diaria', 'Semanal' ou 'Mensal'
    dataframe : pd.DataFrame
        DataFrame com os dados (deve ter 'sold_at', 'total_price', 'lucro_bruto_total')
    start_date : datetime
        Data inicial do período
    end_date : datetime
        Data final do período
    colunas : list
        Lista de colunas a exibir. Ex: ['total_price'] ou ['total_price', 'lucro_bruto_total']
        Padrão: ['total_price', 'lucro_bruto_total']
    tipo_grafico : str
        Tipo de gráfico: 'barras', 'barras_empilhadas' ou 'linhas'
        Padrão: 'barras_empilhadas'
    coluna_data : str
        Nome da coluna que contém a informação temporal. Padrão: 'sold_at'
    cores : dict
        Dicionário de cores por coluna. Ex: {'total_price': '#1f77b4', 'lucro_bruto_total': '#2ca02c'}
        Padrão: cores automáticas
    """
    if dataframe.empty and start_date and end_date:
        dataframe = pd.DataFrame({coluna_data: [start_date], coluna: [0.0]})

    # Configurações padrão
    if colunas is None:
        colunas = ['total_price', 'lucro_bruto_total', 'quantity']
    elif isinstance(colunas, str):
        colunas = [colunas]
    
    if cores is None:
        cores = {
            'total_price': '#1f77b4',
            'lucro_bruto_total': '#2ca02c'
        }
    
    # Mapeamento de nomes amigáveis
    nomes_colunas = {
        'total_price': 'Receita',
        'lucro_bruto_total': 'Lucro Bruto',
        'quantity': 'Quantidade Vendida'
    }
    
    # Validar tipo de gráfico
    tipo_grafico = tipo_grafico.lower()
    if tipo_grafico not in ['barras', 'barras_empilhadas', 'linhas']:
        raise ValueError("tipo_grafico deve ser 'barras', 'barras_empilhadas' ou 'linhas'")
    
    # Tratar dataframe vazio
    if dataframe.empty and start_date and end_date:
        dataframe = pd.DataFrame({
            coluna_data: [start_date], 
            'total_price': [0.0],
            'lucro_bruto_total': [0.0],
            'quantity': [0.0]
        })
    
    # Agrupar dados para cada coluna
    dfs_agrupados = {}
    for coluna in colunas:
        df_temp = agrupar_por_granularidade(dataframe, coluna_data, coluna, granularidade, start_date, end_date)
        dfs_agrupados[coluna] = df_temp
    
    # Mesclar todos os dataframes
    df_merged = dfs_agrupados[colunas[0]][['Tempo']].copy()
    for coluna in colunas:
        df_merged = pd.merge(df_merged, dfs_agrupados[coluna], on='Tempo', how='left').fillna(0)
    
    # Criar figura Plotly
    fig = go.Figure()
    
    # Adicionar traces conforme o tipo de gráfico
    if tipo_grafico == 'linhas':
        for coluna in colunas:
            fig.add_trace(go.Scatter(
                x=df_merged['Tempo'],
                y=df_merged[coluna],
                name=nomes_colunas.get(coluna, coluna),
                mode='lines+markers',
                line=dict(color=cores.get(coluna, '#000000'), width=3),
                marker=dict(size=6),
                hovertemplate=f'<b>%{{x}}</b><br>{nomes_colunas.get(coluna, coluna)}: R$ %{{y:,.2f}}<extra></extra>'
            ))
    else:
        for coluna in colunas:
            fig.add_trace(go.Bar(
                x=df_merged['Tempo'],
                y=df_merged[coluna],
                name=nomes_colunas.get(coluna, coluna),
                marker_color=cores.get(coluna, '#000000'),
                hovertemplate=f'<b>%{{x}}</b><br>{nomes_colunas.get(coluna, coluna)}: R$ %{{y:,.2f}}<extra></extra>'
            ))
    
    # Configurar barmode
    barmode = 'stack' if tipo_grafico == 'barras_empilhadas' else 'group'
    
    st.markdown(f"""
    <div class="section-title">{titulo}</div>
    <div class="section-description">{descricao}</div>
    """, unsafe_allow_html=True)

    fig.update_layout(
        barmode=barmode,
        xaxis_title='Período',
        yaxis_title='Valor (R$)',
        template='plotly_white',
        height=400,
        hovermode='x unified',
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(
            yanchor='top',
            y=0.99,
            xanchor='left',
            x=0.01
        )
    )

    st.plotly_chart(fig, width='stretch')

def get_payment_name(code):
    names = {0: 'Crédito', 1: 'Débito', 2: 'Dinheiro', 3: 'PIX'}
    return names.get(code, 'Outros')
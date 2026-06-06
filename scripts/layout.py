from datetime import datetime, timedelta
from tracemalloc import start
from turtle import pd
from dateutil.relativedelta import relativedelta 

import streamlit as st

def periodo(title):
    col_title, col_filter = st.columns([3, 1])

    with col_title:
        st.title(title)

    with col_filter:
        st.markdown("<br>", unsafe_allow_html=True)
        periodo_selecionado = st.selectbox(
            "Selecione o período:",
            ["Diário", "Semanal", "Mensal", "Trimestral", "Semestral", "Anual", "Personalizado"],
            index=5,
            key="periodo_selectbox"  # Adicionar key para evitar duplicação
        )

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = None
    end_date = None

    if periodo_selecionado == "Diário":
        start_date = today - timedelta(days=1)
        end_date = today
    elif periodo_selecionado == "Semanal":
        start_date = today - timedelta(weeks=1)
        end_date = today
    elif periodo_selecionado == "Mensal":
        # Usando relativedelta para meses precisos
        start_date = today - relativedelta(months=1)
        end_date = today
    elif periodo_selecionado == "Trimestral":
        start_date = today - relativedelta(months=3)
        end_date = today
    elif periodo_selecionado == "Semestral":
        start_date = today - relativedelta(months=6)
        end_date = today
    elif periodo_selecionado == "Anual":
        start_date = today - relativedelta(years=1)
        end_date = today
    elif periodo_selecionado == "Personalizado":
        # Usando colunas normais em vez de sidebar
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Data Inicial", 
                value=today - timedelta(days=30),
                format="DD/MM/YYYY",
                key="start_date"
            )
        with col2:
            end_date = st.date_input(
                "Data Final", 
                value=today,
                format="DD/MM/YYYY",
                key="end_date"
            )
        
        # Validar datas
        if start_date > end_date:
            st.error("A data inicial deve ser anterior à data final!")
            # Inverter as datas ou manter como estão?
            start_date, end_date = end_date, start_date
        
        # Converter para datetime
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())
        
        # Exibir o período selecionado
        st.info(f"Período selecionado: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")

    st.markdown("---")
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    return start_date, end_date

def card_kpi(titulo, valor, icone, descricao=None):
    return f"""
    <div style="
        border:1px solid #e6e6e6;
        padding:16px;
        border-radius:12px;
        display:flex;
        align-items:center;
        gap:12px;
        background-color:#ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    ">
        <img src="{icone}" width="30">
        <div>
            <div style="font-size:15px; color:#6b7280;">
                {titulo}
            </div>
            <div style="font-size:22px; font-weight:600; color:#111827;">
                {valor}
            </div>
            <div style="font-size:14px; color:#6b7280;">
                {descricao if descricao else ''}
            </div>
        </div>
    </div>
    """

def card_estoque(nome, unidade, dias, estoque):
    return f"""
    <div class="card">
        <div class="card-title">{nome} ({unidade})</div>
        
        <div class="card-main">
            <span class="card-value">{dias}</span>
            <span class="card-unit">dias</span>
        </div>
        
        <div class="card-footer">
            Estoque: <b>{estoque}</b>
        </div>
    </div>
    """

def cards_grid(lista, n_colunas=4):
    for i in range(0, len(lista), n_colunas):
        cols = st.columns(n_colunas, gap="large")

        for j in range(n_colunas):
            with cols[j]:
                if i + j < len(lista):
                    st.markdown(
                        card_estoque(*lista[i + j]),
                        unsafe_allow_html=True
                    )
                else:
                    st.empty()

# st.markdown("""
# <style>

# .card {
#     background: white;
#     padding: 16px;
#     border-radius: 10px;
#     border: 1px solid #eee;

#     height: 120px;

#     display: flex;
#     flex-direction: column;
#     justify-content: space-between;

#     box-shadow: 0 2px 5px rgba(0,0,0,0.05);
#     transition: 0.2s;
# }

# .card:hover {
#     transform: translateY(-3px);
#     box-shadow: 0 6px 12px rgba(0,0,0,0.08);
# }

# .card-title {
#     font-size: 13px;
#     color: #6b7280;
# }

# .card-main {
#     display: flex;
#     align-items: baseline;
#     gap: 6px;
# }

# .card-value {
#     font-size: 26px;
#     font-weight: bold;
#     color: #111827;
# }

# .card-unit {
#     font-size: 12px;
#     color: #6b7280;
# }

# .card-footer {
#     font-size: 12px;
#     color: #6b7280;
# }

# </style>
# """, unsafe_allow_html=True)


# produtos = [
#     ("Arroz", "Kg", 13, 49),
#     ("Feijão", "Kg", 1, 4),
#     ("Filé de frango", "Kg", 10, 20),
#     ("Refrigerante", "Uni.", 11, 490),
#     ("Macarrão", "Kg", 5, 30),
#     ("Carne", "Kg", 8, 120),
#     ("Leite", "Uni.", 20, 100),
#     ("Suco", "Uni.", 15, 75),
# ]

# cards_grid(produtos)
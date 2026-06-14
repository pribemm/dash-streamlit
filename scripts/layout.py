from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from dateutil.relativedelta import relativedelta
import sys
import os

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from datetime import datetime, timedelta
from scripts.utils import (exibir_dataframe, 
                           formatar_moeda, 
                           formatar_percentual,
                           formatar_decimal,
                           formatar_peso)

from scripts.db import carregar_tabela

def periodo():
    periodo_selecionado = st.selectbox(
        "Selecione o período:",
        ["Diário", "Semanal", "Mensal", "Trimestral", "Semestral", "Anual", "Personalizado"],
        index=5,
        key="periodo_selectbox"
    )
    
    agora = datetime.now()
    hoje_inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Mapeamento de períodos
    periodos = {
        "Diário": lambda: (hoje_inicio, agora),
        "Semanal": lambda: (hoje_inicio - timedelta(days=(agora.weekday() + 1) % 7), agora),
        "Mensal": lambda: (agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0), agora),
        "Trimestral": lambda: (
            agora.replace(
                month=((agora.month - 1) // 3) * 3 + 1, 
                day=1, hour=0, minute=0, second=0, microsecond=0
            ), 
            agora
        ),
        "Semestral": lambda: (
            agora.replace(month=1 if agora.month <= 6 else 7, day=1, hour=0, minute=0, second=0, microsecond=0),
            agora
        ),
        "Anual": lambda: (agora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0), agora),
    }
    
    if periodo_selecionado in periodos:
        start_date, end_date = periodos[periodo_selecionado]()
        return start_date, end_date
    
    # Personalizado
    col1, col2 = st.columns(2)
    with col1:
        start_date_input = st.date_input(
            "Data Inicial", 
            value=(agora - timedelta(days=30)).date(),
            format="DD/MM/YYYY",
            key="start_date_input"
        )
    with col2:
        end_date_input = st.date_input(
            "Data Final", 
            value=agora.date(),
            format="DD/MM/YYYY",
            key="end_date_input"
        )
    
    if start_date_input > end_date_input:
        st.error("A data inicial deve ser anterior à data final!")
        return None, None
    
    start_date = datetime.combine(start_date_input, datetime.min.time())
    end_date = datetime.combine(end_date_input, datetime.max.time())
    
    return start_date, end_date

# Opção que semanal são os útimos 7 dias, mensal são os últimos 30 dias ...
# def periodo():
#     # st.markdown("<br>", unsafe_allow_html=True)
#     periodo_selecionado = st.selectbox(
#         "Selecione o período:",
#         ["Diário", "Semanal", "Mensal", "Trimestral", "Semestral", "Anual", "Personalizado"],
#         index=5,
#         key="periodo_selectbox"  # Adicionar key para evitar duplicação
#     )
    
#     today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
#     start_date = None
#     end_date = None

#     if periodo_selecionado == "Diário":
#         start_date = today 
#         end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
#     elif periodo_selecionado == "Semanal":
#         start_date = today - timedelta(weeks=1)
#         end_date = today
#     elif periodo_selecionado == "Mensal":
#         start_date = today - relativedelta(months=1)
#         end_date = today
#     elif periodo_selecionado == "Trimestral":
#         start_date = today - relativedelta(months=3)
#         end_date = today
#     elif periodo_selecionado == "Semestral":
#         start_date = today - relativedelta(months=6)
#         end_date = today
#     elif periodo_selecionado == "Anual":
#         start_date = today - relativedelta(years=1)
#         end_date = today
#     elif periodo_selecionado == "Personalizado":
#         col1, col2 = st.columns(2)
#         with col1:
#             start_date = st.date_input(
#                 "Data Inicial", 
#                 value=today - timedelta(days=30),
#                 format="DD/MM/YYYY",
#                 key="start_date"
#             )
#         with col2:
#             end_date = st.date_input(
#                 "Data Final", 
#                 value=today,
#                 format="DD/MM/YYYY",
#                 key="end_date"
#             )

#         if start_date > end_date:
#             st.error("A data inicial deve ser anterior à data final!")

#     # Converter para datetime
#     start_date = datetime.combine(start_date, datetime.min.time())
#     end_date = datetime.combine(end_date, datetime.max.time())

#     return start_date, end_date

def kpi_card(
    titulo: str,
    valor,
    sufixo: str = "",
    classe_status: str = "",
    texto_status: str = "",
    formato: str = "decimal",  # "numero", "percentual", "moeda"
    ajuda: str = None
):
    """
    Componente de KPI reutilizável

    Parâmetros:
    - titulo: nome do KPI
    - valor: valor numérico
    - sufixo: ex "%", "R$", etc
    - classe_status: classe CSS (ex: sucesso, alerta, negativo)
    - texto_status: texto abaixo do valor
    - formato: "decimal", "percentual", "moeda", "inteiro"
    - ajuda: mensagem de ajuda ao passar o mouse (opcional)
    """

    if formato == "percentual":
        valor_fmt = formatar_percentual(valor)
    elif formato == "moeda":
        if valor is None:
            valor_fmt = "—"  # ou "Sem dados"
        else:
            valor_fmt = formatar_moeda(valor)
    elif formato == "decimal":
        valor_fmt = f"{valor:.2f}"
    elif formato == "unidade":
        valor_fmt = f"{valor} un."
    else:
        valor_fmt = f"{valor}"

    # Adicionar classe de tooltip se houver ajuda
    classe_tooltip = "kpi-with-tooltip" if ajuda else ""
    atributo_tooltip = f'data-tooltip="{ajuda}"' if ajuda else ""

    with st.container(border=True):
        st.markdown(f"""
        <div class="kpi-box {classe_tooltip}" {atributo_tooltip}>
            <div class="kpi-label">{titulo}</div>
            <div class="kpi-value">{valor_fmt}{sufixo}</div>
            <div class="{classe_status}">{texto_status}</div>
        </div>
        """, unsafe_allow_html=True)

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

def rodape():
    st.markdown(f"""
    <div class="custom-footer">
        Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
    </div>
    """, unsafe_allow_html=True)

def layout():
    st.markdown("""
    <style>
        /* Fundo geral */
        .stApp {
            background-color: #f5f7fb;
        }

        /* Container principal */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
            max-width: 1450px;
        }

        /* Header padrão transparente */
        header[data-testid="stHeader"] {
            background-color: transparent;
        }

        /* Remove menu e rodapé padrão */
        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        /* Cabeçalho do dashboard */
        .dashboard-header {
            background: linear-gradient(135deg, #ffffff 0%, #eef4ff 100%);
            border: 1px solid #dbe5f5;
            border-radius: 18px;
            padding: 28px 32px;
            margin-bottom: 24px;
            box-shadow: 0 6px 18px rgba(31, 41, 55, 0.06);
        }

        .dashboard-title {
            font-size: 2rem;
            font-weight: 800;
            color: #1f2937;
            margin: 0;
            line-height: 1.2;
        }

        .dashboard-subtitle {
            font-size: 0.95rem;
            color: #6b7280;
            margin-top: 8px;
            margin-bottom: 0;
        }

        /* Subtítulos dentro dos containers */
        .section-title {
            font-size: 1.2rem;
            font-weight: 800;
            color: #1f2937;
            margin-bottom: 4px;
        }

        .section-description {
            font-size: 0.9rem;
            color: #6b7280;
            margin-bottom: 18px;
        }

        /* KPI customizado */
        .kpi-box {
            background: #ffffff;
            border-radius: 14px;
            padding: 8px 4px 4px 4px;
        }

        .kpi-label {
            font-size: 0.85rem;
            color: #6b7280;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .kpi-value {
            font-size: 1.8rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 4px;
        }

        .kpi-positive {
            color: #059669;
            font-size: 0.9rem;
            font-weight: 700;
        }

        .kpi-negative {
            color: #dc2626;
            font-size: 0.9rem;
            font-weight: 700;
        }

        /* Tooltip para KPI */
        .kpi-with-tooltip {
            position: relative;
            cursor: help;
            border-bottom: 1px dotted #6b7280;
        }

        .kpi-with-tooltip::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background-color: #1f2937;
            color: #ffffff;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.85rem;
            white-space: nowrap;
            z-index: 1000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .kpi-with-tooltip::before {
            content: '';
            position: absolute;
            bottom: 115%;
            left: 50%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: #1f2937;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
            z-index: 1000;
        }

        .kpi-with-tooltip:hover::after,
        .kpi-with-tooltip:hover::before {
            opacity: 1;
        }

        .kpi-neutral {
            color: #2563eb;
            font-size: 0.9rem;
            font-weight: 700;
        }
        [data-testid="stDataFrame"] {
            border-radius: 12px;
            overflow: hidden;
        }

        /* Espaçamento dos containers com borda */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff;
            border-radius: 16px;
            box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
        }

        /* Linha divisória discreta */
        .soft-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #d1d5db, transparent);
            margin: 28px 0;
        }

        /* Rodapé customizado */
        .custom-footer {
            text-align: center;
            color: #6b7280;
            font-size: 0.85rem;
            margin-top: 26px;
            padding-top: 12px;
        }
    </style>
    """, unsafe_allow_html=True)

def cabecalho(title, subtitle):
    st.markdown(f"""
    <div class="dashboard-header">
        <p class="dashboard-title">📊 {title}</p>
        <p class="dashboard-subtitle">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)

def divisor():
    st.markdown("""
    <div class="soft-divider"></div>
    """, unsafe_allow_html=True)

def secao_container(
    titulo: str,
    descricao: str = "",
    conteudo=None,
    altura_tabela: int = 250,
    mensagem_vazio: str = "Nenhum dado disponível.",
    icone: str = "📊"
):
    """
    Componente de seção padronizada

    Parâmetros:
    - titulo: título da seção
    - descricao: texto descritivo
    - conteudo: dataframe ou qualquer render
    - altura_tabela: altura da tabela
    - mensagem_vazio: fallback
    - icone: emoji opcional
    """

    with st.container(border=True):
        st.markdown(f"""
        <div class="section-title">{icone} {titulo}</div>
        <div class="section-description">{descricao}</div>
        """, unsafe_allow_html=True)

        if conteudo is None:
            st.info(mensagem_vazio)

        elif hasattr(conteudo, "empty"):
            if not conteudo.empty:
                exibir_dataframe(conteudo, altura=altura_tabela)
            else:
                st.info(mensagem_vazio)

        else:
            conteudo()

def estilo_grafico_barras():
    st.markdown("""
    <style>
    .bar-row {
        display: flex;
        align-items: center;
        margin-bottom: 14px;
    }
    .bar-label {
        width: 180px;
        font-size: 13px;
        color: #333;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .bar-container {
        flex: 1;
        background-color: #e5e7eb;
        border-radius: 20px;
        height: 22px;
        margin: 0 12px;
        overflow: hidden;
    }
    .bar-fill {
        background-color: #111;
        height: 100%;
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 10px;
        color: white;
        font-size: 11px;
        font-weight: 600;
        min-width: 30px;
    }
    .bar-value {
        width: 90px;
        text-align: right;
        font-size: 12px;
        color: #555;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)


# def secao_ranking_barras(
#     df: pd.DataFrame,
#     col_nome: str,
#     col_valor: str,
#     titulo: str = "Ranking",
#     descricao: str = "",
#     top_n: int = 5,
#     tipo_valor: str = "moeda",
#     mensagem_vazio: str = "Nenhum dado disponível.",
# ):
#     """
#     Componente de ranking com barras horizontais

#     Parâmetros:
#     - df: dataframe base
#     - col_nome: coluna exibida à esquerda (label)
#     - col_valor: coluna usada para tamanho da barra
#     - titulo: título da seção
#     - descricao: descrição
#     - top_n: quantidade de itens
#     - prefixo_valor: prefixo monetário (apenas para tipo_valor='moeda')
#     - tipo_valor: formata os valores como 'moeda', 'percentual', 'peso' ou 'unidade'
#     - mensagem_vazio: mensagem de fallback
#     """

#     with st.container(border=True):

#         st.markdown(f"""
#         <div class="section-title">{titulo}</div>
#         <div class="section-description">{descricao}</div>
#         """, unsafe_allow_html=True)
        
#         st.markdown("""
#         <style>
#         .bar-row {
#             display: flex;
#             align-items: center;
#             margin-bottom: 14px;
#         }
#         .bar-label {
#             width: 350px;
#             font-size: 13px;
#             color: #333;
#             white-space: normal;
#             word-break: break-word;
#             overflow: hidden;
#             text-overflow: ellipsis;
#         }
#         .bar-container {
#             flex: 1;
#             background-color: #e5e7eb;
#             border-radius: 20px;
#             min-height: 28px;
#             height: auto;
#             margin: 0 12px;
#             overflow: hidden;
#         }
#         .bar-fill {
#             background-color: #111;
#             height: auto;
#             border-radius: 20px;
#             display: flex;
#             align-items: center;
#             justify-content: flex-end;
#             padding-right: 10px;
#             padding: 4px 10px;
#             color: white;
#             font-size: 11px;
#             font-weight: 600;
#             white-space: normal;
#             word-break: break-word;
#             min-width: fit-content;
#         }
#         .bar-value {
#             width: 100px;
#             text-align: right;
#             font-size: 12px;
#             color: #555;
#             white-space: nowrap;
#         }
#         </style>
#         """, unsafe_allow_html=True)

#         if df is None or df.empty:
#             st.info(mensagem_vazio)
#             return

#         df_plot = df.copy()

#         # garantir numérico
#         df_plot[col_valor] = pd.to_numeric(df_plot[col_valor], errors='coerce').fillna(0)
        
#         # ordenar + top N
#         df_plot = df_plot.sort_values(by=col_valor, ascending=False).head(top_n)

#         max_valor = df_plot[col_valor].max()

#         def formatar_valor(valor, tipo: str):
#             if tipo == "percentual":
#                 return formatar_percentual(valor)
#             if tipo == "peso":
#                 return f"{valor:,.2f} kg".replace(".", ",")
#             if tipo == "unidade":
#                 return f"{int(valor)} un."
#             return formatar_moeda(valor)

#         for _, row in df_plot.iterrows():

#             nome = row[col_nome]
#             valor = row[col_valor]
           
#             percentual = (valor / max_valor * 100) if max_valor > 0 else 0
#             valor_formatado = formatar_valor(valor, tipo_valor)
#             texto_barra_formatado = formatar_valor(texto_barra, tipo_texto_barra) if col_texto_barra is not None else " "

#             st.markdown(f"""
#             <div class="bar-row">
#                 <div class="bar-label">{nome}</div>
#                 <div class="bar-container">
#                     <div class="bar-fill" style="width: {percentual:.2f}%;">
#                         {texto_barra_formatado}
#                     </div>
#                 </div>
#                 <div class="bar-value">{valor_formatado}</div>
#             </div>
#             """, unsafe_allow_html=True)

def secao_ranking_barras(
    df: pd.DataFrame,
    col_nome: str,
    col_valor: str,
    titulo: str = "Ranking",
    descricao: str = "",
    top_n: int = 5,
    tipo_valor: str = "moeda",
    largura_maxima_label: int = 200,
    mensagem_vazio: str = "Nenhum dado disponível.",
):
    with st.container(border=True):
        
        # Preparar dados
        df_plot = df.copy()
        df_plot[col_valor] = pd.to_numeric(df_plot[col_valor], errors='coerce').fillna(0)
        df_plot = df_plot.sort_values(by=col_valor, ascending=False).head(top_n)
        max_valor = df_plot[col_valor].max() if not df_plot.empty else 1
        
        # Calcular largura ideal baseada no texto
        if not df_plot.empty:
            max_text_len = df_plot[col_nome].astype(str).map(len).max()
            # ~7-8 pixels por caractere para fonte 13px
            ideal_width = min(max_text_len * 8, largura_maxima_label)
            ideal_width = max(ideal_width, 100)  # mínimo 100px
        else:
            ideal_width = 200
        
        st.markdown(f"""
         <div class="section-title">{titulo}</div>
         <div class="section-description">{descricao}</div>
         """, unsafe_allow_html=True)
        
        # CSS dinâmico
        st.markdown(f"""
        <style>
        .bar-row {{
            display: flex;
            align-items: center;
            margin-bottom: 14px;
            gap: 12px;
        }}
        .bar-label {{
            width: {ideal_width}px;
            font-size: 13px;
            color: #333;
            white-space: normal;
            word-break: break-word;
            line-height: 1.3;
        }}
        .bar-container {{
            flex: 1;
            background-color: #e5e7eb;
            border-radius: 20px;
            min-height: 32px;
            overflow: hidden;
        }}
        .bar-fill {{
            background-color: #111;
            height: 32px;
            border-radius: 20px;
            min-width: 8px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
        }}
        .bar-value {{
            width: 100px;
            text-align: right;
            font-size: 12px;
            color: #555;
            white-space: nowrap;
            font-weight: 500;
        }}
        </style>
        """, unsafe_allow_html=True)

        if df is None or df.empty:
            st.info(mensagem_vazio)
            return

        df_plot = df.copy()

        # garantir numérico
        df_plot[col_valor] = pd.to_numeric(df_plot[col_valor], errors='coerce').fillna(0)

        # ordenar + top N
        df_plot = df_plot.sort_values(by=col_valor, ascending=False).head(top_n)

        max_valor = df_plot[col_valor].max()

        def formatar_valor(valor, tipo: str):
            if tipo == "percentual":
                return formatar_percentual(valor)
            if tipo == "peso":
                return formatar_peso(valor)
            if tipo == "unidade":
                return f"{int(valor)} un."
            if tipo == "decimal":
                return formatar_decimal(valor)
            if tipo == "moeda":
                return formatar_moeda(valor)
            else:
                return valor


        for _, row in df_plot.iterrows():

            nome = row[col_nome]
            valor = row[col_valor]

            percentual = (valor / max_valor * 100) if max_valor > 0 else 0
            valor_formatado = formatar_valor(valor, tipo_valor)

            st.markdown(f"""
            <div class="bar-row">
                <div class="bar-label">{nome}</div>
                <div class="bar-container">
                    <div class="bar-fill" style="width: {percentual:.2f}%;"></div>
                </div>
                <div class="bar-value">{valor_formatado}</div>
            </div>
            """, unsafe_allow_html=True)


def render_cards_cobertura(df: pd.DataFrame, n: int = 8) -> None:
    """
    Renderiza cards dos N insumos com menor cobertura (mais próximos de acabar).

    Parâmetros
    ----------
    df : DataFrame retornado por get_giro_estoque_insumos()
         Colunas necessárias: Insumo, Unidade, Cobertura, Estoque Atual
    n  : quantidade máxima de cards exibidos (padrão: 8)
    """

    def _parse_cobertura(val: str) -> int:
        val = str(val)
        if "999" in val:
            return 999
        try:
            return int(val.replace(" dias", "").strip())
        except ValueError:
            return 999

    df_temp = df.copy()
    df_temp["_dias"] = df_temp["Cobertura"].apply(_parse_cobertura)

    # Apenas cobertura positiva e definida, do menor para o maior
    menores = (
        df_temp[(df_temp["_dias"] > 0) & (df_temp["_dias"] < 999)]
        .sort_values("_dias")
        .head(n)
    )

    if menores.empty:
        st.info("Nenhum insumo com cobertura positiva no período.")
        return

    def _card_html(titulo: str, dias: int, estoque: str, nivel: str) -> str:
        """
        Retorna HTML do card com estilos 100% inline.
        Não depende de CSS externo — funciona em qualquer contexto do Streamlit.
        """
        estilos = {
            "critico": {
                "border": "2px solid #E24B4A",
                "badge_bg": "#FCEBEB",
                "badge_color": "#A32D2D",
                "badge_texto": "⚠ Crítico",
            },
            "atencao": {
                "border": "2px solid #EF9F27",
                "badge_bg": "#FAEEDA",
                "badge_color": "#854F0B",
                "badge_texto": "Atenção",
            },
            "normal": {
                "border": "1px solid #e0e0e0",
            },
        }

        e = estilos[nivel]
        badge = ""
        if nivel != "normal":
            badge = (
                f'<div style="margin-bottom:6px;">'
                f'<span style="display:inline-block;font-size:11px;font-weight:500;'
                f'padding:2px 8px;border-radius:4px;'
                f'background:{e["badge_bg"]};color:{e["badge_color"]};">'
                f'{e["badge_texto"]}</span></div>'
            )

        return (
            f'<div style="border:{e["border"]};border-radius:12px;padding:14px 16px;">'
            f'{badge}'
            f'<p style="font-size:12px;color:#888;margin:0 0 4px 0;">{titulo}</p>'
            f'<p style="font-size:34px;font-weight:700;color:#111;line-height:1.1;margin:0;">'
            f'{dias}<span style="font-size:20px;font-weight:400;color:#888;"> d</span></p>'
            f'<p style="font-size:12px;color:#888;margin:8px 0 0 0;">Estoque: {estoque}</p>'
            f'</div>'
        )

    # Grid com st.columns — 4 cards por linha
    cols_por_linha = 4
    linhas = [
        menores.iloc[i : i + cols_por_linha]
        for i in range(0, len(menores), cols_por_linha)
    ]

    for linha_df in linhas:
        cols = st.columns(cols_por_linha)
        for col, (_, row) in zip(cols, linha_df.iterrows()):
            dias = int(row["_dias"])
            unidade = row.get("Unidade", "")
            titulo = f"{row['Insumo']} ({unidade})" if unidade else row["Insumo"]
            estoque = row["Estoque Atual"]

            if dias <= 7:
                nivel = "critico"
            elif dias <= 15:
                nivel = "atencao"
            else:
                nivel = "normal"

            with col:
                # st.html() é o método correto para HTML em Streamlit >= 1.36
                # Não sofre com o escaping do st.markdown em contextos de colunas
                st.html(_card_html(titulo, dias, estoque, nivel))

def get_alertas_estoque() -> pd.DataFrame:
    """
    Retorna insumos com menor cobertura baseada no estoque ATUAL.
    Independente do período selecionado no dashboard.
    """
    ingredients  = carregar_tabela("ingredients")
    recipes      = carregar_tabela("recipes")
    recipe_items = carregar_tabela("recipe_items")
    sales        = carregar_tabela("sales")
    sale_items   = carregar_tabela("sale_items")

    # Consumo sempre nos últimos 30 dias (referência fixa)
    end_date   = pd.Timestamp.now().normalize()
    start_date = end_date - pd.Timedelta(days=29)

    sales["sold_at"] = pd.to_datetime(sales["sold_at"], utc=True).dt.tz_convert(None)
    if "status" in sales.columns:
        sales = sales[sales["status"] == 0]

    sales_30d = sales[(sales["sold_at"] >= start_date) & (sales["sold_at"] <= end_date)]

    sale_items = sale_items.rename(columns={"quantity": "qty_sold"})
    df = pd.merge(
        sale_items[["sale_id", "product_id", "qty_sold"]],
        sales_30d[["id"]],
        left_on="sale_id", right_on="id", how="inner"
    ).drop(columns=["id"])

    recipes = recipes.rename(columns={"id": "recipe_id"})
    if "active" in recipes.columns:
        recipes = recipes[recipes["active"] == True]

    df = pd.merge(df, recipes[["recipe_id", "product_id"]], on="product_id", how="inner")

    recipe_items = recipe_items.rename(columns={"quantity": "qty_recipe"})
    df = pd.merge(df, recipe_items[["recipe_id", "ingredient_id", "qty_recipe"]],
                  on="recipe_id", how="inner")

    df["consumo"] = df["qty_sold"] * df["qty_recipe"]
    consumo = df.groupby("ingredient_id", as_index=False)["consumo"].sum()
    consumo["consumo_diario"] = consumo["consumo"] / 30

    # Estoque ATUAL: sempre current_stock, nunca calculado pelo período
    if "active" in ingredients.columns:
        ingredients = ingredients[ingredients["active"] == True]

    resultado = pd.merge(
        consumo,
        ingredients[["id", "name", "unit", "current_stock"]].rename(
            columns={"id": "ingredient_id"}
        ),
        on="ingredient_id", how="left"
    )

    resultado["Cobertura"] = resultado.apply(
        lambda r: int(r["current_stock"] / r["consumo_diario"])
        if r["consumo_diario"] > 0 else 999,
        axis=1
    )

    return resultado.rename(columns={
        "name": "Insumo",
        "unit": "Unidade",
        "current_stock": "Estoque Atual",
    })[["Insumo", "Unidade", "Estoque Atual", "Cobertura"]]
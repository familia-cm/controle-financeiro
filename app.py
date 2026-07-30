import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Controle Financeiro Familiar",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .alert-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .alert-danger {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .alert-success {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Dados do planejamento
ENTRADA_MENSAL = 11600.00

# Cronograma de mudanças por mês
CRONOGRAMA = {
    1: {"gilson": 400, "marketing": 300, "edson": 200, "dep01": 427, "dep02": 200},
    2: {"gilson": 400, "marketing": 300, "edson": 200, "dep01": 427, "dep02": 200},
    3: {"gilson": 400, "marketing": 300, "edson": 200, "dep01": 427, "dep02": 200},
    4: {"gilson": 400, "marketing": 300, "edson": 200, "dep01": 427, "dep02": 200},
    5: {"gilson": 400, "marketing": 300, "edson": 200, "dep01": 427, "dep02": 200},
    6: {"gilson": 400, "marketing": 300, "edson": 200, "dep01": 0, "dep02": 200},
    7: {"gilson": 0, "marketing": 300, "edson": 200, "dep01": 0, "dep02": 792},
    8: {"gilson": 0, "marketing": 300, "edson": 200, "dep01": 0, "dep02": 792},
    9: {"gilson": 0, "marketing": 300, "edson": 200, "dep01": 0, "dep02": 792},
    10: {"gilson": 0, "marketing": 300, "edson": 200, "dep01": 0, "dep02": 792},
    11: {"gilson": 0, "marketing": 0, "edson": 0, "dep01": 0, "dep02": 296},
    12: {"gilson": 0, "marketing": 0, "edson": 0, "dep01": 0, "dep02": 0},
}

DESPESAS_FIXAS_BASE = {
    "Dízimo": {"valor": lambda mes: ENTRADA_MENSAL * 0.10, "categoria": "Fixa"},
    "Carro": {"valor": 2332, "categoria": "Fixa"},
    "Água": {"valor": 150, "categoria": "Fixa"},
    "Luz": {"valor": 300, "categoria": "Fixa"},
    "Curso Victor": {"valor": 200, "categoria": "Fixa"},
    "Ginástica Sofia": {"valor": 295, "categoria": "Fixa"},
    "Academia": {"valor": 160, "categoria": "Fixa"},
    "Internet": {"valor": 200, "categoria": "Fixa"},
    "Celular": {"valor": 100, "categoria": "Fixa"},
    "Terapia Day": {"valor": 120, "categoria": "Fixa"},
    "Plano Dentário": {"valor": 108, "categoria": "Fixa"},
    "Depósito Material 01": {"valor": lambda mes: CRONOGRAMA[mes]["dep01"], "categoria": "Fixa"},
    "Depósito Material 02": {"valor": lambda mes: CRONOGRAMA[mes]["dep02"], "categoria": "Fixa"},
    "Farmácia": {"valor": 250, "categoria": "Fixa"},
    "Apartamento": {"valor": 1500, "categoria": "Fixa"},
    "Taxa MEI": {"valor": 180, "categoria": "Fixa"},
    "Gilson": {"valor": lambda mes: CRONOGRAMA[mes]["gilson"], "categoria": "Fixa"},
    "Cursos Marketing": {"valor": lambda mes: CRONOGRAMA[mes]["marketing"], "categoria": "Fixa"},
}

DESPESAS_VARIAVEIS_BASE = {
    "Mercado": {"valor": 1000, "categoria": "Variável"},
    "Mistura": {"valor": 580, "categoria": "Variável"},
    "Feira": {"valor": 200, "categoria": "Variável"},
    "Lazer Família": {"valor": 200, "categoria": "Variável"},
    "Edson": {"valor": lambda mes: CRONOGRAMA[mes]["edson"], "categoria": "Variável"},
    "Estética": {"valor": 200, "categoria": "Variável"},
}

DESPESAS_INVISIVEIS_BASE = {
    "Café da Manhã": {"valor": 400, "categoria": "Invisível"},
    "Spotify + YouTube": {"valor": 80, "categoria": "Invisível"},
    "Despesas Extras": {"valor": 200, "categoria": "Invisível"},
}

# Funções auxiliares
def calcular_orcamento_mes(mes):
    """Calcula o orçamento planejado para um mês específico"""
    orcamento = {}
    
    for nome, config in {**DESPESAS_FIXAS_BASE, **DESPESAS_VARIAVEIS_BASE, **DESPESAS_INVISIVEIS_BASE}.items():
        if callable(config["valor"]):
            orcamento[nome] = {"valor": config["valor"](mes), "categoria": config["categoria"]}
        else:
            orcamento[nome] = {"valor": config["valor"], "categoria": config["categoria"]}
    
    return orcamento

def calcular_total_categoria(orcamento, categoria):
    """Calcula o total de uma categoria"""
    return sum(v["valor"] for v in orcamento.values() if v["categoria"] == categoria)

def inicializar_dados():
    """Inicializa os dados no session state"""
    if "transacoes" not in st.session_state:
        st.session_state.transacoes = []
    if "mes_atual" not in st.session_state:
        st.session_state.mes_atual = datetime.now().month
    if "ano_atual" not in st.session_state:
        st.session_state.ano_atual = datetime.now().year

def salvar_transacao(data, categoria, subcategoria, valor, tipo, descricao=""):
    """Salva uma nova transação"""
    transacao = {
        "data": data.strftime("%Y-%m-%d"),
        "categoria": categoria,
        "subcategoria": subcategoria,
        "valor": float(valor),
        "tipo": tipo,
        "descricao": descricao,
        "timestamp": datetime.now().isoformat()
    }
    st.session_state.transacoes.append(transacao)

def get_transacoes_mes(mes, ano):
    """Retorna transações de um mês específico"""
    if not st.session_state.transacoes:
        return pd.DataFrame()
    
    df = pd.DataFrame(st.session_state.transacoes)
    df["data"] = pd.to_datetime(df["data"])
    df_filtrado = df[(df["data"].dt.month == mes) & (df["data"].dt.year == ano)]
    return df_filtrado

def calcular_gasto_real(mes, ano, subcategoria):
    """Calcula quanto já foi gasto em uma subcategoria no mês"""
    df = get_transacoes_mes(mes, ano)
    if df.empty:
        return 0
    
    gasto = df[(df["subcategoria"] == subcategoria) & (df["tipo"] == "Saída")]["valor"].sum()
    return float(gasto)

def calcular_entrada_real(mes, ano):
    """Calcula entradas reais do mês"""
    df = get_transacoes_mes(mes, ano)
    if df.empty:
        return 0
    return float(df[df["tipo"] == "Entrada"]["valor"].sum())

def calcular_reserva_acumulada():
    """Calcula a reserva acumulada até o momento"""
    if not st.session_state.transacoes:
        return 0
    
    df = pd.DataFrame(st.session_state.transacoes)
    entradas = df[df["tipo"] == "Entrada"]["valor"].sum()
    saidas = df[df["tipo"] == "Saída"]["valor"].sum()
    return float(entradas - saidas)

def exportar_dados():
    """Exporta dados para Excel"""
    if not st.session_state.transacoes:
        return None
    
    output = BytesIO()
    
    df = pd.DataFrame(st.session_state.transacoes)
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values("data", ascending=False)
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Transações', index=False)
        
        # Resumo mensal
        resumo = df.groupby([df["data"].dt.month, "tipo"])["valor"].sum().unstack(fill_value=0)
        resumo.to_excel(writer, sheet_name='Resumo Mensal')
    
    output.seek(0)
    return output

def get_mes_planejamento(mes_calendario):
    """Converte mês do calendário para mês do planejamento (1-12)"""
    # Assumindo que janeiro é o mês 1 do planejamento
    return mes_calendario

# Inicializar dados
inicializar_dados()

# Sidebar
with st.sidebar:
    st.title("💰 Controle Financeiro")
    st.markdown("---")
    
    pagina = st.radio(
        "Navegação",
        ["📊 Dashboard", "➕ Nova Transação", "📈 Relatórios", "📅 Cronograma 12 Meses", "⚙️ Configurações"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Seletor de mês/ano
    col1, col2 = st.columns(2)
    with col1:
        mes_selecionado = st.selectbox(
            "Mês",
            range(1, 13),
            index=st.session_state.mes_atual - 1,
            format_func=lambda x: [
                "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                "Jul", "Ago", "Set", "Out", "Nov", "Dez"
            ][x-1]
        )
    with col2:
        ano_selecionado = st.selectbox(
            "Ano",
            [2024, 2025, 2026],
            index=0
        )
    
    st.markdown("---")
    st.markdown("### 📥 Dados")
    
    if st.button("💾 Backup"):
        dados_json = json.dumps(st.session_state.transacoes, indent=2)
        st.download_button(
            "⬇️ Baixar Backup (JSON)",
            dados_json,
            "backup_financeiro.json",
            "application/json"
        )
    
    arquivo_excel = exportar_dados()
    if arquivo_excel:
        st.download_button(
            "📊 Exportar Excel",
            arquivo_excel,
            "relatorio_financeiro.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# PÁGINA: DASHBOARD
if pagina == "📊 Dashboard":
    st.title("📊 Dashboard Financeiro")
    
    mes_plan = get_mes_planejamento(mes_selecionado)
    orcamento_mes = calcular_orcamento_mes(mes_plan)
    
    # Cards principais
    col1, col2, col3, col4 = st.columns(4)
    
    total_planejado = sum(v["valor"] for v in orcamento_mes.values())
    sobra_planejada = ENTRADA_MENSAL - total_planejado
    
    entrada_real = calcular_entrada_real(mes_selecionado, ano_selecionado)
    total_gasto = sum(calcular_gasto_real(mes_selecionado, ano_selecionado, sub) 
                     for sub in orcamento_mes.keys())
    saldo_real = entrada_real - total_gasto
    
    with col1:
        st.metric("💵 Entrada Planejada", f"R$ {ENTRADA_MENSAL:,.2f}")
        if entrada_real > 0:
            st.metric("💵 Entrada Real", f"R$ {entrada_real:,.2f}")
    
    with col2:
        st.metric("💸 Gastos Planejados", f"R$ {total_planejado:,.2f}")
        st.metric("💸 Gastos Reais", f"R$ {total_gasto:,.2f}")
    
    with col3:
        st.metric("💰 Sobra Planejada", f"R$ {sobra_planejada:,.2f}")
        delta_sobra = saldo_real - sobra_planejada if entrada_real > 0 else 0
        st.metric(
            "💰 Saldo Real", 
            f"R$ {saldo_real:,.2f}",
            delta=f"R$ {delta_sobra:,.2f}" if entrada_real > 0 else None,
            delta_color="normal" if delta_sobra >= 0 else "inverse"
        )
    
    with col4:
        reserva = calcular_reserva_acumulada()
        st.metric("🏦 Reserva Acumulada", f"R$ {reserva:,.2f}")
        meta_reserva = 22000
        progresso = (reserva / meta_reserva) * 100
        st.progress(min(progresso / 100, 1.0))
        st.caption(f"{progresso:.1f}% da meta (R$ 22.000)")
    
    st.markdown("---")
    
    # Gastos por categoria
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Despesas por Categoria")
        
        categorias = ["Fixa", "Variável", "Invisível"]
        dados_categorias = []
        
        for cat in categorias:
            planejado = calcular_total_categoria(orcamento_mes, cat)
            real = sum(calcular_gasto_real(mes_selecionado, ano_selecionado, sub) 
                      for sub, config in orcamento_mes.items() if config["categoria"] == cat)
            dados_categorias.append({
                "Categoria": cat,
                "Planejado": planejado,
                "Real": real
            })
        
        df_cat = pd.DataFrame(dados_categorias)
        
        fig = go.Figure(data=[
            go.Bar(name='Planejado', x=df_cat['Categoria'], y=df_cat['Planejado'], marker_color='lightblue'),
            go.Bar(name='Real', x=df_cat['Categoria'], y=df_cat['Real'], marker_color='darkblue')
        ])
        fig.update_layout(barmode='group', height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Status das Subcategorias")
        
        dados_status = []
        for sub, config in orcamento_mes.items():
            if config["valor"] == 0:
                continue
            
            planejado = config["valor"]
            real = calcular_gasto_real(mes_selecionado, ano_selecionado, sub)
            percentual = (real / planejado * 100) if planejado > 0 else 0
            
            status = "🟢"
            if percentual >= 100:
                status = "🔴"
            elif percentual >= 80:
                status = "🟡"
            
            dados_status.append({
                "Status": status,
                "Item": sub,
                "Real": f"R$ {real:.2f}",
                "Planejado": f"R$ {planejado:.2f}",
                "%": f"{percentual:.0f}%"
            })
        
        df_status = pd.DataFrame(dados_status).sort_values("Status")
        st.dataframe(df_status, hide_index=True, use_container_width=True, height=300)
    
    st.markdown("---")
    
    # Alertas
    st.subheader("⚠️ Alertas")
    
    alertas = []
    for sub, config in orcamento_mes.items():
        if config["valor"] == 0:
            continue
        
        planejado = config["valor"]
        real = calcular_gasto_real(mes_selecionado, ano_selecionado, sub)
        percentual = (real / planejado * 100) if planejado > 0 else 0
        
        if percentual >= 100:
            alertas.append(("danger", f"🔴 **{sub}**: ultrapassou o limite! (R$ {real:.2f} de R$ {planejado:.2f})"))
        elif percentual >= 80:
            alertas.append(("warning", f"🟡 **{sub}**: chegou a {percentual:.0f}% do limite (R$ {real:.2f} de R$ {planejado:.2f})"))
    
    if alertas:
        for tipo, msg in alertas:
            if tipo == "danger":
                st.markdown(f'<div class="alert-danger">{msg}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-warning">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-success">✅ Tudo dentro do planejado!</div>', unsafe_allow_html=True)

# PÁGINA: NOVA TRANSAÇÃO
elif pagina == "➕ Nova Transação":
    st.title("➕ Registrar Nova Transação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
        data_transacao = st.date_input("Data", value=date.today())
    
    with col2:
        mes_plan = get_mes_planejamento(data_transacao.month)
        orcamento_mes = calcular_orcamento_mes(mes_plan)
        
        if tipo == "Saída":
            categoria = st.selectbox(
                "Categoria",
                ["Fixa", "Variável", "Invisível"]
            )
            
            subcategorias_disponiveis = [
                nome for nome, config in orcamento_mes.items() 
                if config["categoria"] == categoria
            ]
            subcategoria = st.selectbox("Subcategoria", subcategorias_disponiveis)
        else:
            categoria = "Entrada"
            subcategoria = st.text_input("Descrição da Entrada", "Salário")
    
    valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01, format="%.2f")
    descricao = st.text_area("Observações (opcional)")
    
    if st.button("💾 Salvar Transação", type="primary"):
        salvar_transacao(data_transacao, categoria, subcategoria, valor, tipo, descricao)
        st.success(f"✅ Transação de {tipo} registrada: {subcategoria} - R$ {valor:.2f}")
        st.balloons()

# PÁGINA: RELATÓRIOS
elif pagina == "📈 Relatórios":
    st.title("📈 Relatórios e Análises")
    
    if not st.session_state.transacoes:
        st.info("Nenhuma transação registrada ainda.")
    else:
        df = pd.DataFrame(st.session_state.transacoes)
        df["data"] = pd.to_datetime(df["data"])
        df = df.sort_values("data", ascending=False)
        
        st.subheader("📋 Todas as Transações")
        st.dataframe(
            df[["data", "tipo", "categoria", "subcategoria", "valor", "descricao"]],
            hide_index=True,
            use_container_width=True,
            column_config={
                "data": "Data",
                "tipo": "Tipo",
                "categoria": "Categoria",
                "subcategoria": "Item",
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "descricao": "Observações"
            }
        )
        
        st.markdown("---")
        
        # Gráfico de evolução mensal
        st.subheader("📊 Evolução Mensal")
        
        df["mes_ano"] = df["data"].dt.to_period("M").astype(str)
        evolucao = df.groupby(["mes_ano", "tipo"])["valor"].sum().unstack(fill_value=0)
        
        fig = go.Figure()
        if "Entrada" in evolucao.columns:
            fig.add_trace(go.Scatter(
                x=evolucao.index, 
                y=evolucao["Entrada"],
                name="Entradas",
                line=dict(color='green', width=3)
            ))
        if "Saída" in evolucao.columns:
            fig.add_trace(go.Scatter(
                x=evolucao.index, 
                y=evolucao["Saída"],
                name="Saídas",
                line=dict(color='red', width=3)
            ))
        
        fig.update_layout(height=400, xaxis_title="Mês", yaxis_title="Valor (R$)")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Top gastos
        st.subheader("🔝 Maiores Gastos")
        
        gastos = df[df["tipo"] == "Saída"].groupby("subcategoria")["valor"].sum().sort_values(ascending=False).head(10)
        
        fig = px.bar(
            x=gastos.values,
            y=gastos.index,
            orientation='h',
            labels={'x': 'Valor (R$)', 'y': 'Categoria'},
            color=gastos.values,
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# PÁGINA: CRONOGRAMA 12 MESES
elif pagina == "📅 Cronograma 12 Meses":
    st.title("📅 Planejamento de 12 Meses")
    
    st.markdown("""
    Este é o planejamento completo do seu orçamento para os próximos 12 meses, 
    incluindo quitação de dívidas e construção de reserva.
    """)
    
    st.markdown("---")
    
    # Tabela do cronograma
    dados_cronograma = []
    reserva_acum = 0
    
    for mes in range(1, 13):
        orcamento = calcular_orcamento_mes(mes)
        total_gastos = sum(v["valor"] for v in orcamento.values())
        sobra = ENTRADA_MENSAL - total_gastos
        reserva_acum += sobra
        
        dados_cronograma.append({
            "Mês": mes,
            "Carro": f"R$ {orcamento['Carro']['valor']:.2f}",
            "Dep. 01": f"R$ {orcamento['Depósito Material 01']['valor']:.2f}",
            "Dep. 02": f"R$ {orcamento['Depósito Material 02']['valor']:.2f}",
            "Gilson": f"R$ {orcamento['Gilson']['valor']:.2f}",
            "Marketing": f"R$ {orcamento['Cursos Marketing']['valor']:.2f}",
            "Edson": f"R$ {orcamento['Edson']['valor']:.2f}",
            "Total Gastos": f"R$ {total_gastos:.2f}",
            "Sobra": f"R$ {sobra:.2f}",
            "Reserva Acum.": f"R$ {reserva_acum:.2f}"
        })
    
    df_crono = pd.DataFrame(dados_cronograma)
    
    st.dataframe(
        df_crono,
        hide_index=True,
        use_container_width=True,
        height=500
    )
    
    st.markdown("---")
    
    # Marcos importantes
    st.subheader("🎯 Marcos Importantes")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="alert-success">✅ <b>Mês 6</b><br>Depósito 01 quitado<br>R$ 2.135 eliminados</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="alert-success">✅ <b>Mês 7</b><br>Gilson liberado<br>+R$ 400/mês disponível</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="alert-success">✅ <b>Mês 11</b><br>Marketing + Edson liberados<br>+R$ 500/mês disponível</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="alert-success">✅ <b>Mês 12</b><br>TODAS AS DÍVIDAS QUITADAS<br>Sobra permanente: R$ 1.592/mês</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráfico de evolução
    st.subheader("📈 Evolução da Reserva")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, 13)),
        y=[float(row["Reserva Acum."].replace("R$ ", "").replace(",", "")) for _, row in df_crono.iterrows()],
        mode='lines+markers',
        name='Reserva',
        line=dict(color='green', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        height=400,
        xaxis_title="Mês",
        yaxis_title="Reserva Acumulada (R$)",
        hovermode='x'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Resultado em 12 meses
    st.subheader("🏆 Resultado em 12 Meses")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💸 Dívidas Quitadas", "R$ 5.135,00")
        st.caption("Depósito 01 + Depósito 02")
    
    with col2:
        st.metric("🏦 Reserva Acumulada", "R$ 7.905,00")
        st.caption("36% da meta de 3 meses")
    
    with col3:
        st.metric("💰 Nova Sobra Mensal", "R$ 1.592,00")
        st.caption("+336% vs início (era R$ 365)")

# PÁGINA: CONFIGURAÇÕES
elif pagina == "⚙️ Configurações":
    st.title("⚙️ Configurações")
    
    st.subheader("📋 Orçamento Base")
    
    st.markdown(f"""
    **Entrada Mensal:** R$ {ENTRADA_MENSAL:,.2f}
    
    **Despesas Fixas Base:** R$ 7.975,00
    - Dízimo: R$ 1.160,00 (10%)
    - Carro: R$ 2.332,00
    - Água: R$ 150,00
    - Luz: R$ 300,00
    - Outros: R$ 4.033,00
    
    **Despesas Variáveis:** R$ 2.380,00
    **Despesas Invisíveis:** R$ 880,00
    """)
    
    st.markdown("---")
    
    st.subheader("🗑️ Gerenciar Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Restaurar Backup", type="secondary"):
            arquivo_upload = st.file_uploader("Escolha o arquivo JSON", type="json")
            if arquivo_upload:
                dados = json.load(arquivo_upload)
                st.session_state.transacoes = dados
                st.success("✅ Backup restaurado com sucesso!")
                st.rerun()
    
    with col2:
        if st.button("⚠️ Limpar Todos os Dados", type="secondary"):
            if st.checkbox("Confirmar exclusão (não pode ser desfeito)"):
                st.session_state.transacoes = []
                st.success("🗑️ Todos os dados foram removidos.")
                st.rerun()
    
    st.markdown("---")
    
    st.subheader("ℹ️ Sobre")
    st.markdown("""
    **Controle Financeiro Familiar v1.0**
    
    Desenvolvido para acompanhamento completo do orçamento familiar com:
    - Dashboard em tempo real
    - Registro de transações
    - Alertas automáticos
    - Cronograma de 12 meses
    - Relatórios e análises
    
    📧 Suporte: contato@otimizzai.com
    """)

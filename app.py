import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Configuração da página
st.set_page_config(
    page_title="Calculadora de Metas & Histórico", page_icon="📊", layout="centered"
)


# --- CONEXÃO COM O GOOGLE SHEETS VIA GSPREAD ---
@st.cache_resource
def conectar_google_sheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    # Lê as credenciais seguras dos Secrets do Streamlit
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(credentials)
    # Abre a planilha pelo nome exato no Google Drive
    sheet = client.open("Historico_Comissoes").sheet1
    return sheet


try:
    sheet = conectar_google_sheets()
except Exception as e:
    st.error(f"⚠️ Detalhe do Erro: {e}")

st.title("📊 Calculadora de Comissão & Histórico Mensal")
st.caption("Dados salvos de forma 100% privada e segura no seu Google Drive.")

st.divider()

# --- SEÇÃO 0: SELEÇÃO DO MÊS ---
st.subheader("🗓️ Mês de Referência")
col_mes, col_ano = st.columns(2)
mes_selecionado = col_mes.selectbox(
    "Selecione o Mês:",
    [
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ],
    index=5,
)
ano_selecionado = col_ano.number_input("Ano:", value=2026, step=1)

ref_mes_ano = f"{mes_selecionado}/{ano_selecionado}"

st.divider()

# --- SEÇÃO 1: GANHOS FIXOS E REEMBOLSOS ---
st.subheader("1. Entradas e Reembolsos")
col_fixo, col_ajuda = st.columns(2)
salario_base = col_fixo.number_input(
    "Salário Base Fixo (R$)", value=2667.47, step=100.0
)
ajuda_custo = col_ajuda.number_input(
    "Ajuda de Custo / Reembolso (R$)", value=1645.0, step=50.0
)

st.divider()

# --- SEÇÃO 2: FATURAMENTO BRUTO ---
st.subheader("2. Meta e Realizado de Faturamento")
col_fat_meta, col_fat_real = st.columns(2)
meta_fat = col_fat_meta.number_input(
    "Meta Faturamento (R$)", value=355000.0, step=1000.0
)
real_fat = col_fat_real.number_input(
    "Faturamento Realizado (R$)", value=381152.38, step=1000.0
)

atingimento_fat = real_fat / meta_fat if meta_fat > 0 else 0.0

st.divider()

# --- SEÇÃO 3: MIX DE PRODUTOS ---
st.subheader("3. Atingimento do Mix de Produtos")

categorias = [
    {"nome": "Positivação", "peso": 0.15, "key": "pos"},
    {"nome": "Coquetel", "peso": 0.10, "key": "coq"},
    {"nome": "Fritos Lanche", "peso": 0.20, "key": "fri"},
    {"nome": "Croissant / Folhados", "peso": 0.10, "key": "cro"},
    {"nome": "Fermentados", "peso": 0.10, "key": "fer"},
    {"nome": "Pão de Queijo", "peso": 0.30, "key": "pao"},
    {"nome": "Donnuts", "peso": 0.05, "key": "don"},
    {"nome": "Tortas / Quiches", "peso": 0.00, "key": "tor"},
]

atingimentos = {}
st.write("Insira o % de atingimento realizado em cada categoria:")

cols = st.columns(2)
for idx, cat in enumerate(categorias):
    col = cols[idx % 2]
    val_default = 90.6 if cat["key"] == "pos" else 100.0
    atingimentos[cat["key"]] = (
        col.number_input(
            f"{cat['nome']} (Peso: {int(cat['peso'] * 100)}%)",
            value=val_default,
            step=1.0,
            format="%.1f",
        )
        / 100.0
    )

mix_ponderado = sum(atingimentos[cat["key"]] * cat["peso"] for cat in categorias)

st.divider()

# --- SEÇÃO 4: DESPESAS E CUSTOS ---
st.subheader("4. Despesas de Trabalho e Veículo")
col_c1, col_c2, col_c3 = st.columns(3)
parcela_carro = col_c1.number_input("Parcela do Carro (R$)", value=1500.0, step=100.0)
gastos_combustivel = col_c2.number_input("Combustível (R$)", value=1500.0, step=50.0)
gastos_alimentacao = col_c3.number_input("Alimentação (R$)", value=400.0, step=50.0)

custos_totais_trabalho = parcela_carro + gastos_combustivel + gastos_alimentacao


# --- REGRAS DE NEGÓCIO ---
def get_pct_fat(ating):
    if ating < 0.85:
        return 0.0
    elif ating < 0.90:
        return 0.005
    elif ating < 0.95:
        return 0.006
    elif ating < 1.00:
        return 0.007
    else:
        return 0.008


def get_pct_mix(ating):
    if ating < 0.85:
        return 0.0
    elif ating < 0.90:
        return 0.008
    elif ating < 0.95:
        return 0.010
    elif ating < 1.00:
        return 0.011
    else:
        return 0.014


pct_comissao_fat = get_pct_fat(atingimento_fat)
pct_comissao_mix = get_pct_mix(mix_ponderado)
pct_total = pct_comissao_fat + pct_comissao_mix

comissao_reais = real_fat * pct_total
ganho_bruto_total = salario_base + ajuda_custo + comissao_reais
saldo_liquido_real = ganho_bruto_total - custos_totais_trabalho

st.divider()

# --- DASHBOARD DE RESULTADOS ---
st.subheader(f"🎯 Resumo Financeiro ({ref_mes_ano})")

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric(
    "Atingimento Faturamento",
    f"{atingimento_fat * 100:.1f}%",
    f"% Comissão: {pct_comissao_fat * 100:.2f}%",
)
col_m2.metric(
    "Mix Ponderado",
    f"{mix_ponderado * 100:.2f}%",
    f"% Bônus Mix: {pct_comissao_mix * 100:.2f}%",
)
col_m3.metric("Comissão Total", f"{pct_total * 100:.2f}%", f"R$ {comissao_reais:,.2f}")

st.info(f"💵 **Ganho Bruto Total:** R$ {ganho_bruto_total:,.2f}")
st.warning(f"💸 **Total de Despesas:** R$ {custos_totais_trabalho:,.2f}")
st.success(f"### 🚀 Saldo Líquido Efetivo: R$ {saldo_liquido_real:,.2f}")

# --- BOTÃO PARA SALVAR DIRETO NO GOOGLE SHEETS ---
st.write("---")
if st.button(f"💾 Salvar / Atualizar Fechamento de {ref_mes_ano} no Drive"):
    try:
        dados_existentes = sheet.get_all_records()

        # Procura se o mês já existe na planilha para atualizar a linha
        linha_para_atualizar = None
        for idx, row in enumerate(dados_existentes, start=2):  # Linha 1 é o cabeçalho
            if row.get("Mês/Ano") == ref_mes_ano:
                linha_para_atualizar = idx
                break

        nova_linha = [
            ref_mes_ano,
            round(real_fat, 2),
            f"{mix_ponderado * 100:.2f}%",
            round(comissao_reais, 2),
            round(ganho_bruto_total, 2),
            round(custos_totais_trabalho, 2),
            round(saldo_liquido_real, 2),
        ]

        if linha_para_atualizar:
            sheet.update(
                f"A{linha_para_atualizar}:G{linha_para_atualizar}", [nova_linha]
            )
            st.success(
                f"Fechamento de {ref_mes_ano} atualizado na planilha com sucesso!"
            )
        else:
            sheet.append_row(nova_linha)
            st.success(f"Fechamento de {ref_mes_ano} registrado no Google Sheets!")

    except Exception as e:
        st.error(f"Erro ao salvar na planilha: {e}")

# --- SEÇÃO 5: TABELA DO GOOGLE SHEETS & GERENCIAMENTO ---
st.divider()
st.subheader("📋 Histórico de Fechamentos (Google Sheets)")

try:
    dados_planilha = sheet.get_all_records()
    if len(dados_planilha) > 0:
        df_sheets = pd.DataFrame(dados_planilha)
        st.dataframe(df_sheets, use_container_width=True)

        st.write("---")
        st.caption("🛠️ **Gerenciar Linhas da Planilha:**")

        col_del_sel, col_del_btn = st.columns([2, 1])
        meses_salvos = [row["Mês/Ano"] for row in dados_planilha]
        mes_para_remover = col_del_sel.selectbox(
            "Escolha um mês para remover da planilha:", meses_salvos
        )

        if col_del_btn.button("❌ Remover do Drive"):
            for idx, row in enumerate(dados_planilha, start=2):
                if row["Mês/Ano"] == mes_para_remover:
                    sheet.delete_rows(idx)
                    st.success(f"{mes_para_remover} removido com sucesso!")
                    st.rerun()
    else:
        st.write("Nenhum registro encontrado na planilha do Google Drive ainda.")
except Exception as e:
    st.warning(
        "Não foi possível carregar a tabela. Verifique a conexão com o Google Sheets."
    )

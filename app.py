import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Calculadora de Metas & Comissão", page_icon="💰", layout="centered"
)

st.title("📊 Calculadora de Comissão & Salário")
st.caption("Acompanhamento mensal de atingimento de metas e simulador de ganhos.")

st.divider()

# --- SEÇÃO 1: DADOS FIXOS ---
st.subheader("1. Configurações Contratuais")
col_fixo, col_ajuda = st.columns(2)
salario_base = col_fixo.number_input(
    "Salário Base Fixo (R$)", value=2667.47, step=100.0
)
ajuda_custo = col_ajuda.number_input("Ajuda de Custo (R$)", value=1645.0, step=50.0)

st.divider()

# --- SEÇÃO 2: AVALIAÇÃO DE CATEGORIAS (MIX DE PRODUTOS) ---
st.subheader("2. Atingimento do Mix de Produtos")

# Definição das categorias com peso e chave
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
    # Valores default aproximados do seu fechamento
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

# Cálculo do Mix Ponderado
mix_ponderado = sum(atingimentos[cat["key"]] * cat["peso"] for cat in categorias)

st.divider()

# --- SEÇÃO 3: FATURAMENTO BRUTO ---
st.subheader("3. Meta e Realizado de Faturamento")
col_fat_meta, col_fat_real = st.columns(2)
meta_fat = col_fat_meta.number_input(
    "Meta Faturamento (R$)", value=355000.0, step=1000.0
)
real_fat = col_fat_real.number_input(
    "Faturamento Realizado (R$)", value=381152.38, step=1000.0
)

atingimento_fat = real_fat / meta_fat if meta_fat > 0 else 0.0


# --- LÓGICA DE REGRA DE NEGÓCIO ---
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
total_receber = salario_base + ajuda_custo + comissao_reais

st.divider()

# --- DASHBOARD DE RESULTADOS ---
st.subheader("🎯 Resumo Financeiro do Fechamento")

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

st.success(f"### 💵 Total Bruto a Receber: R$ {total_receber:,.2f}")

# --- ALERTA DE REGRAS ---
if atingimento_fat < 0.85 or mix_ponderado < 0.85:
    st.error("⚠️ Atenção: Atingimento abaixo de 85% zera a premiação correspondente!")

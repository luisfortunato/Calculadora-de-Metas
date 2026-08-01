import os
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Configuração da página
st.set_page_config(
    page_title="Calculadora de Metas & Histórico", page_icon="📊", layout="centered"
)

# Lista de todas as 22 colunas salvas na planilha
COLUNAS_PLANILHA = [
    "Mês/Ano",
    "Salário Base (R$)",
    "Ajuda de Custo (R$)",
    "Meta Fat. (R$)",
    "Fat. Realizado (R$)",
    "Ating. Fat. (%)",
    "Positivação (%)",
    "Coquetel (%)",
    "Fritos Lanche (%)",
    "Croissant/Folhados (%)",
    "Fermentados (%)",
    "Pão de Queijo (%)",
    "Donnuts (%)",
    "Tortas/Quiches (%)",
    "Mix Ponderado (%)",
    "Comissão Total (R$)",
    "Ganho Bruto (R$)",
    "Parcela Carro (R$)",
    "Combustível (R$)",
    "Alimentação (R$)",
    "Custos Totais (R$)",
    "🚀 Saldo Líquido Efetivo (R$)",
]


# --- CONEXÃO INTELIGENTE COM O GOOGLE SHEETS ---
@st.cache_resource
def conectar_google_sheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    caminho_chave_local = "chave.json"

    # 1. Tenta arquivo local (chave.json)
    if os.path.exists(caminho_chave_local):
        credentials = Credentials.from_service_account_file(
            caminho_chave_local, scopes=scope
        )
    # 2. Tenta Streamlit Secrets na Nuvem
    elif "gcp_service_account" in st.secrets:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope
        )
    else:
        raise FileNotFoundError(
            "Nenhuma credencial encontrada ('chave.json' ou 'st.secrets')."
        )

    client = gspread.authorize(credentials)
    sheet = client.open("Historico_Comissoes").sheet1
    return sheet


# Tenta inicializar a conexão
sheet = None
try:
    sheet = conectar_google_sheets()
except Exception as e:
    st.error(f"⚠️ Erro ao conectar com o Google Sheets: {e}")

st.title("📊 Calculadora de Comissão & Histórico Completo")
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

# --- SEÇÃO 3: AVALIAÇÃO DE CATEGORIAS (MIX DE PRODUTOS) ---
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

atingimentos_dict = {}
cols = st.columns(2)
for idx, cat in enumerate(categorias):
    col = cols[idx % 2]
    val_default = 90.6 if cat["key"] == "pos" else 100.0
    val_input = col.number_input(
        f"{cat['nome']} (Peso: {int(cat['peso'] * 100)}%)",
        value=val_default,
        step=1.0,
        format="%.1f",
    )
    atingimentos_dict[cat["key"]] = val_input

mix_ponderado = sum(
    (atingimentos_dict[cat["key"]] / 100.0) * cat["peso"] for cat in categorias
)

st.divider()

# --- SEÇÃO 4: DESPESAS E CUSTOS ---
st.subheader("4. Despesas de Trabalho e Veículo")
col_c1, col_c2, col_c3 = st.columns(3)
parcela_carro = col_c1.number_input("Parcela do Carro (R$)", value=1500.0, step=100.0)
gastos_combustivel = col_c2.number_input("Combustível (R$)", value=1500.0, step=50.0)
gastos_alimentacao = col_c3.number_input("Alimentação (R$)", value=400.0, step=50.0)

custos_totais_trabalho = parcela_carro + gastos_combustivel + gastos_alimentacao


# --- REGRAS DE NEGÓCIO DA COMISSÃO ---
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

# --- BOTÃO PARA SALVAR TUDO NO GOOGLE SHEETS ---
st.write("---")
if st.button(f"💾 Salvar Fechamento COMPLETO de {ref_mes_ano} no Drive"):
    if sheet is None:
        st.error("Não há conexão ativa com o Google Sheets.")
    else:
        try:
            # 1. Atualiza/Garante o cabeçalho correto da planilha (Linha 1)
            sheet.update("A1:V1", [COLUNAS_PLANILHA])

            dados_existentes = sheet.get_all_records()

            # 2. Procura se o mês selecionado já foi salvo antes para atualizar a linha
            linha_para_atualizar = None
            for idx, row in enumerate(dados_existentes, start=2):
                if str(row.get("Mês/Ano")) == ref_mes_ano:
                    linha_para_atualizar = idx
                    break

            # 3. Prepara TODOS os dados imputados e calculados
            nova_linha = [
                ref_mes_ano,
                round(meta_fat, 2),
                round(real_fat, 2),
                f"{atingimento_fat * 100:.1f}%",
                f"{atingimentos_dict['pos']:.1f}%",
                f"{atingimentos_dict['coq']:.1f}%",
                f"{atingimentos_dict['fri']:.1f}%",
                f"{atingimentos_dict['cro']:.1f}%",
                f"{atingimentos_dict['fer']:.1f}%",
                f"{atingimentos_dict['pao']:.1f}%",
                f"{atingimentos_dict['don']:.1f}%",
                f"{atingimentos_dict['tor']:.1f}%",
                f"{mix_ponderado * 100:.2f}%",
                round(comissao_reais, 2),
                round(ganho_bruto_total, 2),
                round(custos_totais_trabalho, 2),
                round(saldo_liquido_real, 2),
            ]

            if linha_para_atualizar:
                sheet.update(
                    f"A{linha_para_atualizar}:V{linha_para_atualizar}", [nova_linha]
                )
                st.success(
                    f"Fechamento de {ref_mes_ano} atualizado com sucesso no Google Sheets!"
                )
            else:
                sheet.append_row(nova_linha)
                st.success(
                    f"Fechamento de {ref_mes_ano} salvo com sucesso no Google Sheets!"
                )

            st.rerun()

        except Exception as e:
            st.error(f"Erro ao salvar na planilha: {e}")

# --- SEÇÃO 5: TABELA DO GOOGLE SHEETS ---
st.divider()
st.subheader("📋 Histórico Completo de Fechamentos (Google Sheets)")

if sheet is not None:
    try:
        dados_planilha = sheet.get_all_records()
        if len(dados_planilha) > 0:
            df_sheets = pd.DataFrame(dados_planilha)

            # Colunas originais exibidas na tabela
            colunas_resumo = [
                "Mês/Ano",
                "Fat. Realizado (R$)",
                "Ating. Fat. (%)",
                "Mix Ponderado (%)",
                "Comissão Total (R$)",
                "Custos Totais (R$)",
                "🚀 Saldo Líquido Efetivo (R$)",
            ]

            # Filtra garantindo que só exiba se a coluna existir no DataFrame
            colunas_presentes = [
                col for col in colunas_resumo if col in df_sheets.columns
            ]
            df_exibicao = df_sheets[colunas_presentes]

            # Exibe a tabela simplificada
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

            st.write("---")
            st.caption("🛠️ **Gerenciar Registros:**")

            col_del_sel, col_del_btn = st.columns([2, 1])
            meses_salvos = [
                str(row["Mês/Ano"]) for row in dados_planilha if "Mês/Ano" in row
            ]

            if meses_salvos:
                mes_para_remover = col_del_sel.selectbox(
                    "Escolha um mês para remover:", meses_salvos
                )

                if col_del_btn.button("❌ Remover do Drive"):
                    for idx, row in enumerate(dados_planilha, start=2):
                        if str(row.get("Mês/Ano")) == mes_para_remover:
                            sheet.delete_rows(idx)
                            st.success(
                                f"Registro de {mes_para_remover} removido com sucesso!"
                            )
                            st.rerun()
        else:
            st.info("Nenhum registro encontrado na planilha do Google Drive ainda.")
    except Exception as e:
        st.warning(f"Não foi possível carregar a tabela. Detalhe técnico do erro: {e}")
else:
    st.warning("Verifique a conexão com o Google Sheets no topo da página.")

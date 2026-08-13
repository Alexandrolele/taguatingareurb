import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re

# --- CONFIGURAÇÃO E INICIALIZAÇÃO FIREBASE ---
def inicializar_firebase():
    if not firebase_admin._apps:
        # Carrega as credenciais a partir do Secrets do Streamlit
        key_dict = dict(st.secrets["firebase_credentials"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': st.secrets["firebase_database_url"]
        })

inicializar_firebase()
ref_autorizacoes = db.reference("autorizacoes")

# --- FUNÇÕES DE PDF (Mantida a lógica original) ---
def gerar_pdf_autorizacao_fpdf(dados):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    
    def f(campo):
        val = str(dados.get(campo, ""))
        return "" if val == "nan" else val

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "TÍTULO DE PERMISSÃO", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 10)
    texto = f"Nome: {f('Nome')}\nCPF: {f('CPF')}\nLote: {f('Lote')} - Quadra: {f('Quadra')}\nSetor: {f('Setor')}"
    pdf.multi_cell(0, 5, texto)
    
    return pdf.output(dest="S")

# --- FUNÇÕES DE BANCO DE DADOS (Firebase) ---
def salvar_no_firebase(dados):
    # Cria uma chave única baseada no CPF e Lote
    id_registro = f"{dados['CPF']}_L{dados['Lote']}_Q{dados['Quadra']}"
    ref_autorizacoes.child(id_registro).set(dados)
    st.success("✅ Registro salvo com sucesso no Firebase!")

def buscar_todos():
    dados = ref_autorizacoes.get()
    if not dados: return pd.DataFrame()
    return pd.DataFrame.from_dict(dados, orient='index')

# --- FORMULÁRIO E INTERFACE ---
def exibir_formulario():
    st.header("Novo Cadastro")
    with st.form("form_autorizacao"):
        nome = st.text_input("Nome")
        cpf = st.text_input("CPF")
        lote = st.text_input("Lote")
        quadra = st.text_input("Quadra")
        setor = st.text_input("Setor")
        # ... (adicione aqui todos os outros campos que você já possui)
        
        submitted = st.form_submit_button("SALVAR")
        if submitted:
            dados = {
                "Nome": nome, "CPF": cpf, "Lote": lote, 
                "Quadra": quadra, "Setor": setor
            }
            salvar_no_firebase(dados)

def gerenciar_dados():
    st.header("Gerenciamento")
    df = buscar_todos()
    
    if df.empty:
        st.info("Nenhum dado encontrado.")
        return

    busca = st.text_input("Filtrar por nome")
    if busca:
        df = df[df['Nome'].str.contains(busca, case=False, na=False)]

    for idx, row in df.iterrows():
        with st.container(border=True):
            st.write(f"**{row['Nome']}** (CPF: {row['CPF']})")
            c1, c2 = st.columns(2)
            
            if c1.button("Gerar PDF", key=f"pdf_{idx}"):
                pdf = gerar_pdf_autorizacao_fpdf(row.to_dict())
                st.download_button("Baixar PDF", pdf, file_name="titulo.pdf")
            
            if c2.button("Excluir", key=f"del_{idx}"):
                ref_autorizacoes.child(idx).delete()
                st.rerun()

# --- EXECUÇÃO PRINCIPAL ---
st.title("Sistema de Autorização")
aba1, aba2 = st.tabs(["Cadastro", "Gerenciar"])
with aba1: exibir_formulario()
with aba2: gerenciar_dados()

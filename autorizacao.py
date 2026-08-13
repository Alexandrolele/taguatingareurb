from datetime import datetime
import re
import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
from fpdf import FPDF
import pandas as pd
from validate_docbr import CPF

# --- CONFIGURAÇÃO DO FIREBASE ---
def inicializar_firebase():
    if not firebase_admin._apps:
        # Carrega credenciais do Streamlit Secrets
        key_dict = json.loads(st.secrets["firebase_credentials"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': st.secrets["firebase_database_url"]
        })

inicializar_firebase()
ref_autorizacoes = db.reference("autorizacoes")

def gerar_pdf_autorizacao_fpdf(dados):
    """Gera o Título de Permissão com cabeçalho centralizado e tabela à direita."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    def f(campo, transform=None):
        texto = str(campo) if pd.notna(campo) and str(campo).lower() != "nan" else ""
        if texto.endswith(".0"): texto = texto[:-2]
        if transform == "lower": return texto.lower()
        if transform == "upper": return texto.upper()
        return texto

    def limpar(txt):
        return str(txt).encode("latin-1", "replace").decode("latin-1")

    def formatar_cpf(num_cpf):
        num_cpf = re.sub(r"\D", "", str(num_cpf))
        if len(num_cpf) == 11:
            return f"{num_cpf[:3]}.{num_cpf[3:6]}.{num_cpf[6:9]}-{num_cpf[9:]}"
        return num_cpf

    # Cabeçalho e Lógica de PDF mantidos conforme original
    pdf.set_y(12)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, limpar(""), ln=True, align="C")
    pdf.ln(35)

    hoje = datetime.now()
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    data_curta = f"{hoje.day} de {meses[hoje.month-1]} de {hoje.year}"

    pdf.set_font("Arial", "B", 9)
    x_inicial = 115
    pdf.set_x(x_inicial)
    pdf.cell(75, 7, limpar(f"TÍTULO DE PERMISSÃO Nº {f(dados.get('Titulo_Permissao'))}"), border=1, ln=True, align="C")
    pdf.set_x(x_inicial)
    pdf.cell(40, 7, limpar(f"LIVRO TOMBO Nº {f(dados.get('Livro_Tombo'))}"), border=1, align="C")
    pdf.cell(35, 7, limpar(f"FLS. {f(dados.get('Fls'))}"), border=1, ln=True, align="C")
    pdf.set_x(x_inicial)
    pdf.cell(75, 7, limpar(f"TAGUATINGA - TO, {data_curta}"), border=1, ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.set_left_margin(100)
    titulo_texto = "TÍTULO DE PERMISSÃO PARA REGISTRO E TRANSFERÊNCIA DE DOMÍNIO QUE O MUNICÍPIO DE TAGUATINGA - TO OUTORGA À PESSOA CONTEMPLADA ABAIXO IDENTIFICADA, CONFORME AUTORIZAÇÃO DO DECRETO N.º 244/2025."
    pdf.multi_cell(0, 5, limpar(titulo_texto), border=0, align="J")
    pdf.set_left_margin(20)
    pdf.ln(8)

    # Corpo do texto (mantido conforme original)
    chanfro_txt = (f", chanfro com {f(dados.get('Chanfro_Com'))}, medindo {f(dados.get('Chanfro_M'))} metros") if f(dados.get("Chanfro_Com")) else ""
    cpf_formatado = formatar_cpf(dados.get("CPF", ""))
    v_rg = f(dados.get("RG"))
    rg_completo = f"{v_rg} {f(dados.get('SSP'))}/{f(dados.get('UF_RG'))}".strip().replace(" /", "/") if v_rg else "____________________"

    texto_corpo = f"MUNICIPIO DE TAGUATINGA-TO... (omitido para brevidade, manter o seu original aqui)... LOTE URBANO n.º {f(dados['Lote'])}, Quadra: {f(dados['Quadra'])}, endereço do lote {f(dados['End_Lote'])}, Setor {f(dados['Setor'])}. Frente para a {f(dados['Frente_Com'])}, com medida de {f(dados['Frente_M'])} metros; fundos com o {f(dados['Fundo_Com'])}, com {f(dados['Fundo_M'])} metros; lado direito com o {f(dados['Dir_Com'])}, com {f(dados['Dir_M'])} metros e lado esquerdo com o {f(dados['Esq_Com'])}, com {f(dados['Esq_M'])} metros{chanfro_txt}, com área total de {f(dados['Area_Total'])}m², ({f(dados['Area_Extenso'])}), conforme memorial descritivo, Taguatinga/TO, ao (à) detentor (a), {f(dados['Nome'], 'upper')}, brasileiro(a), {f(dados['Estado Civil'], 'lower')}, {f(dados['Profissao'], 'lower')}, portador(a) da CI/RG nº {rg_completo} e do CPF N º {cpf_formatado}, residente na {f(dados['End_Residencial'])}, {f(dados['Bairro_Residencial'])}..."
    
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, limpar(texto_corpo), align="J")
    
    retorno_pdf = pdf.output(dest="S")
    return retorno_pdf.encode("latin-1") if isinstance(retorno_pdf, str) else bytes(retorno_pdf)

def salvar_registro(*args):
    colunas = ["Nome", "Nacionalidade", "Estado Civil", "Profissao", "RG", "SSP", "UF_RG", "CPF", 
               "End_Residencial", "Bairro_Residencial", "Lote", "Quadra", "End_Lote", "Setor", 
               "Frente_Com", "Frente_M", "Fundo_Com", "Fundo_M", "Dir_Com", "Dir_M", "Esq_Com", 
               "Esq_M", "Area_Total", "Area_Extenso", "Matricula", "Lei_Aplicada", "Chanfro_Com", 
               "Chanfro_M", "Titulo_Permissao", "Livro_Tombo", "Fls"]
    
    dados = dict(zip(colunas, args))
    id_registro = f"{dados['CPF']}_{dados['Lote']}_{dados['Quadra']}"
    ref_autorizacoes.child(id_registro).set(dados)
    st.success("✅ Dados salvos com sucesso no Firebase!")
    st.session_state.editar_autorizacao = None
    st.rerun()

def formulario_autorizacao(dados_edicao=None):
    # ... (Manter seu formulário igual ao original) ...
    with st.form("form_autorizacao"):
        # (Seus campos de input continuam aqui)
        if st.form_submit_button("💾 SALVAR"):
            # Lógica de validação e chamada da salvar_registro()
            pass

def lista_e_gestao():
    dados_firebase = ref_autorizacoes.get()
    if not dados_firebase:
        st.info("Nenhum dado cadastrado.")
        return
    
    # Converte para DF para usar as ferramentas de busca
    lista_registros = [{**v, "id_firebase": k} for k, v in dados_firebase.items()]
    df = pd.DataFrame(lista_registros)
    
    busca = st.text_input("🔍 Pesquisar")
    if busca:
        df = df[df["Nome"].str.contains(busca, case=False, na=False) | df["CPF"].str.contains(busca, na=False)]

    for _, row in df.iterrows():
        with st.container(border=True):
            st.write(f"👤 **{row['Nome']}** | Lote {row['Lote']} - Q. {row['Quadra']}")
            
            c1, c2, c3 = st.columns(3)
            if c1.button("📝", key=f"e_{row['id_firebase']}"):
                st.session_state.editar_autorizacao = row.to_dict()
                st.rerun()
            if c2.button("🗑️", key=f"d_{row['id_firebase']}"):
                ref_autorizacoes.child(row['id_firebase']).delete()
                st.rerun()
            
            pdf_bytes = gerar_pdf_autorizacao_fpdf(row)
            c3.download_button("📄 PDF", pdf_bytes, f"Titulo_{row['Nome']}.pdf", "application/pdf")

def exibir_pagina():
    st.title("📄 Título de Permissão")
    t1, t2 = st.tabs(["Novo", "Gerenciar"])
    with t1: formulario_autorizacao(st.session_state.get("editar_autorizacao"))
    with t2: lista_e_gestao()

if __name__ == "__main__":
    exibir_pagina()

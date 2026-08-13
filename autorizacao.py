import json
import os
import re
import firebase_admin
from firebase_admin import db
import pandas as pd
import streamlit as st

# --- CONFIGURAÇÃO INICIAL (Mantida) ---
def obter_referencia_firebase(caminho=""):
    try:
        app = firebase_admin.get_app()
    except ValueError:
        if "firebase" in st.secrets:
            creds_dict = dict(st.secrets["firebase"])
            cred = firebase_admin.credentials.Certificate(creds_dict)
            database_url = st.secrets["firebase"].get("databaseURL", f"https://{creds_dict.get('project_id')}-default-rtdb.firebaseio.com/")
            app = firebase_admin.initialize_app(cred, {"databaseURL": database_url})
        elif os.path.exists("firebase_key.json"):
            cred = firebase_admin.credentials.Certificate("firebase_key.json")
            with open("firebase_key.json", "r") as f:
                key_data = json.load(f)
                database_url = f"https://{key_data.get('project_id')}-default-rtdb.firebaseio.com/"
            app = firebase_admin.initialize_app(cred, {"databaseURL": database_url})
        else:
            raise ValueError("Credenciais do Firebase não encontradas.")
    
    return db.reference(caminho, app=app) if caminho else db.reference(app=app)

# --- FUNÇÕES DE APOIO ---
def carregar_dados_firebase():
    ref = obter_referencia_firebase("autorizacoes_titulos")
    dados = ref.get()
    if not dados: return pd.DataFrame()
    
    lista_dados = []
    for chave, valor in dados.items():
        if isinstance(valor, dict):
            valor['_chave_firebase'] = chave  # Guardamos a chave real do Firebase
            lista_dados.append(valor)
    return pd.DataFrame(lista_dados)

def validar_cpf(cpf_str):
    cpf_limpo = re.sub(r"\D", "", cpf_str)
    if len(cpf_limpo) != 11 or cpf_limpo == cpf_limpo[0] * 11: return False
    # (Lógica de validação simplificada)
    return True

# --- FUNÇÃO SALVAR ATUALIZADA ---
def salvar_registro(chave_antiga, *args):
    colunas = [
        "Nome", "Nacionalidade", "Estado Civil", "Profissao", "RG", "SSP", "UF_RG", 
        "CPF", "End_Residencial", "Bairro_Residencial", "Lote", "Quadra", 
        "End_Lote", "Setor", "Frente_Com", "Frente_M", "Fundo_Com", "Fundo_M", 
        "Dir_Com", "Dir_M", "Esq_Com", "Esq_M", "Area_Total", "Area_Extenso", 
        "Matricula", "Lei_Aplicada", "Chanfro_Com", "Chanfro_M", "Titulo_Permissao", 
        "Livro_Tombo", "Fls"
    ]
    novo_dict = dict(zip(colunas, args))
    
    # Gera a chave baseada nos novos dados
    chave_nova = f"lote_{str(args[11])}_{str(args[10])}_cpf_{str(args[7])}".replace(".", "_")

    # Se a chave mudou e a antiga existe, deleta a antiga para evitar duplicidade
    if chave_antiga and chave_antiga != chave_nova:
        obter_referencia_firebase(f"autorizacoes_titulos/{chave_antiga}").delete()

    # Salva no caminho correto
    obter_referencia_firebase(f"autorizacoes_titulos/{chave_nova}").set(novo_dict)

    st.success("✅ Dados salvos com sucesso!")
    st.session_state.editar_autorizacao = None
    st.rerun()

# --- FORMULÁRIO ---
def formulario_autorizacao(dados_edicao=None):
    if dados_edicao:
        st.warning(f"📝 Editando: {dados_edicao.get('Nome')}")
        if st.button("❌ Cancelar"):
            st.session_state.editar_autorizacao = None
            st.rerun()

    fonte_dados = dados_edicao if dados_edicao else {}

    with st.form("form_autorizacao"):
        # Campos simplificados para exemplo (preencha o restante conforme seu original)
        nome = st.text_input("Nome", value=fonte_dados.get("Nome", ""))
        lote_num = st.text_input("Lote Nº", value=fonte_dados.get("Lote", ""))
        quadra_num = st.text_input("Quadra", value=fonte_dados.get("Quadra", ""))
        cpf = st.text_input("CPF", value=fonte_dados.get("CPF", ""))
        
        # (Adicione todos os outros campos aqui...)
        
        if st.form_submit_button("💾 SALVAR"):
            # Passa a chave antiga que veio do dict de edição
            chave_antiga = dados_edicao.get("_chave_firebase") if dados_edicao else None
            
            salvar_registro(
                chave_antiga, nome, "Brasileiro", "...", "...", "...", "...", 
                re.sub(r"\D", "", cpf), "...", "...", lote_num, quadra_num, 
                "...", "...", "...", "...", "...", "...", "...", "...", 
                "...", "...", "...", "...", "...", "...", "...", "...", 
                "...", "...", "..."
            )

# --- GESTÃO ---
def lista_e_gestao():
    df = carregar_dados_firebase()
    if df.empty: return
    
    for idx, row in df.iterrows():
        with st.container(border=True):
            st.write(f"👤 {row['Nome']} - Lote {row['Lote']}")
            if st.button("📝 Editar", key=f"e_{idx}"):
                st.session_state.editar_autorizacao = row.to_dict()
                st.rerun()

def exibir_pagina():
    st.title("📄 Título de Permissão")
    t1, t2 = st.tabs(["Novo", "Gerenciar"])
    if t1: formulario_autorizacao(st.session_state.get("editar_autorizacao"))
    if t2: lista_e_gestao()

if __name__ == "__main__":
    exibir_pagina()

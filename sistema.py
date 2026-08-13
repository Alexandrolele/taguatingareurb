from datetime import datetime
import base64
import json
import os
import re
import shutil
import pandas as pd
import streamlit as st
from validate_docbr import CPF
import firebase_admin
from firebase_admin import credentials, db

# --- 2. CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira chamada do Streamlit) ---
st.set_page_config(
    page_title="REURB - Taguatinga-TO", 
    page_icon="logo_prefeitura.png",
    layout="wide"
)

# --- 0. INICIALIZAÇÃO DO FIREBASE (NUVEM / LOCAL) ---
def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            # 1. Tenta carregar dos segredos do Streamlit Cloud
            if "firebase" in st.secrets:
                creds_dict = dict(st.secrets["firebase"])
                cred = credentials.Certificate(creds_dict)
                database_url = st.secrets["firebase"].get("databaseURL", "")
                firebase_admin.initialize_app(cred, {'databaseURL': database_url})
            # 2. Se não estiver no Cloud, carrega o arquivo local de chave
            elif os.path.exists("firebase_key.json"):
                cred = credentials.Certificate("firebase_key.json")
                with open("firebase_key.json", "r") as f:
                    key_data = json.load(f)
                    project_id = key_data.get("project_id", "")
                    database_url = f"https://{project_id}-default-rtdb.firebaseio.com/"
                firebase_admin.initialize_app(cred, {'databaseURL': database_url})
        except Exception as e:
            st.warning(f"Aviso Firebase: {e}")

inicializar_firebase()

# Importações dos seus arquivos e funções internas (após o Firebase inicializado)
import autorisação as autorizacao  # verifique se o nome do seu arquivo é autorizacao.py
from gerar_certidao import gerar_pdf_projeto
import certidaoreurb 

# --- Ocultar menu, cabeçalho, rodapé e o botão "Manage app" ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppHeader {display: none;}
    div[data-testid="stToolbar"] {display: none;}
    div[data-testid="stStatusWidget"] {display: none;}
    .viewerBadge_container__163Vn {display: none !important;}
    
    /* Esconde o botão "Manage app" e elementos de desenvolvedor do Streamlit Cloud */
    [data-testid="stDecoration"] {display: none;}
    div[class*="viewerBadge"] {display: none !important;}
    button[title="Manage app"] {display: none !important;}
    div[data-testid="manage-app-button"] {display: none !important;}
    #stDecoration {display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 1. FUNÇÃO DE BACKUP AUTOMÁTICO ---
def realizar_backup():
    arquivos_para_backup = ["dados_autorizacoes.csv"]
    
    for f in os.listdir('.'):
        if f.endswith('.csv') and f.startswith('proprietarios_'):
            arquivos_para_backup.append(f)
            
    if not os.path.exists("backups"):
        os.makedirs("backups")
    
    agora = datetime.now()
    data_hoje = agora.strftime("%Y-%m-%d")
    hora_atual = agora.strftime("%H-%M-%S")
    
    for arquivo_original in arquivos_para_backup:
        if os.path.exists(arquivo_original):
            arquivos_na_pasta = os.listdir("backups")
            backups_de_hoje = sorted([
                os.path.join("backups", f) for f in arquivos_na_pasta 
                if f.startswith(f"backup_{data_hoje}") and arquivo_original in f
            ])
            
            if len(backups_de_hoje) >= 3:
                try:
                    os.remove(backups_de_hoje[0])
                except Exception:
                    pass
            
            nome_backup = f"backups/backup_{data_hoje}_{hora_atual}_{arquivo_original}"
            shutil.copy2(arquivo_original, nome_backup)

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- 3. TELA DE LOGIN SEGURA ---
def tela_login():
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        with st.container(border=True):
            try:
                if os.path.exists("logo_prefeitura.png"):
                    with open("logo_prefeitura.png", "rb") as img_file:
                        img_base64 = base64.b64encode(img_file.read()).decode()
                    
                    st.markdown(
                        f"""
                        <div style='text-align: center; width: 100%;'>
                            <div style="display: block; margin-left: auto; margin-right: auto; width: 120px; margin-bottom: 10px;">
                                <img src="data:image/png;base64,{img_base64}" width="120">
                            </div>
                            <div style='line-height: 1.0;'>
                                <h1 style='margin: 0; padding: 0; font-size: 2.0rem;'>SISTEMA REURB</h1>
                                <p style='margin: 0; padding: 0; color: #555; font-size: 1.1rem; font-weight: bold;'>ESTADO DO TOCANTINS</p>
                                <p style='margin: 0; padding: 0; color: #333; font-size: 1.2rem; font-weight: bold;'>PREFEITURA MUNICIPAL DE TAGUATINGA</p>
                                <p style='margin: 2px 0; padding: 0; color: #004a99; font-style: italic; font-size: 0.9rem;'>“O PROGRESSO CONTINUA!”</p>
                                <p style='margin: 8px 0 0 0; padding: 0; font-size: 1.5rem; font-weight: bold;'>DEPARTAMENTO DE REGULARIZAÇÃO FUNDIÁRIA</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            except Exception:
                st.error("Erro ao carregar cabeçalho visual.")
                    
            st.divider()
                    
            usuario = st.text_input("Usuário", value="Michelaine")
            senha = st.text_input("Senha", type="password")
            
            st.write("<br>", unsafe_allow_html=True)
            
            if st.button("Acessar Sistema", use_container_width=True):
                senha_correta = st.secrets.get("SENHA_ADMIN", "lele4619") if "SENHA_ADMIN" in st.secrets else "lele4619"
                if senha == senha_correta:
                    realizar_backup() 
                    st.session_state.usuario_logado = usuario
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Senha incorreta. Tente novamente.")

if not st.session_state.autenticado:
    tela_login()
    st.stop()

# --- FUNÇÕES DE APOIO ---
def listar_projetos():
    return [f for f in os.listdir('.') if f.endswith('.json') and f.startswith('projeto_')]

def listar_csvs():
    return [f for f in os.listdir('.') if f.endswith('.csv') and f.startswith('proprietarios_')]

if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'
if 'projeto_ativo' not in st.session_state:
    st.session_state.projeto_ativo = None
if 'quadra_selecionada' not in st.session_state:
    st.session_state.quadra_selecionada = None
if 'nome_arquivo_original' not in st.session_state:
    st.session_state.nome_arquivo_original = None

# --- SIDEBAR ---
nome_usuario = st.session_state.get('usuario_logado', 'Usuário')

st.sidebar.markdown(f"👋 **Olá, {nome_usuario}!**")
st.sidebar.caption("Bem-vindo(a) ao Sistema REURB.")
st.sidebar.divider()

st.sidebar.title("MENU REURB")
if st.sidebar.button("🏠 Início"):
    st.session_state.pagina = 'inicio'
    st.session_state.projeto_ativo = None
    st.session_state.quadra_selecionada = None
    st.session_state.nome_arquivo_original = None
    st.rerun()

if st.sidebar.button("➕ Novo Núcleo"):
    st.session_state.pagina = 'cadastro_nucleo'
    st.session_state.projeto_ativo = None
    st.session_state.nome_arquivo_original = None
    st.rerun()

if st.sidebar.button("🔍 Pesquisar"):
    st.session_state.pagina = 'pesquisar'
    st.rerun()

if st.sidebar.button("📊 Relatórios"):
    st.session_state.pagina = 'relatorios'
    st.rerun()

if st.sidebar.button("📜 Certidão REURB"):
    st.session_state.pagina = 'certidaoreurb'
    st.rerun()

if st.sidebar.button("📄 Autorização"):
    st.session_state.pagina = 'autorizacao'
    st.rerun()

st.sidebar.divider()

if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state.autenticado = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("🚀 Desenvolvido por:")
st.sidebar.subheader("Alexandro Freire")
st.sidebar.caption("Versão 1.0 | 2026")
st.sidebar.markdown("---")


# --- 1. TELA INICIAL ---
if st.session_state.pagina == 'inicio':
    st.title("🏛️ Painel de Projetos")
    arquivos = listar_projetos()
    if not arquivos:
        st.info("Nenhum núcleo cadastrado.")
    else:
        cols = st.columns(3)
        for idx, arq in enumerate(arquivos):
            with open(arq, "r", encoding="utf-8") as f:
                dados = json.load(f)
            with cols[idx % 3]:
                with st.container(border=True):
                    st.subheader(f"📍 {dados['nome']}")
                    
                    crf_n = dados.get('num_crf', dados.get('num_decreto', '')) 
                    ano_c = dados.get('ano_crf', dados.get('ano_decreto', ''))
                    
                    if crf_n and ano_c:
                        st.markdown(f"**CRF Nº:** {crf_n}/{ano_c}")
                    else:
                        st.markdown("*CRF: Não informada*")
                        
                    st.write(f"**Local:** {dados['local']}")
                    if st.button(f"Abrir Detalhes", key=f"abrir_{arq}"):
                        st.session_state.projeto_ativo = dados
                        st.session_state.nome_arquivo_original = arq
                        st.session_state.pagina = 'detalhes_projeto'
                        st.rerun()

# --- 2. CADASTRO / EDIÇÃO DE NÚCLEO ---
elif st.session_state.pagina == 'cadastro_nucleo':
    editando = st.session_state.projeto_ativo is not None
    st.title("📋 " + ("Editar Núcleo" if editando else "Novo Núcleo"))
    p = st.session_state.projeto_ativo if editando else {}

    if editando:
        with st.expander("⚠️ Zona de Perigo"):
            if st.button("🗑️ EXCLUIR ESTE NÚCLEO DEFINITIVAMENTE"):
                try:
                    nome_json = st.session_state.nome_arquivo_original
                    nome_csv = nome_json.replace('projeto_', 'proprietarios_').replace('.json', '.csv')
                    if os.path.exists(nome_json): 
                        os.remove(nome_json)
                    if os.path.exists(nome_csv): 
                        os.remove(nome_csv)
                        
                    st.session_state.pagina = 'inicio'
                    st.session_state.projeto_ativo = None
                    st.session_state.nome_arquivo_original = None
                    st.success("Núcleo excluído com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir núcleo: {e}")

    with st.form("form_n"):
        c1, c2 = st.columns(2)
        nome_n = c1.text_input("Nome do Núcleo", value=p.get('nome', ''))
        local = c1.text_input("Localização", value=p.get('local', ''))
        mod = c1.selectbox("Modalidade", ["Reurb-S (Social)", "Reurb-E (Específica)"], index=0 if p.get('modalidade') == "Reurb-S (Social)" else 1)
        
        num_crf = c1.text_input("Número da CRF", value=p.get('num_crf', p.get('num_decreto', '')), placeholder="Ex: 01")
        ano_crf = c1.text_input("Ano da CRF", value=p.get('ano_crf', p.get('ano_decreto', '')), placeholder="Ex: 2026")
        
        val_area_original = p.get('area_total', '0,00')
        if isinstance(val_area_original, (int, float)):
            val_area_str = f"{val_area_original:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            val_area_str = str(val_area_original)
            
        val_viaria_original = p.get('area_viaria', '0,00')
        if isinstance(val_viaria_original, (int, float)):
            val_viaria_str = f"{val_viaria_original:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            val_viaria_str = str(val_viaria_original)

        area_txt = c2.text_input("Área Total (m²)", value=val_area_str, placeholder="00.000,00")
        ruas = c2.number_input("Qtd Ruas", step=1, value=int(p.get('ruas', 0)))
        viario_txt = c2.text_input("Área Viária (m²)", value=val_viaria_str, placeholder="00.000,00")
        
        padrao_q = len(p.get('quadras', [])) if editando else 1
        qtd_q = st.number_input("Quantidade de Quadras", min_value=1, step=1, value=max(1, padrao_q))
        
        lista_q = []
        col_q = st.columns(4)
        for i in range(int(qtd_q)):
            val_q = p['quadras'][i]['quadra'] if editando and i < len(p['quadras']) else f"{i+1}"
            val_l = p['quadras'][i]['lotes'] if editando and i < len(p['quadras']) else 0
            with col_q[i % 4]:
                qid = st.text_input(f"Nº Q. {i+1}", value=val_q, key=f"nq_{i}")
                qlt = st.number_input(f"Lotes Q.{qid}", min_value=0, step=1, value=int(val_l), key=f"nl_{i}")
                lista_q.append({"quadra": qid, "lotes": qlt})
        
        if st.form_submit_button("Salvar"):
            try:
                area_limpa = area_txt.replace(".", "").replace(",", ".")
                area_float = float(area_limpa) if area_limpa else 0.0
            except ValueError:
                area_float = 0.0
                
            try:
                viario_limpo = viario_txt.replace(".", "").replace(",", ".")
                viario_float = float(viario_limpo) if viario_limpo else 0.0
            except ValueError:
                viario_float = 0.0

            novo_p = {
                "nome": nome_n, 
                "local": local, 
                "modalidade": mod, 
                "num_crf": num_crf,
                "ano_crf": ano_crf,
                "area_total": area_float, 
                "ruas": ruas, 
                "area_viaria": viario_float, 
                "quadras": lista_q
            }
            
            crf_sufixo = f"_crf_{num_crf.strip()}_{ano_crf.strip()}" if num_crf.strip() and ano_crf.strip() else ""
            nome_arq_novo = f"projeto_{nome_n.replace(' ', '_').lower()}{crf_sufixo}.json"
            
            if editando and st.session_state.nome_arquivo_original:
                nome_arq_antigo = st.session_state.nome_arquivo_original
                
                if nome_arq_antigo != nome_arq_novo:
                    antigo_csv = nome_arq_antigo.replace('projeto_', 'proprietarios_').replace('.json', '.csv')
                    novo_csv = nome_arq_novo.replace('projeto_', 'proprietarios_').replace('.json', '.csv')
                    
                    if os.path.exists(antigo_csv):
                        shutil.move(antigo_csv, novo_csv)
                    if os.path.exists(nome_arq_antigo):
                        os.remove(nome_arq_antigo)

            with open(nome_arq_novo, "w", encoding="utf-8") as f:
                json.dump(novo_p, f, indent=4, ensure_ascii=False)
                
            st.session_state.pagina = 'inicio'
            st.session_state.projeto_ativo = None
            st.session_state.nome_arquivo_original = None
            st.rerun()

# --- 3. TELA DE DETALHES ---
elif st.session_state.pagina == 'detalhes_projeto':
    p = st.session_state.projeto_ativo
    st.title(f"📍 Núcleo: {p['nome']}")
    if st.button("📝 Editar Dados / Excluir"):
        st.session_state.pagina = 'cadastro_nucleo'
        st.rerun()
        
    try:
        area_total_val = float(p.get('area_total', 0.0))
        area_total_formatada = f"{area_total_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        area_total_formatada = "0,00"

    try:
        area_viaria_val = float(p.get('area_viaria', 0.0))
        area_viaria_formatada = f"{area_viaria_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        area_viaria_formatada = "0,00"

    with st.expander("📄 Dados Técnicos", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Modalidade:** {p['modalidade']}")
        c2.write(f"**Área Total:** {area_total_formatada} m²")
        c3.write(f"**Área Viária:** {area_viaria_formatada} m²")
        
        crf_n = p.get('num_crf', p.get('num_decreto', ''))
        crf_a = p.get('ano_crf', p.get('ano_decreto', ''))
        if crf_n and crf_a:
            st.write(f"**CRF de Regulamentação:** {crf_n}/{crf_a}")
        
    st.divider()
    cols_q = st.columns(5)
    for idx, q_info in enumerate(p['quadras']):
        with cols_q[idx % 5]:
            if st.button(f"QUADRA {q_info['quadra']}", key=f"sel_q_{idx}", use_container_width=True):
                st.session_state.quadra_selecionada = q_info['quadra']
                st.session_state.pagina = 'cadastro_proprietario'
                st.rerun()

# --- 4. TELA DE CADASTRO DE PROPRIETÁRIOS ---
elif st.session_state.pagina == 'cadastro_proprietario':
    p = st.session_state.projeto_ativo
    q_sel = st.session_state.quadra_selecionada
    
    if st.session_state.nome_arquivo_original:
        nome_csv = st.session_state.nome_arquivo_original.replace('projeto_', 'proprietarios_').replace('.json', '.csv')
    else:
        crf_sufixo = f"_crf_{p.get('num_crf','')}_{p.get('ano_crf','')}" if p.get('num_crf') else ""
        nome_csv = f"proprietarios_{p['nome'].replace(' ', '_').lower()}{crf_sufixo}.csv"
        
    st.title(f"👤 Cadastro - Quadra {q_sel}")
    
    if 'editando_index' not in st.session_state:
        st.session_state.editando_index = None
    if 'dados_edicao' not in st.session_state:
        st.session_state.dados_edicao = {}

    if st.button("⬅️ Voltar"):
        st.session_state.editando_index = None
        st.session_state.dados_edicao = {}
        st.session_state.pagina = 'detalhes_projeto'
        st.rerun()

    dados_autocompletar = {}
    if os.path.exists(nome_csv) and st.session_state.editando_index is None:
        df_existente = pd.read_csv(nome_csv, dtype=str)
        if not df_existente.empty:
            df_unicos = df_existente.drop_duplicates(subset=['CPF', 'Nome'])
            lista_pessoas = ["-- Selecione para copiar dados (Múltiplos Lotes) --"] + [
                f"{row['Nome']} (CPF: {row['CPF']})" for _, row in df_unicos.iterrows()
            ]
            
            selecionado = st.selectbox("👤 Copiar dados de ocupante já cadastrado:", lista_pessoas)
            if selecionado != "-- Selecione para copiar dados (Múltiplos Lotes) --":
                nome_selecionado = selecionado.split(" (CPF:")[0]
                dados_autocompletar = df_unicos[df_unicos['Nome'] == nome_selecionado].iloc[0].fillna("").to_dict()

    with st.form("form_prop", clear_on_submit=False):
        if st.session_state.editando_index is not None:
            st.warning(f"📝 Editando o Lote {st.session_state.dados_edicao.get('Lote', '')}")
            fonte_dados = st.session_state.dados_edicao
        else:
            fonte_dados = dados_autocompletar
            
        st.subheader("Dados do Ocupante")
        c1, c2, c3 = st.columns(3)
        
        lote_n = c1.text_input("Lote Nº", value=st.session_state.dados_edicao.get("Lote", ""))
        matricula = c2.text_input("Matrícula", value=st.session_state.dados_edicao.get("Matrícula", ""))
        nome = c3.text_input("Nome Completo", value=fonte_dados.get("Nome", ""))
        
        opcoes_civil = ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"]
        civil_salvo = fonte_dados.get("Estado Civil", "Solteiro(a)")
        idx_civil = opcoes_civil.index(civil_salvo) if civil_salvo in opcoes_civil else 0
        
        st_civil = c1.selectbox("Estado Civil", opcoes_civil, index=idx_civil)
        profissao = c2.text_input("Profissão", value=fonte_dados.get("Profissão", ""))
        cpf = c3.text_input("CPF", placeholder="000.000.000-00", value=fonte_dados.get("CPF", ""))
        
        rg = c1.text_input("CI/RG", placeholder="0000000", value=fonte_dados.get("RG", ""))
        ssp = c2.text_input("SSP/UF", value=fonte_dados.get("SSP", ""))
        endereco = c3.text_input("Endereço", value=fonte_dados.get("Endereço", ""))
        
        bairro = c1.text_input("Bairro", value=fonte_dados.get("Bairro", ""))
        cidade = c2.text_input("Cidade", value=fonte_dados.get("Cidade", "Taguatinga"))
        uf = c3.text_input("UF", value=fonte_dados.get("UF", "TO"))
        
        st.divider()
        st.subheader("Dados do Cônjuge / Herdeiro")
        hc1, hc2, hc3 = st.columns(3)
        h_nome = hc1.text_input("Nome (Cônjuge/Herdeiro)", value=fonte_dados.get("H_Nome", ""))
        
        opcoes_h_civil = ["N/A", "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"]
        h_civil_salvo = fonte_dados.get("H_Est_Civil", "N/A")
        idx_h_civil = opcoes_h_civil.index(h_civil_salvo) if h_civil_salvo in opcoes_h_civil else 0
        
        h_est_civil = hc2.selectbox("Estado Civil (Cônjuge/Herdeiro)", opcoes_h_civil, index=idx_h_civil)
        h_profissao = hc3.text_input("Profissão (Cônjuge/Herdeiro)", value=fonte_dados.get("H_Profissao", ""))
        
        h_rg = hc1.text_input("CI/RG (Cônjuge/Herdeiro)", placeholder="0000000", value=fonte_dados.get("H_RG", ""))
        h_ssp_uf = hc2.text_input("SSP/UF (Cônjuge/Herdeiro)", value=fonte_dados.get("H_SSP", ""))
        h_cpf = hc3.text_input("CPF (Cônjuge/Herdeiro)", placeholder="000.000.000-00", value=fonte_dados.get("H_CPF", ""))
        
        texto_botao = "Salvar Alterações" if st.session_state.editando_index is not None else "Salvar Cadastro"
        if st.form_submit_button(texto_botao):
            validador = CPF()
            
            cpf_limpo = re.sub(r'\D', '', cpf)
            rg_numeros = re.sub(r'[.-]', '', rg)
            h_cpf_limpo = re.sub(r'\D', '', h_cpf)
            h_rg_numeros = re.sub(r'[.-]', '', h_rg)
            cpf_so_numeros = re.sub(r'[.-]', '', cpf)
            h_cpf_so_numeros = re.sub(r'[.-]', '', h_cpf)

            erro = False
            
            if not nome:
                st.error("⚠️ O nome do ocupante é obrigatório.")
                erro = True
            elif cpf_so_numeros != "" and not cpf_so_numeros.isdigit():
                st.error("❌ CPF do Titular não pode conter letras.")
                erro = True
            elif not rg_numeros.isdigit() or len(rg_numeros) < 4:
                st.error("❌ RG do Titular inválido (use apenas números).")
                erro = True
            elif not validador.validate(cpf_limpo):
                st.error("❌ CPF do Titular matematicamente inválido.")
                erro = True
            
            if not erro:
                if h_cpf_so_numeros != "" and not h_cpf_so_numeros.isdigit():
                    st.error("❌ CPF do Cônjuge/Herdeiro não pode conter letras.")
                    erro = True
                elif h_cpf_limpo != "" and not validador.validate(h_cpf_limpo):
                    st.error("❌ CPF do Cônjuge/Herdeiro inválido.")
                    erro = True
                elif h_rg_numeros != "" and not h_rg_numeros.isdigit():
                    st.error("❌ RG do Cônjuge/Herdeiro deve conter apenas números.")
                    erro = True

            if not erro:
                colunas = ["Quadra", "Lote", "Matrícula", "Nome", "Estado Civil", "Profissão", "RG", "SSP", "CPF", 
                           "Endereço", "Bairro", "Cidade", "UF", 
                           "H_Nome", "H_Est_Civil", "H_Profissao", "H_RG", "H_SSP", "H_CPF"]
                
                dados_linha = [str(q_sel), lote_n, matricula, nome, st_civil, profissao, rg.strip().upper(), ssp, cpf_limpo, 
                               endereco, bairro, cidade, uf, 
                               h_nome, h_est_civil, h_profissao, h_rg.strip().upper(), h_ssp_uf, h_cpf_limpo]
                
                if st.session_state.editando_index is not None:
                    df_completo = pd.read_csv(nome_csv, dtype=str)
                    df_completo.iloc[st.session_state.editando_index] = dados_linha
                    df_completo.to_csv(nome_csv, index=False, encoding="utf-8-sig")
                    st.success(f"✅ Lote {lote_n} atualizado!")
                    
                    st.session_state.editando_index = None
                    st.session_state.dados_edicao = {}
                else:
                    novo_dado = pd.DataFrame([dados_linha], columns=colunas)
                    if not os.path.exists(nome_csv):
                        novo_dado.to_csv(nome_csv, index=False, encoding="utf-8-sig")
                    else:
                        novo_dado.to_csv(nome_csv, mode='a', header=False, index=False, encoding="utf-8-sig")
                    st.success(f"✅ Lote {lote_n} cadastrado com sucesso!")
                
                st.rerun()
    
    if os.path.exists(nome_csv):
        df = pd.read_csv(nome_csv, dtype=str)
        df_q = df[df['Quadra'] == str(q_sel)].reset_index()
        if not df_q.empty:
            st.subheader(f"📋 Lista de Ocupantes - Quadra {q_sel}")
            h1, h2, h3, h4 = st.columns([1, 2, 4, 2])
            h1.write("**Lote**"); h2.write("**Matrícula**"); h3.write("**Nome**"); h4.write("**Ações**")
            for index, row in df_q.iterrows():
                r1, r2, r3, r4 = st.columns([1, 2, 4, 2])
                r1.write(row['Lote']); r2.write(row['Matrícula']); r3.write(row['Nome'])
                
                btn_col1, btn_col2 = r4.columns(2)
                
                if btn_col1.button("📝", key=f"edit_{row['index']}"):
                    st.session_state.editando_index = int(row['index'])
                    st.session_state.dados_edicao = row.fillna("").to_dict()
                    st.rerun()
                
                if btn_col2.button("🗑️", key=f"del_{row['index']}"):
                    df.drop(int(row['index'])).to_csv(nome_csv, index=False, encoding="utf-8-sig")
                    if st.session_state.editando_index == int(row['index']):
                        st.session_state.editando_index = None
                        st.session_state.dados_edicao = {}
                    st.rerun()

# --- 5. TELA DE PESQUISA ---
elif st.session_state.pagina == 'pesquisar':
    st.title("🔍 Pesquisar Ocupantes")
    termo = st.text_input("Pesquisar por Nome ou CPF", placeholder="Digite o nome ou CPF...")
    
    csvs = listar_csvs()
    if not csvs:
        st.info("Nenhum dado cadastrado para pesquisa.")
    elif termo:
        resultados = []
        for csv in csvs:
            df_temp = pd.read_csv(csv, dtype=str)
            
            nome_limpo = csv.replace('proprietarios_', '').replace('.csv', '')
            nome_limpo = re.sub(r'_crf_.*', '', nome_limpo)
            df_temp['Núcleo'] = nome_limpo.replace('_', ' ').title()
            
            filtro = df_temp['Nome'].str.contains(termo, case=False, na=False) | df_temp['CPF'].str.contains(termo, na=False)
            resultados.append(df_temp[filtro])
        
        if resultados:
            df_final = pd.concat(resultados)
            if not df_final.empty:
                st.write(f"Foram encontrados {len(df_final)} registros:")
                st.dataframe(df_final[["Núcleo", "Quadra", "Lote", "Nome", "CPF", "Matrícula"]], use_container_width=True)
            else:
                st.warning("Nenhum registro encontrado com esse termo.")

# --- 6. TELA DE RELATÓRIOS ---
elif st.session_state.pagina == 'relatorios':
    st.title("📊 Relatórios e Documentos")
    st.subheader("📄 Gerar Certidão de Regularização (Projeto)")
    arquivos_projetos = listar_projetos()

    if arquivos_projetos:
        nomes_projetos = {}
        for arq in arquivos_projetos:
            with open(arq, "r", encoding="utf-8") as f:
                d = json.load(f)
                label = f"{d['nome']} (CRF: {d.get('num_crf','')} / {d.get('ano_crf','')})" if d.get('num_crf') else d['nome']
                nomes_projetos[label] = (d, arq)

        projeto_selecionado_nome = st.selectbox("Selecione o Núcleo para gerar a Certidão:", options=list(nomes_projetos.keys()))
        
        data_emissao = st.date_input(
            "Selecione a data de emissão da Certidão:", 
            value=datetime.today().date(),
            format="DD/MM/YYYY"
        )
        
        if st.button("Gerar PDF Completo (Projeto + Fichas)"):
            dados_p, arq_json = nomes_projetos[projeto_selecionado_nome]
            nome_csv = arq_json.replace('projeto_', 'proprietarios_').replace('.json', '.csv')
            
            if os.path.exists(nome_csv):
                df_cadastrados = pd.read_csv(nome_csv, dtype=str)
            else:
                df_cadastrados = None
            
            try:
                pdf_output = gerar_pdf_projeto(dados_p, df_cadastrados, data_emissao)
                st.download_button(
                    label="⬇️ Baixar Certidão do Núcleo",
                    data=pdf_output,
                    file_name=f"Certidao_Nucleo_{dados_p['nome'].replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                st.success("PDF gerado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
    else:
        st.warning("Nenhum projeto encontrado para gerar certidão.")

# --- 7. TELA DE CERTIDÃO INDIVIDUAL ---
elif st.session_state.pagina == 'certidaoreurb':
    certidaoreurb.exibir_pagina_certidao()

# --- 8. TELA DE AUTORIZAÇÃO ---
elif st.session_state.pagina == 'autorizacao':
    autorizacao.exibir_pagina()

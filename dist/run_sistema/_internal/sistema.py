import streamlit as st
import base64
import json
import os
import pandas as pd
import shutil
from datetime import datetime

# ADICIONE ESTAS DUAS LINHAS AQUI:
import re
from validate_docbr import CPF

# Importações dos seus arquivos e funções internas
import autorizacao  
from gerar_certidao import gerar_pdf_projeto

# --- 1. FUNÇÃO DE BACKUP AUTOMÁTICO ---
def realizar_backup():
    # Arquivos que serão protegidos
    arquivos_para_backup = ["dados_autorizacoes.csv", "proprietarios_setor_britizinho.csv"]
    
    if not os.path.exists("backups"):
        os.makedirs("backups")
    
    agora = datetime.now()
    data_hoje = agora.strftime("%Y-%m-%d")
    hora_atual = agora.strftime("%H-%M-%S")
    
    for arquivo_original in arquivos_para_backup:
        if os.path.exists(arquivo_original):
            # Procura backups desse arquivo feitos HOJE
            arquivos_na_pasta = os.listdir("backups")
            backups_de_hoje = sorted([
                os.path.join("backups", f) for f in arquivos_na_pasta 
                if f.startswith(f"backup_{data_hoje}") and arquivo_original in f
            ])
            
            # Se já tem 3, apaga o mais antigo do dia antes de criar o novo
            if len(backups_de_hoje) >= 3:
                try:
                    os.remove(backups_de_hoje[0])
                except:
                    pass
            
            # Cria o novo backup (sempre terá no máximo 3 por dia)
            nome_backup = f"backups/backup_{data_hoje}_{hora_atual}_{arquivo_original}"
            shutil.copy2(arquivo_original, nome_backup)

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="REURB - Taguatinga-TO", layout="wide")

# Inicialização do estado de autenticação
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- 3. TELA DE LOGIN ---
def tela_login():
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        with st.container(border=True):
            try:
                # Carregamento da logo para o cabeçalho do login
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
                # Senha padrão definida por você
                if senha == "lele4619":
                    # REALIZA O BACKUP NO MOMENTO DO ACESSO
                    realizar_backup() 
                    
                    # SALVA O NOME DE QUEM LOGOU
                    st.session_state.usuario_logado = usuario
                    
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Senha incorreta. Tente novamente.")

# --- 4. EXECUÇÃO DA LÓGICA DE ACESSO ---
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

# --- SIDEBAR ---
# --- SIDEBAR ---
# Pega o nome salvo ou usa "Usuário" caso algo falhe
nome_usuario = st.session_state.get('usuario_logado', 'Usuário')

st.sidebar.markdown(f"👋 **Olá, {nome_usuario}!**")
st.sidebar.caption("Bem-vindo(a) ao painel de controle.")
st.sidebar.divider()

st.sidebar.title("MENU REURB")
if   st.sidebar.button("🏠 Início"):
    st.session_state.pagina = 'inicio'
    st.session_state.projeto_ativo = None
    st.session_state.quadra_selecionada = None
    st.rerun()

if st.sidebar.button("➕ Novo Núcleo"):
    st.session_state.pagina = 'cadastro_nucleo'
    st.session_state.projeto_ativo = None
    st.rerun()

if st.sidebar.button("🔍 Pesquisar"):
    st.session_state.pagina = 'pesquisar'
    st.rerun()

if st.sidebar.button("📊 Relatórios"):
    st.session_state.pagina = 'relatorios'
    st.rerun()

if st.sidebar.button("📄 Autorização"):
    st.session_state.pagina = 'autorizacao'
    st.rerun()

st.sidebar.divider()
# --- SIDEBAR ---
# ... (mantenha os botões que já existem) ...

if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state.autenticado = False
    st.rerun()

# ADICIONE AQUI:
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
                    st.write(f"**Local:** {dados['local']}")
                    if st.button(f"Abrir Detalhes", key=f"abrir_{arq}"):
                        st.session_state.projeto_ativo = dados
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
                nome_json = f"projeto_{p['nome'].replace(' ', '_').lower()}.json"
                nome_csv = f"proprietarios_{p['nome'].replace(' ', '_').lower()}.csv"
                if os.path.exists(nome_json): os.remove(nome_json)
                if os.path.exists(nome_csv): os.remove(nome_csv)
                st.session_state.pagina = 'inicio'
                st.session_state.projeto_ativo = None
                st.rerun()

    with st.form("form_n"):
        c1, c2 = st.columns(2)
        nome_n = c1.text_input("Nome do Núcleo", value=p.get('nome', ''))
        local = c1.text_input("Localização", value=p.get('local', ''))
        mod = c1.selectbox("Modalidade", ["Reurb-S (Social)", "Reurb-E (Específica)"], index=0 if p.get('modalidade') == "Reurb-S (Social)" else 1)
        area = c2.number_input("Área Total (m²)", format="%.2f", value=float(p.get('area_total', 0.0)))
        ruas = c2.number_input("Qtd Ruas", step=1, value=int(p.get('ruas', 0)))
        viario = c2.number_input("Área Viária (m²)", format="%.2f", value=float(p.get('area_viaria', 0.0)))
        
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
            novo_p = {"nome": nome_n, "local": local, "modalidade": mod, "area_total": area, "ruas": ruas, "area_viaria": viario, "quadras": lista_q}
            nome_arq = f"projeto_{nome_n.replace(' ', '_').lower()}.json"
            with open(nome_arq, "w", encoding="utf-8") as f:
                json.dump(novo_p, f, indent=4, ensure_ascii=False)
            st.session_state.pagina = 'inicio'
            st.rerun()

# --- 3. TELA DE DETALHES ---
elif st.session_state.pagina == 'detalhes_projeto':
    p = st.session_state.projeto_ativo
    st.title(f"📍 Núcleo: {p['nome']}")
    if st.button("📝 Editar Dados / Excluir"):
        st.session_state.pagina = 'cadastro_nucleo'
        st.rerun()
    with st.expander("📄 Dados Técnicos", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Modalidade:** {p['modalidade']}")
        c2.write(f"**Área Total:** {p['area_total']} m²")
        c3.write(f"**Área Viária:** {p['area_viaria']} m²")
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
    nome_csv = f"proprietarios_{p['nome'].replace(' ', '_').lower()}.csv"
    st.title(f"👤 Cadastro - Quadra {q_sel}")
    if st.button("⬅️ Voltar"):
        st.session_state.pagina = 'detalhes_projeto'
        st.rerun()
        
    with st.form("form_prop", clear_on_submit=False):
        st.subheader("Dados do Ocupante")
        c1, c2, c3 = st.columns(3)
        lote_n = c1.text_input("Lote Nº")
        matricula = c2.text_input("Matrícula")
        nome = c3.text_input("Nome Completo")
        
        est_civil = c1.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"])
        profissao = c2.text_input("Profissão")
        cpf = c3.text_input("CPF", placeholder="000.000.000-00")
        
        rg = c1.text_input("CI/RG", placeholder="0000000")
        ssp = c2.text_input("SSP/UF")
        endereco = c3.text_input("Endereço")
        
        bairro = c1.text_input("Bairro")
        cidade = c2.text_input("Cidade", value="Taguatinga")
        uf = c3.text_input("UF", value="TO")
        
        st.divider()
        st.subheader("Dados do Cônjuge / Herdeiro")
        hc1, hc2, hc3 = st.columns(3)
        h_nome = hc1.text_input("Nome (Cônjuge/Herdeiro)")
        h_est_civil = hc2.selectbox("Estado Civil (Cônjuge/Herdeiro)", ["N/A", "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"])
        h_profissao = hc3.text_input("Profissão (Cônjuge/Herdeiro)")
        
        h_rg = hc1.text_input("CI/RG (Cônjuge/Herdeiro)", placeholder="0000000")
        h_ssp_uf = hc2.text_input("SSP/UF (Cônjuge/Herdeiro)")
        h_cpf = hc3.text_input("CPF (Cônjuge/Herdeiro)", placeholder="000.000.000-00")
        
        if st.form_submit_button("Salvar Cadastro"):
            validador = CPF()
            
            # --- PREPARAÇÃO DOS DADOS (LIMPEZA) ---
            # Titular
            cpf_limpo = re.sub(r'\D', '', cpf)
            rg_numeros = re.sub(r'[.-]', '', rg)
            
            # Cônjuge
            h_cpf_limpo = re.sub(r'\D', '', h_cpf)
            h_rg_numeros = re.sub(r'[.-]', '', h_rg)
            
            # Verificadores de letras (para barrar texto onde deve ser número)
            # Removemos pontos e traços para checar se o que sobrou é apenas dígito
            cpf_so_numeros = re.sub(r'[.-]', '', cpf)
            h_cpf_so_numeros = re.sub(r'[.-]', '', h_cpf)

            erro = False
            
            # --- VALIDAÇÃO TITULAR ---
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
            
            # --- VALIDAÇÃO CÔNJUGE (SÓ SE PREENCHIDO) ---
            if not erro:
                # Valida se tem letras no CPF do cônjuge
                if h_cpf_so_numeros != "" and not h_cpf_so_numeros.isdigit():
                    st.error("❌ CPF do Cônjuge/Herdeiro não pode conter letras.")
                    erro = True
                # Valida se o CPF é matematicamente real
                elif h_cpf_limpo != "" and not validador.validate(h_cpf_limpo):
                    st.error("❌ CPF do Cônjuge/Herdeiro inválido.")
                    erro = True
                # Valida letras no RG do cônjuge
                elif h_rg_numeros != "" and not h_rg_numeros.isdigit():
                    st.error("❌ RG do Cônjuge/Herdeiro deve conter apenas números.")
                    erro = True

            # --- SALVAMENTO ---
            if not erro:
                colunas = ["Quadra", "Lote", "Matrícula", "Nome", "Estado Civil", "Profissão", "RG", "SSP", "CPF", 
                           "Endereço", "Bairro", "Cidade", "UF", 
                           "H_Nome", "H_Est_Civil", "H_Profissao", "H_RG", "H_SSP", "H_CPF"]
                
                dados_linha = [str(q_sel), lote_n, matricula, nome, est_civil, profissao, rg.strip().upper(), ssp, cpf_limpo, 
                               endereco, bairro, cidade, uf, 
                               h_nome, h_est_civil, h_profissao, h_rg.strip().upper(), h_ssp_uf, h_cpf_limpo]
                
                novo_dado = pd.DataFrame([dados_linha], columns=colunas)
                
                if not os.path.exists(nome_csv):
                    novo_dado.to_csv(nome_csv, index=False, encoding="utf-8-sig")
                else:
                    novo_dado.to_csv(nome_csv, mode='a', header=False, index=False, encoding="utf-8-sig")
                
                st.success(f"✅ Lote {lote_n} salvo com sucesso!")
                st.rerun()
    
    if os.path.exists(nome_csv):
        df = pd.read_csv(nome_csv, dtype={'Quadra': str})
        df_q = df[df['Quadra'] == str(q_sel)].reset_index()
        if not df_q.empty:
            st.subheader(f"📋 Lista de Ocupantes - Quadra {q_sel}")
            h1, h2, h3, h4 = st.columns([1, 2, 4, 2])
            h1.write("**Lote**"); h2.write("**Matrícula**"); h3.write("**Nome**"); h4.write("**Ações**")
            for index, row in df_q.iterrows():
                r1, r2, r3, r4 = st.columns([1, 2, 4, 2])
                r1.write(row['Lote']); r2.write(row['Matrícula']); r3.write(row['Nome'])
                if r4.button("🗑️", key=f"del_{row['index']}"):
                    df.drop(row['index']).to_csv(nome_csv, index=False, encoding="utf-8-sig")
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
            # Adiciona o nome do núcleo para saber de onde vem o dado
            df_temp['Núcleo'] = csv.replace('proprietarios_', '').replace('.csv', '').replace('_', ' ').title()
            # Filtro
            filtro = df_temp['Nome'].str.contains(termo, case=False, na=False) | df_temp['CPF'].str.contains(termo, na=False)
            resultados.append(df_temp[filtro])
        
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
        # Criar uma lista de nomes amigáveis para o selectbox
        nomes_projetos = {}
        for arq in arquivos_projetos:
            with open(arq, "r", encoding="utf-8") as f:
                d = json.load(f)
                nomes_projetos[d['nome']] = d

        projeto_selecionado_nome = st.selectbox("Selecione o Núcleo para gerar a Certidão:", options=list(nomes_projetos.keys()))
        
        if st.button("Gerar PDF Completo (Projeto + Fichas)"):
            dados_p = nomes_projetos[projeto_selecionado_nome]
            
            # --- AJUSTE AQUI: Carregando os ocupantes do núcleo ---
            nome_csv = f"proprietarios_{dados_p['nome'].replace(' ', '_').lower()}.csv"
            
            if os.path.exists(nome_csv):
                df_cadastrados = pd.read_csv(nome_csv, dtype=str)
            else:
                df_cadastrados = None # Caso o núcleo não tenha ninguém cadastrado ainda
            
            # Chamada da função passando os dois parâmetros agora
            try:
                pdf_output = gerar_pdf_projeto(dados_p, df_cadastrados)
                
                st.download_button(
                    label="⬇️ Baixar Certidão do Núcleo",
                    data=pdf_output,
                    file_name=f"Certidao_Nucleo_{projeto_selecionado_nome.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                st.success("PDF gerado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
    else:
        st.warning("Nenhum projeto encontrado para gerar certidão.")
        # ... (abaixo da parte da tela de relatórios)

# --- 7. TELA DE AUTORIZAÇÃO (Adicione aqui) ---
elif st.session_state.pagina == 'autorizacao':
    autorizacao.exibir_pagina()
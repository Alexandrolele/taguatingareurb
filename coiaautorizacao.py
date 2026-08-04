import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# Nome do arquivo de banco de dados
DB_AUTORIZACAO = "dados_autorizacoes.csv"

def gerar_pdf_autorizacao_fpdf(dados):
    """Gera o documento PDF formatado com tratamento para campos vazios."""
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_margins(25, 25, 25)
    
    # --- FUNÇÃO PARA TRATAR DADOS NULOS ---
    def f(campo, transform=None):
        texto = str(campo) if pd.notna(campo) and str(campo).lower() != 'nan' else ""
        if transform == "lower": return texto.lower()
        if transform == "upper": return texto.upper()
        return texto

    def limpar_texto(txt):
        if not txt: return ""
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

    # --- INSERÇÃO DA LOGO ---
    try:
        if os.path.exists("logo_prefeitura.png"):
            pdf.image("logo_prefeitura.png", x=90, y=10, w=30)
            pdf.ln(25)
        else:
            pdf.ln(10)
    except:
        pdf.ln(10)

    # --- CABEÇALHO ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 7, "ESTADO DO TOCANTINS", ln=True, align='C')
    pdf.cell(0, 7, "PREFEITURA MUNICIPAL DE TAGUATINGA", ln=True, align='C')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 7, "DEPARTAMENTO DE REGULARIZAÇÃO FUNDIÁRIA", ln=True, align='C')
    pdf.cell(0, 5, '"O PROGRESSO CONTINUA!"', ln=True, align='C')
    pdf.ln(10)
    
    # --- TÍTULO ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "AUTORIZAÇÃO PARA TITULAÇÃO DE IMÓVEL URBANO", ln=True, align='C')
    pdf.ln(8)
    
    # --- CORPO DO TEXTO ---
    pdf.set_font("Arial", '', 11)
    
    p1 = limpar_texto(
        f"A PREFEITURA MUNICIPAL DE TAGUATINGA, Estado do Tocantins, por meio do Departamento de "
        f"Regularização Fundiária, no uso de suas atribuições legais, AUTORIZA a emissão de título definitivo em favor de "
        f"{f(dados['Nome'], 'upper')}, nacionalidade {f(dados['Nacionalidade'], 'lower')}, {f(dados['Estado Civil'], 'lower')}, "
        f"{f(dados['Profissao'], 'lower')}, inscrito(a) no CPF sob o nº {f(dados['CPF'])} e portador(a) do RG nº {f(dados['RG'])} "
        f"{f(dados['SSP'])}/{f(dados['UF_RG'])}, residente e domiciliado(a) na {f(dados['End_Residencial'])}, "
        f"Bairro {f(dados['Bairro_Residencial'])}, em Taguatinga-TO."
    )
    
    pdf.multi_cell(0, 7, p1, align='J')
    pdf.ln(4)
    
    p2 = limpar_texto(
        f"O referido imóvel urbano consiste no LOTE Nº {f(dados['Lote'])}, da QUADRA Nº {f(dados['Quadra'])}, "
        f"localizado no Setor {f(dados['Setor'])}, na {f(dados['End_Lote'])}, nesta cidade de Taguatinga-TO, "
        f"apresentando uma ÁREA TOTAL de {f(dados['Area_Total'])} m² ({f(dados['Area_Extenso'])}), "
        f"conforme as confrontações e medidas descritas abaixo:"
    )
    
    pdf.multi_cell(0, 7, p2, align='J')
    pdf.ln(4)

    # --- LIMITES E CONFRONTAÇÕES ---
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 7, "LIMITES E CONFRONTAÇÕES:", ln=True)
    pdf.set_font("Arial", '', 11)
    
    pdf.cell(0, 7, limpar_texto(f"- FRENTE: {f(dados['Frente_Com'])}, medindo {f(dados['Frente_M'])} metros;"), ln=True)
    pdf.cell(0, 7, limpar_texto(f"- FUNDO: {f(dados['Fundo_Com'])}, medindo {f(dados['Fundo_M'])} metros;"), ln=True)
    pdf.cell(0, 7, limpar_texto(f"- LADO DIREITO: {f(dados['Dir_Com'])}, medindo {f(dados['Dir_M'])} metros;"), ln=True)
    pdf.cell(0, 7, limpar_texto(f"- LADO ESQUERDO: {f(dados['Esq_Com'])}, medindo {f(dados['Esq_M'])} metros;"), ln=True)
    
    # Adiciona o Chanfro se houver dados preenchidos
    if f(dados.get('Chanfro_Com')):
        pdf.cell(0, 7, limpar_texto(f"- CHANFRO: {f(dados['Chanfro_Com'])}, medindo {f(dados['Chanfro_M'])} metros;"), ln=True)
    
    pdf.ln(4)
    if 'Matricula' in dados and pd.notna(dados['Matricula']):
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 7, limpar_texto(f"Matrícula de Origem: {f(dados['Matricula'])}"), ln=True)
    
    # --- DATA E ASSINATURA ---
    pdf.ln(12)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    hoje = datetime.now()
    data_str = f"Taguatinga - TO, {hoje.day} de {meses[hoje.month-1]} de {hoje.year}."
    
    pdf.cell(0, 10, data_str, ln=True, align='R')
    pdf.ln(20)
    pdf.cell(0, 5, "________________________________________________________", ln=True, align='C')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "DIRETORIA DE REGULARIZAÇÃO FUNDIÁRIA", ln=True, align='C')
    pdf.cell(0, 5, "Prefeitura Municipal de Taguatinga-TO", ln=True, align='C')

    return pdf.output(dest='S').encode('latin-1')

def salvar_registro(*args):
    colunas = ["Nome", "Nacionalidade", "Estado Civil", "Profissao", "RG", "SSP", "UF_RG", "CPF", 
               "End_Residencial", "Bairro_Residencial", "Lote", "Quadra", "End_Lote", "Setor",
               "Frente_Com", "Frente_M", "Fundo_Com", "Fundo_M", "Dir_Com", "Dir_M", "Esq_Com", "Esq_M",
               "Area_Total", "Area_Extenso", "Matricula", "Chanfro_Com", "Chanfro_M"]
    novo_df = pd.DataFrame([args], columns=colunas)
    if os.path.exists(DB_AUTORIZACAO):
        df_ex = pd.read_csv(DB_AUTORIZACAO, dtype=str)
        df_ex = df_ex[df_ex['CPF'] != args[7]] 
        df_final = pd.concat([df_ex, novo_df], ignore_index=True)
    else:
        df_final = novo_df
    df_final.to_csv(DB_AUTORIZACAO, index=False, encoding="utf-8-sig")
    st.success("✅ Cadastro salvo!")
    st.session_state.editar_autorizacao = None
    st.rerun()

def formulario_autorizacao(dados_edicao=None):
    if dados_edicao is not None:
        st.warning(f"Modo Edição: {dados_edicao['Nome']}")
        if st.button("Cancelar Edição"):
            st.session_state.editar_autorizacao = None
            st.rerun()

    with st.form("form_autorizacao", clear_on_submit=True):
        st.subheader("👤 Dados do Requerente")
        col1, col2, col3 = st.columns([2, 1, 1])
        nome = col1.text_input("Nome Completo", value=dados_edicao['Nome'] if dados_edicao else "")
        nacionalidade = col2.text_input("Nacionalidade", value=dados_edicao['Nacionalidade'] if dados_edicao else "Brasileiro")
        
        opcoes_civil = ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"]
        idx_civil = 0
        if dados_edicao and dados_edicao['Estado Civil'] in opcoes_civil:
            idx_civil = opcoes_civil.index(dados_edicao['Estado Civil'])
        estado_civil = col3.selectbox("Estado Civil", opcoes_civil, index=idx_civil)

        c1, c2, c3, c4 = st.columns([1.5, 1, 0.5, 1.5])
        profissao = c1.text_input("Profissão", value=dados_edicao['Profissao'] if dados_edicao else "")
        rg = c2.text_input("CI/RG", value=dados_edicao['RG'] if dados_edicao else "")
        ssp = c3.text_input("SSP", value=dados_edicao['SSP'] if dados_edicao else "")
        uf_rg = c4.text_input("UF (RG)", value=dados_edicao['UF_RG'] if dados_edicao else "TO")
        
        col_cpf, col_end, col_bairro = st.columns([1.5, 2, 1])
        cpf = col_cpf.text_input("CPF", value=dados_edicao['CPF'] if dados_edicao else "")
        endereco_res = col_end.text_input("Endereço Residencial", value=dados_edicao['End_Residencial'] if dados_edicao else "")
        bairro_res = col_bairro.text_input("Bairro", value=dados_edicao['Bairro_Residencial'] if dados_edicao else "")

        st.divider()
        st.subheader("🏘️ Dados do Lote Urbano")
        l1, l2, l3, l4 = st.columns([1, 1, 2, 1])
        lote_num = l1.text_input("Lote Nº", value=dados_edicao['Lote'] if dados_edicao else "")
        quadra_num = l2.text_input("Quadra", value=dados_edicao['Quadra'] if dados_edicao else "")
        endereco_lote = l3.text_input("Endereço do Lote", value=dados_edicao['End_Lote'] if dados_edicao else "")
        setor_lote = l4.text_input("Setor", value=dados_edicao['Setor'] if dados_edicao else "")

        st.divider()
        st.subheader("📏 Confrontações e Dimensões")
        conf1, conf2 = st.columns(2)
        with conf1:
            frente = st.text_input("Frente com", value=dados_edicao['Frente_Com'] if dados_edicao else "")
            frente_m = st.text_input("Medida Frente (m)", value=dados_edicao['Frente_M'] if dados_edicao else "")
            dir_conf = st.text_input("Lado Direito com", value=dados_edicao['Dir_Com'] if dados_edicao else "")
            dir_m = st.text_input("Medida Lado Direito (m)", value=dados_edicao['Dir_M'] if dados_edicao else "")
        with conf2:
            fundo = st.text_input("Fundo com", value=dados_edicao['Fundo_Com'] if dados_edicao else "")
            fundo_m = st.text_input("Medida Fundo (m)", value=dados_edicao['Fundo_M'] if dados_edicao else "")
            esq_conf = st.text_input("Lado Esquerdo com", value=dados_edicao['Esq_Com'] if dados_edicao else "")
            esq_m = st.text_input("Medida Lado Esquerdo (m)", value=dados_edicao['Esq_M'] if dados_edicao else "")
        
        # --- NOVO CAMPO DE CHANFRO ---
        st.write("**Opcional (Esquinas):**")
        ch1, ch2 = st.columns(2)
        chanfro_com = ch1.text_input("Chanfro com", value=dados_edicao['Chanfro_Com'] if dados_edicao and 'Chanfro_Com' in dados_edicao else "")
        chanfro_m = ch2.text_input("Medida Chanfro (m)", value=dados_edicao['Chanfro_M'] if dados_edicao and 'Chanfro_M' in dados_edicao else "")

        st.write("---")
        area_total = st.text_input("Área Total (m²)", value=dados_edicao['Area_Total'] if dados_edicao else "")
        area_extenso = st.text_area("Área Total por Extenso", value=dados_edicao['Area_Extenso'] if dados_edicao else "")
        matricula = st.text_input("Nº Matrícula", value=dados_edicao['Matricula'] if dados_edicao else "")

        if st.form_submit_button("💾 Salvar Cadastro", use_container_width=True):
            salvar_registro(nome, nacionalidade, estado_civil, profissao, rg, ssp, uf_rg, cpf, 
                           endereco_res, bairro_res, lote_num, quadra_num, endereco_lote, setor_lote,
                           frente, frente_m, fundo, fundo_m, dir_conf, dir_m, esq_conf, esq_m,
                           area_total, area_extenso, matricula, chanfro_com, chanfro_m)

def lista_e_gestao():
    if not os.path.exists(DB_AUTORIZACAO):
        st.info("Nenhum cadastro encontrado.")
        return
    df = pd.read_csv(DB_AUTORIZACAO, dtype=str)
    busca = st.text_input("🔍 Pesquisar por Nome ou CPF")
    if busca:
        df = df[df['Nome'].str.contains(busca, case=False, na=False) | df['CPF'].str.contains(busca, na=False)]

    for idx, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2.5, 0.8, 0.8, 1.2])
            c1.write(f"👤 **{row['Nome']}** | CPF: {row['CPF']}")
            c1.write(f"📍 Lote: {row['Lote']} Q: {row['Quadra']} - {row['Setor']}")
            
            if c2.button("📝 Editar", key=f"edit_{idx}"):
                st.session_state.editar_autorizacao = row.to_dict()
                st.rerun()
            
            if c3.button("🗑️", key=f"del_{idx}"):
                df_temp = pd.read_csv(DB_AUTORIZACAO, dtype=str)
                df_temp = df_temp[df_temp['CPF'] != row['CPF']]
                df_temp.to_csv(DB_AUTORIZACAO, index=False, encoding="utf-8-sig")
                st.rerun()

            pdf_bytes = gerar_pdf_autorizacao_fpdf(row)
            c4.download_button(
                label="📄 Emitir PDF",
                data=pdf_bytes,
                file_name=f"Autorizacao_{str(row['Nome']).replace(' ', '_')}.pdf",
                mime="application/pdf",
                key=f"pdf_{idx}"
            )

def exibir_pagina():
    st.title("📄 Sistema de Autorização de Titulação")
    tab1, tab2 = st.tabs(["📝 Novo Cadastro / Edição", "🔍 Consultar e Gerenciar"])
    with tab1:
        dados_ed = st.session_state.get('editar_autorizacao', None)
        formulario_autorizacao(dados_ed)
    with tab2:
        lista_e_gestao()

if __name__ == "__main__":
    exibir_pagina()
import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
from validate_docbr import CPF
import re

# Nome do arquivo de banco de dados
DB_AUTORIZACAO = "dados_autor_titulos.csv"

def gerar_pdf_autorizacao_fpdf(dados):
    """Gera o Título de Permissão com cabeçalho centralizado e tabela à direita."""
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    
    # --- FUNÇÕES DE APOIO ---
    def f(campo, transform=None):
        texto = str(campo) if pd.notna(campo) and str(campo).lower() != 'nan' else ""
        if transform == "lower": return texto.lower()
        if transform == "upper": return texto.upper()
        return texto

    def limpar(txt):
        if not txt: return ""
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

    # --- CABEÇALHO CENTRALIZADO ---
    pdf.set_y(12) 
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 6, limpar(""), ln=True, align='C')
    pdf.cell(0, 6, limpar(""), ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, limpar(""), ln=True, align='C')
    pdf.ln(50) 

    # --- TABELA DE IDENTIFICAÇÃO (DIREITA) ---
    hoje = datetime.now()
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    data_curta = f"{hoje.day} de {meses[hoje.month-1]} de {hoje.year}"

    pdf.set_text_color(0, 0, 0) 
    pdf.set_font("Arial", 'B', 9)
    
    largura_tabela = 75
    x_inicial = 115 
    pdf.set_x(x_inicial)

    # Campos dinâmicos no cabeçalho do PDF
    titulo_num = f(dados.get('Titulo_Permissao'))
    livro_num = f(dados.get('Livro_Tombo'))
    folhas_num = f(dados.get('Fls'))

    pdf.cell(largura_tabela, 7, limpar(f"TÍTULO DE PERMISSÃO Nº {titulo_num}"), border=1, ln=True, align='C')
    
    pdf.set_x(x_inicial)
    pdf.cell(40, 7, limpar(f"LIVRO TOMBO Nº {livro_num}"), border=1, align='C') 
    pdf.cell(35, 7, limpar(f"FLS. {folhas_num}"), border=1, ln=True, align='C')    
    
    pdf.set_x(x_inicial)
    pdf.cell(largura_tabela, 7, limpar(f"TAGUATINGA - TO, {data_curta}"), border=1, ln=True, align='C')
    
    pdf.ln(10) 

    # --- TÍTULO JURÍDICO ---
    pdf.set_font("Arial", 'B', 10)
    pdf.set_left_margin(100) 
    
    titulo_texto = (
        f"TÍTULO DE PERMISSÃO PARA REGISTRO E TRANSFERÊNCIA DE DOMÍNIO QUE O MUNICÍPIO DE TAGUATINGA - TO "
        f"OUTORGA À PESSOA CONTEMPLADA ABAIXO IDENTIFICADA, CONFORME AUTORIZAÇÃO DO DECRETO N.º 244/2025."
    )
    
    pdf.multi_cell(0, 5, limpar(titulo_texto), border=0, align='J')
    pdf.set_left_margin(20) 
    pdf.ln(8)

    # --- CORPO DO TEXTO JURÍDICO ---
    pdf.set_font("Arial", '', 10)
    
    chanfro_txt = f", chanfro com {f(dados.get('Chanfro_Com'))}, medindo {f(dados.get('Chanfro_M'))} metros" if f(dados.get('Chanfro_Com')) else ""

    texto_corpo = (
        f"MUNICIPIO DE TAGUATINGA-TO, pessoa jurídica de direito público interno, inscrita no CNPJ/MF sob a n° 02.306.900/0001-97 "
        f"com sede administrativa sito à Avenida Airosa de Sousa Godinho, Quadra 10, Lote 11, s/nº Setor Bom Jesus Taguatinga TO, "
        f"neste ato representado pelo Prefeito Municipal PAULO ROBERTO RIBEIRO, brasileiro, casado, empresário, portador da CI/RG nº 446.212 SDGPC-GO "
        f"e do CPF/MF nº 088.124.461-91, residente e domiciliado em Taguatinga TO, a presente permissão é realizada com amparo no Processo Administrativo "
        f"em epígrafe e em estrita consonância com as disposições do Decreto nº 244 de 10 de dezembro de 2025, de imóveis urbanos a partir de 80m², "
        f"após detida análise dos documentos e provas juntadas pelo o Outorgado, a posse deste Título concede a plena autorização para a lavratura da "
        f"competente Escritura Pública de Compra e Venda perante o Cartório de Notas e seu posterior e obrigatório registro junto ao Cartório de Registro "
        f"de Imóveis. O procedimento de regularização será integralmente concluído após o recolhimento do Imposto sobre a Transmissão de Bens Imóveis (ITBI), "
        f"ônus que será assumido por esta Municipalidade, concernente ao LOTE URBANO n.º {f(dados['Lote'])}, Quadra: {f(dados['Quadra'])}, "
        f"endereço do lote {f(dados['End_Lote'])}, Setor {f(dados['Setor'])}. Dentro dos seguintes limites e confrontações: "
        f"frente para a {f(dados['Frente_Com'])}, com medida de {f(dados['Frente_M'])} metros; fundos com o {f(dados['Fundo_Com'])}, "
        f"com {f(dados['Fundo_M'])} metros; lado direito com o {f(dados['Dir_Com'])}, com {f(dados['Dir_M'])} metros e lado esquerdo "
        f"com o {f(dados['Esq_Com'])}, com {f(dados['Esq_M'])} metros{chanfro_txt}, com área total de {f(dados['Area_Total'])}m², ({f(dados['Area_Extenso'])}), "
        f"conforme memorial descritivo, Taguatinga/TO, ao (à) detentor (a), {f(dados['Nome'], 'upper')}, brasileiro(a), "
        f"estado civil {f(dados['Estado Civil'], 'lower')}, profissão {f(dados['Profissao'], 'lower')}, portador(a) do CPF N º {f(dados['CPF'])}, "
        f"residente na {f(dados['End_Residencial'])}, e setor {f(dados['Bairro_Residencial'])}. "
        f"O Município de Taguatinga TO, aqui designado OUTORGANTE, é legitimo titular do domínio do imóvel público municipal, conforme Título Definitivo "
        f"de Domínio nº 109/2014, lavrado no livra 85/2014, na folha 009 e expedido em Palmas TO, no dia 14/05/2014, pelo ITERTINS Instituto de Terras "
        f"do Estado do Tocantins, registrado no Cartório de Registro de Imóveis e Tabelionato 1º de Notas da Comarca de Taguatinga TO, sob a Matricula nº 2869, "
        f"Livro 2-RGR-01 em 23/07/2014, posteriormente desmembrado para a {f(dados['Lei_Aplicada'])}, em ato contínuo desmembrado referido lote "
        f"para a MATRÍCULA nº {f(dados['Matricula'])}, recebido pela OURTOGANTE, conforme estabelecido no parágrafo 3º, do artigo 1º, da Lei Municipal n°438/2014. "
        f"Certifica e da fé que foram cumpridas as exigências legais que capacitam e autorizam a ilustríssima senhora Oficiala de Registro de Imóveis que "
        f"transfira a propriedade da matricula que foi aberta no livro Geral de Reg. de Imóveis dessa Comarca. Pelo presente, o OUTORGANTE, na qualidade "
        f"de legítimo titular do domínio, transfere e cede ao OUTORGADO todo o domínio, ações, direitos, jus e posse que até então exercia sobre o aludido imóvel, "
        f"passando o OUTORGADO a consolidar e exercer o pleno DIREITO DE PROPRIEDADE sobre o lote em questão. O OUTORGADO declara aceitar o presente Título "
        f"Definitivo de Domínio em todos os seus termos, cláusulas e condições. O presente Título é emitido em estrita observância ao Decreto nº 244/2025, "
        f"que autoriza a transferência do domínio do imóvel, devidamente comprovada a titularidade do OUTORGANTE conforme a Matrícula n.º {f(dados['Matricula'])}. "
        f"O ato finaliza o Processo Administrativo n.º 01/2024 e habilita o registro imediato do pleno Direito de Propriedade em nome do OUTORGADO perante "
        f"o Cartório de Registro de Imóveis. E por estarem justos, contratados e de pleno acordo com todas as condições estabelecidas, as partes firmam "
        f"o presente Título de Domínio em 02 (duas) vias de igual teor e forma, que será devidamente assinado por elas e por 02 (duas) testemunhas."
    )

    pdf.multi_cell(0, 5, limpar(texto_corpo), align='J')
    pdf.ln(10)

    pdf.set_font("Arial", 'I', 10)
    data_final = f"Taguatinga-TO, {hoje.day} de {meses[hoje.month-1]} de {hoje.year}."
    pdf.cell(0, 10, limpar(data_final), ln=True, align='R')
    pdf.ln(15)

    # --- ASSINATURAS ---
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "__________________________________________", ln=True, align='C')
    pdf.cell(0, 5, limpar("PAULO ROBERTO RIBEIRO"), ln=True, align='C')
    pdf.set_font("Arial", '', 8)
    pdf.cell(0, 4, limpar("Prefeito Municipal"), ln=True, align='C')
    pdf.ln(8)

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "__________________________________________", ln=True, align='C')
    pdf.cell(0, 5, limpar("LUAN AIRES RIBEIRO"), ln=True, align='C')
    pdf.set_font("Arial", '', 8)
    pdf.cell(0, 4, limpar("Secretário de Regularização Fundiária"), ln=True, align='C')
    pdf.ln(8)

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "__________________________________________", ln=True, align='C')
    pdf.cell(0, 5, limpar(f(dados['Nome'], 'upper')), ln=True, align='C')
    pdf.set_font("Arial", '', 8)
    pdf.cell(0, 4, limpar("Outorgado Adquirente"), ln=True, align='C')

    return pdf.output(dest='S').encode('latin-1')

def salvar_registro(*args):
    colunas = ["Nome", "Nacionalidade", "Estado Civil", "Profissao", "RG", "SSP", "UF_RG", "CPF", 
               "End_Residencial", "Bairro_Residencial", "Lote", "Quadra", "End_Lote", "Setor",
               "Frente_Com", "Frente_M", "Fundo_Com", "Fundo_M", "Dir_Com", "Dir_M", "Esq_Com", "Esq_M",
               "Area_Total", "Area_Extenso", "Matricula", "Lei_Aplicada", "Chanfro_Com", "Chanfro_M",
               "Titulo_Permissao", "Livro_Tombo", "Fls"] # Novas colunas adicionadas
    
    novo_df = pd.DataFrame([args], columns=colunas)
    
    if os.path.exists(DB_AUTORIZACAO):
        df_ex = pd.read_csv(DB_AUTORIZACAO, dtype=str)
        df_ex = df_ex[df_ex['CPF'] != args[7]] 
        df_final = pd.concat([df_ex, novo_df], ignore_index=True)
    else:
        df_final = novo_df
        
    df_final.to_csv(DB_AUTORIZACAO, index=False, encoding="utf-8-sig")
    st.success("✅ Dados salvos com sucesso!")
    
    st.session_state.editar_autorizacao = None
    st.rerun()

def formulario_autorizacao(dados_edicao=None):
    if dados_edicao is not None:
        st.warning(f"📝 Editando: {dados_edicao['Nome']}")
        if st.button("❌ Cancelar"):
            st.session_state.editar_autorizacao = None
            st.rerun()

    with st.form("form_autorizacao", clear_on_submit=False):
        st.subheader("👤 Requerente")
        col1, col2, col3 = st.columns([2, 1, 1])
        nome = col1.text_input("Nome", value=dados_edicao['Nome'] if dados_edicao else "")
        nacionalidade = col2.text_input("Nacionalidade", value=dados_edicao['Nacionalidade'] if dados_edicao else "Brasileiro")
        estado_civil = col3.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"])

        c1, c2, c3, c4 = st.columns([1.5, 1, 0.5, 1.5])
        profissao = c1.text_input("Profissão", value=dados_edicao['Profissao'] if dados_edicao else "")
        rg = c2.text_input("RG", value=dados_edicao['RG'] if dados_edicao else "", placeholder="Apenas números")
        ssp = c3.text_input("SSP", value=dados_edicao['SSP'] if dados_edicao else "")
        uf_rg = c4.text_input("UF", value=dados_edicao['UF_RG'] if dados_edicao else "TO")
        
        col_cpf, col_end, col_bairro = st.columns([1.5, 2, 1])
        cpf = col_cpf.text_input("CPF", value=dados_edicao['CPF'] if dados_edicao else "", placeholder="000.000.000-00")
        endereco_res = col_end.text_input("Endereço", value=dados_edicao['End_Residencial'] if dados_edicao else "")
        bairro_res = col_bairro.text_input("Bairro", value=dados_edicao['Bairro_Residencial'] if dados_edicao else "")

        st.divider()
        st.subheader("🏘️ Lote")
        l1, l2, l3, l4 = st.columns([1, 1, 2, 1])
        lote_num = l1.text_input("Lote Nº", value=dados_edicao['Lote'] if dados_edicao else "")
        quadra_num = l2.text_input("Quadra", value=dados_edicao['Quadra'] if dados_edicao else "")
        end_lote = l3.text_input("Endereço do Lote", value=dados_edicao['End_Lote'] if dados_edicao else "")
        setor = l4.text_input("Setor", value=dados_edicao['Setor'] if dados_edicao else "")

        st.divider()
        st.subheader("📏 Confrontações")
        f1, f2 = st.columns(2)
        frente_c = f1.text_input("Frente com", value=dados_edicao['Frente_Com'] if dados_edicao else "")
        frente_m = f2.text_input("Frente (m)", value=dados_edicao['Frente_M'] if dados_edicao else "")
        f3, f4 = st.columns(2)
        fundo_c = f3.text_input("Fundo com", value=dados_edicao['Fundo_Com'] if dados_edicao else "")
        fundo_m = f4.text_input("Fundo (m)", value=dados_edicao['Fundo_M'] if dados_edicao else "")
        f5, f6 = st.columns(2)
        dir_c = f5.text_input("Direita com", value=dados_edicao['Dir_Com'] if dados_edicao else "")
        dir_m = f6.text_input("Direita (m)", value=dados_edicao['Dir_M'] if dados_edicao else "")
        f7, f8 = st.columns(2)
        esq_c = f7.text_input("Esquerda com", value=dados_edicao['Esq_Com'] if dados_edicao else "")
        esq_m = f8.text_input("Esquerda (m)", value=dados_edicao['Esq_M'] if dados_edicao else "")
        
        st.write("**📐 Chanfro (Opcional)**")
        ch1, ch2 = st.columns(2)
        chan_c = ch1.text_input("Chanfro com", value=dados_edicao['Chanfro_Com'] if dados_edicao else "")
        chan_m = ch2.text_input("Chanfro (m)", value=dados_edicao['Chanfro_M'] if dados_edicao else "")

        st.write("---")
        area_t = st.text_input("Área Total", value=dados_edicao['Area_Total'] if dados_edicao else "")
        area_e = st.text_area("Área Extenso", value=dados_edicao['Area_Extenso'] if dados_edicao else "")
        
        col_mat, col_lei = st.columns(2)
        matr = col_mat.text_input("Matrícula", value=dados_edicao['Matricula'] if dados_edicao else "")
        
        opcoes_leis = [
            "MATRÍCULA nº 5.771 - Setor Norte 2° ETAPA",
            "MATRÍCULA nº 6.043 - Setor Buritizinho",
            "MATRÍCULA nº 3.752 - Setor Leste",
            "MATRÍCULA nº 4.244 - Setor Serra Azul",
            "MATRÍCULA nº 4.527 - Setor Bom Jesus",
            "MATRÍCULA nº 3.470 - Setor Vila Santa Maria Leste",
        ]
        lei_atual = dados_edicao['Lei_Aplicada'] if dados_edicao else ""
        lei_selecionada = col_lei.selectbox("Legislação Aplicável", options=opcoes_leis, index=opcoes_leis.index(lei_atual) if lei_atual in opcoes_leis else 0)

        # --- NOVOS CAMPOS ABAIXO DE MATRÍCULA E LEGISLAÇÃO ---
        st.subheader("📑 Informações do Título")
        nt1, nt2, nt3 = st.columns([1.5, 1.5, 1])
        titulo_permissao = nt1.text_input("TÍTULO DE PERMISSÃO Nº", value=dados_edicao['Titulo_Permissao'] if dados_edicao else "")
        livro_tombo = nt2.text_input("LIVRO TOMBO Nº", value=dados_edicao['Livro_Tombo'] if dados_edicao else "")
        fls = nt3.text_input("FLS.", value=dados_edicao['Fls'] if dados_edicao else "")

        if st.form_submit_button("💾 SALVAR"):
            cpf_limpo = re.sub(r'\D', '', cpf)
            rg_limpo = re.sub(r'[\s.-]', '', rg)
            validador_cpf = CPF()
            
            if not validador_cpf.validate(cpf_limpo):
                st.error("❌ CPF INVÁLIDO")
            elif not rg_limpo.isdigit():
                st.error("❌ RG INVÁLIDO: Digite apenas números.")
            else:
                salvar_registro(
                    nome, nacionalidade, estado_civil, profissao, rg.strip().upper(), ssp, uf_rg, cpf_limpo,
                    endereco_res, bairro_res, lote_num, quadra_num, end_lote, setor,
                    frente_c, frente_m, fundo_c, fundo_m, dir_c, dir_m, esq_c, esq_m,
                    area_t, area_e, 
                    matr, lei_selecionada, chan_c, chan_m,
                    titulo_permissao, livro_tombo, fls # Enviando os novos campos
                )

def lista_e_gestao():
    if not os.path.exists(DB_AUTORIZACAO):
        st.info("Nenhum dado cadastrado.")
        return
    df = pd.read_csv(DB_AUTORIZACAO, dtype=str)
    busca = st.text_input("🔍 Pesquisar")
    if busca:
        df = df[df['Nome'].str.contains(busca, case=False, na=False)]

    for idx, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2.5, 0.8, 0.8, 1.2])
            c1.write(f"👤 **{row['Nome']}**")
            if c2.button("📝", key=f"e_{idx}"):
                st.session_state.editar_autorizacao = row.to_dict()
                st.rerun()
            if c3.button("🗑️", key=f"d_{idx}"):
                df = df[df['CPF'] != row['CPF']]
                df.to_csv(DB_AUTORIZACAO, index=False)
                st.rerun()
            
            pdf_bytes = gerar_pdf_autorizacao_fpdf(row) 
            c4.download_button("📄 PDF", pdf_bytes, f"Titulo_{row['Nome']}.pdf", "application/pdf", key=f"p_{idx}")

def exibir_pagina():
    st.title("📄 Título de Permissão")
    t1, t2 = st.tabs(["Novo", "Gerenciar"])
    with t1: formulario_autorizacao(st.session_state.get('editar_autorizacao'))
    with t2: lista_e_gestao()

if __name__ == "__main__":
    exibir_pagina()
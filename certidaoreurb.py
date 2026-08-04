import streamlit as st
import pandas as pd
import json
import os
import io
import re
from datetime import datetime

# Importações do ReportLab para construir os PDFs
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

# --- FUNÇÃO DE AUXÍLIO PARA FORMATAR CPF ---
def formatar_cpf_display(valor):
    if not valor or str(valor).lower() in ['nan', 'none', 'n/a']: 
        return "N/A"
    
    # Remove decimais se veio de float (ex: 12345678901.0 -> 12345678901)
    val_str = str(valor).split('.')[0]
    
    # Remove tudo que não é número
    cpf_limpo = re.sub(r'\D', '', val_str)
    
    # Preenche com zeros à esquerda caso venha incompleto do Excel/CSV
    if 0 < len(cpf_limpo) < 11:
        cpf_limpo = cpf_limpo.zfill(11)
        
    if len(cpf_limpo) == 11:
        return f"{cpf_limpo[0:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}"
        
    return str(valor).strip()

# --- FUNÇÃO DE AUXÍLIO PARA TRATAR TEXTO E ENCODING ---
def limpar_texto(txt):
    if txt is None or str(txt).lower() in ['nan', 'none', 'n/a']: 
        return ""
    return str(txt).strip()

# --- FUNÇÃO GERADORA DE PDF ---
def construir_pdf_certidao(dados_projeto, moradores_df, data_emissao, morador_unico_row=None):
    """
    Gera o PDF das certidões ajustado para PAPEL TIMBRADO.
    - Se morador_unico_row for fornecido, gera APENAS a certidão dele (Segunda Via).
    - Se morador_unico_row for None, gera a certidão de todos com quebra de página (Coletiva).
    """
    buffer = io.BytesIO()
    
    # Ajuste de margens para papel timbrado oficial
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=50, leftMargin=50, 
        topMargin=140, bottomMargin=25
    )
    
    styles = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle(
        'TituloOficial', 
        parent=styles['Normal'], 
        fontSize=14, 
        leading=18, 
        alignment=TA_CENTER, 
        fontName='Helvetica-Bold'
    )
    
    estilo_corpo = ParagraphStyle(
        'CorpoTexto', 
        parent=styles['Normal'], 
        fontSize=11, 
        leading=15, 
        alignment=TA_JUSTIFY, 
        fontName='Helvetica'
    )
    
    estilo_assinatura = ParagraphStyle(
        'AssinaturaBloco', 
        parent=styles['Normal'], 
        fontSize=10, 
        leading=13, 
        alignment=TA_CENTER, 
        fontName='Helvetica'
    )

    story = []
    
    if morador_unico_row is not None:
        lista_moradores = [morador_unico_row]
    else:
        df_trabalho = moradores_df.copy()
        # Tenta ordenação numérica de Quadra/Lote com fallback para string
        df_trabalho['Quadra_Int'] = pd.to_numeric(df_trabalho['Quadra'], errors='coerce')
        df_trabalho['Lote_Int'] = pd.to_numeric(df_trabalho['Lote'], errors='coerce')
        df_ordenado = df_trabalho.sort_values(by=['Quadra_Int', 'Lote_Int', 'Quadra', 'Lote'])
        lista_moradores = [row for _, row in df_ordenado.iterrows()]

    total_registros = len(lista_moradores)
    nome_nucleo = limpar_texto(dados_projeto.get('nome', '')).upper()
    modalidade_projeto = limpar_texto(dados_projeto.get('modalidade', 'Reurb-S (Social)'))
    local_projeto = limpar_texto(dados_projeto.get('local', 'Taguatinga-TO'))
    
    meses = {
        'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
        'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
        'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
        'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
    }

    for idx, row in enumerate(lista_moradores):
        story.append(Paragraph("<b>CERTIDÃO DE REGULARIZAÇÃO FUNDIÁRIA INDIVIDUAL</b>", estilo_titulo))
        story.append(Paragraph(f"<b>INTEGRANTE DA CRF NÚCLEO: {nome_nucleo}</b>", estilo_titulo))
        story.append(Spacer(1, 20)) 
        
        m_nome = limpar_texto(row.get('Nome', 'N/A'))
        m_cpf = formatar_cpf_display(row.get('CPF', 'N/A'))
        m_rg = limpar_texto(row.get('RG', 'N/A'))
        m_ssp = limpar_texto(row.get('SSP', ''))
        m_est_civil = limpar_texto(row.get('Estado Civil', 'N/A'))
        m_profissao = limpar_texto(row.get('Profissão', 'N/A'))
        m_endereco = limpar_texto(row.get('Endereço', 'N/A'))
        m_bairro = limpar_texto(row.get('Bairro', 'N/A'))
        m_quadra = limpar_texto(row.get('Quadra', 'N/A'))
        m_lote = limpar_texto(row.get('Lote', 'N/A'))
        m_matricula = limpar_texto(row.get('Matrícula', 'N/A'))

        rg_completo = f"{m_rg} {m_ssp}".strip() if m_ssp else m_rg

        texto_formal = f"""
        O <b>MUNICÍPIO DE TAGUATINGA</b>, Estado do Tocantins, por meio de seu Departamento de Regularização Fundiária, no uso de suas atribuições legais e em conformidade com a Lei Federal nº 13.465/2017, <b>CERTIFICA</b> para os devidos fins de direito e registro cartorário que o imóvel abaixo caracterizado foi devidamente regularizado, integrando o projeto de Regularização Fundiária Urbana (REURB), na modalidade <b>{modalidade_projeto}</b>.
        <br/><br/>
        <b> 1 - QUALIFICAÇÃO DO(A) BENEFICIÁRIO(A) TITULAR:</b><br/>
        • <b>Nome Completo:</b> {m_nome}<br/>
        • <b>Inscrição no CPF/MF:</b> {m_cpf} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Cédula de Identidade (RG):</b> {rg_completo}<br/>
        • <b>Estado Civil:</b> {m_est_civil} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Profissão:</b> {m_profissao}<br/>
        • <b>Endereço:</b> {m_endereco}, Bairro: {m_bairro}, Taguatinga-TO.<br/><br/>
        <b> 2 - CARACTERÍSTICAS E LOCALIZAÇÃO DO IMÓVEL:</b><br/>
        • <b>Núcleo Urbano:</b> {nome_nucleo}<br/>
        • <b>Localização/Setor:</b> {local_projeto}<br/>
        • <b>Quadra:</b> {m_quadra} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Lote:</b> {m_lote}<br/>
        • <b>Matrícula Imobiliária Correspondente:</b> {m_matricula}<br/>
        """
        story.append(Paragraph(texto_formal, estilo_corpo))
        story.append(Spacer(1, 8)) 
        
        data_formatada = data_emissao.strftime('%d de %B de %Y')
        for eng, pt in meses.items():
            data_formatada = data_formatada.replace(eng, pt)
            
        texto_encerramento = f"""
        Por ser a expressão da verdade, firmo a presente certidão para que surta seus efeitos jurídicos e legais junto ao Cartório de Registro de Imóveis competente.
        <br/><br/>
        Taguatinga - TO, {data_formatada}.
        """ 
        story.append(Paragraph(texto_encerramento, estilo_corpo))
        story.append(Spacer(1, 35))
        
        # Bloco de Assinaturas
        p_prefeito = Paragraph("""
            __________________________________________________________<br/>
            <b>Paulo Roberto Ribeiro</b><br/>
            Prefeito Municipal de Taguatinga - TO
        """, estilo_assinatura)
        
        p_viceprefeita = Paragraph("""
            __________________________________________________________<br/>
            <b>Izabella Antunes de França</b><br/>
            Vice-Prefeita Municipal de Taguatinga - TO
        """, estilo_assinatura)

        p_secretario = Paragraph("""
            __________________________________________________________<br/>
            <b>Luan Aires Ribeiro</b><br/>
            Secretário Municipal de Regularização Fundiária
        """, estilo_assinatura)
        
        tabela_assinaturas = Table([
            [p_prefeito],
            [Spacer(1, 15)], 
            [p_viceprefeita],
            [Spacer(1, 15)],
            [p_secretario]
        ], colWidths=[512])
        
        tabela_assinaturas.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        
        story.append(tabela_assinaturas)
        
        if idx < total_registros - 1:
            story.append(PageBreak())
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# --- FUNÇÃO PRINCIPAL DE RENDERIZAÇÃO DA PÁGINA STREAMLIT ---
def exibir_pagina_certidao():
    st.title("📜 Central de Certidões REURB")
    st.caption("Emissão de documentos em lote para entrega oficial ou busca direcionada de segunda via.")
    st.write("<br>", unsafe_allow_html=True)

    def listar_projetos():
        return [f for f in os.listdir('.') if f.endswith('.json') and f.startswith('projeto_')]

    arquivos_projetos = listar_projetos()

    if not arquivos_projetos:
        st.info("🏛️ Nenhum núcleo ou projeto urbanístico foi cadastrado no sistema ainda.")
        return

    nomes_projetos = {}
    for arq in arquivos_projetos:
        with open(arq, "r", encoding="utf-8") as f:
            d = json.load(f)
            nomes_projetos[d['nome']] = (d, arq)

    aba_completa, aba_individual = st.tabs([
        "📦 Certidão Coletiva (Entrega Oficial)", 
        "👤 Certidão Individual (Segunda Via)"
    ])

    # 1. ABA: CERTIDÃO COLETIVA DO SETOR
    with aba_completa:
        st.subheader("Emissão Completa do Setor")
        st.markdown("""
        Esta opção é ideal para a **fase de entrega dos títulos**. Ela gera um único arquivo PDF 
        consolidado contendo a certidão de todos os moradores cadastrados no setor, aplicando automaticamente 
        **uma quebra de página para cada lote/matrícula**. O espaçamento foi configurado para **papel timbrado**.
        """)
        
        with st.container(border=True):
            projeto_sel_c = st.selectbox(
                "Selecione o Núcleo Urbano para processamento coletivo:", 
                options=list(nomes_projetos.keys()),
                key="sb_proj_coletivo"
            )
            
            data_emissao_c = st.date_input(
                "Data oficial de emissão do documento:", 
                value=datetime.today().date(),
                format="DD/MM/YYYY",
                key="dt_coletivo"
            )
            
            st.write("<br>", unsafe_allow_html=True)
            
            dados_p, arq_json = nomes_projetos[projeto_sel_c]
            nome_csv = arq_json.replace('projeto_', 'proprietarios_').replace('.json', '.csv')
            
            if os.path.exists(nome_csv):
                df_cadastrados = pd.read_csv(nome_csv, dtype=str)
                qtd_moradores = len(df_cadastrados)
                
                st.info(f"📊 O núcleo **{projeto_sel_c}** possui atualmente **{qtd_moradores}** lotes/ocupantes cadastrados.")
                
                if st.button("🚀 Processar e Compilar Certidão Coletiva", type="primary", key="btn_gerar_coletivo"):
                    with st.spinner("Estruturando páginas para papel timbrado..."):
                        try:
                            pdf_data = construir_pdf_certidao(dados_p, df_cadastrados, data_emissao_c, morador_unico_row=None)
                            
                            st.success(f"✅ Sucesso! Arquivo pronto com {qtd_moradores} páginas exclusivas.")
                            st.download_button(
                                label="⬇️ Baixar Arquivo de Impressão Coletiva",
                                data=pdf_data,
                                file_name=f"Certidao_COLETIVA_{projeto_sel_c.replace(' ', '_').upper()}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Erro crítico ao gerar o PDF Coletivo: {e}")
            else:
                st.warning("⚠️ Não existem ocupantes ou lotes cadastrados na planilha deste núcleo para gerar o documento.")

    # 2. ABA: CERTIDÃO INDIVIDUAL
    with aba_individual:
        st.subheader("Busca de Ocupante e Emissão de Segunda Via")
        st.markdown("""
        Utilize esta ferramenta para o **atendimento de balcão**. Se um morador precisar de uma segunda via 
        ou via avulsa da certidão dele, digite o nome, CPF ou Lote para imprimir **apenas a folha dele** imediatamente.
        """)
        
        projeto_sel_i = st.selectbox(
            "Selecione o Núcleo Urbano para busca:", 
            options=list(nomes_projetos.keys()),
            key="sb_proj_individual"
        )
        
        dados_p, arq_json = nomes_projetos[projeto_sel_i]
        nome_csv = arq_json.replace('projeto_', 'proprietarios_').replace('.json', '.csv')
        
        if os.path.exists(nome_csv):
            df_cadastrados = pd.read_csv(nome_csv, dtype=str).fillna("")
            
            busca = st.text_input("🔍 Digite o Nome, CPF ou Número do Lote para filtrar:", placeholder="Ex: João da Silva / 000.000... / Lote 02")
            
            if busca:
                df_filtrado = df_cadastrados[
                    df_cadastrados['Nome'].str.contains(busca, case=False, na=False) |
                    df_cadastrados['CPF'].str.contains(busca, na=False) |
                    df_cadastrados['Lote'].str.contains(busca, na=False)
                ]
            else:
                df_filtrado = df_cadastrados

            st.write("---")
            
            if not df_filtrado.empty:
                st.caption(f"Exibindo {len(df_filtrado)} registro(s) localizado(s):")
                
                # Limita a exibição para evitar sobrecarga caso haja muitos resultados sem filtro
                max_exibicao = 20
                if len(df_filtrado) > max_exibicao:
                    st.warning(f"Exibindo os primeiros {max_exibicao} resultados. Refine sua busca para encontrar outros registros.")
                    df_exibir = df_filtrado.head(max_exibicao)
                else:
                    df_exibir = df_filtrado

                for idx, row in df_exibir.iterrows():
                    with st.container(border=True):
                        col_dados, col_botao = st.columns([3.5, 1.5])
                        
                        with col_dados:
                            st.markdown(f"👤 **{row['Nome']}**")
                            st.markdown(f"💳 **CPF:** {formatar_cpf_display(row['CPF'])} &nbsp;|&nbsp; 📝 **RG:** {row['RG']} {row['SSP']}")
                            st.caption(f"📍 Quadra: {row['Quadra']} &nbsp;•&nbsp; Lote: {row['Lote']} &nbsp;•&nbsp; Matrícula: {row['Matrícula']}")
                        
                        with col_botao:
                            data_emissao_i = st.date_input(
                                "Emissão da 2ª Via:", 
                                value=datetime.today().date(),
                                format="DD/MM/YYYY",
                                key=f"dt_ind_{idx}"
                            )
                            
                            try:
                                pdf_individual_data = construir_pdf_certidao(dados_p, None, data_emissao_i, morador_unico_row=row)
                                
                                st.download_button(
                                    label="🖨️ Baixar 2ª Via",
                                    data=pdf_individual_data,
                                    file_name=f"Segunda_Via_Certidao_Lote_{row['Lote']}_{row['Nome'].replace(' ', '_').upper()}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_ind_{idx}",
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error("Erro ao gerar PDF.")
            else:
                st.warning("❌ Nenhum morador ou lote foi localizado com o termo digitado.")
        else:
            st.error("⚠️ Este núcleo urbano ainda não possui nenhuma planilha de moradores cadastrada.")

if __name__ == "__main__":
    exibir_pagina_certidao()
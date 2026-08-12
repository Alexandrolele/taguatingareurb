from datetime import datetime
import os
import re
from fpdf import FPDF
import pandas as pd
import streamlit as st
from validate_docbr import CPF
import firebase_admin
from firebase_admin import credentials, db

import base64
import json


# Decodifica a string Base64 salva no Secrets do Streamlit
firebase_base64_str = st.secrets["FIREBASE_BASE64"]
cred_dict = json.loads(base64.b64decode(firebase_base64_str).decode("utf-8"))

# --- INICIALIZAÇÃO DO FIREBASE ---
# Evita reinicializar o app múltiplas vezes no Streamlit
if not firebase_admin._apps:
  # Puxa as credenciais diretamente do st.secrets configurado no Streamlit Cloud
  cred_dict = dict(st.secrets["firebase"])
  cred = credentials.Certificate(cred_dict)
  firebase_admin.initialize_app(
      cred, {"databaseURL": "https://delegacia-3f2fe-default-rtdb.firebaseio.com/"}
  )


def gerar_pdf_autorizacao_fpdf(dados):
  """Gera o Título de Permissão com cabeçalho centralizado e tabela à direita."""
  pdf = FPDF(orientation="P", unit="mm", format="A4")
  pdf.add_page()
  pdf.set_margins(20, 20, 20)

  # --- FUNÇÕES DE APOIO ---
  def f(campo, transform=None):
    texto = (
        str(campo) if pd.notna(campo) and str(campo).lower() != "nan" else ""
    )
    # Remove o ".0" que o pandas joga em números vindos do banco
    if texto.endswith(".0"):
      texto = texto[:-2]
    if transform == "lower":
      return texto.lower()
    if transform == "upper":
      return texto.upper()
    return texto

  def limpar(txt):
    if not txt:
      return ""
    return str(txt).encode("latin-1", "replace").decode("latin-1")

  def formatar_cpf(num_cpf):
    num_cpf = re.sub(r"\D", "", str(num_cpf))
    if len(num_cpf) == 11:
      return f"{num_cpf[:3]}.{num_cpf[3:6]}.{num_cpf[6:9]}-{num_cpf[9:]}"
    return num_cpf

  # --- CABEÇALHO CENTRALIZADO ---
  pdf.set_y(12)
  pdf.set_font("Arial", "B", 12)
  pdf.cell(0, 6, limpar(""), ln=True, align="C")
  pdf.cell(0, 6, limpar(""), ln=True, align="C")
  pdf.set_font("Arial", "", 10)
  pdf.cell(0, 5, limpar(""), ln=True, align="C")
  pdf.ln(25)

  # --- TABELA DE IDENTIFICAÇÃO (DIREITA) ---
  hoje = datetime.now()
  meses = [
      "janeiro",
      "fevereiro",
      "março",
      "abril",
      "maio",
      "junho",
      "julho",
      "agosto",
      "setembro",
      "outubro",
      "novembro",
      "dezembro",
  ]
  data_curta = f"{hoje.day} de {meses[hoje.month-1]} de {hoje.year}"

  pdf.set_text_color(0, 0, 0)
  pdf.set_font("Arial", "B", 9)

  largura_tabela = 75
  x_inicial = 115
  pdf.set_x(x_inicial)

  # Campos dinâmicos no cabeçalho do PDF
  titulo_num = f(dados.get("Titulo_Permissao"))
  livro_num = f(dados.get("Livro_Tombo"))
  folhas_num = f(dados.get("Fls"))

  pdf.cell(
      largura_tabela,
      7,
      limpar(f"TÍTULO DE PERMISSÃO Nº {titulo_num}"),
      border=1,
      ln=True,
      align="C",
  )

  pdf.set_x(x_inicial)
  pdf.cell(40, 7, limpar(f"LIVRO TOMBO Nº {livro_num}"), border=1, align="C")
  pdf.cell(35, 7, limpar(f"FLS. {folhas_num}"), border=1, ln=True, align="C")

  pdf.set_x(x_inicial)
  pdf.cell(
      largura_tabela,
      7,
      limpar(f"TAGUATINGA - TO, {data_curta}"),
      border=1,
      ln=True,
      align="C",
  )

  pdf.ln(8)

  # --- TÍTULO JURÍDICO ---
  pdf.set_font("Arial", "B", 10)

  pdf.set_x(x_inicial)
  titulo_texto = (
      "TÍTULO DE PERMISSÃO PARA REGISTRO E TRANSFERÊNCIA DE DOMÍNIO QUE O"
      " MUNICÍPIO DE TAGUATINGA - TO OUTORGA À PESSOA CONTEMPLADA ABAIXO"
      " IDENTIFICADA, CONFORME AUTORIZAÇÃO DO DECRETO N.º 244/2025."
  )

  pdf.multi_cell(largura_tabela, 5, limpar(titulo_texto), border=0, align="J")
  pdf.ln(6)

  # --- CORPO DO TEXTO JURÍDICO ---
  pdf.set_font("Arial", "", 10)
  pdf.set_x(20)

  chanfro_txt = (
      (
          f", chanfro com {f(dados.get('Chanfro_Com'))}, medindo"
          f" {f(dados.get('Chanfro_M'))} metros"
      )
      if f(dados.get("Chanfro_Com"))
      else ""
  )
  cpf_formatado = formatar_cpf(dados.get("CPF", ""))

  v_rg = f(dados.get("RG"))
  v_ssp = f(dados.get("SSP"))
  v_uf = f(dados.get("UF_RG"))
  if v_rg:
    rg_completo = f"{v_rg} {v_ssp}/{v_uf}".strip().replace(" /", "/")
  else:
    rg_completo = "____________________"

  texto_corpo = (
      f"MUNICIPIO DE TAGUATINGA-TO, pessoa jurídica de direito público interno,"
      f" inscrita no CNPJ/MF sob a n° 02.306.900/0001-97 com sede administrativa"
      f" sito à Avenida Airosa de Sousa Godinho, Quadra 10, Lote 11, s/nº Setor"
      f" Bom Jesus Taguatinga TO, neste ato representado pelo Prefeito Municipal"
      f" PAULO ROBERTO RIBEIRO, brasileiro, casado, empresário, portador da"
      f" CI/RG nº 446.212 SDGPC-GO e do CPF/MF nº 088.124.461-91, residente e"
      f" domiciliado em Taguatinga TO, a presente permissão é realizada com"
      f" amparo no Processo Administrativo em epígrafe e em estrita consonância"
      f" com as disposições do Decreto nº 244 de 10 de dezembro de 2025, de"
      f" imóveis urbanos a partir de 80m², após detida análise dos documentos e"
      f" provas juntadas pelo Outorgado, a posse deste Título concede a plena"
      f" autorização para a lavratura da competente Escritura Pública de"
      f" Compra e Venda perante o Cartório de Notas e seu posterior e"
      f" obrigatório registro junto ao Cartório de Registro de Imóveis. O"
      f" procedimento de regularização será integralmente concluído após o"
      f" recolhimento do Imposto sobre a Transmissão de Bens Imóveis (ITBI),"
      f" ônus que será assumido por esta Municipalidade, concernente ao LOTE"
      f" URBANO n.º {f(dados.get('Lote'))}, Quadra: {f(dados.get('Quadra'))},"
      f" endereço do lote {f(dados.get('End_Lote'))}, Setor"
      f" {f(dados.get('Setor'))}. Dentro dos seguintes limites e confrontações:"
      f" frente para a {f(dados.get('Frente_Com'))}, com medida de"
      f" {f(dados.get('Frente_M'))} metros; fundos com o"
      f" {f(dados.get('Fundo_Com'))}, com {f(dados.get('Fundo_M'))} metros; lado"
      f" direito com o {f(dados.get('Dir_Com'))}, com {f(dados.get('Dir_M'))}"
      f" metros e lado esquerdo com o {f(dados.get('Esq_Com'))}, com"
      f" {f(dados.get('Esq_M'))} metros{chanfro_txt}, com área total de"
      f" {f(dados.get('Area_Total'))}m², ({f(dados.get('Area_Extenso'))}),"
      f" conforme memorial descritivo, Taguatinga/TO, ao (à) detentor (a),"
      f" {f(dados.get('Nome'), 'upper')}, brasileiro(a), estado civil"
      f" {f(dados.get('Estado Civil'), 'lower')}, profissão"
      f" {f(dados.get('Profissao'), 'lower')}, portador(a) da CI/RG nº"
      f" {rg_completo} e do CPF N º {cpf_formatado}, residente na"
      f" {f(dados.get('End_Residencial'))}, {f(dados.get('Bairro_Residencial'))}."
      f" O Município de Taguatinga TO, aqui designado OUTORGANTE, é legítimo"
      f" titular do domínio do imóvel público municipal, conforme Título"
      f" Definitivo de Domínio nº 109/2014, lavrado no livro 85/2014, na folha"
      f" 009 e expedido em Palmas TO, no dia 14/05/2014, pelo ITERTINS Instituto"
      f" de Terras do Estado do Tocantins, registrado no Cartório de Registro"
      f" de Imóveis e Tabelionato 1º de Notas da Comarca de Taguatinga TO, sob a"
      f" Matrícula nº 2869, Livro 2-RGR-01 em 23/07/2014, posteriormente"
      f" desmembrado para a {f(dados.get('Lei_Aplicada'))}, em ato contínuo"
      f" desmembrado referido lote para a MATRÍCULA nº"
      f" {f(dados.get('Matricula'))}, recebido pela OUTORGANTE, conforme"
      f" estabelecido no parágrafo 3º, do artigo 1º, da Lei Municipal"
      f" n°438/2014. Certifica e dá fé que foram cumpridas as exigências"
      f" legais que capacitam e autorizam a ilustríssima senhora Oficiala de"
      f" Registro de Imóveis que transfira a propriedade da matrícula que foi"
      f" aberta no Livro Geral de Reg. de Imóveis dessa Comarca. Pelo presente,"
      f" o OUTORGANTE, na qualidade de legítimo titular do domínio, transfere e"
      f" cede ao OUTORGADO todo o domínio, ações, direitos, jus e posse que até"
      f" então exercia sobre o aludido imóvel, passando o OUTORGADO a"
      f" consolidar e exercer o pleno DIREITO DE PROPRIEDADE sobre o lote em"
      f" questão. O OUTORGADO declara aceitar o presente Título Definitivo de"
      f" Domínio em todos os seus termos, cláusulas e condições. O presente"
      f" Título é emitido em estrita observância ao Decreto nº 244/2025, que"
      f" autoriza a transferência do domínio do imóvel, devidamente comprovada"
      f" a titularidade do OUTORGANTE conforme a Matrícula n.º"
      f" {f(dados.get('Matricula'))}. O ato finaliza o Processo Administrativo"
      f" n.º 01/2024 e habilita o registro imediato do pleno Direito de"
      f" Propriedade em nome do OUTORGADO perante o Cartório de Registro de"
      f" Imóveis. E por estarem justos, contratados e de pleno acordo com todas"
      f" as condições estabelecidas, as partes firmam o presente Título de"
      f" Domínio em 02 (duas) vias de igual teor e forma, que será devidamente"
      f" assinado por elas e por 02 (duas) testemunhas."
  )

  pdf.multi_cell(0, 5, limpar(texto_corpo), align="J")
  pdf.ln(6)

  pdf.set_font("Arial", "I", 10)
  data_final = (
      f"Taguatinga-TO, {hoje.day} de {meses[hoje.month-1]} de {hoje.year}."
  )
  pdf.cell(0, 8, limpar(data_final), ln=True, align="R")
  pdf.ln(6)

  # --- ASSINATURAS PRINCIPAIS ---
  pdf.set_font("Arial", "B", 9)
  pdf.cell(0, 5, "__________________________________________", ln=True, align="C")
  pdf.cell(0, 5, limpar("PAULO ROBERTO RIBEIRO"), ln=True, align="C")
  pdf.set_font("Arial", "", 8)
  pdf.cell(0, 4, limpar("Prefeito Municipal"), ln=True, align="C")
  pdf.ln(6)

  pdf.set_font("Arial", "B", 9)
  pdf.cell(0, 5, "__________________________________________", ln=True, align="C")
  pdf.cell(0, 5, limpar("LUAN AIRES RIBEIRO"), ln=True, align="C")
  pdf.set_font("Arial", "", 8)
  pdf.cell(0, 4, limpar("Secretário de Regularização Fundiária"), ln=True, align="C")
  pdf.ln(6)

  pdf.set_font("Arial", "B", 9)
  pdf.cell(0, 5, "__________________________________________", ln=True, align="C")
  pdf.cell(0, 5, limpar(f(dados.get("Nome"), "upper")), ln=True, align="C")
  pdf.set_font("Arial", "", 8)
  pdf.cell(0, 4, limpar("Outorgado Adquirente"), ln=True, align="C")
  pdf.ln(8)

  # --- TESTEMUNHAS ---
  pdf.set_font("Arial", "B", 9)
  pdf.cell(0, 5, "__________________________________________", ln=True, align="L")
  pdf.set_font("Arial", "", 8)
  pdf.cell(0, 4, limpar("Testemunha 01"), ln=True, align="L")
  pdf.cell(0, 4, limpar("CPF:_____._____._____-___"), ln=True, align="L")
  pdf.ln(6)

  pdf.set_font("Arial", "B", 9)
  pdf.cell(0, 5, "__________________________________________", ln=True, align="L")
  pdf.set_font("Arial", "", 8)
  pdf.cell(0, 4, limpar("Testemunha 02"), ln=True, align="L")
  pdf.cell(0, 4, limpar("CPF:_____._____._____-___"), ln=True, align="L")

  retorno_pdf = pdf.output(dest="S")
  if isinstance(retorno_pdf, str):
    return retorno_pdf.encode("latin-1")
  return bytes(retorno_pdf)


# --- FUNÇÕES DE BANCO DE DADOS COM FIREBASE ---
def carregar_dados_firebase():
  ref = db.reference("autorizacoes_titulos")
  dados = ref.get()
  if not dados:
    return pd.DataFrame()
  # Transforma o dicionário salvo no Firebase em um DataFrame do Pandas
  lista_registros = list(dados.values())
  return pd.DataFrame(lista_registros)


def salvar_registro(*args):
  colunas = [
      "Nome",
      "Nacionalidade",
      "Estado Civil",
      "Profissao",
      "RG",
      "SSP",
      "UF_RG",
      "CPF",
      "End_Residencial",
      "Bairro_Residencial",
      "Lote",
      "Quadra",
      "End_Lote",
      "Setor",
      "Frente_Com",
      "Frente_M",
      "Fundo_Com",
      "Fundo_M",
      "Dir_Com",
      "Dir_M",
      "Esq_Com",
      "Esq_M",
      "Area_Total",
      "Area_Extenso",
      "Matricula",
      "Lei_Aplicada",
      "Chanfro_Com",
      "Chanfro_M",
      "Titulo_Permissao",
      "Livro_Tombo",
      "Fls",
  ]

  novo_dict = dict(zip(colunas, args))

  # Criamos uma chave única segura com base no CPF, Lote e Quadra para evitar duplicatas erradas
  cpf_sanitizado = str(args[7])
  lote_sanitizado = str(args[10])
  quadra_sanitizada = str(args[11])
  chave_registro = f"lote_{quadra_sanitizada}_{lote_sanitizado}_cpf_{cpf_sanitizado}".replace(
      ".", "_"
  )

  ref = db.reference(f"autorizacoes_titulos/{chave_registro}")
  ref.set(novo_dict)

  st.success("✅ Dados salvos com sucesso no Firebase!")
  st.session_state.editar_autorizacao = None
  st.rerun()


def formulario_autorizacao(dados_edicao=None):
  if dados_edicao is not None:
    st.warning(
        f"📝 Editando: {dados_edicao.get('Nome', '')} (Lote"
        f" {dados_edicao.get('Lote','')}, Q. {dados_edicao.get('Quadra','')})"
    )
    if st.button("❌ Cancelar"):
      st.session_state.editar_autorizacao = None
      st.rerun()

  dados_autocompletar = {}
  df_existente = carregar_dados_firebase()

  if not df_existente.empty and dados_edicao is None:
    df_unicos = df_existente.drop_duplicates(subset=["CPF", "Nome"])
    lista_pessoas = [
        "-- Selecione para copiar dados (Múltiplos Lotes) --"
    ] + [f"{row['Nome']} (CPF: {row['CPF']})" for _, row in df_unicos.iterrows()]

    selecionado = st.selectbox(
        "👤 Copiar dados de requerente já cadastrado:", lista_pessoas
    )
    if selecionado != "-- Selecione para copiar dados (Múltiplos Lotes) --":
      nome_selecionado = selecionado.split(" (CPF:")[0]
      dados_autocompletar = (
          df_unicos[df_unicos["Nome"] == nome_selecionado]
          .iloc[0]
          .fillna("")
          .to_dict()
      )

  with st.form("form_autorizacao", clear_on_submit=False):
    if dados_edicao is not None:
      fonte_dados = dados_edicao
    else:
      fonte_dados = dados_autocompletar

    st.subheader("👤 Requerente")
    col1, col2, col3 = st.columns([2, 1, 1])
    nome = col1.text_input("Nome", value=fonte_dados.get("Nome", ""))
    nacionalidade = col2.text_input(
        "Nacionalidade", value=fonte_dados.get("Nacionalidade", "Brasileiro")
    )

    opcoes_civil = [
        "Solteiro(a)",
        "Casado(a)",
        "Divorciado(a)",
        "Viúvo(a)",
        "União Estável",
    ]
    civil_salvo = fonte_dados.get("Estado Civil", "Solteiro(a)")
    idx_civil = (
        opcoes_civil.index(civil_salvo) if civil_salvo in opcoes_civil else 0
    )
    estado_civil = col3.selectbox("Estado Civil", opcoes_civil, index=idx_civil)

    c1, c2, c3, c4 = st.columns([1.5, 1, 0.5, 1.5])
    profissao = c1.text_input("Profissão", value=fonte_dados.get("Profissao", ""))
    rg = c2.text_input(
        "RG", value=fonte_dados.get("RG", ""), placeholder="Apenas números"
    )
    ssp = c3.text_input("SSP", value=fonte_dados.get("SSP", ""))
    uf_rg = c4.text_input("UF", value=fonte_dados.get("UF_RG", "TO"))

    col_cpf, col_end, col_bairro = st.columns([1.5, 2, 1])
    cpf = col_cpf.text_input(
        "CPF", value=fonte_dados.get("CPF", ""), placeholder="000.000.000-00"
    )
    endereco_res = col_end.text_input(
        "Endereço", value=fonte_dados.get("End_Residencial", "")
    )
    bairro_res = col_bairro.text_input(
        "Bairro", value=fonte_dados.get("Bairro_Residencial", "")
    )

    st.divider()
    st.subheader("🏘️ Lote")
    l1, l2, l3, l4 = st.columns([1, 1, 2, 1])
    lote_num = l1.text_input(
        "Lote Nº",
        value=dados_edicao.get("Lote", "")
        if dados_edicao
        else fonte_dados.get("Lote", ""),
    )
    quadra_num = l2.text_input(
        "Quadra",
        value=dados_edicao.get("Quadra", "")
        if dados_edicao
        else fonte_dados.get("Quadra", ""),
    )
    end_lote = l3.text_input(
        "Endereço do Lote", value=fonte_dados.get("End_Lote", "")
    )
    setor = l4.text_input("Setor", value=fonte_dados.get("Setor", ""))

    st.divider()
    st.subheader("📏 Confrontações")
    f1, f2 = st.columns(2)
    finter_c = f1.text_input(
        "Frente com", value=fonte_dados.get("Frente_Com", "")
    )
    finter_m = f2.text_input("Frente (m)", value=fonte_dados.get("Frente_M", ""))
    f3, f4 = st.columns(2)
    fundo_c = f3.text_input(
        "Fundo com", value=fonte_dados.get("Fundo_Com", "")
    )
    fundo_m = f4.text_input("Fundo (m)", value=fonte_dados.get("Fundo_M", ""))
    f5, f6 = st.columns(2)
    dir_c = f5.text_input("Direita com", value=fonte_dados.get("Dir_Com", ""))
    dir_m = f6.text_input("Direita (m)", value=fonte_dados.get("Dir_M", ""))
    f7, f8 = st.columns(2)
    esq_c = f7.text_input(
        "Esquerda com", value=fonte_dados.get("Esq_Com", "")
    )
    esq_m = f8.text_input("Esquerda (m)", value=fonte_dados.get("Esq_M", ""))

    st.write("**📐 Chanfro (Opcional)**")
    ch1, ch2 = st.columns(2)
    chan_c = ch1.text_input(
        "Chanfro com", value=fonte_dados.get("Chanfro_Com", "")
    )
    chan_m = ch2.text_input("Chanfro (m)", value=fonte_dados.get("Chanfro_M", ""))

    st.write("---")
    area_t = st.text_input("Área Total", value=fonte_dados.get("Area_Total", ""))
    area_e = st.text_area(
        "Área Extenso", value=fonte_dados.get("Area_Extenso", "")
    )

    col_mat, col_lei = st.columns(2)
    matr = st.text_input("Matrícula", value=fonte_dados.get("Matricula", ""))

    opcoes_leis = [
        "MATRÍCULA nº 5.771 - Setor Norte 2° ETAPA",
        "MATRÍCULA nº 6.043 - Setor Buritizinho",
        "MATRÍCULA nº 3.752 - Setor Leste",
        "MATRÍCULA nº 4.244 - Setor Serra Azul",
        "MATRÍCULA nº 4.527 - Setor Bom Jesus",
        "MATRÍCULA nº 3.470 - Setor Vila Santa Maria Leste",
    ]
    lei_atual = fonte_dados.get("Lei_Aplicada", "")
    lei_selecionada = col_lei.selectbox(
        "Legislação Aplicável",
        options=opcoes_leis,
        index=opcoes_leis.index(lei_atual) if lei_atual in opcoes_leis else 0,
    )

    st.subheader("📑 Informações do Título")
    nt1, nt2, nt3 = st.columns([1.5, 1.5, 1])
    titulo_permissao = nt1.text_input(
        "TÍTULO DE PERMISSÃO Nº",
        value=fonte_dados.get("Titulo_Permissao", ""),
    )
    livro_tombo = nt2.text_input(
        "LIVRO TOMBO Nº", value=fonte_dados.get("Livro_Tombo", "")
    )
    fls = nt3.text_input("FLS.", value=fonte_dados.get("Fls", ""))

    if st.form_submit_button("💾 SALVAR"):
      cpf_limpo = re.sub(r"\D", "", cpf)
      rg_limpo = re.sub(r"[\s.-]", "", rg)
      validador_cpf = CPF()

      if not validador_cpf.validate(cpf_limpo):
        st.error("❌ CPF INVÁLIDO")
      elif not rg_limpo.isdigit():
        st.error("❌ RG INVÁLIDO: Digite apenas números.")
      elif not lote_num or not quadra_num:
        st.error("❌ O preenchimento do Lote e da Quadra é obrigatório.")
      else:
        salvar_registro(
            nome,
            nacionalidade,
            estado_civil,
            profissao,
            rg.strip().upper(),
            ssp,
            uf_rg,
            cpf_limpo,
            endereco_res,
            bairro_res,
            lote_num,
            quadra_num,
            end_lote,
            setor,
            finter_c,
            finter_m,
            fundo_c,
            fundo_m,
            dir_c,
            dir_m,
            esq_c,
            esq_m,
            area_t,
            area_e,
            matr,
            lei_selecionada,
            chan_c,
            chan_m,
            titulo_permissao,
            livro_tombo,
            fls,
        )


def lista_e_gestao():
  df = carregar_dados_firebase()
  if df.empty:
    st.info("Nenhum dado cadastrado.")
    return

  df = df.fillna("")
  busca = st.text_input("🔍 Pesquisar")
  if busca:
    df = df[
        df["Nome"].str.contains(busca, case=False, na=False)
        | df["CPF"].str.contains(busca, na=False)
    ]

  for idx, row in df.iterrows():
    with st.container(border=True):
      c1, c2, c3, c4 = st.columns([2.5, 0.8, 0.8, 1.2])
      c1.write(
          f"👤 **{row['Nome']}** \n📍 Lote {row['Lote']} - Quadra {row['Quadra']}"
          f" - Setor {row['Setor']}"
      )

      if c2.button("📝", key=f"e_{idx}"):
        st.session_state.editar_autorizacao = row.to_dict()
        st.rerun()

      if c3.button("🗑️", key=f"d_{idx}"):
        cpf_del = str(row["CPF"])
        lote_del = str(row["Lote"])
        quadra_del = str(row["Quadra"])
        chave_del = f"lote_{quadra_del}_{lote_del}_cpf_{cpf_del}".replace(
            ".", "_"
        )

        db.reference(f"autorizacoes_titulos/{chave_del}").delete()
        st.rerun()

      pdf_bytes = gerar_pdf_autorizacao_fpdf(row)
      c4.download_button(
          "📄 PDF",
          pdf_bytes,
          f"Titulo_{row['Nome']}_Lote_{row['Lote']}.pdf",
          "application/pdf",
          key=f"p_{idx}",
      )


def exibir_pagina():
  st.title("📄 Título de Permissão")
  t1, t2 = st.tabs(["Novo", "Gerenciar"])
  with t1:
    formulario_autorizacao(st.session_state.get("editar_autorizacao"))
  with t2:
    lista_e_gestao()


if __name__ == "__main__":
  exibir_pagina()

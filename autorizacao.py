import json
import os
import firebase_admin
from firebase_admin import db, exceptions
import pandas as pd
import streamlit as st


# --- FUNÇÃO NATIVA PARA VALIDAR CPF ---
def validar_cpf(cpf_str):
  cpf_limpo = re.sub(r"\D", "", cpf_str)

  if len(cpf_limpo) != 11 or cpf_limpo == cpf_limpo[0] * 11:
    return False

  # Validação do 1º dígito verificador
  soma = sum(int(cpf_limpo[i]) * (10 - i) for i in range(9))
  resto = (soma * 10) % 11
  if resto == 10 or resto == 11:
    resto = 0
  if resto != int(cpf_limpo[9]):
    return False

  # Validação do 2º dígito verificador
  soma = sum(int(cpf_limpo[i]) * (11 - i) for i in range(10))
  resto = (soma * 10) % 11
  if resto == 10 or resto == 11:
    resto = 0
  if resto != int(cpf_limpo[10]):
    return False

  return True


# --- FUNÇÃO SEGURA PARA OBTER REFERÊNCIA DO FIREBASE ---
def obter_referencia_firebase(caminho=""):
  """Garante que a conexão com o Firebase utilize o app inicializado corretamente."""
  try:
    app = firebase_admin.get_app()
  except ValueError:
    # Se o app padrão não existir, inicializa agora usando st.secrets ou arquivo local
    if "firebase" in st.secrets:
      creds_dict = dict(st.secrets["firebase"])
      cred = firebase_admin.credentials.Certificate(creds_dict)
      database_url = st.secrets["firebase"].get("databaseURL", "")
      if not database_url:
        project_id = creds_dict.get("project_id", "")
        database_url = f"https://{project_id}-default-rtdb.firebaseio.com/"
      app = firebase_admin.initialize_app(cred, {"databaseURL": database_url})
    else:
      if os.path.exists("firebase_key.json"):
        cred = firebase_admin.credentials.Certificate("firebase_key.json")
        with open("firebase_key.json", "r") as f:
          key_data = json.load(f)
          project_id = key_data.get("project_id", "")
          database_url = f"https://{project_id}-default-rtdb.firebaseio.com/"
        app = firebase_admin.initialize_app(
            cred, {"databaseURL": database_url}
        )
      else:
        raise ValueError(
            "As credenciais do Firebase não foram encontradas no st.secrets nem"
            " em arquivo local."
        )

  if caminho:
    return db.reference(caminho, app=app)
  return db.reference(app=app)


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

  cpf_sanitizado = str(args[7])
  lote_sanitizado = str(args[10])
  quadra_sanitizada = str(args[11])
  chave_registro = (
      f"lote_{quadra_sanitizada}_{lote_sanitizado}_cpf_{cpf_sanitizado}".replace(
          ".", "_"
      )
  )

  ref = obter_referencia_firebase(f"autorizacoes_titulos/{chave_registro}")
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
  df_existente = (
      carregar_dados_firebase()
  )  # Certifique-se de que esta função existe

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
    fonte_dados = (
        dados_edicao if dados_edicao is not None else dados_autocompletar
    )

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
    lote_num = l1.text_input("Lote Nº", value=fonte_dados.get("Lote", ""))
    quadra_num = l2.text_input("Quadra", value=fonte_dados.get("Quadra", ""))
    end_lote = l3.text_input(
        "Endereço do Lote", value=fonte_dados.get("End_Lote", "")
    )
    setor = l4.text_input("Setor", value=fonte_dados.get("Setor", ""))

    st.divider()
    st.subheader("📏 Confrontações")
    f1, f2 = st.columns(2)
    finter_c = f1.text_input("Frente com", value=fonte_dados.get("Frente_Com", ""))
    finter_m = f2.text_input("Frente (m)", value=fonte_dados.get("Frente_M", ""))
    f3, f4 = st.columns(2)
    fundo_c = f3.text_input("Fundo com", value=fonte_dados.get("Fundo_Com", ""))
    fundo_m = f4.text_input("Fundo (m)", value=fonte_dados.get("Fundo_M", ""))
    f5, f6 = st.columns(2)
    dir_c = f5.text_input("Direita com", value=fonte_dados.get("Dir_Com", ""))
    dir_m = f6.text_input("Direita (m)", value=fonte_dados.get("Dir_M", ""))
    f7, f8 = st.columns(2)
    esq_c = f7.text_input("Esquerda com", value=fonte_dados.get("Esq_Com", ""))
    esq_m = f8.text_input("Esquerda (m)", value=fonte_dados.get("Esq_M", ""))

    st.write("**📐 Chanfro (Opcional)**")
    ch1, ch2 = st.columns(2)
    chan_c = ch1.text_input("Chanfro com", value=fonte_dados.get("Chanfro_Com", ""))
    chan_m = ch2.text_input("Chanfro (m)", value=fonte_dados.get("Chanfro_M", ""))

    st.write("---")
    area_t = st.text_input("Área Total", value=fonte_dados.get("Area_Total", ""))
    area_e = st.text_area("Área Extenso", value=fonte_dados.get("Area_Extenso", ""))

    col_mat, col_lei = st.columns(2)
    matr = col_mat.text_input("Matrícula", value=fonte_dados.get("Matricula", ""))
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
        "TÍTULO DE PERMISSÃO Nº", value=fonte_dados.get("Titulo_Permissao", "")
    )
    livro_tombo = nt2.text_input(
        "LIVRO TOMBO Nº", value=fonte_dados.get("Livro_Tombo", "")
    )
    fls = nt3.text_input("FLS.", value=fonte_dados.get("Fls", ""))

    if st.form_submit_button("💾 SALVAR"):
      cpf_limpo = re.sub(r"\D", "", cpf)
      rg_limpo = re.sub(r"[\s.-]", "", rg)

      if not validar_cpf(cpf_limpo):
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
          f"👤 **{row['Nome']}** \n📍 Lote {row['Lote']} - Quadra"
          f" {row['Quadra']} - Setor {row['Setor']}"
      )

      if c2.button("📝", key=f"e_{idx}"):
        st.session_state.editar_autorizacao = row.to_dict()
        st.rerun()

      if c3.button("🗑️", key=f"d_{idx}"):
        cpf_del = str(row["CPF"])
        lote_del = str(row["Lote"])
        quadra_del = str(row["Quadra"])
        chave_del = (
            f"lote_{quadra_del}_{lote_del}_cpf_{cpf_del}".replace(".", "_")
        )
        obter_referencia_firebase(f"autorizacoes_titulos/{chave_del}").delete()
        st.rerun()

      if "gerar_pdf_autorizacao_fpdf" in globals():
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

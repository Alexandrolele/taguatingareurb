import datetime
import re
import pandas as pd
import streamlit as st
from fpdf import FPDF
from validate_docbr import CPF


# --- FUNÇÃO DE AUXÍLIO PARA FORMATAR CPF ---
def formatar_cpf_display(valor):
    # Remove tudo que não é número
    cpf_limpo = re.sub(r"\D", "", str(valor))
    if len(cpf_limpo) == 11:
        # Retorna com a máscara 000.000.000-00
        return CPF().mask(cpf_limpo)
    return str(valor)  # Se estiver incompleto ou vazio, retorna o original


def limpar_texto(txt):
    if not txt or str(txt).lower() in ["nan", "none", "n/a"]:
        return ""
    return str(txt).encode("latin-1", "replace").decode("latin-1")


def obter_mes_extenso(mes):
    meses = {
        1: "janeiro",
        2: "fevereiro",
        3: "março",
        4: "abril",
        5: "maio",
        6: "junho",
        7: "julho",
        8: "agosto",
        9: "setembro",
        10: "outubro",
        11: "novembro",
        12: "dezembro",
    }
    return meses.get(mes, "")


# --- CLASSE DA CERTIDÃO ---
class CertidaoREURB(FPDF):

    def header(self):
        # Inserção da Logomarca
        try:
            self.image("logo_prefeitura.png", 10, 8, 33)
        except Exception:
            pass

        # Texto do cabeçalho
        self.set_font("Arial", "B", 12)
        self.set_x(45)
        self.cell(0, 7, "ESTADO DO TOCANTINS", 0, 1, "C")

        self.set_x(45)
        self.cell(0, 7, "PREFEITURA MUNICIPAL DE TAGUATINGA", 0, 1, "C")

        # Slogan
        self.set_font("Arial", "I", 10)
        self.set_x(45)
        self.cell(0, 7, limpar_texto('"O PROGRESSO CONTINUA!"'), 0, 1, "C")

        self.ln(5)
        self.set_line_width(0.5)
        self.line(10, 35, 200, 35)
        self.ln(12)

    def footer(self):
        self.set_y(-25)
        self.set_font("Arial", "I", 8)
        self.cell(
            0,
            5,
            limpar_texto(
                "Avenida Airosa de Souza Godinho, Quadra 10, Lote 11, s/n Setor"
                " Bom Jesus"
            ),
            0,
            1,
            "C",
        )
        self.cell(0, 5, "Taguatinga - TO, CEP: 77320-000", 0, 1, "C")
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "R")


def gerar_pdf_projeto(dados_projeto, df_proprietarios, data_manual):
    pdf = CertidaoREURB()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # --- TÍTULO COM NÚMERO E ANO DA CRF DINÂMICA ---
    pdf.set_font("Arial", "B", 14)

    num_crf = dados_projeto.get("num_crf", "")
    ano_crf = dados_projeto.get("ano_crf", "")

    if num_crf and ano_crf:
        titulo_completo = (
            f"CERTIDÃO DE REGULARIZAÇÃO FUNDIÁRIA - CRF Nº {num_crf}/{ano_crf}"
        )
    else:
        titulo_completo = "CERTIDÃO DE REGULARIZAÇÃO FUNDIÁRIA"

    pdf.cell(0, 10, limpar_texto(titulo_completo), 0, 1, "C")
    pdf.ln(5)

    # --- TEXTO JURÍDICO INICIAL ---
    pdf.set_font("Arial", "", 11)
    texto_inicial = (
        "O MUNICÍPIO DE TAGUATINGA - TO, pessoa jurídica de direito público"
        " interno, inscrito no CNPJ sob o nº 02.306.900/0001-97, com sede"
        " administrativa na Avenida Airosa de Souza Godinho, Quadra 10, Lote"
        " 11, s/n, Setor Bom Jesus, Taguatinga - TO, CEP: 77320-000, neste ato"
        " representado pelo Prefeito Municipal, PAULO ROBERTO RIBEIRO,"
        " brasileiro, casado, empresário, portador da CI/RG nº 446.212-SDGPC/GO"
        " e do CPF/MF nº 088.124.461-91, residente e domiciliado em Taguatinga"
        " - TO, na forma da lei e nos termos dos artigos 30, III, e 41 da Lei"
        " nº 13.465/2017 e art. 38 do Decreto nº 9.310/2018, CERTIFICA, para os"
        " devidos fins de registro imobiliário, que tramitou perante a Secretaria"
        " Municipal de Regularização Fundiária deste Município o Processo"
        " Administrativo nº 01/2021, oriundo da instauração de ofício pelo"
        " Município, conforme a legitimidade dada pelo art. 14, I, da Lei nº"
        " 13.465/2017, finalizado pelo Decreto Municipal nº 46/2026 em 10 de"
        " março de 2026."
    )
    pdf.multi_cell(0, 7, limpar_texto(texto_inicial), align="J")
    pdf.ln(5)

    # --- 1. CARACTERÍSTICAS (TABELA + PARÁGRAFO) ---
    pdf.set_font("Arial", "B", 11)
    pdf.cell(
        0, 10, limpar_texto("1. CARACTERÍSTICAS DO NÚCLEO URBANO INFORMAL:"), 0, 1
    )

    pdf.ln(5)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(90, 8, limpar_texto("Nome do núcleo urbano regularizado:"), 1, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(100, 8, limpar_texto(dados_projeto.get("nome", "")), 1, 1)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(90, 8, limpar_texto("Localização:"), 1, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(100, 8, limpar_texto(dados_projeto.get("local", "")), 1, 1)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(90, 8, limpar_texto("Modalidade predominante da regularização:"), 1, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(100, 8, limpar_texto(dados_projeto.get("modalidade", "")), 1, 1)
    pdf.ln(5)

    # --- Formatação das áreas para o padrão 00.000,00 no parágrafo técnico ---
    try:
        a_tot = float(dados_projeto.get("area_total", 0.0))
        area_total_fmt = (
            f"{a_tot:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    except Exception:
        area_total_fmt = str(dados_projeto.get("area_total", "0,00"))

    try:
        a_via = float(dados_projeto.get("area_viaria", 0.0))
        area_viaria_fmt = (
            f"{a_via:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    except Exception:
        area_viaria_fmt = str(dados_projeto.get("area_viaria", "0,00"))

    quadras_list = dados_projeto.get("quadras", [])
    detalhe_quadras = ", ".join(
        [f"{q['lotes']} lote(s) na quadra {q['quadra']}" for q in quadras_list]
    )
    ruas_num = dados_projeto.get("ruas", 0)

    texto_tecnico = (
        f"A área do núcleo de {area_total_fmt} m², será parcelada de forma a"
        f" abarcar {detalhe_quadras}, contendo {ruas_num} ruas e além de"
        f" {area_viaria_fmt} m² de sistema viário."
    )
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7, limpar_texto(texto_tecnico), align="J")

    # --- 2. MATRÍCULAS ATINGIDAS ---
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, limpar_texto("2. MATRÍCULAS ATINGIDAS:"), 0, 1)

    # --- TEXTO DESCRITIVO CORRIGIDO E INSERIDO ---
    pdf.set_font("Arial", "", 11)
    texto_matriculas = (
        "O núcleo urbano atinge parte ou a totalidade das seguintes "
        "matrículas do Cartório de Registro de Imóveis de Taguatinga - TO:"
    )
    pdf.multi_cell(0, 7, limpar_texto(texto_matriculas), align="J")
    pdf.ln(3)

    if df_proprietarios is not None and not df_proprietarios.empty:
        df_prop = df_proprietarios.copy()
        for col in [
            "H_Nome",
            "H_Est_Civil",
            "H_Profissao",
            "H_RG",
            "H_SSP",
            "H_CPF",
        ]:
            if col not in df_prop.columns:
                df_prop[col] = ""

        # Garante ordenação puramente numérica crescente das Quadras e dos Lotes
        df_prop["Quadra_Num"] = pd.to_numeric(
            df_prop["Quadra"], errors="coerce"
        ).fillna(999)
        df_prop["Lote_Num"] = pd.to_numeric(
            df_prop["Lote"], errors="coerce"
        ).fillna(999)
        df_prop = df_prop.sort_values(by=["Quadra_Num", "Lote_Num"])

        for q in df_prop["Quadra"].unique():
            pdf.ln(4)
            pdf.set_font("Arial", "B", 12)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(0, 9, limpar_texto(f"QUADRA {q}"), 1, 1, "C", True)

            df_q = df_prop[df_prop["Quadra"] == q]
            for _, row in df_q.iterrows():
                pdf.ln(2)
                pdf.set_font("Arial", "B", 10)
                pdf.set_fill_color(245, 245, 245)
                pdf.cell(
                    0,
                    7,
                    limpar_texto(f"FICHA DE CADASTRO - LOTE {row['Lote']}"),
                    1,
                    1,
                    "L",
                    True,
                )

                pdf.set_font("Arial", "B", 8)
                pdf.cell(30, 6, "LOTE N.:", 1, 0)
                pdf.set_font("Arial", "", 9)
                pdf.cell(65, 6, limpar_texto(row.get("Lote", "")), 1, 0)

                pdf.set_font("Arial", "B", 8)
                pdf.cell(30, 6, "MATRÍCULA:", 1, 0)
                pdf.set_font("Arial", "", 9)
                pdf.cell(65, 6, limpar_texto(row.get("Matrícula", "")), 1, 1)

                pdf.set_font("Arial", "B", 8)
                pdf.cell(30, 6, "NOME:", 1, 0)
                pdf.set_font("Arial", "", 9)
                pdf.cell(160, 6, limpar_texto(row.get("Nome", "")), 1, 1)

                pdf.set_font("Arial", "B", 8)
                pdf.cell(30, 6, "EST. CIVIL:", 1, 0)
                pdf.set_font("Arial", "", 9)
                pdf.cell(65, 6, limpar_texto(row.get("Estado Civil", "")), 1, 0)

                pdf.set_font("Arial", "B", 8)
                pdf.cell(30, 6, "PROFISSÃO:", 1, 0)
                pdf.set_font("Arial", "", 9)
                pdf.cell(65, 6, limpar_texto(row.get("Profissão", "")), 1, 1)

                # --- AJUSTE TITULAR: RG e CPF ---
                rg_val = str(row.get("RG", "")).strip().upper()
                ssp_val = limpar_texto(row.get("SSP", ""))
                rg_titular = f"{rg_val} / {ssp_val}" if ssp_val else rg_val
                cpf_titular = formatar_cpf_display(row.get("CPF", ""))

                pdf.set_font("Arial", "B", 8)
                pdf.cell(30, 6, "RG / SSP:", 1, 0)
                pdf.set_font("Arial", "", 9)
                pdf.cell(65, 6, rg_titular, 1, 0)

                pdf.set_font("Arial", "B", 8)
                pdf.cell(30, 6, "CPF N.:", 1, 0)
                pdf.set_font("Arial", "", 9)
                pdf.cell(65, 6, cpf_titular, 1, 1)

                pdf.set_font("Arial", "B", 8)
                pdf.cell(30, 6, "RESIDENTE:", 1, 0)
                pdf.set_font("Arial", "", 9)
                pdf.cell(160, 6, limpar_texto(row.get("Endereço", "")), 1, 1)

                pdf.set_font("Arial", "B", 8)
                pdf.cell(30, 6, "BAIRRO:", 1, 0)
                pdf.set_font("Arial", "", 9)
                pdf.cell(65, 6, limpar_texto(row.get("Bairro", "")), 1, 0)

                pdf.set_font("Arial", "B", 8)
                pdf.cell(30, 6, "CIDADE / UF:", 1, 0)
                pdf.set_font("Arial", "", 9)
                cidade_uf = f"{row.get('Cidade', '')} - {row.get('UF', '')}"
                pdf.cell(65, 6, limpar_texto(cidade_uf), 1, 1)

                # --- BLOCO DO CÔNJUGE / HERDEIRO ---
                nome_h = limpar_texto(str(row.get("H_Nome", "")))
                if nome_h != "":
                    pdf.set_font("Arial", "B", 8)
                    pdf.set_fill_color(252, 252, 252)
                    pdf.cell(
                        190, 5, "DADOS DO CÔNJUGE / HERDEIRO", 1, 1, "C", True
                    )

                    pdf.set_font("Arial", "B", 8)
                    pdf.cell(30, 6, "NOME:", 1, 0)
                    pdf.set_font("Arial", "", 9)
                    pdf.cell(160, 6, nome_h, 1, 1)

                    # --- AJUSTE CÔNJUGE: RG e CPF ---
                    h_rg = str(row.get("H_RG", "")).strip().upper()
                    h_ssp = limpar_texto(str(row.get("H_SSP", "")))
                    h_cpf = formatar_cpf_display(row.get("H_CPF", ""))
                    identidade_h = f"{h_rg} {h_ssp} / {h_cpf}".strip()

                    pdf.set_font("Arial", "B", 8)
                    pdf.cell(30, 6, "RG / CPF:", 1, 0)
                    pdf.set_font("Arial", "", 9)
                    pdf.cell(160, 6, identidade_h, 1, 1)

                    pdf.set_font("Arial", "B", 8)
                    pdf.cell(30, 6, "EST. CIVIL:", 1, 0)
                    pdf.set_font("Arial", "", 9)
                    pdf.cell(
                        65, 6, limpar_texto(row.get("H_Est_Civil", "")), 1, 0
                    )

                    pdf.set_font("Arial", "B", 8)
                    pdf.cell(30, 6, "PROFISSÃO:", 1, 0)
                    pdf.set_font("Arial", "", 9)
                    pdf.cell(
                        65, 6, limpar_texto(row.get("H_Profissao", "")), 1, 1
                    )

                pdf.ln(4)

    # --- 3. DO RELATÓRIO ---
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, limpar_texto("3. DO RELATÓRIO"), 0, 1)
    pdf.set_font("Arial", "", 11)

    texto_relatorio = (
        "Conforme documentação que integra o procedimento administrativo,"
        " afirmo e certifico, sob responsabilidade civil, criminal e"
        " administrativa, que:\n\nOs lotes ocupados e não titulados neste"
        " momento permanecerão em nome dos proprietários originários, até"
        " posterior lista de titulação que será encaminhada ao Registro de"
        " Imóveis quando da apuração dos reais ocupantes, conforme previsto no"
        " art. 52 e art. 16, § 7º do Decreto 9.310/2018.\nNão serão remetidos"
        " todos os títulos individualizados e/ou cópia dos documentos pessoais"
        " dos beneficiários para registro dos direitos reais outorgados,"
        " substituindo-os pela listagem final de ocupantes;\nO núcleo urbano"
        " informal consolidado foi formado antes de 22 de dezembro de 2016,"
        " sendo a legitimação fundiária o principal instrumento escolhido para"
        " titulação dos ocupantes, ou seja, adquire-se a unidade imobiliária"
        " com destinação urbana livre e desembaraçada de quaisquer ônus, direitos"
        " reais, gravames ou inscrições eventualmente existentes em sua matrícula"
        " de origem, exceto quando disserem respeito ao próprio"
        " legitimado.\nFoi dispensado o Instrumento da Demarcação Urbanística,"
        " nos termos do § 9º do art. 31 da Lei Federal nº 13.465/2017.\nO"
        " projeto de regularização fundiária apresentado atende aos requisitos"
        " previstos nos artigos 35 e 36 da Lei Federal nº 13.465/2017, deixo"
        " de apresentar o cronograma físico e o termo de compromisso por se"
        " tratar de regularização de núcleo urbano informal que já possua a"
        " infraestrutura essencial implantada e para o qual não haja"
        " compensações urbanísticas ou ambientais ou outras obras e serviços a"
        " serem executados (art. 30, § 1º do Decreto nº 9.310/2018).\nTambém"
        " deixo de apresentar a A.R.T./R.R.T. referente ao projeto de"
        " regularização fundiária, haja vista que o responsável técnico se trata"
        " de servidor ou empregado público (art. 21, § 3º do Decreto nº"
        " 9.310/2018).\n\nO presente processo foi instaurado para titulação"
        " final dos beneficiários do Núcleo Urbano Consolidado, cujo parcelamento"
        " do solo encontra-se registrado junto ao Cartório de Registro de"
        " Imóveis de Taguatinga - TO, conforme Certidão de Inteiro Teor da"
        " Matrícula nº 6.043, o que dispensa a apresentação do projeto de"
        " regularização fundiária aprovado, conforme o parágrafo único do art."
        " 38 do Decreto 9.310/2018.\n\nQuanto à etapa de buscas e notificações,"
        " cumpre informar que, após a expedição das notificações dos"
        " proprietários tabulares, confrontantes e terceiros diretamente"
        " interessados, houve a publicação de edital de forma a gerar ampla"
        " publicidade dos trabalhos realizados por este Município, cumprindo"
        " todos os requisitos impostos pelo art. 31, § 1º ao 9º da Lei Federal"
        " nº 13.465/2017. Vencidos os prazos a partir de cada uma das"
        " notificações, bem como do edital, certifico que não houve nenhuma"
        " impugnação, havendo, assim, presunção de concordância ao"
        " procedimento, conforme disposto no artigo 31, § 6º da Lei Federal nº"
        " 13.465/2017.\nDeste modo, o oficial de registro fica dispensado de"
        " providenciar quaisquer notificações, conforme o art. 42, § 9º do"
        " Decreto nº 9.310/2018, uma vez cumprido esse rito pelo Município.\nInformo,"
        " ainda, que o presente procedimento independe da existência de lei"
        " municipal específica que trate de medidas ou posturas de interesse"
        " local aplicáveis a projetos de regularização fundiária urbana, nos"
        " termos do parágrafo único do art. 28 da Lei Federal nº 13.465/2017."
    )
    pdf.multi_cell(0, 6, limpar_texto(texto_relatorio), align="J")

    # --- 4. DA CONCLUSÃO ---
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, limpar_texto("4. DA CONCLUSÃO"), 0, 1)
    pdf.set_font("Arial", "", 11)

    texto_conclusao = (
        "Ante o exposto, uma vez cumpridas todas as fases do processo"
        " administrativo de regularização fundiária, certifico, neste ato, sua"
        " conclusão, nos termos do art. 40 da Lei 13.465/2017, em virtude da"
        " aprovação do Projeto de Regularização Fundiária e identificação dos"
        " ocupantes de cada unidade imobiliária, conforme Decreto Municipal nº"
        " 46/2026, publicado em 10 de março de 2026, e listagem de ocupantes,"
        " ambas anexas a esta certidão."
    )
    pdf.multi_cell(0, 7, limpar_texto(texto_conclusao), align="J")

    # --- ASSINATURA ---
    pdf.ln(15)
    mes_str = obter_mes_extenso(data_manual.month)
    data_formatada = (
        f"Taguatinga/TO, {data_manual.day} de {mes_str} de {data_manual.year}."
    )
    pdf.cell(0, 10, limpar_texto(data_formatada), 0, 1, "R")

    # --- VERIFICAÇÃO DE ESPAÇO CRÍTICO ---
    espaco_restante = pdf.page_break_trigger - pdf.get_y()
    if espaco_restante < 50:
        pdf.add_page()
        pdf.ln(15)
    else:
        pdf.ln(20)

    # Desenha a linha e os textos da assinatura
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "PAULO ROBERTO RIBEIRO", 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "Prefeito Municipal de Taguatinga - TO", 0, 1, "C")

    retorno_pdf = pdf.output(dest="S")
    if isinstance(retorno_pdf, str):
        return retorno_pdf.encode("latin-1")
    return bytes(retorno_pdf)

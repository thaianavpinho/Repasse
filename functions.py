import polars as pl
import pandas as pd
import re
import zipfile
import os
import glob
import streamlit as st
import datetime
import calendar
import pathlib
import time


def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split("([0-9]+)", key)]
    return sorted(l, key=alphanum_key)


def append_skus(selecionados, lista):
    lista.append(selecionados)


def read_all_bases():
    if check_for_new_file("data/deparas.xlsx", "data/*.parquet"):
        ini = time.time()
        read_excel_parquets("data/deparas.xlsx")
        fim = time.time()
        st.write(f"atualizou em {int(fim-ini)} segundos!")

    cestas = pl.read_parquet("data/cestas.parquet")
    clientes = pl.read_parquet("data/cliente.parquet")
    segs = pl.read_parquet("data/seg_consolidado.parquet")
    depara_acoes = pl.read_parquet("data/depara_acoes.parquet")
    depara_acoes = depara_acoes.with_columns(
        pl.concat_str(["COD_INICIATIVA", "INICIATIVA"], separator=" - ").alias(
            "depara_acao"
        )
    ).sort(by="COD_INICIATIVA")
    # pallets = pl.read_parquet('data/pallet.parquet').select(['cod_sku', 'Caixas Pallet'])

    clientes = clientes.join(segs, on="segmento", how="left")

    produtos = pl.read_parquet("data/produtos.parquet")
    # produtos = produtos.join(pallets, on='cod_sku', how='left')

    precos = (
        pl.read_parquet("data/precos.parquet")
        .select(
            [
                pl.concat_str(
                    [pl.col("Cob UNB").cast(pl.Utf8), pl.col("Cod Prod").cast(pl.Utf8)],
                    sep="_",
                ).alias("chave"),
                "Cob UNB",
                "Cod Prod",
                "Nome Produto",
                "TTV CX Frio",
                "TTV CX ASR",
            ]
        )
        .sort(["Cob UNB", "Cod Prod"])
    )

    bases_foco = pl.read_parquet("data/bloqueios.parquet")

    produtos = produtos.with_columns(
        pl.concat_str([pl.col("cod_sku"), pl.col("nome_sku")], sep=" - ").alias(
            "cod_nome_sku"
        )
    )

    clientes = clientes.with_columns(pl.col("seg_consolidado").fill_null("outros"))
    return clientes, cestas, segs, produtos, precos, bases_foco, depara_acoes


def get_excel_sheet_names(file_path):
    sheets = []
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        xml = zip_ref.read("xl/workbook.xml").decode("utf-8")
    for s_tag in re.findall("<sheet [^>]*", xml):
        sheets.append(re.search('name="[^"]*', s_tag).group(0)[6:])
    return sheets


def check_for_new_file(base_files: str, parquet_files: str) -> bool:
    """
    passa os caminhos dos arquivos que serão passados para o glob, pode usar '*' como wildcard
    retorna true se algum dos aquivos do base files for mais recente que os arquivos em parquet
    """
    if glob.glob(parquet_files):
        base_files_dates = [os.path.getmtime(file) for file in glob.glob(base_files)]
        parquet_files_dates = [
            os.path.getmtime(parquet) for parquet in glob.glob(parquet_files)
        ]
        return any([x > y for x in base_files_dates for y in parquet_files_dates])
    return True


def read_excel_parquets(path: str, destino: str) -> None:
    """Lê o Excel e Salva em parquets"""
    sheets = get_excel_sheet_names(path)
    for sheet in sheets:
        if sheet in ["repasse", "cerveja", "depara_repasse"]:
            p = pd.read_excel(path, sheet_name=sheet)
            p.replace("-", "0.0")
            p.to_parquet(f"{destino}/{sheet}.parquet")


def fazer_acao(nome_ação, n_acao, cestas, clientes, produtos, bases_foco, depara_acoes):

    produtos = produtos.clone()
    cestas = cestas.clone()
    clientes = clientes.clone()

    with st.expander(nome_ação, True):
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.multiselect(
                "Cestas", sorted(cestas["Cesta"].unique()), key="cesta_" + str(n_acao)
            )

            if st.session_state["cesta_" + str(n_acao)]:
                skus = (
                    cestas.filter(
                        pl.col("Cesta").is_in(st.session_state["cesta_" + str(n_acao)])
                    )
                    .select(pl.col("cod_sku"))
                    .unique()
                )
                skus = list(list(skus)[0])
                produtos = produtos.filter(pl.col("cod_sku").is_in(skus))

            st.multiselect(
                "Marcas",
                sorted(list(produtos["marca"].unique())),
                key="marcas_" + str(n_acao),
            )

            if st.session_state["marcas_" + str(n_acao)]:
                produtos = produtos.filter(
                    pl.col("marca").is_in(st.session_state["marcas_" + str(n_acao)])
                )

            st.multiselect(
                "Embalagens",
                sorted(produtos["embalagem"].unique()),
                key="embalagem_" + str(n_acao),
            )

            if st.session_state["embalagem_" + str(n_acao)]:
                produtos = produtos.filter(
                    pl.col("embalagem").is_in(
                        st.session_state["embalagem_" + str(n_acao)]
                    )
                )

            st.multiselect(
                "Produtos",
                sorted(produtos["cod_nome_sku"].unique()),
                key="produto_" + str(n_acao),
            )

            if st.session_state["produto_" + str(n_acao)]:
                produtos = produtos.filter(
                    pl.col("cod_nome_sku").is_in(
                        st.session_state["produto_" + str(n_acao)]
                    )
                )

            if "selected_" + str(n_acao) not in st.session_state:
                st.session_state["selected_" + str(n_acao)] = ""
            if produtos.shape[0] <= 100:
                st.session_state["selected_" + str(n_acao)] = ", ".join(
                    [str(x) for x in produtos.to_pandas()["cod_sku"].unique()]
                )
            else:
                st.session_state["selected_" + str(n_acao)] = (
                    "excedendo limite de 100 skus"
                )

            st.text_area(
                "Custom Filters",
                value=st.session_state["selected_" + str(n_acao)],
                key="custom_" + str(n_acao),
            )

        with col2:
            st.multiselect(
                "Comercial",
                sorted(clientes["comercial"].unique()),
                key="comercial_" + str(n_acao),
            )

            if st.session_state["comercial_" + str(n_acao)]:
                clientes = clientes.filter(
                    pl.col("comercial").is_in(
                        st.session_state["comercial_" + str(n_acao)]
                    )
                )

            st.multiselect(
                "Operação",
                sorted(clientes["operacao"].unique()),
                key="operacao_" + str(n_acao),
            )

            if st.session_state["operacao_" + str(n_acao)]:
                clientes = clientes.filter(
                    pl.col("operacao").is_in(
                        st.session_state["operacao_" + str(n_acao)]
                    )
                )

            st.multiselect(
                "Segmento Consolidado",
                sorted(clientes["seg_consolidado"].unique()),
                key="seg_consolidado_" + str(n_acao),
            )

            if st.session_state["seg_consolidado_" + str(n_acao)]:
                clientes = clientes.filter(
                    pl.col("seg_consolidado").is_in(
                        st.session_state["seg_consolidado_" + str(n_acao)]
                    )
                )

            st.multiselect(
                "Segmento",
                sorted(clientes["segmento"].unique()),
                key="segmento_" + str(n_acao),
            )

            if st.session_state["segmento_" + str(n_acao)]:
                clientes = clientes.filter(
                    pl.col("segmento").is_in(
                        st.session_state["segmento_" + str(n_acao)]
                    )
                )

            st.radio(
                "Incluir ou Bloquear?",
                ["Incluir", "Bloquear"],
                horizontal=True,
                key="foco_incluir_" + str(n_acao),
            )
            st.multiselect(
                "Bases Foco",
                sorted(bases_foco["motivo"].unique()),
                key="bases_foco_" + str(n_acao),
            )

            if st.session_state["bases_foco_" + str(n_acao)]:
                bases_foco = bases_foco.filter(
                    pl.col("motivo").is_in(
                        st.session_state["bases_foco_" + str(n_acao)]
                    )
                )
                if st.session_state["foco_incluir_" + str(n_acao)] == "Incluir":
                    clientes = clientes.filter(
                        pl.col("chave").is_in(bases_foco["chave"].unique())
                    )
                else:
                    clientes = clientes.filter(
                        ~pl.col("chave").is_in(bases_foco["chave"].unique())
                    )

                if "df_bases_foco_" + str(n_acao) not in st.session_state:
                    st.session_state["df_bases_foco_" + str(n_acao)] = clientes
                else:
                    st.session_state["df_bases_foco_" + str(n_acao)] = clientes

        with col3:
            st.text_input("Nome Ação", key="nome_acao_" + str(n_acao))
            st.text_input("Justificativa Ação", key="just_acao_" + str(n_acao))
            st.date_input("Data Inicial", key="data_inicial_" + str(n_acao))
            ano = datetime.date.today().year
            mes = datetime.date.today().month
            st.date_input(
                "Data Final",
                value=datetime.date(ano, mes, calendar.monthrange(ano, mes)[1]),
                key="data_final_" + str(n_acao),
            )
            st.text_input("TTV Fixo", "", key="ttv_fixo_" + str(n_acao))
            st.text_input("TTV %", "", key="ttv_porcento_" + str(n_acao))

        with col4:
            st.text_input("Iniciativa", "INI-", key="iniciativa_" + str(n_acao))
            st.number_input("Min SKU", value=1, key="min_sku_" + str(n_acao))
            st.number_input("Max SKU", value=1000, key="max_sku_" + str(n_acao))
            st.number_input(
                "Max SKU Ação", value=999999, key="max_sku_acao_" + str(n_acao)
            )
            st.number_input(
                "Disponibilidade Pedidos", value=100, key="disp_pedidos_" + str(n_acao)
            )
            st.number_input(
                "Disponibilidade SKU", value=1000, key="disp_sku_" + str(n_acao)
            )

        with col5:
            st.selectbox(
                "Origem verba",
                ["1 - GEO", "2 - AC"],
                index=0,
                key="origem_verba_" + str(n_acao),
            )
            st.selectbox(
                "ZBB",
                ["1 - CERV", "2 - NAB", "3 - MATCH", "4 - MKTPLACE"],
                index=1,
                key="zbb_verba_" + str(n_acao),
            )
            st.selectbox(
                "Canal",
                ["1 - ASR", "2 - ON TRADE", "3 - Central de Bebidas"],
                index=1,
                key="canal_verba_" + str(n_acao),
            )
            st.selectbox(
                "Iniciativa",
                natural_sort(depara_acoes["depara_acao"].unique()),
                key="acoes_verba" + str(n_acao),
            )

        with col6:

            st.metric("Clientes", clientes.shape[0])
            st.metric("Skus", produtos.shape[0])
            st.file_uploader(
                "Importar Base Fechada (CSV com UNB, PDV)",
                key="base_fechada_" + str(n_acao),
                accept_multiple_files=False,
                type=["csv"],
            )

            if st.session_state["base_fechada_" + str(n_acao)]:
                base = pl.read_csv(
                    st.session_state["base_fechada_" + str(n_acao)],
                    encoding="latin1",
                    infer_schema_length=200,
                    sep=";",
                )
                base.columns = ["unb", "cod_pdv"]
                base = base.with_columns(pl.concat_str("*", sep="_").alias("chave"))

                if st.session_state["bases_foco_" + str(n_acao)]:
                    if st.session_state["foco_incluir_" + str(n_acao)] == "Incluir":
                        base = base.filter(
                            pl.col("chave").is_in(bases_foco["chave"].unique())
                        )
                    else:
                        base = base.filter(
                            ~pl.col("chave").is_in(bases_foco["chave"].unique())
                        )

                clientes = base.drop("chave")

        # st.download_button('Baixar Formato Lift', criar_template_lift(clientes).to_csv(index=False, quotechar='"',sep=';', header=False).encode('ISO-8859-15'), 'base.csv', mime='text/csv', key = 'download_csv_lift'+str(n_acao))

    if "df_base_fechada_" + str(n_acao) not in st.session_state:
        st.session_state["df_base_fechada_" + str(n_acao)] = clientes
    else:
        st.session_state["df_base_fechada_" + str(n_acao)] = clientes


def criar_template_lift(cliente: pl.DataFrame):
    cliente = cliente.clone()

    cliente = cliente.with_columns(
        [
            pl.col("chave").str.split("_").arr.get(0).alias("unb").str.zfill(4),
            pl.col("chave").str.split("_").arr.get(1).alias("pdv"),
        ]
    ).select(pl.concat_str(["pdv", "unb"], separator="_"))

    return cliente.to_pandas()


def criar_template_cora_acao(
    session, clientes: pl.DataFrame, depara_ações: pl.DataFrame
):
    all_dfs = []

    n_acao = sorted(
        [int(x.split("_")[-1]) for x in session.keys() if x.startswith("nome_acao")]
    )
    for n in n_acao:
        clientes_local = clientes.clone()
        filters = {
            name + "_" + str(n): [name, session[name + "_" + str(n)]]
            for name in ["comercial", "operacao", "seg_consolidado", "segmento"]
            if session[name + "_" + str(n)]
        }

        for name in filters.keys():
            clientes_local = clientes_local.filter(
                pl.col(filters[name][0]).is_in(filters[name][1])
            )

        skus_selecionados = session["selected_" + str(n)]

        if session["base_fechada_" + str(n)] or session["bases_foco_" + str(n)]:
            clientes_local = st.session_state["df_base_fechada_" + str(n)]

        clientes_local = (
            clientes_local.select(["unb", "cod_pdv"])
            .sort(["unb", "cod_pdv"])
            .with_columns(
                [
                    pl.lit(skus_selecionados).alias("cod_sku"),
                    pl.lit(
                        "_".join(
                            [
                                session["origem_verba_" + str(n)].split(" - ")[0],
                                session["zbb_verba_" + str(n)].split(" - ")[0],
                                session["canal_verba_" + str(n)].split(" - ")[0],
                                session["acoes_verba" + str(n)].split(" - ")[0],
                            ]
                        )
                        + "."
                        + session["just_acao_" + str(n)]
                    ).alias("promo_justificativa"),
                    pl.lit(n).alias("agrupador"),
                ]
                + [
                    pl.lit(session[x[1] + str(n)]).alias(x[0])
                    for x in [
                        ("titulo", "nome_acao_"),
                        ("descricao", "nome_acao_"),
                        ("ttv_fixo", "ttv_fixo_"),
                        ("desconto_percentual", "ttv_porcento_"),
                        ("data_inicio", "data_inicial_"),
                        ("data_fim", "data_final_"),
                        ("min_sku", "min_sku_"),
                        ("max_sku", "max_sku_"),
                        ("quantidade_maxima_skus_promocao", "max_sku_acao_"),
                        ("disponibilidade_pedido", "disp_pedidos_"),
                        ("disponibilidade_sku", "disp_sku_"),
                        ("id_iniciativa", "iniciativa_"),
                    ]
                ]
            )
            .with_columns([pl.col("data_fim").dt.offset_by("7d").alias("data_entrega")])
            .with_columns(
                [
                    pl.col(name).dt.strftime("%d/%m/%Y")
                    for name in ["data_inicio", "data_fim", "data_entrega"]
                ]
            )
            .select(
                [
                    "agrupador",
                    "titulo",
                    "descricao",
                    "unb",
                    "cod_pdv",
                    "cod_sku",
                    "ttv_fixo",
                    "desconto_percentual",
                    "data_inicio",
                    "data_fim",
                    "data_entrega",
                    "min_sku",
                    "max_sku",
                    "quantidade_maxima_skus_promocao",
                    "disponibilidade_pedido",
                    "disponibilidade_sku",
                    "promo_justificativa",
                    "id_iniciativa",
                ]
            )
        )

        all_dfs.append(clientes_local)

    return pl.concat(all_dfs).to_pandas()


def salvar_template_ação(session, number_acao):
    return True


def create_promos_from_file(session):
    file = st.file_uploader(
        "Importar Base Fechada (CSV com UNB, PDV)",
        key="base_fechada_" + str(0),
        accept_multiple_files=False,
        type=["csv"],
    )

    if file != None:
        df = pd.read_csv(file, encoding="latin1", delimiter=";")
        session["count"] = df.shape[0]
        campos = [
            "operacao_",
            "nome_acao_",
            "nome_acao_",
            "ttv_fixo_",
            "ttv_porcento_",
            "data_inicial_",
            "data_final_",
            "min_sku_",
            "max_sku_",
            "disp_pedidos_",
            "disp_sku_",
            "just_acao_",
            "iniciativa_",
        ]
        for n in range(df.shape[0]):
            session["operacao_" + str(n + 1)] = df.loc[n + 1, "operacao"]
            session["selected_" + str(n + 1)] = str(df.loc[n + 1, "cod_sku"])

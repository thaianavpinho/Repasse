import streamlit as st

import altair as alt

from functions import *

import pandas as pd
import polars as pl

from pandas.api.types import is_numeric_dtype

from PIL import Image as PILImage
import io
import base64


def convert_image(string: str) -> str:
    image = PILImage.open(string)
    output = io.BytesIO()
    image.save(output, format="PNG")
    encoded_string = (
        "data:image/png;base64," + base64.b64encode(output.getvalue()).decode()
    )
    return encoded_string


def make_text(
    df, texto: str, fonte, offset, x, y, color_param="black", f_weight="normal"
):
    canal = st.session_state["canal"]
    select_canal = {
        "BAR": "rota-delta ttv",
        "ASR": "asr-delta ttv",
        "VAREJO": "varejo-delta ttc",
        "ATACADO": "atacado-delta ttc",
    }
    if texto.endswith("delta"):
        text_chart = (
            alt.Chart(df)
            .mark_text(align="center", dy=offset, size=fonte, fontWeight=f_weight)
            .encode(
                x=f"{x}:N",  # pixels from left
                color=alt.condition(
                    alt.datum[select_canal[canal]] <= 0,
                    alt.value("green"),
                    alt.value("red"),
                ),
                y=alt.Y(y, axis=alt.Axis(labels=False, title="")),  # pixels from top
                text=texto,
            )
        )
    else:
        text_chart = (
            alt.Chart(df)
            .mark_text(
                align="center",
                dy=offset,
                size=fonte,
                color=color_param,
                fontWeight=f_weight,
            )
            .encode(
                x=f"{x}:N",  # pixels from left
                y=alt.Y(y, axis=alt.Axis(labels=False, title="")),  # pixels from top
                text=texto,
            )
        )

    return text_chart


def make_graph_repasse(df: pd.DataFrame, h_chart, w_chart, h_pic, w_pic, canal):
    match canal:
        case "BAR":
            y = "rota-ttc pos"
            df["line1"] = df["nome_slide"]
            df["line2"] = "TTV Pré: R$ " + df["rota-ttv pre"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
            df["line3"] = "TTV Pós: R$ " + df["rota-ttv pos"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
            df["line_delta"] = "Delta TTV: R$ " + df["rota-delta ttv"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
            df["line4"] = "TTC Pós: R$ " + df["rota-ttc pos"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
        case "ASR":
            y = "asr-ttc pos"
            df["line1"] = df["nome_slide"]
            df["line2"] = "TTV Pré: R$ " + df["asr-ttv pre"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
            df["line3"] = "TTV Pós: R$ " + df["asr-ttv pos"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
            df["line_delta"] = "Delta TTV: R$ " + df["asr-delta ttv"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
            df["line4"] = "TTC Pós: R$ " + df["asr-ttc pos"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
        case "VAREJO":
            y = "varejo-ttc pos"
            df["line1"] = df["nome_slide"]
            df["line2"] = "TTC Pré: R$ " + df["varejo-ttc pre"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
            df["line3"] = "TTC Pós: R$ " + df["varejo-ttc pos"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
            df["line_delta"] = "Delta TTC: R$ " + df["varejo-delta ttc"].round(2).map(
                "{:,.2f}".format
            ).astype(str)

        case "ATACADO":
            y = "atacado-ttc pos"
            df["line1"] = df["nome_slide"]
            df["line2"] = "TTC Pré: R$ " + df["atacado-ttc pre"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
            df["line4"] = "TTC Pós: R$ " + df["atacado-ttc pos"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
            df["line_delta"] = "Delta TTC: R$ " + df["atacado-delta ttc"].round(2).map(
                "{:,.2f}".format
            ).astype(str)
        case _:
            y = "a"

    df["nome_sorted"] = (
        df[y]
        .round(2)
        .astype(str)
        .str.replace("10", "zzy")
        .str.replace("11", "zzz")
        .str.replace(".", "")
        + df["nome_slide"]
    )

    y_min = df[y].min()
    y_max = df[y].max()

    df["text1"] = df["nome_sorted"]

    chart = (
        alt.Chart(df)
        .mark_image(height=h_pic, baseline="bottom")
        .encode(
            x=alt.X("nome_sorted:N", axis=alt.Axis(labels=False, title="")),
            y=alt.Y(
                f"{y}:Q",
                axis=alt.Axis(labels=False, grid=False, title=""),
                scale=alt.Scale(domain=[y_min - 0.5, y_max + 0.5]),
            ),
            url="caminho",
        )
        .properties(height=h_chart, width=w_chart)
    )

    tick_offset = 20
    font_size = 15

    tick = chart.mark_tick(
        yOffset=tick_offset,
        color="black",
        thickness=2,
        size=w_chart / len(df["nome_sorted"].unique()) - 50,  # controls width of tick.
    ).encode(x="nome_sorted", y=alt.Y(y, axis=alt.Axis(labels=False)))

    lines = ["bold"] + ["normal"] * len([x for x in df.columns if x.startswith("line")])

    texts = [
        make_text(
            df,
            name,
            font_size,
            tick_offset + font_size * (i + 1),
            "nome_sorted",
            y,
            f_weight=lines[i],
        )
        for i, name in enumerate([x for x in df.columns if x.startswith("line")])
    ]

    return alt.layer(chart, *texts, tick)


# read_excel_parquets('data/repasse/graficos.xlsx', 'data/repasse')
# depara_repasse = pl.read_parquet('data/repasse/depara_repasse.parquet').to_pandas()
# depara_repasse['Caminho'] = depara_repasse['Caminho'].apply(convert_image)
# depara_repasse.to_parquet('data/repasse/depara_repasse.parquet')

repasse = pl.read_parquet("data/repasse/repasse.parquet")

depara_repasse = pl.read_parquet("data/repasse/depara_repasse.parquet")

repasse = repasse.join(depara_repasse, left_on="SKU", right_on="SKU")

repasse.columns = [x.lower() for x in repasse.columns]

title = "Out/25"

st.set_page_config(
    page_title=f"PINC NAB - {title}",
    page_icon="📈",
    initial_sidebar_state="expanded",
    layout="wide",
)

reduce_header_height_style = """
    <style>
        div.block-container {padding-top:1rem;}
    </style>
"""
st.markdown(reduce_header_height_style, unsafe_allow_html=True)

st.header(f"Resumo Repasse - {title}")

col1, col2, col3, col4, col5 = st.columns(5)

grupo_dict = {"Single": ["Single", "Premium"], "Multi": ["Multi1", "Multi2"]}

with col1:
    uf = st.selectbox("UF", sorted(repasse["uf"].unique()), 0, key="uf")
with col2:
    canal = st.selectbox("Canal", ["BAR", "ASR", "VAREJO", "ATACADO"], 0, key="canal")
# with col3:
# grupo_select = st.selectbox('Grupo', ['Single', 'Multi'], 0, key='grupo')

comum = [
    "uf",
    "geo",
    "emb.",
    "sku",
    "qtd cx",
    "nome_slide",
    "grupo",
    "nome",
    "marca",
    "caminho",
]

canais = {
    "BAR": ["rota-ttv pre", "rota-ttv pos", "rota-delta ttv", "rota-ttc pos"],
    "ASR": ["asr-ttv pre", "asr-ttv pos", "asr-delta ttv", "asr-ttc pos"],
    "VAREJO": ["varejo-ttc pre", "varejo-ttc pos", "varejo-delta ttc"],
    "ATACADO": ["atacado-ttc pre", "atacado-ttc pos", "atacado-delta ttc"],
}

resumo_canais = repasse.clone()
resumo_canais = resumo_canais[
    [
        "uf",
        "geo",
        "sku",
        "rota-ttv pos",
        "asr-ttv pos",
        "varejo-ttc pos",
        "atacado-ttc pos",
    ]
]
resumo_canais.columns = ["UF", "Geo", "SKU", "ROTA", "ASR", "VAREJO", "ATACADO"]

repasse = repasse.filter(pl.col("uf") == st.session_state["uf"])
# repasse = repasse.filter(pl.col('grupo').is_in(grupo_dict.get(grupo_select)))
repasse = repasse.select(comum + canais.get(st.session_state["canal"])).to_pandas()

graphs = [
    make_graph_repasse(repasse[repasse["grupo"] == grupo], 250, 1600, 120, 75, canal)
    for grupo in ["Single", "Premium", "Multi1", "Multi2"]
]  # grupo_dict.get(grupo_select)]

graph = alt.vconcat(*graphs).properties(
    title=alt.Title(
        f'{st.session_state["canal"].title()} - {st.session_state["uf"]}',
        fontSize=30,
        fontWeight="bold",
    )
)

st.altair_chart(graph)

tab1, tab2 = st.columns(2)

with tab1:
    st.dataframe(
        repasse.drop(
            ["emb.", "qtd cx", "nome_slide", "grupo", "nome", "marca", "caminho"],
            axis=1,
        ),
        hide_index=True,
        column_config={
            s: st.column_config.NumberColumn(s.split("-")[-1].upper(), format="R$ %.2f")
            for s in repasse.columns
            if is_numeric_dtype(repasse[s])
        },
        use_container_width=True,
        height=2000,
    )

with tab2:
    st.dataframe(
        resumo_canais.filter(pl.col("UF") == st.session_state["uf"]).to_pandas(),
        hide_index=True,
        column_config={
            "UF": "Estado",
            "ROTA": st.column_config.NumberColumn(
                "Rota",
                format="R$ %2f",
            ),
            "ASR": st.column_config.NumberColumn(
                "ASR",
                format="R$ %2f",
            ),
            "VAREJO": st.column_config.NumberColumn(
                "Varejo",
                format="R$ %2f",
            ),
            "ATACADO": st.column_config.NumberColumn(
                "Atacado",
                format="R$ %2f",
            ),
        },
        use_container_width=True,
        height=2000,
    )


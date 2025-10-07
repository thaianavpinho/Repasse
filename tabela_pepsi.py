import streamlit as st
import polars as pl

import random
from datetime import date

from functions import *

import numpy as np
import pandas as pd
import io
import base64
from PIL import Image as PILImage



def convert_image(string: str) -> str:
    image = PILImage.open(string)
    output = io.BytesIO()    
    image.save(output, format='PNG')
    encoded_string = "data:image/png;base64,"+base64.b64encode(output.getvalue()).decode()
    return encoded_string

st.set_page_config("Profiles", "👤", layout='wide')


# if check_for_new_file('data/repasse/graficos.xlsx', 'data/repasse/*.parquet'):   
#     read_excel_parquets('data/repasse/graficos.xlsx')
#     depara_repasse = pl.read_parquet('data/repasse/depara_repasse.parquet').to_pandas()
#     depara_repasse['Caminho'] = depara_repasse['Caminho'].apply(convert_image)
#     depara_repasse.to_parquet('data/repasse/depara_repasse.parquet')

# depara = pl.from_pandas(pd.read_excel('data/repasse/graficos.xlsx', sheet_name='nome_ac'))
# depara_repasse = pl.from_pandas(pd.read_excel('data/repasse/graficos.xlsx', sheet_name='depara_repasse'))

depara = pl.read_parquet('data/repasse/nome_ac.parquet')
depara_repasse = pl.read_parquet('data/repasse/depara_repasse.parquet')

depara = depara.join(depara_repasse, left_on='nome_sku', right_on='SKU', how='left')

df = pd.read_csv('precos.csv', sep=';', encoding='latin1')
df.columns = ['ano', 'mes', 'tipo_operação', 'sku', 'nome_sku', 'volume', 'caixas', 'unidades', 'faturamento','cobertura']

df = pl.from_pandas(df).with_columns([
    pl.col(['volume', 'faturamento']).str.strip('-R$ ').str.replace(',','.').cast(pl.Float64),
    pl.when(pl.col('tipo_operação') == 'DIRETA').then(pl.lit('DIRETA')).otherwise(pl.lit('ROTA')).alias('tipo_operação')
]).filter(pl.col('volume') > 0).join(depara, left_on='sku', right_on='sku', how='left').filter(pl.col('ano') == 2023)

df = df.groupby(['mes', 'nome_slide', 'tipo_operação', 'Grupo', 'Caminho']).agg([
    pl.sum('faturamento'),
    pl.sum('volume'),
    pl.sum('caixas'),
    pl.sum('unidades'),
    pl.sum('cobertura').alias('distribuição'),
]).with_columns([
    (pl.col('faturamento')/pl.col('unidades')).alias('TTV'),
    pl.col('nome_slide').alias('nome_sku'),
    pl.col('Caminho').alias('caminho64')
    ]).filter(pl.col('mes') < 11).filter(pl.col('tipo_operação') == 'ROTA')\
        .filter(pl.col('Grupo').is_in(['Multi1', 'Multi2']))\
        .sort('mes')\
        .groupby(by=['nome_slide', 'caminho64', 'Grupo'], maintain_order=True).agg([
        #pl.col('faturamento'),
        pl.col('volume'),
        #pl.col('caixas'),
        #pl.col('unidades'),
        pl.col('distribuição'),
        pl.col('TTV'),
    ]).with_columns([
        pl.col('volume').list.get(-1).alias('Volume M-1'),
        pl.col('distribuição').list.get(-1).alias('Disttribuição M-1'),
        pl.concat_str([((pl.col('TTV').list.get(-1)/pl.col('TTV').list.get(0)-1)*100).round(1).cast(pl.Utf8), pl.lit(' %')]).alias('Variação TTV'),
    ]).drop(['Grupo', 'distribuição'])

st.data_editor(df.to_pandas(), column_config={
    "caminho64": st.column_config.ImageColumn("Produto"),
    'volume': st.column_config.BarChartColumn(
        "Volume (hl)",
        width="medium",
    ),
    "TTV": st.column_config.LineChartColumn(
        "TTV",
        width="medium",
        y_min=0,
    ),
    "Variação TTV": st.column_config.TextColumn(
        "Variação TTV"
        ),
    
    }, hide_index=True, height=1500)

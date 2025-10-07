import streamlit as st

import altair as alt

from functions import *

import pandas as pd
import polars as pl

from pandas.api.types import is_numeric_dtype

from PIL import Image as PILImage
import io
import base64


st.set_page_config(
    page_title="PINC Cerveja - Jan/24", page_icon="🍺", initial_sidebar_state="expanded", layout='wide'
)

reduce_header_height_style = """
    <style>
        div.block-container {padding-top:1rem;}
    </style>
"""
st.markdown(reduce_header_height_style, unsafe_allow_html=True)

def convert_image(string: str) -> str:
    image = PILImage.open(string)
    output = io.BytesIO()    
    image.save(output, format='PNG')
    encoded_string = "data:image/png;base64,"+base64.b64encode(output.getvalue()).decode()
    return encoded_string
    
def make_text(df, texto: str, fonte, offset, x, y, color_param = 'black', f_weight = 'normal'):
    canal = 'BAR'
    select_canal = {'BAR': 'rota-delta ttv', 'ASR': 'asr-delta ttv', 'VAREJO': 'varejo-delta ttc', 'ATACADO': 'atacado-delta ttc'}
    if texto.endswith('delta'):
        text_chart = alt.Chart(df).mark_text(
            align="center",
            dy=offset,
            size=fonte, fontWeight=f_weight
        ).encode(
            x=f'{x}:N',  # pixels from left
            color = alt.condition(
                alt.datum['delta ttc'] <= 0,
                alt.value("green"), alt.value("red")
            ),
            y=alt.Y(y,axis=alt.Axis(labels=False, title='')),  # pixels from top
            text=texto)
    else:
        text_chart = alt.Chart(df).mark_text(
            align="center",
            dy=offset,
            size=fonte, color = color_param, fontWeight=f_weight
        ).encode(
            x=f'{x}:N',  # pixels from left
            y=alt.Y(y,axis=alt.Axis(labels=False, title='')),  # pixels from top
            text=texto)   
    
    return text_chart

def make_graph_repasse(df: pd.DataFrame, h_chart, w_chart, h_pic, w_pic, canal):
    match canal:
        case 'BAR':
            y = 'ttc'
            df['line1'] = df['sku']
            df['line2'] = 'TTV: R$ ' + df['ttv'].round(2).map('{:,.2f}'.format).astype(str)
            df['line3'] = 'TTC: R$ ' + df['ttc'].round(2).map('{:,.2f}'.format).astype(str)
            df['line_delta'] = 'Delta TTC: R$ ' + df['delta ttc'].round(2).map('{:,.2f}'.format).astype(str)
            df['line4'] = 'Margem: ' + df['margem'].round(2).map('{:,.0%}'.format).astype(str)
        case 'ASR':
            y = 'asr-ttv pos'
            df['line1'] = df['nome_slide']
            df['line2'] = 'TTV Pré: R$ ' + df['asr-ttv pre'].round(2).map('{:,.2f}'.format).astype(str)
            df['line3'] = 'TTV Pós: R$ ' + df['asr-ttv pos'].round(2).map('{:,.2f}'.format).astype(str)
            df['line_delta'] = 'Delta TTV: R$ ' + df['asr-delta ttv'].round(2).map('{:,.2f}'.format).astype(str)
            df['line4'] = 'TTC Pós: R$ ' + df['asr-ttc pos'].round(2).map('{:,.2f}'.format).astype(str)
        case 'VAREJO':
            y = 'varejo-ttc pos'
            df['line1'] = df['nome_slide']
            df['line2'] = 'TTC Pré: R$ ' + df['varejo-ttc pre'].round(2).map('{:,.2f}'.format).astype(str)
            df['line3'] = 'TTC Pós: R$ ' + df['varejo-ttc pos'].round(2).map('{:,.2f}'.format).astype(str)
            df['line_delta'] = 'Delta TTC: R$ ' + df['varejo-delta ttc'].round(2).map('{:,.2f}'.format).astype(str)
            df['line4'] = 'Promo'
            df['line5'] = 'Pré: R$ ' + df['varejo-promo pre'].astype(str) + ' | ' + df['varejo-%promo pre'].map('{:,.1%}'.format).astype(str)
            df['line6'] = 'Pós: R$ ' + df['varejo-promo pos'].astype(str) + ' | ' + df['varejo-%promo pos'].map('{:,.1%}'.format).astype(str)
        case 'ATACADO':
            y = 'atacado-ttc pos'
            df['line1'] = df['nome_slide']
            df['line2'] = 'TTC Pré: R$ ' + df['atacado-ttc pre'].round(2).map('{:,.2f}'.format).astype(str)
            df['line3'] = 'Desin Pré: R$ ' + df['atacado-desin pre'].round(2).map('{:,.2f}'.format).astype(str)
            df['line4'] = 'TTC Pós: R$ ' + df['atacado-ttc pos'].round(2).map('{:,.2f}'.format).astype(str)
            df['line5'] = 'Desin Pós: R$ ' + df['atacado-desin pos'].round(2).map('{:,.2f}'.format).astype(str)
            df['line_delta'] = 'Delta TTC: R$ ' + df['atacado-delta ttc'].round(2).map('{:,.2f}'.format).astype(str)
        case _:
            y = 'a'
    
    df['nome_sorted'] = df[y].round(2).astype(str).str.replace('.','')
    
    for key, value in zip(reversed(['0','1','2','3','4','5','6','7','8','9','10', '11', '12', '13', '14', '15', '16', '115']), reversed('abcdefghijlmnopqrs')):
        df['nome_sorted'] = df['nome_sorted'].str.replace(key, value)
    
    df['nome_sorted'] = df['nome_sorted'] + df['sku']
    
    y_min = df[y].min()
    y_max = df[y].max()
    
    df['text1'] = df['nome_sorted']
    
    chart = alt.Chart(df).mark_image(
    height=h_pic,
    baseline='bottom').encode(
        x=alt.X('nome_sorted:N', axis=alt.Axis(labels=False, title='')),
        y=alt.Y(f'{y}:Q', axis=alt.Axis(labels=False, grid=False, title=''), scale=alt.Scale(domain=[y_min-0.5,y_max+0.5])),
        url='caminho').properties(
            height = h_chart,
            width = w_chart
        )
    
    tick_offset = 20
    font_size = 12
    
    tick = chart.mark_tick(
        yOffset=tick_offset,
        color='black',
        thickness=2,
        size = w_chart/len(df['nome_sorted'].unique()) - 10  # controls width of tick.
    ).encode(
        x='nome_sorted',
        y=alt.Y(y, axis=alt.Axis(labels=False))
    )
    
    lines = ['bold'] + ['normal']*len([x for x in df.columns if x.startswith('line')])
    
    texts = [
        make_text(df, name, font_size, tick_offset + font_size*(i+1), 'nome_sorted', y, f_weight=lines[i])
        for i, name in enumerate(
            [x for x in df.columns if x.startswith('line')]
            )
        ]
    
    return alt.layer(chart, *texts, tick)

read_excel_parquets('data/cerveja/graficos_cerveja.xlsx', 'data/cerveja')
depara_repasse = pl.read_parquet('data/cerveja/depara_repasse.parquet').to_pandas()
depara_repasse['Caminho'] = depara_repasse['Caminho'].apply(convert_image)
depara_repasse.to_parquet('data/cerveja/depara_repasse.parquet')

repasse = pl.read_parquet('data/cerveja/cerveja.parquet')   

repasse.columns = [x.lower() for x in repasse.columns]

depara_repasse = pl.read_parquet('data/cerveja/depara_repasse.parquet')

depara_repasse.columns = [x.lower() for x in depara_repasse.columns]

repasse = repasse.join(depara_repasse, left_on='sku', right_on = 'sku', suffix='_depara')

st.header('Resumo Repasse Cerveja - Mar/24')

col1, col2, col3, col4, col5 = st.columns(5)

grupo_dict = {'Single': ['Single', 'Premium'],
               'Multi': ['Multi1', 'Multi2']}

with col1:
    st.selectbox('Comercial', sorted(repasse.select('comercial').unique().to_series().to_list()), 0, key='comercial')
with col2:
    op = sorted(repasse.filter(pl.col('comercial') == st.session_state['comercial']).select('operação').unique().to_series().to_list())
    uf = st.selectbox('Comercial', op, 0, key='operacao')
#with col3:
    #grupo_select = st.selectbox('Grupo', ['Single', 'Multi'], 0, key='grupo')
    
comum = ['comercial','operação','sku','pack','marca', 'grupo', 'caminho']

canais = {
    'BAR': ['ttc', 'ttv', 'delta ttc', 'margem'],
    'ASR': ['asr-ttv pre', 'asr-ttv pos', 'asr-delta ttv', 'asr-ttc pos'],
    'VAREJO': ['varejo-ttc pre', 'varejo-promo pre', 'varejo-%promo pre', 'varejo-ttc pos', 'varejo-promo pos', 'varejo-%promo pos', 'varejo-delta ttc'],
    'ATACADO': ['atacado-ttc pre', 'atacado-desin pre', 'atacado-ttc pos', 'atacado-desin pos', 'atacado-delta ttc'],
}
    
repasse = repasse.filter((pl.col('comercial') == st.session_state['comercial']) & (pl.col('operação') == st.session_state['operacao']))
#repasse = repasse.filter(pl.col('grupo').is_in(grupo_dict.get(grupo_select)))
grupos = sorted(repasse.select('grupo').unique().to_series().to_list())
repasse = repasse.select(comum + canais.get('BAR')).to_pandas()

graphs = [
    make_graph_repasse(repasse[repasse['grupo'] == grupo], 250, 1600, 120, 75, 'BAR') 
    for grupo in grupos if grupo != 'NENHUM']


graph = alt.vconcat(*graphs).properties(title = alt.Title(f'{st.session_state["comercial"].upper()} - {st.session_state["operacao"].upper()}', fontSize=30, fontWeight='bold'))

st.altair_chart(graph)

# tab1, tab2 = st.columns(2)

# with tab1:
#     st.dataframe(
#         repasse.drop(['emb.', 'qtd cx', 'nome_slide', 'grupo', 'nome', 'marca', 'caminho'], axis=1),
#         hide_index=True,
#         column_config={s: st.column_config.NumberColumn(s.split('-')[-1].upper(), format='R$ %.2f')
#                        for s in repasse.columns if is_numeric_dtype(repasse[s])},
#         use_container_width=True, height=2000)
    
# with tab2:
#     st.dataframe(resumo_canais.filter(pl.col('UF') == st.session_state['uf']).to_pandas(), hide_index=True,
#                  column_config={
#                      'UF': 'Estado',
#                      'ROTA': st.column_config.NumberColumn('Rota', format='R$ %2f', ),
#                      'ASR': st.column_config.NumberColumn('ASR', format='R$ %2f', ),
#                      'VAREJO': st.column_config.NumberColumn('Varejo', format='R$ %2f', ),
#                      'ATACADO': st.column_config.NumberColumn('Atacado', format='R$ %2f', ),
#                      },
#                  use_container_width=True, height=2000)

from PIL import Image
import requests
import pandas as pd

translations = ''.maketrans('äãõüáéíóúâêîôûàèìòùç', 'aaouaeiouaeiouaeiouc', ''.join(c for c in map(chr, range(256)) if not c.isalnum()))


marcas = pd.read_csv('marcas.csv', encoding='latin1', sep=';')
marcas['endereço'] = 'data\\img\\' + marcas['marca'].str.translate(translations).replace('[^0-9a-zA-Z]', '') + "_" + marcas['nome_sku'].str.translate(translations).replace('[^0-9a-zA-Z]', '') +'.png'

marcas.to_csv('marcas.csv', encoding='latin1', sep=';', index_label=False)

print(marcas)

for index, row in marcas.iterrows():
    print(row['endereço'])
    img_url = row['link_foto']
    img = Image.open(requests.get(img_url, stream = True).raw)
    img.save(row['endereço'])
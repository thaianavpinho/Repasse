import requests
from bs4 import BeautifulSoup
import pandas as pd

frames = []

url = 'https://www.catalogoambev.com.br/site'



r = requests.get(url)

soup = BeautifulSoup(r.content,'html.parser')

marcas = soup.select('a[title]')

links_marcas = [x.get('href') for x in marcas]

for url in links_marcas:

    r = requests.get(url)
    soup = BeautifulSoup(r.content,'html.parser')
    prods = soup.select('img')

    try:
        if prods[0].get('class')[0] == 'box-image-logo':
            prods = soup.select('a[title]')
            links_marcas_interno = [x.get('href') for x in prods]
            
            for link in links_marcas_interno:
                r = requests.get(link)
                soup = BeautifulSoup(r.content,'html.parser')
                
                marca = soup.h3.string
                print(marca)
                
                prods = soup.select('li')
                
                produtos = {'marca':[],
                            'descrição':[],
                            'nome_sku':[],
                            'link_foto':[]}
                
                for x in prods:
                    z = x.find_all('img')
                    for y in z:
                        produtos['marca'].append(marca)
                        produtos['link_foto'].append(y.get('src'))
                        produtos['descrição'].append(y.get('alt'))
                    i = x.find_all("a", {"class": "no-padding-bottom"})
                    for j in i:
                        produtos['nome_sku'].append(j.string.strip())

                data = pd.DataFrame(produtos)
                
                frames.append(data)
                
                

    except:

        marca = soup.h3.string
        print(marca)
        
        prods = soup.select('li')
        
        produtos = {'marca':[],
                            'descrição':[],
                            'nome_sku':[],
                            'link_foto':[]}

        for x in prods:
            z = x.find_all('img')
            for y in z:
                produtos['marca'].append(marca)
                produtos['link_foto'].append(y.get('src'))
                produtos['descrição'].append(y.get('alt'))
            i = x.find_all("a", {"class": "no-padding-bottom"})
            for j in i:
                produtos['nome_sku'].append(j.string.strip())

        data = pd.DataFrame(produtos)
        
        frames.append(data)
        
frames = pd.concat(frames)

frames.to_csv('marcas.csv', encoding='latin1', sep=';', index_label=False)

print(frames)




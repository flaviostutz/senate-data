from bs4 import BeautifulSoup
import sys, traceback
import pandas as pd
import numpy as np
import requests
import csv

def download_senator_speeches(from_date, to_date, output_csvfile, max=None):
    headers = {'Accept': 'application/json'}
    res = requests.get('http://legis.senado.leg.br/dadosabertos/plenario/lista/discursos/' + from_date + '/' + to_date, headers=headers)
    contents = res.json()

    with open(output_csvfile, 'w', encoding='utf-8') as ofile:
        writer = csv.writer(ofile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        row = [
            'CodigoPronunciamento',
            'TipoPronunciamento',
            'Data',
            'SiglaCasa',
            'TipoSessao',
            'NomeAutor',
            'CodigoParlamentar',
            'Partido',
            'UF',
            'SexoParlamentar',
            'DataNascimentoParlamentar',
            'Indexacao',
            'TextoIntegral',
        ]
        writer.writerow(row)

        sessoes = contents['DiscursosSessao']['Sessoes']['Sessao']
        c = 0
        print('Downloading speeches')
        for sessao in sessoes:
            if 'Pronunciamentos' in sessao:
                for pron in sessao['Pronunciamentos']['Pronunciamento']:
                    if max!=None and c >= max:
                        break

                    try:
                        url = pron['TextoIntegral']
                        speech_contents = get_senator_speech(url)
                        senator_info = get_senator_info(pron['CodigoParlamentar'])

                        #fields id, senador, partido, uf, sexo, data, indexacaoTexto, speechContents
                        row = [
                            pron['CodigoPronunciamento'],
                            pron['TipoPronunciamento'],
                            pron['Data'],
                            sessao['SiglaCasa'],
                            sessao['TipoSessao'],
                            pron['NomeAutor'],
                            pron['CodigoParlamentar'],
                            dict_attr(pron, 'Partido', 'none'),
                            dict_attr(pron, 'UF', 'none'),
                            senator_info['IdentificacaoParlamentar']['SexoParlamentar'],
                            senator_info['DadosBasicosParlamentar']['DataNascimento'],
                            dict_attr(pron, 'Indexacao'),
                            speech_contents,
                        ]
                        writer.writerow(row)
                        sys.stdout.write('.')
                        c = c + 1

                    except Exception as e:
                        traceback.print_exc(file=sys.stdout)
                        print('exception ' + str(e))

    print('Done downloading ' + str(c) + ' speeches to ' + output_csvfile)


def get_senator_speech(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    text_div = soup.findAll("div", {"class": "texto-integral"})
    if len(text_div) == 0:
        raise  'Unavailable speech at  ' + url
    else:    
        speech = text_div[0].get_text()
        return speech.replace(u'\xa0', u' ')


senator_info_cache = dict()
def get_senator_info(senator_id, cache=True):
    if cache and senator_id in senator_info_cache:
        return senator_info_cache[senator_id]
    else:
        headers = {'Accept': 'application/json'}
        contents = requests.get('http://legis.senado.leg.br/dadosabertos/senador/' + senator_id, headers=headers).json()
        info = contents['DetalheParlamentar']['Parlamentar']
        senator_info_cache[senator_id] = info
        return info


def dict_attr(valueDict, attrPath, defaultValue=''):
    if type(valueDict) != dict:
        raise 'valueDict must be dict type'
    parts = attrPath.split('.')
    cv = valueDict
    for p in parts:
        if p in cv:
            cv = cv.get(p)
        else:
            return defaultValue
    return cv
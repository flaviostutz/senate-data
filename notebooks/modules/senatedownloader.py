from bs4 import BeautifulSoup
import sys, traceback
import pandas as pd
import numpy as np
import requests
import csv
import math

def download_senate_materias(year, output_csvfile, type='pls', max=None):
    headers = {'Accept': 'application/json'}
    res = requests.get('http://legis.senado.leg.br/dadosabertos/materia/pesquisa/lista?sigla=' + type + '&ano=' + str(year), headers=headers)
    contents = res.json()

    with open(output_csvfile, 'w', encoding='utf-8') as ofile:
        writer = csv.writer(ofile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        row = [
            'CodigoMateria',
            'SiglaCasaMateria',
            'SiglaSubtipoMateria',
            'AnoMateria',
            'DescricaoMateria',
            'EmentaMateria',
            'ExplicacaoEmentaMateria',
            'DataApresentacao',
            'NomeNatureza',
            'CodigoParlamentarAutor',
            'NomeParlamentarAutor',
            'SexoParlamentarAutor',
            'UfParlamentarAutor',
            'PartidoParlamentarAutor',
            'SiglaSituacaoMateria',
            'SiglaLocalMateria',
            'CodigosRelatoresMateria'
        ]
        writer.writerow(row)

        materias = contents['PesquisaBasicaMateria']['Materias']['Materia']
        c = 0
        print('Downloading materias')
        for materia in materias:
            if max!=None and c >= max:
                break

            try:
                # get relatores
                codigoMateria = materia['IdentificacaoMateria']['CodigoMateria']
                res = requests.get('http://legis.senado.leg.br/dadosabertos/materia/relatorias/' + codigoMateria, headers=headers)
                mc = res.json()

                codigosRelatores = ''
                if 'HistoricoRelatoria' in mc['RelatoriaMateria']['Materia']:
                    relatores = mc['RelatoriaMateria']['Materia']['HistoricoRelatoria']['Relator']
                    if 'IdentificacaoParlamentar' in relatores:
                        codigosRelatores = str(relatores['IdentificacaoParlamentar']['CodigoParlamentar'])
                    else:
                        codigosRelatores = ' '.join([str(x['IdentificacaoParlamentar']['CodigoParlamentar']) for x in relatores])

                row = [
                    codigoMateria,
                    materia['IdentificacaoMateria']['SiglaCasaIdentificacaoMateria'],
                    materia['IdentificacaoMateria']['SiglaSubtipoMateria'],
                    materia['IdentificacaoMateria']['AnoMateria'],
                    materia['IdentificacaoMateria']['DescricaoIdentificacaoMateria'],
                    materia['DadosBasicosMateria']['EmentaMateria'],
                    dict_attr(materia, 'DadosBasicosMateria.ExplicacaoEmentaMateria', ''),
                    materia['DadosBasicosMateria']['DataApresentacao'],
                    materia['DadosBasicosMateria']['NaturezaMateria']['NomeNatureza'],
                    dict_attr(materia, 'AutoresPrincipais.AutorPrincipal.IdentificacaoParlamentar.CodigoParlamentar', 0),
                    dict_attr(materia, 'AutoresPrincipais.AutorPrincipal.IdentificacaoParlamentar.NomeParlamentar', dict_attr(materia, 'AutoresPrincipais.AutorPrincipal.NomeAutor', '')),
                    dict_attr(materia, 'AutoresPrincipais.AutorPrincipal.IdentificacaoParlamentar.SexoParlamentar', ''),
                    dict_attr(materia, 'AutoresPrincipais.AutorPrincipal.IdentificacaoParlamentar.UfParlamentar', ''),
                    dict_attr(materia, 'AutoresPrincipais.AutorPrincipal.IdentificacaoParlamentar.SiglaPartidoParlamentar', ''),
                    materia['SituacaoAtual']['Autuacoes']['Autuacao']['Situacao']['SiglaSituacao'],
                    materia['SituacaoAtual']['Autuacoes']['Autuacao']['Local']['SiglaLocal'],
                    codigosRelatores
                ]
                writer.writerow(row)
                sys.stdout.write('.')
                c = c + 1

            except Exception as e:
                traceback.print_exc(file=sys.stdout)
                print('exception ' + str(e))


def download_senate_speeches(from_date, to_date, output_csvfile, max=None):
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
            if cv == 'NaN':
                return defaultValue
        else:
            return defaultValue
    return cv


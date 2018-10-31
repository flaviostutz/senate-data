import nltk
import re
from nltk.corpus import floresta
from nltk.stem import SnowballStemmer

class StemFilterTokenizeProcessor:

    def __init__(self, stopwords=[], min_size=3, filter_regex='.*', stem_language=None, stem_complete=False, only_nouns=False):
        if only_nouns and stem_language!='portuguese':
            raise 'only portuguese is supported for "only_nouns=True"'
        self.stopwords = stopwords
        self.min_size = min_size
        self.filter_regex = filter_regex
        self.stem_language = stem_language
        self.stem_complete = stem_complete
        self.only_nouns = only_nouns

        #nouns list
        self.pt_terms = {}
        tsents = floresta.tagged_sents()
        for sent in tsents:
            for (w,t) in sent:
                self.pt_terms[w.lower()] = t

        self.stem_dict = dict()
        self.stemmer = None
        if stem_language != None:
            self.stemmer = SnowballStemmer(stem_language)

    def is_noun(self, term):
        if term.lower() in self.pt_terms:
            tt = self.pt_terms[term.lower()]
            return re.match('.*\+n$', tt) or re.match('^N<\+.*$', tt)
        else:
            return False

    def is_prop(self, term):
        if term.lower() in self.pt_terms:
            tt = self.pt_terms[term.lower()]
            return re.match('^H\+prop$', tt) or re.match('^SUBJ\+prop$', tt) or re.match('^P<\+prop$', tt)
        else:
            return False

    def tokenize_text(self, text):
        tokens = nltk.word_tokenize(text.lower())
        # for tt in tokens:
        #     if self.only_nouns and not self.is_noun(tt):
        #         print('NOT NOUN: ' + tt)
        #         if tt in self.pt_terms:
        #             print('>>' + self.pt_terms[tt])
        tokens = [self.stem(t) for t in tokens if (self.only_nouns==False or self.is_noun(t) or self.is_prop(t)) and ((len(t)>=self.min_size) and (t not in self.stopwords) and (re.match(self.filter_regex, t)))]
        if self.stem_complete:
            tokens = [self.stem_dict[t] for t in tokens]
        return tokens

    def tokenize_documents(self, documents):
        return [self.tokenize_text(d) for d in documents]

    def process_text(self, text):
        result = ''
        for dt in self.tokenize_text(text):
            result = result + ' ' + dt
        return result

    def stem(self, word):
        if self.stemmer != None:
            stemmed_word = self.stemmer.stem(word)
            self.stem_dict[stemmed_word] = word
            return stemmed_word
        else:
            return word

    def stem_dict(self) :
        return self.stem_dict


import os.path
import PyPDF2
def pdf_text_extract(pdf_path):
    if os.path.isfile(pdf_path) == False:
        raise Exception('File not found: ' + pdf_path)
    with open(pdf_path,'rb') as pf:
        pdfReader = PyPDF2.PdfFileReader(pf)
        num_pages = pdfReader.numPages
        count = 0
        text = ''
        while count < num_pages:
            pageObj = pdfReader.getPage(count)
            count +=1
            text += pageObj.extractText()
        return text

import numpy as np
from sklearn.metrics import pairwise_distances_argmin_min
from nltk import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
def summarize_kmeans(text_contents, n_sentences, stopwords=[], language='portuguese'):
    sents = sent_tokenize(text_contents)
    sents = [s for s in sents if len(s)>40]

    proc = StemFilterTokenizeProcessor(min_size=4, filter_regex='[a-z]', stem_language=language, stem_complete=True, only_nouns=True)
    vec = TfidfVectorizer(min_df=0.01, stop_words=stopwords, analyzer='word', ngram_range=(1, 2), preprocessor=proc.process_text)
    X = vec.fit_transform(sents)

    kmeans_model = KMeans(n_clusters=n_sentences)
    y_kmeans = kmeans_model.fit_predict(X)

    avg = []
    for j in range(n_sentences):
        idx = np.where(kmeans_model.labels_ == j)[0]
        avg.append(np.mean(idx))
    closest, _ = pairwise_distances_argmin_min(kmeans_model.cluster_centers_, X, metric='cosine')
    ordering = sorted(range(n_sentences), key=lambda k: avg[k])

    return [sents[closest[idx]] for idx in ordering]

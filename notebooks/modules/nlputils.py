import nltk
import re
from nltk.corpus import floresta
from nltk.stem import SnowballStemmer

#nouns list
nouns = []
tsents = floresta.tagged_sents()
for sent in tsents:
    for (w,t) in sent:
        if t=='H+n':
            nouns.append(w.lower())
nouns = set(nouns)

#documents - [string contents]
def tokenize_filter_stem(documents, stopwords=[], min_size=3, filter_regex='.*', stem_language=None, stem_complete=False, only_nouns=False):
    stem_dict = dict()
    stemmer = None
    if stem_language != None:
        stemmer = SnowballStemmer(stem_language)
    def stem(word):
        if stemmer != None:
            stemmed_word = stemmer.stem(word)
            stem_dict[stemmed_word] = word
            return stemmed_word
        else:
            return word
    tokens = [nltk.word_tokenize(s.lower()) for s in documents]
    tokens = [[stem(t) for t in tt if (only_nouns==False or t in nouns) and ((len(t)>=min_size) and (t not in stopwords) and (re.match(filter_regex, t)))] for tt in tokens]
    if stem_complete:
        tokens = [[stem_dict[t] for t in tt] for tt in tokens]
    return tokens

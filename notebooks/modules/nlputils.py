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
        pt_nouns = []
        tsents = floresta.tagged_sents()
        for sent in tsents:
            for (w,t) in sent:
                if t=='H+n':
                    pt_nouns.append(w.lower())
        self.pt_nouns = set(pt_nouns)

        self.stem_dict = dict()
        self.stemmer = None
        if stem_language != None:
            self.stemmer = SnowballStemmer(stem_language)

    def tokenize_text(self, text):
        tokens = nltk.word_tokenize(text.lower())
        tokens = [self.stem(t) for t in tokens if (self.only_nouns==False or t in self.pt_nouns) and ((len(t)>=self.min_size) and (t not in self.stopwords) and (re.match(self.filter_regex, t)))]
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

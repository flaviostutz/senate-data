import sys
import numpy as np

def display_lda_topics(model, feature_names, nr_top_words):
    for topic_idx, topic in enumerate(model.components_):
        sys.stdout.write("Topic " + str(topic_idx) + ': ')
        topics = np.flip(topic.argsort(), axis=0)
        for i in topics[:nr_top_words]:
            sys.stdout.write(feature_names[i] + ' ')
        print('')

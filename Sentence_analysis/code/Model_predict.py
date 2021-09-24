
from keras.preprocessing.sequence import pad_sequences
import pandas as pd
from keras.preprocessing.text import Tokenizer
import tensorflow as tf

import argparse

parser=argparse.ArgumentParser(description='Classification')
parser.add_argument('location',type=(str))
args=parser.parse_args()

if __name__=='__main__':
    # this is the training data path (make sure that caution marks around the path):
    """./argparse/Sentence binary classification training data.csv"""
    prediction = pd.read_csv(args.location)
    prediction_list = []
    prediction_list.append("Predition")
    loaded_model = tf.keras.models.load_model('E:/Research/NLP_Deep Learning/sentence_classifier.h5')
    tokenizer = Tokenizer(num_words=5000)
    tokenizer.fit_on_texts(prediction['span'].values)
    maxlen = 100
    for i in prediction['span']:
        i = [i]
        X_predict = tokenizer.texts_to_sequences(i)
        X_predict = pad_sequences(X_predict, padding='post', maxlen=maxlen)
        new_prediction = loaded_model.predict_classes(X_predict)
        prediction_list.append(new_prediction)
        print(new_prediction)
    prediction_list = pd.DataFrame(prediction_list)
    short_list = prediction_list.iloc[:,0]
    prediction = prediction.join(short_list)
    prediction.to_csv('E:/Research/NLP_Deep Learning/codes for github/Sentence_analysis/code/concept-annotations_pmc_PMC_SUBSET_27_part1_prepared1_result.csv')

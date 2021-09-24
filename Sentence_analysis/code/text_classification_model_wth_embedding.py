
import pandas as pd
from sklearn.model_selection import train_test_split
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.models import Sequential
from keras import layers
from keras import callbacks
from sklearn.metrics import classification_report
import tensorflow as tf


import argparse

parser=argparse.ArgumentParser(description='Classification')
parser.add_argument('location',type=(str))
args=parser.parse_args()

if __name__=='__main__':
    # this is the training data path (make sure that caution marks around the path):
    """./argparse/Sentence binary classification training data.csv"""
    df = pd.read_csv(args.location)
    
    sentences = df['span'].values
    y = df['IGNORANCE TYPE'].values
    sentences_train, sentences_test, y_train, y_test = train_test_split(sentences, y, test_size=0.1, random_state=10, stratify=y)
    
    tokenizer = Tokenizer(num_words=5000)
    tokenizer.fit_on_texts(sentences_train)
    
    X_train = tokenizer.texts_to_sequences(sentences_train)
    X_test = tokenizer.texts_to_sequences(sentences_test)
    
    vocab_size = len(tokenizer.word_index) + 1  # Adding 1 because of reserved 0 index
    
    print(sentences_train[2])
    print(X_train[2])
    
    for word in ['the', 'all']:
         print('{}: {}'.format(word, tokenizer.word_index[word]))
        
    maxlen = 100
    
    X_train = pad_sequences(X_train, padding='post', maxlen=maxlen)
    X_test = pad_sequences(X_test, padding='post', maxlen=maxlen)
    print(X_train[0, :])
    
    embedding_dim = 50
    
    model = Sequential()
    model.add(layers.Embedding(input_dim=vocab_size, 
                               output_dim=embedding_dim, 
                               input_length=maxlen))
    model.add(layers.Flatten())
    model.add(layers.Dense(50, activation='relu'))
    model.add(layers.Dense(1, activation='sigmoid'))
    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])
    model.summary()
    
     
    earlystopping = callbacks.EarlyStopping(monitor ="val_loss",  
                                            mode ="min", patience = 5,  
                                            restore_best_weights = True)
    
    history = model.fit(X_train, y_train,
                         epochs=50,
                         verbose=True,
                         validation_data=(X_test, y_test),
                         batch_size=16,callbacks =[earlystopping])
    loss, accuracy = model.evaluate(X_train, y_train, verbose=False)
    print("Training Accuracy: {:.4f}".format(accuracy))
    loss, accuracy = model.evaluate(X_test, y_test, verbose=False)
    print("Testing Accuracy:  {:.4f}".format(accuracy))
    
    
    y_pred = model.predict(X_test)
    yhat_classes = model.predict_classes(X_test)
    
    def classification_report_csv(report):
        report_data = []
        lines = report.split('\n')
        for line in lines[2:-3]:
            row = {}
            row_data = line.split('      ')
            row['class'] = row_data[0]
            row['precision'] = float(row_data[1])
            row['recall'] = float(row_data[2])
            row['f1_score'] = float(row_data[3])
            row['support'] = float(row_data[4])
            report_data.append(row)
        dataframe = pd.DataFrame.from_dict(report_data)
        # dataframe.to_csv('classification_report.csv', index = False)
    
    report = classification_report(y_test, yhat_classes)
    print (report)
    
    model.evaluate(X_test, y_test)[1]
    
    predict = ["Treating Obesity in Heart Failure"]
    X_predict = tokenizer.texts_to_sequences(predict)
    X_predict = pad_sequences(X_predict, padding='post', maxlen=maxlen)
    X_predict
    
    new_prediction = model.predict_classes(X_predict)
    print (new_prediction)



# If the current model performce is efficient, you can uncomment the following section and test sentence by sentence. 
'''model.save('D:/Research/NLP_Deep Learning/sentence_classifier.h5')
loaded_model = tf.keras.models.load_model('D:/Research/NLP_Deep Learning/sentence_classifier.h5')
maxlen = 100
tokenizer = Tokenizer(num_words=5000)
predict = ["evaluated data from 9 studies including 110 patients to determine the impact of weight loss interventions on invasive hemodynamic parameters in obese patients without heart failure (HF)"]
X_predict = tokenizer.texts_to_sequences(predict)
X_predict = pad_sequences(X_predict, padding='post', maxlen=maxlen)
X_predict

new_prediction = loaded_model.predict_classes(X_predict)
print (new_prediction)'''



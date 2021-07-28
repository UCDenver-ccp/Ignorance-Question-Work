

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras import callbacks, layers 
from sklearn.metrics import classification_report

import argparse

parser=argparse.ArgumentParser(description='Calc volume')
parser.add_argument('location',type=(str))
args=parser.parse_args()

if __name__=='__main__':
    # this is the training data path (make sure that caution marks around the path):
    """./argparse/Sentence binary classification training data.csv"""
    df = pd.read_csv(args.location)
    
    sentences = df['span'].to_list()
    vectorizer = CountVectorizer(min_df=0, lowercase=False)
    vectorizer.fit(sentences)
    vectorizer.vocabulary_
    
    
    vectorizer.transform(sentences).toarray()
    
    sentences = df['span'].values
    y = df['IGNORANCE TYPE'].values
    sentences_train, sentences_test, y_train, y_test = train_test_split(sentences, y, test_size=0.1, random_state=10, stratify=y)
    
    vectorizer = CountVectorizer()
    vectorizer.fit(sentences_train)
    X_train = vectorizer.transform(sentences_train)
    X_test  = vectorizer.transform(sentences_test)
    X_train
    
    
    classifier = LogisticRegression()
    classifier.fit(X_train, y_train)
    score = classifier.score(X_test, y_test)
    print("Accuracy:", score)
    
    
    sentences = df['span'].values
    y = df['IGNORANCE TYPE'].values
    sentences_train, sentences_test, y_train, y_test = train_test_split(sentences, y, test_size=0.1, random_state=10, stratify=y)
    
    vectorizer = CountVectorizer()
    vectorizer.fit(sentences_train)
    X_train = vectorizer.transform(sentences_train)
    X_test  = vectorizer.transform(sentences_test)
    
    classifier = LogisticRegression()
    classifier.fit(X_train, y_train)
    score = classifier.score(X_test, y_test)
    print('Accuracy for {} data: {:.4f}'.format("Accuracy:", score))
    
    
    input_dim = X_train.shape[1]  # Number of features
    model = Sequential()
    model.add(layers.Dense(50, input_dim=input_dim, activation='relu'))
    model.add(layers.Dense(1, activation='sigmoid'))
    model.compile(loss='binary_crossentropy', 
                   optimizer='adam', 
                   metrics=['accuracy'])
    model.summary()
    
    earlystopping = callbacks.EarlyStopping(monitor ="val_loss",  
                                            mode ="min", patience = 5,  
                                            restore_best_weights = True)
    
    history = model.fit(X_train, y_train,
                         epochs=50,
                         verbose=True,
                         validation_data=(X_test, y_test),
                         batch_size=16,callbacks =[earlystopping], class_weight=None)
    
    loss, accuracy = model.evaluate(X_train, y_train, verbose=True)
    print("Training Accuracy: {:.4f}".format(accuracy))
    loss, accuracy = model.evaluate(X_test, y_test, verbose=True)
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
        dataframe.to_csv('classification_report.csv', index = False)
    
    report = classification_report(y_test, yhat_classes)
    print (report)
    
    model.evaluate(X_test, y_test)[1]


from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
import pandas as pd
from sklearn.metrics import classification_report
import argparse

parser=argparse.ArgumentParser(description='Classification')
parser.add_argument('location',type=(str))
args=parser.parse_args()

if __name__=='__main__':
    # this is the training data path (make sure that caution marks around the path):
    """./argparse/Sentence binary classification training data.csv"""
    df = pd.read_csv(args.location)

    sentences = df['span'].to_list()
    sentences = df['span'].values
    y = df['IGNORANCE TYPE'].values
    sentences_train, sentences_test, y_train, y_test = train_test_split(sentences, y, test_size=0.1, random_state=10)
    
    from sklearn.feature_extraction.text import CountVectorizer
    vectorizer = CountVectorizer()
    vectorizer.fit(sentences_train)
    X_train = vectorizer.transform(sentences_train).toarray()
    X_test  = vectorizer.transform(sentences_test).toarray()
    
    gnb = GaussianNB()
    y_pred = gnb.fit(X_train, y_train).predict(X_test)
    print("Number of mislabeled points out of a total %d points : %d" % (X_test.shape[0], (y_test != y_pred).sum()))
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

    report = classification_report(y_test, y_pred)
    print (report)




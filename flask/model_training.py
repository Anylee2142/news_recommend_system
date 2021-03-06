import MySQLdb as db
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from konlpy.tag import Twitter as t
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime

test_nbr = 100

def tagger(doc):
    pos_tagger = t()
    return ["/".join(t) for t in pos_tagger.pos(doc)]

def fetch_all_data():
    # Reason why it fecthes all data from DB is that traing model with TFIDF cannot be applied with online learning
    here = datetime.now()
    print('Loading data from DB')
    
    import json

    with open('/home/ej/github/news_config.json') as f:
        config = json.load(f)
    
    data = pd.read_sql('SELECT * FROM ARTICLE;', db.connect(
        config['ADDR'],
        config['ID'],
        config['PW'],
        config['DB'],
        charset='utf8'
    ))
    td = datetime.now() - here
    minutes = td.seconds // 60 % 60
    print('Completed !', '{} min'.format(minutes),'{} sec'.format(td.seconds - minutes * 60))

    return data

def training_model(data):
    # training model
    here = datetime.now()

    print('Model training started')

    X = data.content
    y = data.area

    # if test, uncomment belows
    # X_train, X_test, y_train, y_test = train_test_split(data.content, data.area, test_size=0.3, random_state=0)
    #
    # X_train = X_train[:test_nbr]
    # y_train = y_train[:test_nbr]
    # X = X_train
    # y = y_train

    # alpha for multinomial nb is smoothing parameter
    model = Pipeline([
        ('vect', TfidfVectorizer(tokenizer=tagger)),
        ('clf',MultinomialNB(alpha=0.01)),
    ]).fit(X, y)
    td = datetime.now() - here
    minutes = td.seconds // 60 % 60
    print('Completed !', '{} min'.format(minutes),'{} sec'.format(td.seconds - minutes * 60))

    return model

def cross_validation(data, how_many_folds=3):
    # Conduct cross validation
    # returns lists of confusion matrix, classification report of each fold

    cnf_mat = []
    clf_rep = []

    total_here = datetime.now()

    print('Cross validaiton started !')
    for idx in range(0,how_many_folds):
        here = datetime.now()
        X_train, X_test, y_train, y_test = train_test_split(data.content, data.area, test_size=0.3, random_state=idx)
        clf = Pipeline([
        ('vect', TfidfVectorizer(tokenizer=tagger)),
        ('clf',MultinomialNB(alpha=0.01)),
        ])

        # if test, uncomment belows
        # X_train, X_test, y_train, y_test = X_train[:test_nbr], X_test[:test_nbr], y_train[:test_nbr], y_test[:test_nbr]

        model = clf.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        cnf_mat.append(str(confusion_matrix(y_test, y_pred)))
        clf_rep.append(classification_report(y_test, y_pred))

        td = datetime.now() - here
        minutes = td.seconds // 60 % 60
        print('iteration : ',idx, ', elapsed time :','{} min'.format(minutes),'{} sec'.format(td.seconds - minutes * 60))

    total_td = datetime.now() - total_here
    minutes = total_td.seconds // 60 % 60
    print('Completed !', '{} min'.format(minutes),'{} sec'.format(total_td.seconds - minutes * 60))

    return cnf_mat, clf_rep

def save_model_and_cv_eval(model, cnf_mat, clf_rep, cur_time = datetime.now().strftime('%Y-%m-%d %H-%M-%S')):
    here = datetime.now()

    print("Saving model and each fold's evaluation as confusion matrix, classification report")

    cnf_mat = '\n\n'.join(cnf_mat)
    clf_rep = '\n\n'.join(clf_rep)

    cur_time = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    pickle.dump(model, open("models/twitter_tfidf_mulnb_{}.pkl".format(cur_time), "wb"))
    with open('models/twitter_tfidf_mulnb_cnf_mat_{}.txt'.format(cur_time),'w',encoding='utf-8') as f:
        f.write(str(cnf_mat))
    with open('models/twitter_tfidf_mulnb_clf_rep_{}.txt'.format(cur_time),'w',encoding='utf-8') as f:
        f.write(clf_rep)

    td = datetime.now() - here
    minutes = td.seconds // 60 % 60
    print('Completed !', '{} min'.format(minutes),'{} sec'.format(td.seconds - minutes * 60))

if __name__=='__main__':
    # python model_training.py
    data = fetch_all_data()

    model = training_model(data)

    cnf_mat, clf_rep = cross_validation(data, 3)

    save_model_and_cv_eval(model, cnf_mat, clf_rep)

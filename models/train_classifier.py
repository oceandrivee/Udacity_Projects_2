# import libraries
import sys
import os
import re
# import numpy as np
import pandas as pd

# import sql library
from sqlalchemy import create_engine

# import nltk libraries
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('wordnet')
nltk.download('words')
from nltk.corpus import stopwords

from nltk import pos_tag, ne_chunk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# import scikit-learn libraries
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.metrics import classification_report
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

# import library to save trained model
import pickle



def load_data(database_filepath):
    '''Function to load data from database
    INPUT:
    database_filepath(str) - the name of the stored .db file
    OUTPUT:
    X(series) - messages columns, 
    Y(dataframe) - all list of 36 categories
    cat_names(list) - names of the categories
    '''
    # create SQL engine with database name
    engine = create_engine('sqlite:///{}'.format(database_filepath))

    # extract table name from database name
    table_name = os.path.basename(database_filepath).split('.')[0]

    # read table from database
    df = pd.read_sql_table(table_name, engine)

    # obtain messages and its categories' values and names
    X = df['message'].values
    Y = df[df.columns[4:]]
    cat_names = Y.columns
    return X, Y, cat_names


def tokenize(text):
    """
      Takes a Python string object and outputs list of processed words 
       of the text.
      INPUT:
        - text - Python str object - A raw text data
      OUTPUT:
        - stem_words - Python list object - list of processed words using the input `text`.
    """
   
    # Removes punctuations and covert to lower case 
    #text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9]", " ", text).lower()
    text = word_tokenize(text) 
    # Remove stop words
    text = [w for w in text if w not in stopwords.words("english")]
    # Lemmatize verbs by specifying pos
    text = [WordNetLemmatizer().lemmatize(w) for w in text]
    
    return text


def build_model():
    '''Function to build ml model pipeline with grid search cross validation
    INPUT:
    none
    OUTPUT:
    pipeline(object) - trained model
    '''
    # build pipeline
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ('clf', MultiOutputClassifier(RandomForestClassifier(max_depth=6)))
    ])

    # change parameters set for grid search
    parameters = {
        # 'vect__ngram_range': ((1, 1), (1, 2)),
        'clf__estimator__n_estimators': [10, 20],
        # 'clf__estimator__min_samples_split': [2, 4, 6]
    }

    # find best model in all gridsearchcv set, could take hours(you may try
    # parallel computing to improve efficiency)
    model = GridSearchCV(pipeline, param_grid=parameters,verbose=3)

    return model


def evaluate_model(model, X_test, Y_test):
    '''This function evaluates the model performance for each category
    INPUT:
    model(object) - model to be evaluated
    X_test(list) - X test dataset
    Y_test(dataframe) - Y test dataset
    OUTPUT:
    print out classification report and accuracy score
    '''
    # predict on the test set
    Y_test_pred = model.predict(X_test)

    # classification report on test set
    print(classification_report(Y_test.values, Y_test_pred, target_names=Y_test.columns.values))

    # Model accuracy score on test set
    Y_test_accuracy = (Y_test_pred == Y_test).mean()
    print(Y_test_accuracy)


def save_model(model, model_filepath):
    '''Function saves the pipeline to local
    INPUT:
    model(object) - trained model
    model_filepath(str) - file path of the model
    OUTPUT:
    none
    '''
    with open(model_filepath, 'wb') as f:
        pickle.dump(model, f)

def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()
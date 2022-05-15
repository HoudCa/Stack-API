# -*- coding: utf-8 -*-
"""
Created on Wed May 11 08:51:48 2022

@author: Houda
"""

import json
import requests
from flask import Flask, request, render_template
import numpy as np
import re
from bs4 import BeautifulSoup
from langdetect import detect
from deep_translator import GoogleTranslator
import spacy
import en_core_web_sm
import nltk
nltk.download('punkt')
nltk.download('all') 
from nltk.corpus import stopwords
from nltk.stem import wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import ToktokTokenizer
from nltk.tokenize import word_tokenize
import joblib
app = Flask(__name__)
# Cleaning function for new question
def remove_pos(nlp, x, pos_list):
    """NLP cleaning function based on the POS-Tagging of the Spacy library. 
    It allows you to keep only the Parts Of Speech listed as a parameter. 
    Parameters
    ----------------------------------------
    nlp : spacy pipeline
        Load pipeline with options.
        ex : spacy.load('en', exclude=['tok2vec', 'ner', 'parser', 
                                'attribute_ruler', 'lemmatizer'])
    x : string
        Sequence of characters to modify.
    pos_list : list
        List of POS to conserve.
    ----------------------------------------
    """
    # Test of language detection
    lang = detect(x)
    if(lang != "en"):
        # Deep translate if not in English
        x = GoogleTranslator(source='auto', target='en').translate(x)
    
    doc = nlp(x)
    list_text_row = []
    for token in doc:
        if(token.pos_ in pos_list):
            list_text_row.append(token.text)
    join_text_row = " ".join(list_text_row)
    join_text_row = join_text_row.lower().replace("c #", "c#")
    return join_text_row

def text_cleaner(x, nlp, pos_list, lang="english"):
    """Function allowing to carry out the preprossessing on the textual data. 
        It allows you to remove extra spaces, unicode characters, 
        English contractions, links, punctuation and numbers.
        
        The re library for using regular expressions must be loaded beforehand.
        The SpaCy and NLTK librairies must be loaded too. 
    Parameters
    ----------------------------------------
    nlp : spacy pipeline
        Load pipeline with options.
        ex : spacy.load('en', exclude=['tok2vec', 'ner', 'parser', 
                                'attribute_ruler', 'lemmatizer'])
    x : string
        Sequence of characters to modify.
    pos_list : list
        List of POS to conserve.
    ----------------------------------------
    """
    # Remove POS not in "NOUN", "PROPN"
    x = remove_pos(nlp, x, pos_list)
    # Case normalization
    x = x.lower()
    # Remove unicode characters
    x = x.encode("ascii", "ignore").decode()
    # Remove English contractions
    x = re.sub("\'\w+", '', x)
    # Remove ponctuation but not # (for C# for example)
    x = re.sub('[^\\w\\s#]', '', x)
    # Remove links
    x = re.sub(r'http*\S+', '', x)
    # Remove numbers
    x = re.sub(r'\w*\d+\w*', '', x)
    # Remove extra spaces
    x = re.sub('\s+', ' ', x)
        
    # Tokenization
    x = nltk.tokenize.word_tokenize(x)
    # List of stop words in select language from NLTK
    stop_words = stopwords.words(lang)
    # Remove stop words
    x = [word for word in x if word not in stop_words 
         and len(word)>2]
    # Lemmatizer
    wn = nltk.WordNetLemmatizer()
    x = [wn.lemmatize(word) for word in x]
    
    # Return cleaned text
    return x

nlp = spacy.load('en_core_web_sm')
pos_list = ["NOUN","PROPN"]

# Load pre-trained models
model_path = "static/models/"
vectorizer = joblib.load(model_path + "tfidf_vectorizer_tag.pkl", 'r')
model = joblib.load(model_path + "logit_nlp_model_tag.pkl", 'r')
multilabel_binarizer = joblib.load(model_path + "multilabel_binarizer_tag.pkl", 'r')

@app.route('/')
def index():
    return json.dumps({'name': 'Houda',
                       'email': 'houda@outlook.com'})

@app.route('/pred', methods=['GET', 'POST'])
def form_example():
    # handle the POST request
    if request.method == 'POST':
        Question = request.form.get('Question')
        Question_clean = text_cleaner(Question, nlp, pos_list, "english")
        X_tfidf = vectorizer.transform([Question_clean])
        predict = model.predict(X_tfidf)
        tags_predict = multilabel_binarizer.inverse_transform(predict)
        return '''<h1>The tags are: {}</h1>'''.format(tags_predict)

    # otherwise handle the GET request
    return '''
           <form method="POST">
               <div><label>Question: <input type="text" name="Question"></label></div>
               
               <input type="submit" value="Submit">
           </form>'''
           
           
app.run(debug=True)
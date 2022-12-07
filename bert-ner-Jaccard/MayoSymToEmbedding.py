# use pre-trained BERT to convert NER symptoms to embeddings
# input: 1. scraped symptoms from mayo
#        2. patient descriptions generated from gpt-3

from symtable import symtable
from transformers import AutoTokenizer, AutoModel,pipeline
import pandas as pd
import json
import pickle

tokenizer = AutoTokenizer.from_pretrained("GanjinZero/UMLSBert_ENG")
model = AutoModel.from_pretrained("GanjinZero/UMLSBert_ENG")

def get_pooled_embedding(text, model, tokenizer):
    tokenized_input = tokenizer(text, return_tensors='pt')
    output = model(**tokenized_input)
    
    return output.pooler_output.detach().numpy()[0]

def create_pooled_embedding_df(model, tokenizer, df,col):
    df['pooled_embedding'] = df[col].apply(get_pooled_embedding, args=(model, tokenizer))
    return df
    
file = open("./data/mayo_symptoms_ner.plk",'rb')
df= pickle.load(file)
print(df.columns)
df= create_pooled_embedding_df(model, tokenizer,df,'symptoms')
df.to_pickle("./data/mayo_symptoms_embeddings.plk")

file = open("./data/UserInputSymptoms_ner.plk",'rb')
df= pickle.load(file)
print(df.columns)
df= create_pooled_embedding_df(model, tokenizer,df,'userquerySyms')
df.to_pickle("./data/UserInputSymptoms_embeddings.plk")

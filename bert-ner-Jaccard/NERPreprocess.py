# use NER to glean only the symptoms from unstructured descriptive text
# input: 1. scraped symptoms from mayo
#        2. patient descriptions generated from gpt-3

from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForTokenClassification
import pandas as pd
import json
import pickle

# load model
tokenizer = AutoTokenizer.from_pretrained("d4data/biomedical-ner-all")
model = AutoModelForTokenClassification.from_pretrained("d4data/biomedical-ner-all")
# define ner pipeline
pipe = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple") # pass device=0 if using gpu

# read in scraped mayo symptoms
with open("./data/mayo_data.json", 'r') as j:
     data = json.loads(j.read())

symptoms=[]
specialties=[]
diseases=[]

for disease in list(data.keys()):
    list_of_symptoms=data[disease]['symptoms']
    if len(list_of_symptoms)==0:
        pass
    symptoms.append(list_of_symptoms)
    diseases.append(disease)
    list_of_specialties=data[disease]['specialties']
    specialtystr=','.join(list_of_specialties)
    specialties.append(specialtystr)

# join multiple symptoms to a single symptom string
symptomsstr=[' '.join(s) for s in symptoms]

# use ner to retain symptoms-related phrases in the description
def getsymptom(sym):
    scoring=pipe(sym)
    onlysymptoms=[]
    for sc in scoring:
        if sc["entity_group"] in ['Sign_symptom','Disease_disorder',"Biological_structure"]:
            onlysymptoms.append(sc["word"])
    onlysymptomsstr=','.join(onlysymptoms).replace("##","")
    return onlysymptomsstr

# get symptom key words from scraped mayo symptom to disease mappings
mayosymtoms=[]
for sym in symptomsstr:
    if len(sym)>1:
        mayosymtoms.append(getsymptom(sym))
    else:
        mayosymtoms.append('')

lst = [diseases,mayosymtoms,specialties]
df = pd.DataFrame(
    {'disease': diseases,
     'symptoms': mayosymtoms,
     'specialties': specialties
    })
df=df[df.symptoms.notnull()]
df.to_pickle("./data/mayo_symptoms_ner.plk")
df.to_csv('./data/mayo_symptoms_ner.csv',index=False)

# get symptom key words from GPT-3 user symptom descriptions
file = open("./data/UserInputSymptoms.plk",'rb')
df= pickle.load(file)

userquerySyms=[]
for sym in df.userquery:
    sym=sym.replace('\n',' ').replace('-',' ').replace('*','')
    userquerySyms.append(getsymptom(sym))

df['userquerySyms']=userquerySyms
df.to_pickle("./data/UserInputSymptoms_ner.plk")
df.to_csv('./data/UserInputSymptoms_ner.csv',index=False)

from transformers import AutoTokenizer, AutoModel
import numpy as np
from numpy import dot
from numpy.linalg import norm
import pickle

# convert user input to BERT embeddings
def get_pooled_embedding(text):
    """
    Returns the BERT embeddings based on user symptom 

            Parameters:
                    text (str): symptom description input from user

            Returns:
                    pspecialty : ndarray
                    1D array containing BERT embeddings

    """
    tokenizer = AutoTokenizer.from_pretrained("GanjinZero/UMLSBert_ENG")
    model = AutoModel.from_pretrained("GanjinZero/UMLSBert_ENG")
    tokenized_input = tokenizer(text, return_tensors='pt')
    output = model(**tokenized_input)
    
    return output.pooler_output.detach().numpy()[0]

user=get_pooled_embedding("headache, dizziness, leg pain")
print(user)

# replace below with getting the embeddings from the database
file = open("./data/mayo_symptoms_embeddings.plk",'rb')
df= pickle.load(file)
mayo=df.pooled_embedding.tolist()
specialties=df.specialties.tolist()

# create normalized cosine similarity of user query against every mayo disease symptoms
def cosinesim(user,mayo,specialties):
    """
    Returns the predicted specialty (specialty values separated by commas)

            Parameters:
                    user (str): BERT embeddings of user symptom 
                    mayo (list): a list of mayo symptom embeddings
                    specialties (list): a list of specialties associated with the mayo symptoms

            Returns:
                    pspecialty (str): predicted specialty values separated by commas

    """
    mayo_emb=np.array(mayo)
    user_emb=np.array(user).reshape(1,-1)
    num=np.dot(user_emb,mayo_emb.T)
    p1=np.sqrt(np.sum(user_emb**2,axis=1))[:,np.newaxis]
    p2=np.sqrt(np.sum(mayo_emb**2,axis=1))[np.newaxis,:]
    cos=num/(p1*p2)
    pspecialty=specialties[cos.argmax(axis=1)[0]]

    return pspecialty

print(cosinesim(user,mayo,specialties))
    
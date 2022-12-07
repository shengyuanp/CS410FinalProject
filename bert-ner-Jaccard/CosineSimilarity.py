# Description: Use cosine similarity measure to predict what disease is associated with user input symptoms and benchmark prediction accuracy
# Input: Test data generated by GPT-3 - user descriptions of symptoms on all disease labels in the Mayo symptom to disease mapping

import torch

file = open("./data/mayo_symptoms_embeddings.plk",'rb')
df1= pickle.load(file)
mayo=df1.pooled_embedding.tolist()

file = open("./data/UserInputSymptoms_embeddings.plk",'rb')
df2= pickle.load(file)
user=df2.pooled_embedding.tolist()

# create normalized cosine similarity of every user query against every mayo disease symptoms
mayo_emb = torch.tensor(mayo)                    
mayo_emb /= mayo_emb.norm(dim=-1, p=2).unsqueeze(-1) 
user_emb= torch.tensor(user)                    
user_emb /= user_emb.norm(dim=-1, p=2).unsqueeze(-1)    
sims = user_emb @ mayo_emb.t()

# get the predicted disease by largest cosine similarity
maxcosine,ind  = torch.max(sims ,dim=1)
df2['predicted']=[df1.disease[i] for i in ind.squeeze().tolist()]
# calculate accuracy
acc=sum(df2.predicted==df2.disease)/df2.shape[0]
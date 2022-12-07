import pickle
import json
import pymongo


embeddings_file_path = './mayo_symptoms_embeddings.plk'

file = open(embeddings_file_path, 'rb')
pickle_data = pickle.load(file)
file.close()
json_data = []

for idx, item in pickle_data.iterrows():
	json_data.append({
		'disease': item['disease'],
		'symptoms': item['symptoms'],
		'specialties': item['specialties'],
		'pooled_embedding': item['pooled_embedding'].tolist(),
	})

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient.expert_search
collection = db.mayo_embeddings

collection.insert_many(json_data)



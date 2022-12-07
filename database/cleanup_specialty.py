import json
import pymongo


myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient.expert_search

## Basic cleanup

### 1. sync the field name to 'Specialty'
for record in db.physicians.find():
	if not ('Specialty' in record.keys()):
		if 'Specialties' in record.keys():
			record['Specialty'] = record['Specialties']
			db.physicians.update_one( {'_id': record['_id'] }, {'$set': record} )
			db.physicians.update_one( {'_id': record['_id'] }, {'$unset': {'Specialties': ''}} )

### 2. Titleize the field names
for record in db.physicians.find():
	record_titleized = {}

	for k, v in record.items(): 
		if k != '_id':
			record_titleized[k.title()] = v

	db.physicians_titleized.insert_one(record_titleized)

### 3. Make sure they are all lists
for record in db.physicians_titleized.find():
	if 'Specialty' in record.keys():
		if type(record['Specialty']) != list:
			record['Specialty'] = [record['Specialty']]
			db.physicians_titleized.update_one({'_id': record['_id'] }, {'$set': record})



##  Standardize the values

# 1. Find all unique values
specialties = set()
for record in db.physicians_titleized.find():
	if 'Specialty' in record.keys():
		for specialty in record['Specialty']:
			specialties.add(specialty)

specialties = list(specialties)			


# 2. Determine similar values
import difflib
clusters = []
standardise_dict = {}
total = len(specialties)
for specialty in specialties:
	if len(specialty) > 0:
		try:
			cluster = difflib.get_close_matches(specialty, specialties, n = total, cutoff=0.87)
			cluster.sort()
			if cluster not in clusters:
				clusters.append(cluster)
		except: 
			print(type(specialty))


for cluster in clusters:
	standardized_spec = list(cluster)[0]
	for spec in cluster:
		standardise_dict[spec] = standardized_spec

rev_index = {}
for cluster in clusters:
	standardized_spec = list(cluster)[0]
	rev_index[standardized_spec] = cluster

for k,v in rev_index.items():
	if len(v) > 1:
		print(f"{k} => {v}")


# 3. Add field for standardized specialty
for record in db.physicians_titleized.find():
	if 'StandardizedSpecialties' not in record.keys():
		if 'Specialty' in record.keys():
			record['StandardizedSpecialties'] = []
			for s in record['Specialty']:
				if s in standardise_dict.keys():
					record['StandardizedSpecialties'].append(standardise_dict[s])
			db.physicians_titleized.update_one({'_id': record['_id'] }, {'$set': record})


standardized_specialties = set()
for record in db.physicians_titleized.find():
	if 'StandardizedSpecialties' in record.keys():
		for standardized_specialty in record['StandardizedSpecialties']:
			standardized_specialties.add(standardized_specialty)

standardized_specialties = list(standardized_specialties)			

cleanup_size = len(specialties) - len(standardized_specialties) # 166


# rename collection
# physicians => physicians_old
# physicians_titleized => physicians

standardized_specialties_superset = set()
for record in db.physicians.find():
	if 'StandardizedSpecialties' in record.keys():
		for spec in record['StandardizedSpecialties']:
			standardized_specialties_superset.add(spec)

# ----------------------- Lemmatization ----------------------- #

import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()


for mayo_record in db.mayo_embeddings.find():
	if 'specialties' in mayo_record.keys():
		if 'SplitSpecialties' not in mayo_record.keys():
			spec_list = mayo_record['specialties'].split(',')
			lemmatized_spec_list = list(map(lambda w: lemmatizer.lemmatize(w), spec_list ))
			mayo_record['SplitSpecialties'] = spec_list
			mayo_record['LemmatizedSpecialties'] = lemmatized_spec_list
			db.mayo_embeddings.update_one({'_id': mayo_record['_id'] }, {'$set': mayo_record})


for mayo_record in db.mayo_embeddings.find():
	if 'SplitSpecialties' in mayo_record.keys():
		diff = set(mayo_record['SplitSpecialties']) - set(mayo_record['LemmatizedSpecialties'])
		if len(diff) > 0:
			print(f"{mayo_record['_id']}: {diff}")


for physician_record in db.physicians.find():
	if 'StandardizedSpecialties' in physician_record.keys():
		if 'LemmatizedSpecialties' not in physician_record.keys():
			spec_list = physician_record['StandardizedSpecialties']
			lemmatized_spec_list = list(map(lambda w: lemmatizer.lemmatize(w), spec_list ))
			physician_record['LemmatizedSpecialties'] = lemmatized_spec_list
			db.physicians.update_one({'_id': physician_record['_id'] }, {'$set': physician_record})



for physician_record in db.physicians.find():
	if 'LemmatizedSpecialties' in physician_record.keys():
		diff = set(physician_record['SplitSpecialties']) - set(physician_record['LemmatizedSpecialties'])
		if len(diff) > 0:
			print(f"{physician_record['_id']}: {diff}")


physician_specialties_count_map = {}
for physician_record in db.physicians.find():
	if 'LemmatizedSpecialties' in physician_record.keys():
		for spec in physician_record['LemmatizedSpecialties']:
			if spec in physician_specialties_count_map:
				physician_specialties_count_map[spec] += 1
			else:
				physician_specialties_count_map[spec] = 1

mayo_specialties_count_map = {}
for mayo_record in db.mayo_embeddings.find():
	if 'LemmatizedSpecialties' in mayo_record.keys():
		for spec in mayo_record['LemmatizedSpecialties']:
			if spec in mayo_specialties_count_map:
				mayo_specialties_count_map[spec] += 1
			else:
				mayo_specialties_count_map[spec] = 1

physican_specialties_list = list(physician_specialties_count_map.keys())

fix_map = {} 
dangling = set()
for mayo_spec, v in mayo_specialties_count_map.items():
	if mayo_spec not in physician_specialties_count_map:
		close_matches = difflib.get_close_matches(mayo_spec, physican_specialties_list, 3, 0.78)
		if len(close_matches) > 0:
			print(f"{mayo_spec} {close_matches} ")
			fix_map[mayo_spec] = close_matches
		else: 
			dangling.add(mayo_spec)

dangling_2 = set()
for mayo_spec in list(dangling):
	if mayo_spec not in physician_specialties_count_map:
		close_matches = difflib.get_close_matches(mayo_spec, physican_specialties_list, 3, 0.7)
		if len(close_matches) > 0:
			print(f"{mayo_spec} {close_matches} ")
			fix_map[mayo_spec] = close_matches
		else: 
			dangling_2.add(mayo_spec)


manual_fixes = { 
	'Lung Transplant Program': ['Heart and Lung Transplantation'],
	'Aortic Center': ['Aortic Surgery'] ,
	'Pediatric Brain Tumor Clinic': ['Pediatric Craniofacial'] ,
	'Vascular centers': ['Vascular Surgery', 'Vasculopathies', 'Vascular Neurology'] ,
	'Skull Base Tumors Specialty Group': ['Skull Based Tumors', 'Skull Base Tumors (Complex)'] ,
	'Proton Beam Therapy Program': ['Photodynamic Therapy'] ,
	'Cardio-Oncology Clinic': ['Cardiology', 'Neuro-Oncology', 'Radiation Oncology'] ,
	'Dental Specialties': ['Dental Implants', 'Dental Education'] ,
	'Spinal Cord Injury Rehabilitation Program': ['Spinal Cord Injury Medicine'] ,
	'Cerebrovascular Diseases and Critical Care': ['Pulmonary and Critical Care', 'Cardiovascular Disease, Internal Medicine'] ,
	'Cleft and Craniofacial Clinic': ['Dental and Craniofacial Implantology', 'Craniofacial Implants'] ,
	'Esophageal Clinic': ['Esophageal disorders'] ,
	'Pediatric Sleep Medicine in Minnesota': ['Pediatric / Adolescent Medicine', 'Pediatric Emergency Medicine', 'Pediatric Internal Medicine'] ,
	'Nephrology and Hypertension': ['Pulmonary Hypertension', 'Portal Hypertension', 'Pulmonary Arterial Hypertension'] ,
	'Heart Transplant Program': ['Heart and Lung Transplantation'] ,
	'Breast and Melanoma Surgical Oncology': ['Hematology and Medical Oncology', 'Neurosurgical Oncology', 'Head and Neck Oncology'] ,
	'Sleep Disorders Center in Arizona': ['Sleep Disorders'] ,
	'Laboratory Medicine and Pathology': ['Pulmonary Medicine (Pulmonology)', 'Medical Renal Pathology', 'Internal Medicine'] ,
	'Oncology (Medical)': ['Oncology'] ,
	'Ehlers-Danlos Syndrome Clinic in Florida': ['Ehlers Danlos Syndrome'] ,
	'Psychiatry and Psychology Services': ['Psychology','Psychiatry'] ,
	'Sleep Disorders Center in Florida': ['Sleep Disorders'] ,
	'Fibroid Clinic': ['Fibroids']
}

for mayo_record in db.mayo_embeddings.find():
	if 'LemmatizedSpecialties' in mayo_record.keys():
		mayo_record['FixedLemmatizedSpecialties'] = []
		for spec in mayo_record['LemmatizedSpecialties']:
			if spec in fix_map:
				for val in  fix_map[spec]:
					mayo_record['FixedLemmatizedSpecialties'].append(val)
			elif spec in manual_fixes:
				for val in  manual_fixes[spec]:
					mayo_record['FixedLemmatizedSpecialties'].append(val)
			else:
				mayo_record['FixedLemmatizedSpecialties'].append(spec)
		db.mayo_embeddings.update_one({'_id': mayo_record['_id'] }, {'$set': mayo_record})


# evaluate missing

mayo_specialties_count_map_2 = {}
for mayo_record in db.mayo_embeddings.find():
	if 'FixedLemmatizedSpecialties' in mayo_record.keys():
		for spec in mayo_record['FixedLemmatizedSpecialties']:
			if spec in mayo_specialties_count_map_2:
				mayo_specialties_count_map_2[spec] += 1
			else:
				mayo_specialties_count_map_2[spec] = 1

counter = 0
for mayo_spec, v in mayo_specialties_count_map_2.items():
	if mayo_spec not in physician_specialties_count_map:
		counter += 1
print(f"counter: {counter}")







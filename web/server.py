import os
import asyncio
from pymongo import MongoClient

import tornado.web


class Doctor:
    def __init__(self, name, specialties, location, about):
        self.name = name
        self.specialties = specialties
        self.location = location
        self.about = about

    @classmethod
    def create_from_fields(cls, fields):
        return cls(fields['Name'], fields['StandardizedSpecialties'], fields.get('Location'), fields.get('About'))


class QueryHandler(tornado.web.RequestHandler):

    # function to create a MongoDB connection from localhost and return a database client 
    # returns the database connection object
    def create_db_connection(self, collection, db = "expert_search"):
        client = MongoClient()
        return client.get_database(db).get_collection(collection)

    # function to query the specified collection and return all
    # input: `collection` is a MongoClient database connection object for MongoDB
    # output: list of dicts, where each dict is a doctor profile
    def query_all(self, collection):
        return [doc for doc in collection.find()]

    # function to query and return one document from the specified collection
    # input: `collection` is a MongoClient database connection object for MongoDB
    # output: single doctor (dict object)
    # FOR TESTING PURPOSES ONLY - NOT USED IN APPLICATION
    def query_n(self, collection, n = 1):
        if (doctor := collection.find_one()) is not None:
            return doctor
        else:
            raise tornado.web.HTTPError(404)

    # function to get the term-document frequency (# of documents in which a given term appears)
    # inputs: `term` (string), `collection` (list-of-list-of-strings)
    def get_term_doc_freq(self, term, collection):
        cnt = 0
        for doc in collection:
            if term in doc:
                cnt += 1
        return cnt

    
    # function to perform query preprocessing
    # if 'bow = True' then return dictionary with Bag-of-Words representation
    # else, return list of tokens (after preprocessing)
    def process_query(self, query, bow = True, delim = ' '):
        STOP_WORDS = ['the','a','an','is'] # define a simple list of stopwords for optional removal
        PUNCT = ['.',',','?','!',';',':','$','/'] # define list of punctuation tokens for optional removal
        temp = [w.lower() for w in query.split(delim) if w not in STOP_WORDS] # tokenization + stopword/punct removal
        return {x: temp.count(x) for x in set(temp)} if bow else temp # return BoW (dict) or token list based on 'bow' param

    # function to compare two dictionaries via TF-IDF weighting (user symptom query (d1) and symptom dict (d2))
    # returns an int, which is the number of words (keys) from the user query that match symptom words (keys)
    # value is weighted by both the user query and the disease symptom list, i.e., more frequent term increases rank in linear fashion
    # also performs IDF weighting: divides a term's score by the number of documents in which that term exists (in order to discount the matching of common terms)
    def compare_dicts(self, d1, d2, idf):
        cnt = 0
        for w in d1.keys():
            if w in d2:
                if idf[w] > 0:
                    cnt += ((d1[w] * d2[w]) / idf[w]) # perform TF-IDF weighting: more weight when matching a term multiple times, but discount common terms
                else:
                    cnt += (d1[w] * d2[w]) # if query term doesn't appear in any documents, don't add weight (but avoid divide-by-zero errors)
        return cnt

    def get_doctors(self, query):
        # turn the user's query into a dict representation (keys = unique tokens, values = frequencies)
        user_query = self.process_query(query)

        # retrieve all documents from mayo_embeddings (collection), then create list of dicts
        # ...where each dict is disease(string):symptom(string,comma-deliminated)
        # then, loop through each dict and call "preprocess_query" to turn the symptom string into its own dict
        disease_list = self.query_all(collection=self.create_db_connection(collection="mayo_embeddings"))
        disease_symptom_dict = {x["disease"]: self.process_query(x["symptoms"], delim=',') for x in disease_list}
        disease_specialty_dict = {x["disease"]: self.process_query(x["specialties"], delim=',') for x in disease_list}

        # create a dict of user query tokens (keys) and their document frequencies (values) to perform IDF weighting
        # here, a "document" is a list of symptoms associated with one disease
        disease_symptom_list = [sym['disease'].split(',') for sym in
                                disease_list]  # list-of-lists, where one list is a disease, and it contains a list of symptom tokens
        term_doc_freq = {term: self.get_term_doc_freq(term, disease_symptom_list) for term in
                         user_query}  # create doc freq dictionary for all terms in user query

        # create the query-disease rankings:
        #   Loop through each disease and call "compare_dicts" to compare its token freq dict with the user's query dict
        #   Assign the value (weighted count) to a new dict, with key=disease, val=weighted count
        match_dict = {k: self.compare_dicts(d1=user_query, d2=disease_symptom_dict[k], idf=term_doc_freq) for k in
                      disease_symptom_dict}
        # for k in disease_symptom_dict:
        #    match_dict[k] = self.compare_dicts(d1 = user_query, d2 = disease_symptom_dict[k], idf = term_doc_freq)

        # sort match_dict based on score (disease-query rank)
        match_dict = {k: v for k, v in sorted(match_dict.items(), key=lambda x: x[1], reverse=True)}
        # print(match_dict) # TEST PRINT - dict of diseases ranked by their TF-IDF weight

        ## ---------------------------------------------
        ## PART 2: mapping a disease to a list of specialties, and comparing that list of specialties to doctor specialities (TF-IDF)
        ## ---------------------------------------------
        # for now, hard-code and take only the n=1 most likely disease based on the user query TF-IDF comparison/ranking

        # create a dict of (specialty: frequency) pairs -- with n=1 diseases, frequency should always = 1
        # (but keeping as a dictionary so we can still use the "compare_dicts" method)
        target_specialty_dict = disease_specialty_dict[list(match_dict.keys())[0]]
        # print(target_specialty_dict)

        # retrieve the list of doctors
        doctor_list_raw = self.query_all(
            collection=self.create_db_connection(collection="physicians"))  # currently a list of dicts

        # PREPROCESSING: some doctors don't have StandardizedSpecialties defined. Remove those doctors to avoid errors
        doctor_list = [doc for doc in doctor_list_raw if "StandardizedSpecialties" in doc.keys()]


        doctors_by_name = {doc["Name"]: doc for doc in doctor_list}

        doctor_name_specialty_dict = {
            doc["Name"]: self.process_query(','.join(x for x in doc["StandardizedSpecialties"]), delim=',') for doc in
            doctor_list}

        # create a dict of target disease specialties and their document frequencies (here, each "document" is a doctor's list of specialties)
        doctor_specialty_collection = [doc["StandardizedSpecialties"] for doc in doctor_list]
        specialty_doc_freq = {spec: 1 for spec in target_specialty_dict.keys()}  # use this for IDF weighting

        # print(doctor_name_specialty_dict)

        # get doctor "match list" based on TF ranking (add pseudocount of 1 for IDF - not enough data to capture enough non-zero doc frequencies)
        doctor_match_list = {
            k: self.compare_dicts(d1=target_specialty_dict, d2=doctor_name_specialty_dict[k], idf=specialty_doc_freq)
            for k in doctor_name_specialty_dict}
        doctor_match_list_ranked = {k: v for k, v in
                                    sorted(doctor_match_list.items(), key=lambda x: x[1], reverse=True)}

        # print(doctor_match_list_ranked) # test print the doctors (results) ranked by TF-IDF weighting
        print('User query: ' + query)
        print('------------------')
        print('Most likely condition: ' + list(match_dict.keys())[0])
        print('------------------')
        print('Corresponding specialties: ' + ','.join(
            x for x in disease_specialty_dict[list(match_dict.keys())[0]].keys()))
        print('------------------')
        print('Top 10 doctors matching those specialties: ')
        print('------------------')
        for name in list(doctor_match_list_ranked.keys())[:10]:
            print(name + '\t' + ','.join(doctor_name_specialty_dict[name].keys()) + '\t' + str(
                doctor_match_list_ranked[name]))

        print()

        # top10_doctors = [doctors_by_name[name]: for name in list(doctor_match_list_ranked.keys())[:10]]
        top10_doctors = [
            Doctor.create_from_fields(doctors_by_name[name])
            for name in list(doctor_match_list_ranked.keys())[:10]
        ]
        return top10_doctors

    def get(self):
        query = self.request.arguments['query'][0].decode(encoding='utf-8')
        doctors = self.get_doctors(query)
        self.render(
            'query.html',
            query=query,
            doctors=doctors,
        )


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(
            'main.html'
        )


def make_app():
    settings = {
        'template_path': os.path.join(os.path.dirname(__file__), 'template'),
        'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    }
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/query", QueryHandler),
    ], **settings)


async def main():
    app = make_app()
    app.listen(80)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())

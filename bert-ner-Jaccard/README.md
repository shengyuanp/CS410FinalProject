## Alternative backend options for language modeling and similarity evaluation

These options uses the following HuggingFace models
1. [BERT-NER](https://huggingface.co/d4data/biomedical-ner-all)
2. [UMLSBert_ENG](https://huggingface.co/GanjinZero/UMLSBert_ENG)

This option use the Jaccard similarity
1. [Jaccard similarity](https://en.wikipedia.org/wiki/Jaccard_index)

### 1. UserInputSym.py
Use OpenAI gpt-3 `text-davinci-002` model to create user descriptions for each disease

### 2. NERPreprocess.py
Use BERT-NER to identify symptom keywords from unstructured descriptive text

### 3. MayoSymToEmbedding.py
Use pre-trained clinical BERT to convert NER symptoms to BERT embeddings

### 4. CosineSimilarity
Use cosine similarity measure to predict the disease associated with user input symptom and benchmark prediction accuracy

### 5. Userintput2EmbedFunc.py
Functions to be tested on server as backend retrieval methodology
1) Function to convert user symptom to BERT embeddings
2) Function to create normalized cosine similarity of user query against every Mayo disease symptoms

### 6. JaccardApproach.ipynb
Use user inputs as list and compare with symptoms as list to predict the most likely diseases with Jaccard similarity

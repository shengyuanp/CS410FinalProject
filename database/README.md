
Setup


### If you want to connect from local:

1. Please share your SSH public key with the server administrator sethac3@illinois.edu to get access

2. set up ssh forwarding by typing this in your terminal

```
ssh -L 27017:127.0.0.1:27017 -i <path_to_priv_key> 35.209.9.96
```

3. Use your favourite mongodb client to connect to `mongodb://localhost:27017`


### If you are more comfortable on on the terminal

```
ssh -i <path_to_priv_key> 35.209.9.96

mongo
show dbs

use expert_search

db.physicians.count()
```



import shelve

with shelve.open("database") as db:
    for k, v in db.items():
        print(k, v)
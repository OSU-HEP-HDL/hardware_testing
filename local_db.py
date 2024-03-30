from db_utils import authenticate_user_mongodb
import pymongo
import json

client = authenticate_user_mongodb()

print(client.list_database_names())


mydb = client["visual_test"]
mycol = mydb["inspections"]

mydict = {"mfr_id": "1234", "atlas_id": "5678", "damaged": "yes", "dirty": "no", "missing_parts": "yes", "image": "path/to/image.jpg"}

x = mycol.insert_one(mydict)

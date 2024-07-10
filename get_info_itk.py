import itkdb

client = itkdb.Client()
client.user.authenticate()  
user = client.get("getUser", json={"userIdentity": client.user.identity})
print([institution["code"] for institution in user["institutions"]])

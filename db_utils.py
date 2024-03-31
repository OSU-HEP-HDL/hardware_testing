import itkdb
import pymongo
from dotenv import dotenv_values

def authenticate_user_itkdb():
    '''
    Authenticates user base on ITKDB_ACCESS_CODE1="", ITKDB_ACCESS_CODE2="".
    Prints users first name
    '''
    client = itkdb.Client()
    auth = client.user.authenticate()

    if auth == False:
        print("\nFailed to authenticate user!\n")
    else:
        return client


def authenticate_user_mongodb():
    keys = dotenv_values(".env")
    USERNAME = keys["USERNAME"]
    PASSWORD = keys["PASSWORD"]
    LOCAL_ADDRESS = keys["LOCAL_ADDRESS"]
    client = pymongo.MongoClient('mongodb://%s:%s@%s' % (USERNAME, PASSWORD, LOCAL_ADDRESS))
    return client

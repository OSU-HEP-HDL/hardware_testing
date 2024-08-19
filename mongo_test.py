from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb

def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    db = mongodb_client["local"]
    collection_list = db.list_collections()
    for c in collection_list:
        print(c)

    
if __name__ == '__main__':
  main()
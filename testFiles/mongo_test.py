from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb

def main():
    itkdb_client = authenticate_user_itkdb()
    client = authenticate_user_mongodb()
    db = client["local"]["itk_testing"]
    serial_number = "20UPIPP9040001"
    print(db.find_one({"_id": serial_number}))
    comp = db.find_one({"_id": serial_number})

   
    result = {"$set":{
               "tests":{
                 "visual": "1"
               }
             }
           }
    if "poop" not in db.find_one({"_id": serial_number}):
       print("I want poop")
    db.update_one({"_id": serial_number},result)
    #db.update_one({"_id": serial_number}, {"$set":{"tests.CONNECT":2}})
    
    #db.update_one(
    ##              "$push":{"tests":{"VISUAL":"result1","CONNECT":"result2"}})
    print(comp)
    #db.update_one("")

    
if __name__ == '__main__':
  main()
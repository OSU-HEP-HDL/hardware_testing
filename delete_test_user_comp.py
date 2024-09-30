from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import get_type, get_latest_serial, get_code_and_function, get_flavor, get_N2, get_component_type, get_production_status
from modules.mongo_db import insert_property_names
import datetime
import json



def delete_test_user_comp(itkdb_client, mongo_db):
    print("Searching production database for this type...")
    search_filter = {
        "filterMap": {
            "institute": "OSU"
        }
    }
    existing_components = itkdb_client.get("listComponents", json=search_filter)

    existing_test_components = []
    p = 0
    for i in existing_components:
        '''For deleted components'''
        if i['state'] == "deleted":
            #print(i)
            continue
        userIdentity = str(i["userIdentity"])
        if userIdentity == "7227-934-1":
            existing_test_components.append(i["id"])
            p=p+1
    
    print("Deleting",len(existing_test_components),"test components")
    for comp in existing_test_components:
        del_filter = {
                "component": comp,
                "reason": "deleting test user"
                }
        itkdb_client.post("deleteComponent",json=del_filter)
    print("Successfully deleted test user components!")

def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    delete_test_user_comp(itkdb_client,mongodb_client)

if __name__ == '__main__':
  main()
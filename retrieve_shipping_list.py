from modules.db_auth import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import get_type, get_latest_serial, get_code_and_function, get_flavor, get_N2, get_component_type, get_production_status, get_alternative_serial
from modules.mongo_db import insert_property_names
from modules.utilities import check_sn, create_excel
import datetime
import json

def get_shipping_list(client):
   
    """Retrieve the shipping list from the ITKDB."""
    id = "67ed887473b21e313546e2a7"
    ship_filter = {
            "id": id
    }
    
    shipping_list = client.get('getShipment',json={"component": ship_filter})
    print(shipping_list)
    return shipping_list

def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    
    get_shipping_list(itkdb_client)
 
if __name__ == '__main__':
  main()
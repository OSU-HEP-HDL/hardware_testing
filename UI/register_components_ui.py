from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import get_type, get_latest_serial, get_code_and_function, get_flavor, get_N2, get_component_type, get_production_status
from modules.mongo_db import insert_property_names
import datetime
import json
import argparse

parser = argparse.ArgumentParser(description="Register Component for UI. Takes all component info as string arguments provided from UI")
parser.add_argument("-t",'--type',type=str,required=True,help="Component Type, ex. DATA FLEX ")
parser.add_argument("-s",'--status',type=str,required=True,help="Component Status, ex. Pre-Production ")
parser.add_argument("-pl",'--placement',type=str,required=True,help="Component Placement, ex. Barrel or Ring ")
parser.add_argument("-m",'--modules',type=str,required=True,help="Number of Modules, ex. TRIPLET")
parser.add_argument("-f",'--flavor',type=str,required=True,help="Component Flavor")

args = vars(parser.parse_args())


def upload_component(client,component, serialNumber):
    ''' This is for a single component upload'''
    if isinstance(serialNumber,str):
        ''' retrieve component template to save'''
        project = serialNumber[3]
        subproject = serialNumber[3:5]
        comp_filter = {
        "project": project,
        "code": "IS_TYPE0"
        }
        component_template = client.get('generateComponentTypeDtoSample',json=comp_filter)
        
        purpose = serialNumber[7]
        type_combination = serialNumber[8]
        flavor = serialNumber[9]

        
        print("\nWho is the vendor?")
        vendor_list = ["Altaflex","PFC","Cirexx","EPEC","Vector","Summit"]
        for k, v in enumerate(vendor_list):
            print(f"For {v}, press {k}")
        vendor = input("\nInput Selection: ") 
      
        new_component = {
            **component_template,
            "subproject": subproject,
            "institution": "OSU",
            "type": component,
            "serialNumber": serialNumber,
            "properties": {**component_template['properties'], "PURPOSE": purpose, "TYPE_COMBINATION":type_combination,"FLAVOR":flavor, "VENDOR": vendor}
        }

        print("You are uploading a new", component,"with serial number", serialNumber, "from",vendor_list[int(vendor)],", do you wish to continue? (y or n)")
        answer = input("\nInput Selection: ")
        if answer == "y" or answer == "yes":
            print("Uploading new component...")
            client.post('registerComponent',json=new_component)
            print("Done!")
            local = True
        else:
            print("Exiting...")
            local = False
        return new_component, local
    else:
        ''' retrieve component template to save'''
        project = serialNumber[0][3]
        subproject = serialNumber[0][3:5]
        comp_filter = {
        "project": project,
        "code": "IS_TYPE0"
        }
        component_template = client.get('generateComponentTypeDtoSample',json=comp_filter)
        #print(component_template)
        #print(subproject)
        
        purpose = serialNumber[0][7]
        type_combination = serialNumber[0][8]
        flavor = serialNumber[0][9]

        
        print("\nWho is their vendor?")
        vendor_list = ["Altaflex","PFC","Cirexx","EPEC","Vector","Summit"]
        for k, v in enumerate(vendor_list):
            print(f"For {v}, press {k}")
        vendor = input("\nInput Selection: ") 

        print("You are uploading",str(len(serialNumber)),"new", component, "from",vendor_list[int(vendor)],", do you wish to continue? (y or n)")
        answer = input("\nInput Selection: ")

        if answer == "y" or answer == "yes":
            print("Uploading new components...")
            component_list = []
            for serial in serialNumber:
                new_component = {
                    **component_template,
                    "subproject": subproject,
                    "institution": "OSU",
                    "type": component,
                    "serialNumber": serial,
                    "properties": {**component_template['properties'], "PURPOSE": purpose, "TYPE_COMBINATION":type_combination,"FLAVOR":flavor, "VENDOR": vendor}
                }
                component_list.append(new_component)
                #print(new_component)
                client.post('registerComponent',json=new_component)
            print("Done!")
            local = True
        else:
            print("Not uploading to the production database...")
            local = False
        return component_list,local
        
def upload_component_local(client,component):
    db = client["local"]["itk_testing"]
    print("Uploading to local database...")

    ''' This is for a batch of components to upload locally'''
    if isinstance(component,list):
        for comp in component:
            purpose,type_combination,vendor = insert_property_names(comp)
            updated_component = {
                **comp,
                'stage': 'RECEPTION',
                'properties': {"PURPOSE": purpose, "TYPE_COMBINATION": type_combination, "VENDOR": vendor},
                '_id': comp["serialNumber"]
            }

            ''' Check to see if any components exist locally '''
            try:
                if db.find_one({"_id": comp["serialNumber"]}) != None:
                    raise ValueError
                else:
                    db.insert_one(updated_component)
                    
            except ValueError:
                print("Component with serial number",comp["serialNumber"],"already exists locally!")
                exit
        print("Uploaded components locally!")
    
    else:
        ''' Uploads a single component to local database '''
        purpose,type_combination,vendor = insert_property_names(component)

        updated_component = {
            **component,
            'stage': 'RECEPTION',
            'properties': {"PURPOSE": purpose, "TYPE_COMBINATION": type_combination, "VENDOR": vendor},
            '_id': component["serialNumber"]
        }
        
        '''Check if component exists locally'''
        try:
            if db.find_one({"_id": component["serialNumber"]}) != None:
                raise ValueError
            else:
                db.insert_one(updated_component)
                print("Uploaded component locally!")
        except ValueError:
            print("Component already exists locally!")
            exit
        print("Component uploaded to local database successfully!")

def get_data(itkdb_client):
    register = True
    print(args)
    comp_selection = args['type']
    xxyy = get_code_and_function(comp_selection)
    production_status = get_production_status(args['status'])
    N2 = get_N2(args['placement'],args['modules'])
    comp_type = get_type(xxyy,N2)
    flavor = args['flavor']
    atlas_serial = get_latest_serial(itkdb_client, xxyy, production_status, N2, flavor, register,comp_type)

    return comp_type, atlas_serial


def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    meta_data = get_data(itkdb_client)
    #component,local = upload_component(itkdb_client,meta_data[0],meta_data[1])
    #if local == True:
    #    upload_component_local(mongodb_client,component)

if __name__ == '__main__':
  main()

from modules.db_auth import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import get_type, get_latest_serial, get_code_and_function, get_flavor, get_N2, get_component_type, get_production_status, get_alternative_serial
from modules.mongo_db import insert_property_names
from modules.utilities import check_sn, create_excel
import datetime
import json



def upload_component(client,component, serialNumber,alternative_serial):
    ''' This is for a single component upload'''
    ylist = ["y","yes","Y","YES"]
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
            "properties": {**component_template['properties'], "PURPOSE": purpose, "TYPE_COMBINATION":type_combination,"FLAVOR":flavor, "VENDOR": vendor,"ALTERNATIVE_IDENTIFIER": alternative_serial}
        }
        
        print("You are uploading a new", component,"with serial number", serialNumber, "from",vendor_list[int(vendor)],", do you wish to continue? (y or n)")
        answer = input("\nInput Selection: ")
        if answer in ylist:
            print("Uploading new component...")
            client.post('registerComponent',json=new_component)
            print("Done!")
            local = True
        else:
            print("Exiting...")
            local = False
        
        search_filter = {
        "filterMap":{
            "project": project,
            "subproject": subproject,
            "type": component,
            "institute": "OSU",
            "serialNumber": serialNumber
        }
        }
        posted_component = client.get("listComponents", json=search_filter)
        print(posted_component)
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

        if answer in ylist:
            print("Uploading new components...")
            component_list = []
            for serial,alt in zip(serialNumber,alternative_serial):
                new_component = {
                    **component_template,
                    "subproject": subproject,
                    "institution": "OSU",
                    "type": component,
                    "serialNumber": serial,
                    "properties": {**component_template['properties'], "PURPOSE": purpose, "TYPE_COMBINATION":type_combination,"FLAVOR":flavor, "VENDOR": vendor,"ALTERNATIVE_IDENTIFIER": alt}
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
            purpose, type_combination, flavor, vendor, alternative_id = insert_property_names(comp)
            updated_component = {
                **comp,
                'stage': 'RECEPTION',
                'properties': {"PURPOSE": purpose, "TYPE_COMBINATION": type_combination, "VENDOR": vendor,"FLAVOR":flavor, "VENDOR": vendor,"ALTERNATIVE_IDENTIFIER": alternative_id},
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
        purpose, type_combination, flavor, vendor, alternative_id = insert_property_names(component)

        updated_component = {
            **component,
            'stage': 'RECEPTION',
            'properties': {"PURPOSE": purpose, "TYPE_COMBINATION": type_combination, "VENDOR": vendor,"FLAVOR":flavor, "VENDOR": vendor,"ALTERNATIVE_IDENTIFIER": alternative_id},
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
    comp_selection = get_component_type()
    xxyy = get_code_and_function(comp_selection)
    production_status = get_production_status()
    N2, module = get_N2(xxyy)
    comp_type = get_type(xxyy,N2)
    flavor = get_flavor(comp_type)
    atlas_serial = get_latest_serial(itkdb_client, xxyy, production_status, N2, flavor, register,comp_type)
    alternative_serial = get_alternative_serial(atlas_serial)

    return comp_type, atlas_serial, alternative_serial


def main():
    ylist = ["y","yes","Y","YES"]
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    meta_data = get_data(itkdb_client)
    check = check_sn(meta_data[1])
 
    component,local = upload_component(itkdb_client,meta_data[0],meta_data[1],meta_data[2])
    if local == True:
        upload_component_local(mongodb_client,component)
    print("Create excel of serial numbers?")
    ans = input("\nAnswer (y or n): ")
    if ans in ylist:
        create_excel(meta_data[1],meta_data[2])
    else:
        print("Fin")
if __name__ == '__main__':
  main()

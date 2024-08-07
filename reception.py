from db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from reception_module import get_type, get_latest_serial, get_code_and_function, get_flavor, get_N2, get_component_type, get_production_status
import datetime
import json



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
        #print(component_template)
        #print(subproject)
        
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

        print("You are uploading a new", component,"with SN", serialNumber, "from",vendor_list[int(vendor)],", do you wish to continue? (y or n)")
        answer = input("\nInput Selection: ")
        if answer == "y" or answer == "yes":
            print("Uploading new component...")
            client.post('registerComponent',json=new_component)
            print("Uploading done!")
        else:
            print("Exiting...")
            exit
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
            for serial in serialNumber:
                new_component = {
                    **component_template,
                    "subproject": subproject,
                    "institution": "OSU",
                    "type": component,
                    "serialNumber": serial,
                    "properties": {**component_template['properties'], "PURPOSE": purpose, "TYPE_COMBINATION":type_combination,"FLAVOR":flavor, "VENDOR": vendor}
                }

                #print(new_component)
                client.post('registerComponent',json=new_component)
            print("Uploading done!")
        else:
            print("Exiting...")
            exit
        

def get_data(itkdb_client):
    date = str(datetime.datetime.now())
    comp_selection = get_component_type()
    xxyy = get_code_and_function(comp_selection)
    production_status = get_production_status()
    N2 = get_N2()
    comp_type = get_type(xxyy,N2)
    flavor = get_flavor()
    atlas_serial = get_latest_serial(itkdb_client, xxyy, production_status, N2, flavor)

    return comp_type, atlas_serial


def main():
    itkdb_client = authenticate_user_itkdb()
    #mongodb_client = authenticate_user_mongodb()
    meta_data = get_data(itkdb_client)
    upload_component(itkdb_client,meta_data[0],meta_data[1])


if __name__ == '__main__':
  main()

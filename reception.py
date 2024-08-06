from db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from production_module import get_type, format_number, prepend, create_labels, get_latest_serial
import datetime
import segno
import json

def get_component_type():
    comp_names = ["DATA FLEX", "POWER FLEX", "RING", "Z-RAY", "PPO"]
    print("Select a component type.\n")
    for k, v in enumerate(comp_names):
        print(f"For {v}, press {k}")

    while True:
        try:
            comp_selection = comp_names[int(input("\nInput Selection: "))]
            break
        except (ValueError, IndexError):
            print("Input was not a valid selection. Try again.")
    print(f"Selected {comp_selection}\n")
    return comp_selection


def get_code_and_function(component):
    '''
    Based on component selection, this function returns the XXYY code for the serial number and the function attribute of the component.
    TODO: finish the function attribute for all components
    '''

    if "PP0" in component:
        #code_prefix = "PP"
        code_suffix = "PG"
    else:
        code_prefix = "PI"

        if "DATA" in component:
            code_suffix = "DP"
            function = "D"
        elif "POWER" in component:
            code_suffix = "PP"
            function = "P"
        elif "RING" in component:
            code_suffix = "RF"
            function = "R"
        elif "Z-RAY" in component:
            code_suffix = "PG"
        elif "PPO" in component:
            code_suffix = "PG"
        else:
            code_suffix = None
    xxyy = str(code_prefix) + str(code_suffix)
    return xxyy


def get_production_status():
    status_list = ["Pre-Production", "Production","Dummy"]
    status_num = [0,1,9]
    counter = 0
    for k, v in enumerate(status_list):
        if k == 2:
            k = 9
        print(f"For {v}, press {k}")
    while True:
        try:  
            selection = input("\nInput Selection: ")
            if int(selection) in status_num:
                status = selection
            else:
                raise ValueError
            break
        
        except(ValueError,IndexError):
            print("Invalid Input. Try again.")
            counter = counter +1
            if counter %3 ==0:
                print("")
                for k, v in enumerate(status_list):
                    if k == 2:
                          k = 9
                    print(f"For {v}, press {k}")


    print(f"Selected {status}\n")
    return selection

def get_N2():
    '''
    N2 is a value in the serial number which is dependent on component placement and the number of modules on the component.
    This gives the user a selection for both component placement and # modules.
    Returns N2
    '''

    print("Select Component Placement.")
    placement_options = ["BARREL", "RING"]
    for k, v in enumerate(placement_options):
        print(f"For {v}, press {k}")
    while True:
        try:
            selection_1 = input("\nInput Selection: ")
            placement = placement_options[int(selection_1)]
            break
        except (ValueError, IndexError):
            print("Invalid Input. Try again.")
    print(f"Selected {placement}\n")

    print("Select Number of Modules")
    module_types = ["TRIPLET", "QUAD", "BOTH"]
    for k, v in enumerate(module_types):
        print(f"For {v}, press {k}")
    while True:
        try:
            selection_2 = input("\nInput Selection: ")
            n_modules = module_types[int(selection_2)]
            if int(selection_1) == 0 and int(selection_2) == 2:
                print("Error: You've selected BARREL and BOTH. Only RINGS are BOTH. Try again.")
                raise ValueError
            break
        except (ValueError, IndexError):
            print("Invalid Input. Try again.")
    print(f"Selected {n_modules}\n")

    if int(selection_1) == 0:
        if int(selection_2) == 0:
            N2 = 0
        elif int(selection_2) == 1:
            N2 = 1
    elif int(selection_1) == 1:
        if int(selection_2) == 0:
            N2 = 2
        if int(selection_2) == 1:
            N2 = 3
        if int(selection_2) == 2:
            N2 = 4
    return N2

def get_flavor():
    '''
    Prompts user to select the flavor of component.
    '''
    print("Select Component Flavor.")
    flavor_options = [0, 1, 2, 3, 4]
    for k, v in enumerate(flavor_options):
        print(f"For {v}, press {k}")
    while True:
        try:
            selection = input("\nInput Selection: ")
            flavor = flavor_options[int(selection)]
            break
        except (ValueError, IndexError):
            print("Invalid Input. Try again.")
    print(f"Selected {flavor}\n")

    return flavor


def get_data(itkdb_client):
    date = str(datetime.datetime.now())
    comp_selection = get_component_type()
    xxyy = get_code_and_function(comp_selection)
    production_status = get_production_status()
    N2 = get_N2()
    comp_type = get_type(xxyy,N2)
    flavor = get_flavor()
    atlas_serial = get_latest_serial(itkdb_client, xxyy, production_status, N2, flavor)

    return comp_type, atlas_serial #, json.dumps({"date": date, "atlas_serial": atlas_serial})

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
        print(component_template)
        print(subproject)
        
        print("\nState the purpose:")
        purpose_list = ["Pre-Production", "Production","Dummy"]
        for k, v in enumerate(purpose_list):
            print(f"For {v}, press {k}")
        purpose_selection = input("\nInput Selection: ")
        purpose = purpose_list[int(purpose_selection)]
        
        #### ADD TYPE COMBINATION

        flavor = serialNumber[9]
        #### CHECK WHY SN IS NOT IN TEMPLATE
        print("\nWhat is the vendor?")
        vendor_list = ["Vector","vendor2"]
        for k, v in enumerate(vendor_list):
            print(f"For {v}, press {k}")
        vendor_selection = input("\nInput Selection: ")
        vendor = vendor_list[int(vendor_selection)]

        new_component = {
            **component_template,
            "subproject": subproject,
            "institution": "OSU",
            "type": component,
            "serialNumber": serialNumber,
            "properties": {**component_template['properties'], "PURPOSE": purpose, "FLAVOR":flavor, "VENDOR": vendor}
        }
        print(new_component)


def main():
    itkdb_client = authenticate_user_itkdb()
    #mongodb_client = authenticate_user_mongodb()
    meta_data = get_data(itkdb_client)
    print(meta_data[0],meta_data[1])
    upload_component(itkdb_client,meta_data[0],meta_data[1])
    #create_labels(meta_data)
    # print(meta_data)


if __name__ == '__main__':
  main()

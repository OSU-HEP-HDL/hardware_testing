import itkdb
import csv

client = itkdb.Client()

'''
NOTE: ITKDB_ACCESS_CODE1="", ITKDB_ACCESS_CODE2="" are stored in .env
'''

def authenticate_user(client):
    '''
    Authenticates user base on ITKDB_ACCESS_CODE1="", ITKDB_ACCESS_CODE2="".
    Prints users first name
    '''
    auth = client.user.authenticate()

    if auth == False:
        print("\nFailed to authenticate user!\n")
    else:
        user = client.get("getUser", json={"userIdentity": client.user.identity})
        print("\nAuthenticated as " + user["firstName"] + ".\n")


def list_options(client):
    '''
    Lists current component options for user to choose from.
    Returns user selection.
    '''

    '''
    NOTE: These are names of components which we already have created in the database
    and are relevant to our group.
    '''
    defined_comp_names = ["Data Flex", "Power Flex", "Rigid Ring"]
    comp_type_list = [x["code"] for x in client.get("listComponentTypes", json={"filterMap":{"project": "P"}}) if x["name"] in defined_comp_names]

    print("Select a component type.\n")
    for k, v in enumerate(comp_type_list):
        print(f"For {v}, press {k}")

    while True:
        try:
            comp_selection = comp_type_list[int(input("\nInput Selection: "))]
            break
        except (ValueError, IndexError):
            print("Input was not a valid selection. Try again.")
    print(f"Selected {comp_selection}\n")
    return comp_selection


def get_code_and_function(component):
    '''
    Based on component selction, this function returns the XXYY code for the serial number and the function attribute of the component.
    TODO: finish the function attribute for all components
    '''

    if "PP0" in component:
        code_prefix = "PP"
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
        elif "Z-Ray" in component:
            code_suffix = "PG"
        else:
            code_suffix = None
    xxyy = code_prefix + code_suffix
    return xxyy, function

def get_production_status():
    status_list = ["Pre-Production", "Production"]
    for k, v in enumerate(status_list):
        print(f"For {v}, press {k}")
    while True:
        try:
            selection = input("\nInput Selection: ")
            status = status_list[int(selection)]
            break
        except (ValueError, IndexError):
            print("Invalid Input. Try again.")
    print(f"Selected {status}\n")
    return selection

def get_N2():
    '''
    N2 is a value in the serial number which is dependent on component placement and the number of modules on the component.
    This give the user a selection for both component placement and # modules.
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

    # return selection

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

def format_number(num):
    '''
    This ensures the last four digits of the serial number are in fact four digits when reprsented as a string
    '''
    try:
        num = int(num)
    except ValueError:
        return "Invalid input. Please provide a valid number."

    if 1 <= num <= 9999:
        formatted_num = '{:04d}'.format(num)
        return formatted_num
    else:
        return "Number out of range. Please provide a number between 1 and 9999."

def get_latest_serial(client, xxyy, production_status, N2, flavor):
    '''
    Checks data base for existing components with the same first 10 digits.
    Finds largest existing serial number and increments it by 1.
    Returns the new serial number.
    '''
    partial_serial = "20U" + str(xxyy) + str(production_status) + str(N2) + str(flavor)
    print(partial_serial)
    project = xxyy[0]
    subproject = xxyy[0:1]

    search_filter = {
        "project": project,
        "subproject": subproject,
        "pageInfo": {"pageSize": 32}
    }

    existing_components = client.get("listComponents", json=search_filter)
    for i in existing_components:
        print(i)
    existing_serials = []
    for component in existing_components:
        if component["serialNumber"] is None:
            pass
        elif partial_serial in component["serialNumber"]:
            existing_serials.append(component["serialNumber"])

    latest_serial = 0
    for serial in existing_serials:
        if len(serial) != 14:
            pass
        else:
            if latest_serial < int(serial[10:14]):
                latest_serial = int(serial[10:14])
            else:
                pass
    new_serial = format_number(latest_serial + 1)
    return(latest_serial)


# def upload_component(client, xxyy, function, comp_selection, serial_number):
#     project = xxyy[0]
#     subproject = xxyy[2:4]

#     attributes = {
#         "project": project,
#         "subproject": subproject,
#         "institution": "OSU",
#         "componentType": comp_selection,
#         "properties": {"PROD_SERIAL_NUMBER": serial_number,
#                        "FUNCTION": function}
#     }
#     client.post('register', json=attributes)

authenticate_user(client)
comp_selection = list_options(client)
xxyy, function = get_code_and_function(comp_selection)
production_status = get_production_status()
N2 = get_N2()
flavor = get_flavor()
serial_number = get_latest_serial(client, xxyy, production_status, N2, flavor)
print(serial_number)
# upload_component(client, xxyy, function, comp_selection, serial_number)

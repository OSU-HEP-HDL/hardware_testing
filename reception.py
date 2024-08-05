from db_utils import authenticate_user_itkdb, authenticate_user_mongodb
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

def format_number(latest_serial):
    '''
    This ensures the last four digits of the serial number are in fact four digits when represented as a string
    '''
    answers = ["n","y","no","yes"]
    nol = ["n","no"]
    yesl = ['y',"yes"]
    print("Are you entering a batch? (y or n)")
    while True:
        try:
            answer = input("\nAnswer: ")
            if answer not in answers:
                raise ValueError
            break
        except ValueError:
            print("Invalid answer. Only a y or n")
    if answer in nol:
        try:
            print("The latest serial number is:",latest_serial)
            print("The recommended serial number to enter is:", int(latest_serial)+1)
            print("Enter a number for the component (0 to 9999)")
            number = input("\nInput Selection: ")
            num = int(number)
        except ValueError:
            return "Invalid input. Please provide a valid number."

        if 0 <= num <= 9999:
            formatted_num = '{:04d}'.format(num)
            return formatted_num
        else:
            return "Number out of range. Please provide a number between 1 and 9999."
    
    if answer in yesl:
        try:
           print("Enter how many components to register (2 to 9999)")
           number = input("\nTotal Amount: ")
           num = int(number)
           print("Enter from which number to start from")
           start_number = input("\nStart Number: ")
           start_num = int(start_number)
        except ValueError:
           return "Invalid input. Please provide a valid number."
        
        ''' Need to add a check for existing components'''
        comp_list = []
        for i in range(num):

            if 0 <= i <= 9999:
                formatted_num = '{:04d}'.format(start_num+i)
                comp_list.append(formatted_num)
            else:
                return "Number out of range. Please provide a number between 1 and 9999."
        return comp_list

def get_type(xxyy, N2):
    code = xxyy[2:4]
    if str(code) == "DP" and N2 == 0:
        comp_type = "L0_BARREL_DATA_FLEX"
    elif str(code)== "PP" and N2 == 0:
        comp_type = "L0_BARREL_POWER_FLEX"
    elif str(code) == "DP" and N2 == 1:
        comp_type = "L1_BARREL_DATA_FLEX"
    elif str(code) == "PP" and N2 == 1:
        comp_type = "L1_BARREL_POWER_FLEX"
    elif str(code) == "RF" and N2 == 2:
        comp_type == "INTERMEDIATE_RING"
    elif str(code) == "RF" and N2 == 3:
        comp_type = "QUAD_RING_R1"
    elif str(code) == "RF" and N2 == 4:
        comp_type = "COUPLED_RING_R01"
    elif str(code) == "PG" and N2 == 3:
        comp_type = "QUAD_MODULE_Z_RAY_FLEX"
    elif str(code) == "PP" and N2 == 2:
        print("Select Component which R0 type.")
        r0_options = ["R0_POWER_T","R0_POWER_JUMPER"]
        for k, v in enumerate(r0_options):
            print(f"For {v}, press {k}")
        while True:
            try:
                selection = input("\nInput Selection: ")
                r0 = r0_options[int(selection)]
                break
            except (ValueError, IndexError):
                print("Invalid Input. Try again.")
        print(f"Selected {r0}\n")
        comp_type == r0
    elif str(code) == "DP" and N2 == 2:
        print("Select Component which R0 type.")
        r0t_options = ["R0_DATA_FLEX","R05_DATA_FLEX"]
        for k, v in enumerate(r0t_options):
            print(f"For {v}, press {k}")
        while True:
            try:
                selection = input("\nInput Selection: ")
                r0t = r0t_options[int(selection)]
                break
            except (ValueError, IndexError):
                print("Invalid Input. Try again.")
        print(f"Selected {r0t}\n")
        comp_type == r0t
    elif str(code) == "PG" and N2 == 4:
        comp_type = "TYPE0_TO_PP0"
    else:
        raise ValueError("Your selection does not exist! Please retry.")
    return comp_type

def get_latest_serial(client,xxyy, production_status, N2, flavor): 
    '''
    Checks data base for existing components with the same first 10 digits.
    Finds largest existing serial number and increments it by 1.
    Returns the new serial number.
    '''
    partial_serial = "20U" + str(xxyy) + str(production_status) + str(N2) + str(flavor)
    print("Partial Serial Number: ",partial_serial)
    project = xxyy[0]
    subproject = xxyy[0:2]

    comp_type = get_type(xxyy,N2)
    print("The component type you're entering is: ", comp_type)
    print("Searching production database for this type...")
    search_filter = {
        "project": project,
        "subproject": subproject,
        "type": comp_type,
        "pageInfo": {"pageSize": 32}
    }
    existing_components = client.get("listComponents", json=search_filter)
    print("Total components of type", comp_type,"found is:",existing_components.total)

    existing_osu_components = []
    existing_components_flavor = []
    for i in existing_components:
        code = str(i["institution"]["code"])
        if code == str("OSU"):
            existing_osu_components.append(i)
            if i["serialNumber"][9] == str(flavor):
                 existing_components_flavor.append(i)
    print("Total components of type ", comp_type," with flavor ", flavor, " is ",len(existing_components_flavor))

    existing_serials = []
    for component in existing_components_flavor:
        if partial_serial in component["serialNumber"]:
            existing_serials.append(component["serialNumber"])
        elif component["serialNumber"] is None:
            pass

    latest_serial = 0
    for serial in existing_serials:
        if len(serial) != 14:
            pass
        else:
            if latest_serial < int(serial[10:14]):
                latest_serial = int(serial[10:14])
            else:
                pass
    new_serial = format_number(latest_serial)
    print("New serial: ",partial_serial + new_serial )
    return partial_serial + new_serial #format_number(latest_serial)

def get_data(itkdb_client):
    date = str(datetime.datetime.now())
    comp_selection = get_component_type()
    xxyy = get_code_and_function(comp_selection)
    production_status = get_production_status()
    N2 = get_N2()
    flavor = get_flavor()
    atlas_serial = get_latest_serial(itkdb_client, xxyy, production_status, N2, flavor)

    return json.dumps({"date": date, "atlas_serial": atlas_serial})

def prepend(list, str):
    # Using format()
    str += '{0}'
    list = [str.format(i) for i in list]
    return(list)

def create_labels(meta_data):
    qr_filename = str(json.loads(meta_data)["atlas_serial"]) + ".png"
    qrcode = segno.make_qr(meta_data)

    qrcode.save("labels/"+qr_filename)

def print_labels():
    pass


def main():
    itkdb_client = authenticate_user_itkdb()
    #mongodb_client = authenticate_user_mongodb()
    meta_data = get_data(itkdb_client)
    #create_labels(meta_data)
    # print(meta_data)


if __name__ == '__main__':
  main()

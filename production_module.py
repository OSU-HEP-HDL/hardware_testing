from db_utils import authenticate_user_itkdb, authenticate_user_mongodb
import datetime
import segno
import json

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


def format_number(latest_serial,existing_serials):
    '''
    This ensures the last four digits of the serial number are in fact four digits when represented as a string
    '''
    existing_serial_list = []
    for serial in existing_serials:
        existing_serial_list.append(serial[10:14])

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
        while True:
            try:
                print("The latest serial number is:",latest_serial)
                print("The recommended serial number to enter is:", int(latest_serial)+1)
                while True:
                    print("Enter a number for the component (0 to 9999)")
                    number = input("\nInput Selection: ")
                    num = int(number)
                    try:
                        if '{:04d}'.format(num) in existing_serial_list:
                            raise ValueError
                        else:
                            break
                    except ValueError:
                        print("The number you entered already exists! Please enter a non-existing serial number.")

                if 0 <= num <= 9999:
                    formatted_num = '{:04d}'.format(num)
                    return formatted_num
                else:
                    raise ValueError
            except ValueError:
                print("Invalid input. Please provide a valid number.")
    
    if answer in yesl:
        while True:
            try:
                print("Enter how many components to register in a batch (2 to 9999)")
                number = input("\nTotal Amount: ")
                if 2<= int(number) <= 9999:
                    break
            except ValueError:
                print("Invalid input. Please provide a valid number.")
        num = int(number)
        while True:
            print("The latest serial number is:",latest_serial)
            print("Do you wish to start from the latest serial number position? (y or n)")
            ans = input("\nAnswer: ")
            try:
                if ans == "yes" or ans == "y":
                    start_num = latest_serial+1
                    break
                elif ans == "no" or ans == "n":
                    print("Starting from a different position, please enter starting position")
                    while True:    
                        start_number = input("\nStart Number: ")
                        start_num = int(start_number)
                        try:
                            for p in range(num):
                                if '{:04d}'.format(start_num+p) in existing_serial_list:
                                    raise ValueError
                            break
                        except ValueError:
                            print("The number you entered already exists! Please enter a non-existing serial number.")
                    break
                else:
                    raise ValueError
            except ValueError:
                print("Invalid input. Try yes (y) or no (n)")


        ''' Need to add a check for existing components'''
        comp_list = []
        for i in range(num):

            if 0 <= i <= 9999:
                formatted_num = '{:04d}'.format(start_num+i)
                comp_list.append(formatted_num)
            else:
                return "Number out of range. Please provide a number between 1 and 9999."
        return comp_list
    
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
    new_serial = format_number(latest_serial,existing_serials)
    
    if isinstance(new_serial,str):
        print("New serial: ",partial_serial + new_serial )
        return partial_serial + new_serial
    else:
        serial_list = prepend(new_serial,partial_serial)
        print("new serial numbers: ", serial_list)
        return serial_list
from modules.reception_module import get_type, get_latest_serial, get_code_and_function, get_flavor, get_N2, get_component_type, get_production_status
import datetime
import segno
import json


def format_number():
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

def prepend(list, str):
    # Using format()
    str += '{0}'
    list = [str.format(i) for i in list]
    return(list)

def get_latest_serial(xxyy, production_status, N2, flavor): 
    '''
    Checks data base for existing components with the same first 10 digits.
    Finds largest existing serial number and increments it by 1.
    Returns the new serial number.
    '''
    partial_serial = "20U" + str(xxyy) + str(production_status) + str(N2) + str(flavor)
    latest_serial = format_number()
    if isinstance(latest_serial,list):
        serial = prepend(latest_serial,partial_serial)
        return serial
    else:
        return partial_serial + latest_serial
    
def get_data():
    date = str(datetime.datetime.now())
    comp_selection = get_component_type()
    xxyy = get_code_and_function(comp_selection)
    production_status = get_production_status()
    N2 = get_N2()
    flavor = get_flavor()
    atlas_serial = get_latest_serial(xxyy, production_status, N2, flavor)
    #print("Final ATLAS Serial Number(s): ", atlas_serial)
    return atlas_serial


def create_labels(meta_data):
    qr_filename = str(json.loads(meta_data)["atlas_serial"]) + ".png"
    qrcode = segno.make_qr(meta_data)

    qrcode.save("labels/"+qr_filename)

def print_labels():
    pass


def main():
    meta_data = get_data()
    print("ATLAS SN: ",meta_data)
    #create_labels(meta_data)
    # print(meta_data)


if __name__ == '__main__':
  main()

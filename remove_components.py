from db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from reception_module import get_type, get_latest_serial, get_code_and_function, get_flavor, get_N2, get_component_type, get_production_status, prepend, get_existing_serials
import datetime
import json

def remove_component(comp_type, serialNumber):
   print("hi")

def enter_serial_numbers():
   print("Are you deleting a batch? (y or n)")
   answer = input("\nAnswer: ")
   while True:
        try:
            if answer == "n" or answer == "no":
                print("You are entering a single serial number. Please enter it. (20UXXYYN1N2N3nnnn)")
                in_serial = input("\nSerial Number: ")
                return in_serial
            elif answer == "y" or answer == "yes":
                print("Please enter the partial serial. (20UXXYYN1N2N3)")
                partial_serial = input("\nPartial serial number: ")
                print("How many are you deleting?")
                quantity = input("\nTotal amount to delete: ")
                print("Starting from which number to delete from? (1 to 9999)")
                start_num = input("\nStarting number: ")
                num_list = []
                for i in range(int(quantity)):
                    if 0 <= i <= 9999:
                        formatted_num = '{:04d}'.format(int(start_num)+i)
                        num_list.append(formatted_num)
                in_serials = prepend(num_list,partial_serial)
                return in_serials
            else:
                raise ValueError
        except ValueError:
            print("Please enter a valid answer. Yes (y) or no (n)")

def get_data(itkdb_client):
    register = False
    date = str(datetime.datetime.now())
    comp_selection = get_component_type()
    xxyy = get_code_and_function(comp_selection)
    production_status = get_production_status()
    N2 = get_N2()
    comp_type = get_type(xxyy,N2)
    flavor = get_flavor()
    atlas_serial = get_latest_serial(itkdb_client, xxyy, production_status, N2, flavor,register)

    return comp_type, atlas_serial

def get_serials_to_delete(client):
    print("Would you like to enter the Serial Number of the component(s) to delete? (y or n)")
    ans = input("\nYour answer: ")
    while True:
        try:
            if ans == "y" or ans == "yes":
                while True:
                    try:
                        serial_number = enter_serial_numbers()
                        if isinstance(serial_number,str):
                            xxyy = str(serial_number[3:7])
                            n2 = int(serial_number[8])
                            flavor = int(serial_number[9])
                            partial_serial = serial_number[0:10]
                        else: 
                            xxyy = str(serial_number[0][3:7])
                            n2 = int(serial_number[0][8])
                            flavor = int(serial_number[0][9])
                            partial_serial = serial_number[0][0:10]
                        
                        existing_serials = get_existing_serials(client,partial_serial,xxyy,n2,flavor)
                        
                        if isinstance(serial_number,str):
                            if serial_number not in existing_serials:
                                raise ValueError
                            else:
                                print("Found existing serial number!")
                                break
                        else:
                            for serial in serial_number:
                                if serial not in existing_serials:
                                    raise ValueError
                            print("Found all existing serial numbers!")
                            break
                    except ValueError:
                        print("Entered serial number(s) do not exist! Please enter valid serial number(s)")
                break
            elif ans =="n" or ans == "no":
                meta_data = get_data(client)
                comp_type = meta_data[0]
                serial_number = meta_data[1]
                if isinstance(serial_number,str):
                    xxyy = str(serial_number[3:7])
                    n2 = int(serial_number[8])
                else:
                    xxyy = str(serial_number[0][3:7])
                    n2 = int(serial_number[0][8])
                break
            else:
                raise ValueError
            
        except ValueError:
            print("Not a valid input. Please type yes (y) or no (n)")

    return serial_number, xxyy, n2
    
def main():
    itkdb_client = authenticate_user_itkdb()
    serial_number, xxyy, n2 = get_serials_to_delete(itkdb_client)
    comp_type = get_type(xxyy,n2)
    print(comp_type)
    #remove_component(comp_type,serial_number)



if __name__ == '__main__':
  main()
from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb, authenticate_user_proxmox
from modules.reception_module import get_type, get_latest_serial, get_code_and_function, get_flavor, get_N2, get_component_type, get_production_status, prepend, get_existing_serials, enter_serial_numbers, get_comp_info
from modules.mongo_db import check_directory_exists, remove_remote_directory
import datetime
import json
import paramiko

def remove_component(client, serialNumber):
   
    if isinstance(serialNumber,str):
        search_filter = {
           "component": serialNumber
        }
        component = client.get("getComponent", json=search_filter)
        while True:
            try:
                print("Retrieved existing component with serial number", component["serialNumber"], ", Are you sure you want to delete it? (y or n)")
                ans = input("\nAnswer: ")
                print("What is your reason for deleting it?")
                del_ans = input("\nReason: ")
                if ans == "yes" or ans == "y":
                    del_filter = {
                        "component": component['id'],
                        "reason": del_ans
                    }
                    client.post("deleteComponent",json=del_filter)
                    print("Component successfully deleted!")
                    break
                elif ans == "no" or ans == "n":
                    print("Component not deleted... exiting.")
                    break
                else:
                    raise ValueError
            except ValueError:
               print("Invalid input. Please try yes (y) or no (n).")
    else:
        print("Retrieving components...")
        search_filter = []
        for serial in serialNumber:
            search_filter.append({
                "component": serial
            })
        components = []
        for filt in search_filter:
            components.append(client.get("getComponent", json=filt))
        print("Successfully retrieved all enquired components!")
        while True:
            try:
                print("Are you sure you want to delete all enquired components? (y or n)")
                ans = input("\nAnswer: ")
                if ans == "yes" or ans == "y":
                    print("What is the reason for deletion?")
                    del_reason = input("\nReason: ")
                    delete_filter = []
                    for comp in components:
                        delete_filter.append({
                            "component": comp['id'],
                            "reason": del_reason
                        }) 
                    for filter in delete_filter:
                        client.post("deleteComponent",json=filter)
                    print("Successfully deleted all enquried components!")
                    break
                if ans == "no" or ans == "n":
                    print("components not deleted... exiting")
                    break
                else:
                    raise ValueError
            except ValueError:
                print("Invalid input. Please try yes (y) or no (n).")
    return
    
def remove_component_locally(client,serialNumber):
    db = client["local"]["itk_testing"]
    if isinstance(serialNumber,str):
        print("Deleting component locally...")
        try:
            if db.find_one({"_id": serialNumber})!= None:
                db.delete_one({"_id":serialNumber})
                print("Component deleted successfully!")
            else:
                raise ValueError
        except ValueError:
            print("Component with serial number",serialNumber,"not found locally!")

    else:
        print("Deleting component batch locally...")
        for serial in serialNumber:
            try:
                if db.find_one({"_id": serial})!= None:
                    db.delete_one({"_id":serial})
                else:
                    raise ValueError
            except ValueError:
                print("Component with serial number",serial,"not found locally!")
        print("Component batch deleted locally successfully!")

def get_data(itkdb_client):
    register = False
    date = str(datetime.datetime.now())
    comp_selection = get_component_type()
    xxyy = get_code_and_function(comp_selection)
    production_status = get_production_status()
    N2 = get_N2()
    comp_type = get_type(xxyy,N2)
    flavor = get_flavor()
    atlas_serial = get_latest_serial(itkdb_client, xxyy, production_status, N2, flavor,register,comp_type)

    return comp_type, atlas_serial

def get_serials_to_delete(client):
   
    while True:
        print("Would you like to manually enter the Serial Number of the component(s) to delete? (y or n)")
        ans = input("\nYour answer: ")
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
                while True:
                    try:
                        meta_data = get_data(client)
                        serial_number = meta_data[1]
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
            else:
                raise ValueError
            
        except ValueError:
            print("Not a valid input. Please type yes (y) or no (n)")

    return serial_number
    
def remove_component_proxmox(proxmox_auth, serialNumber,meta_data):

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    host = proxmox_auth["host"]
    port = proxmox_auth["port"]
    user = proxmox_auth["user"]
    password = proxmox_auth["password"]

    # Connect to the server
    ssh.connect(hostname=host, port=port, username=user, password=password)
    

    # Create an SFTP session
    sftp = ssh.open_sftp()

    if isinstance(serialNumber,str):
        comp_info = meta_data["type"]+"/"+meta_data["serialNumber"]
        remote_path = "/mnt/proxmox/images/itk_testing/"+comp_info
        print("Deleting component on proxmox...")
        exists = check_directory_exists(sftp, remote_path,serialNumber)
        if exists == True:
            remove_remote_directory(sftp,remote_path)
            print("Deleted on proxmox successfully...")
        elif exists == False:
            exit

    else:
        print("Deleting component batch on proxmox...")
        for serial, data in zip(serialNumber,meta_data):
            comp_info = data["type"]+"/"+serial
            remote_path = "/mnt/proxmox/images/itk_testing/"+comp_info
            success = False
            try:
                exists = check_directory_exists(sftp, remote_path, serial)
                if exists:
                    remove_remote_directory(sftp,remote_path)
                    success = True
            except ValueError:
                print("Component with serial number",serial,"not found on proxmox!")
        if success:
            print("Component batch deleted on proxmox successfully!")

    # Close the SFTP session and SSH connection
    sftp.close()
    ssh.close()

def get_meta_list(client,serial_number):

    if isinstance(serial_number,str):
        meta_data = get_comp_info(client,serial_number)
    else:
        meta_data=[]
        for serial in serial_number:
            meta_data.append(get_comp_info(client,serial))
    
    return meta_data

def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    proxmox_auth = authenticate_user_proxmox()
    serial_number = get_serials_to_delete(itkdb_client)
    meta_data = get_meta_list(itkdb_client,serial_number)
    remove_component(itkdb_client,serial_number)
    remove_component_locally(mongodb_client,serial_number)
    remove_component_proxmox(proxmox_auth,serial_number,meta_data)




if __name__ == '__main__':
  main()
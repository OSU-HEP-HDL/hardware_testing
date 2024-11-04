from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb,authenticate_user_proxmox
from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import get_type, get_latest_serial, get_code_and_function, get_flavor, get_N2, get_component_type, get_production_status,get_comp_info
from modules.mongo_db import insert_property_names,remove_remote_directory,check_directory_exists
import paramiko

def sync_local_db(itk_client,mongo_client,proxmox_auth):
    
    db = mongo_client["local"]["itk_testing"]

    # Create search filter for the database query
    search_filter = {
        "filterMap": {
            "institute": "OSU"
            }
        }
    itk_existing_components = itk_client.get("listComponents", json=search_filter)
    #if isinstance(itk_existing_components,list):
    #    print("Total components of type found is:",len(itk_existing_components))
    #else:
    #    print("Total components of found is:",itk_existing_components.total)

    itk_sn = []
    itk_dict = []
    for comp in itk_existing_components:
        if comp['state'] == 'deleted':
            continue
        itk_dict.append({comp['serialNumber'],comp['type']['code']})
        itk_sn.append(comp['serialNumber'])

    mongo_inv = db.find()
    mongo_sn = []
    mongo_dict = []
    for inv in mongo_inv:
        mongo_sn.append(inv['_id'])
        mongo_dict.append({'serialNumber': inv['serialNumber'],'type': inv['type']})

    # Convert lists to sets and find the symmetric difference
    unique_to_itk = set(itk_sn) - set(mongo_sn)

    # Find items unique to list2
    unique_to_mongo = set(mongo_sn) - set(itk_sn)
    #print("mongo dictionary: ", mongo_dict)
    #print("Unique SN to Mongo: ",unique_to_mongo)
 
    # Filter out entries not matching any SN in unique_sn_to_mongo
    filtered_mongo_inv = [item for item in mongo_dict if item['serialNumber'] in unique_to_mongo]

    #print(filtered_mongo_inv)
    #print("Items unique to ITk:", list(unique_to_itk))
    #print("Items unique to MongoDB:", list(unique_to_mongo))
    
    unique_to_mongo = list(unique_to_mongo)
    try:
        print("Deleting locally unique components...")
        if len(unique_to_mongo) is int(0):
            raise ValueError
        for item in unique_to_mongo:
            if db.find_one({"_id": item})!= None:
                db.delete_one({"_id":item})
        print("Local components deleted successfully.")
        print("Removing corresponding components on the proxmox server...")
        remove_component_proxmox(proxmox_auth,filtered_mongo_inv)
    except ValueError:
        print("Local database already synced!")

    

def remove_component_proxmox(proxmox_auth, comp_dict):

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
    
    for item in comp_dict:
        comp_info = item["type"]+"/"+item['serialNumber']
        remote_path = "/mnt/proxmox/images/itk_testing/"+comp_info
        success = False
        try:
            exists = check_directory_exists(sftp, remote_path, item['serialNumber'])
            if exists:
                remove_remote_directory(sftp,remote_path)
                success = True
        except ValueError:
                print("Component with serial number",item['serialNumer'],"not found on proxmox!")
        if success:
            print("Component batch deleted on proxmox successfully!")
    
    '''
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
    '''
    # Close the SFTP session and SSH connection
    sftp.close()
    ssh.close()

def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    proxmox = authenticate_user_proxmox()

    sync_local_db(itkdb_client,mongodb_client,proxmox)

if __name__ == '__main__':
  main()
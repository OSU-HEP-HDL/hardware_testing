import paramiko
import os
import stat
import subprocess
from pathlib import Path

def insert_property_names(component):

    register = False
    try:
        comp_purpose = component["properties"][0]["value"]
    except KeyError as e:
        register = True
        comp_purpose = component["properties"]["PURPOSE"]

    if int(comp_purpose) == 0:
        purpose = "prototype"
    elif int(comp_purpose) == 1:
        purpose = "pre-production"
    elif int(comp_purpose) == 2:
        purpose = "production"
    elif int(comp_purpose) == 9:
        purpose = "dummy"
    
    if register:
        comp_type_combination = component["properties"]["TYPE_COMBINATION"]
    else:
        comp_type_combination = component["properties"][1]["value"]
    
    if int(comp_type_combination) == 0:
        type_combination = "barrel-triplet"
    elif int(comp_type_combination) == 1:
        type_combination = "barrel-quad"
    elif int(comp_type_combination) == 2:
        type_combination = "ring-triplet"
    elif int(comp_type_combination) == 3:
        type_combination = "ring-quad"
    elif int(comp_type_combination) == 4:
        type_combination = "ring-both"
    elif int(comp_type_combination) == 5:
        type_combination = "mixed"

    if register:
        flavor = component["properties"]["FLAVOR"]
    else:
        flavor = component["properties"][2]["value"]
    
    if register:
        comp_vendor = component["properties"]["VENDOR"]
    else:
        comp_vendor = component["properties"][3]["value"]
    
    if int(comp_vendor) == 0:
        vendor = "Altaflex"
    elif int(comp_vendor) == 1:
        vendor = "PFC"
    elif int(comp_vendor) == 2:
        vendor = "Cirexx"
    elif int(comp_vendor) == 3:
        vendor = "EPEC"
    elif int(comp_vendor) == 4:
        vendor = "Vector"
    elif int(comp_vendor) == 5:
        vendor = "Summit"
    
    if register:
       alternative_id = component["properties"]["ALTERNATIVE_IDENTIFIER"]
    else:
        alternative_id = component["properties"][4]["value"]
    
    return purpose, type_combination, flavor, vendor, alternative_id

def upload_results_locally(client,results,serial_number,test_type):
   print("\nUploading test results locally...")
   db = client["local"]["itk_testing"]
   try:
       if db.find_one({"_id": serial_number}) is None:
           raise ValueError
       elif 'tests' not in db.find_one({"_id": serial_number}):
           result = {"$set":{
               "tests":{
                 test_type: results
               }
             }
           }
           db.update_one({"_id": serial_number},result)
           print("Uploaded results locally!")
       else:
           key = "tests." + test_type
           result = {"$set":{
               key:results
               
             }
           }
           db.update_one({"_id": serial_number},result)
           print("Updated test results locally!")
 
   except ValueError:
      print("Component with serial number",serial_number,"doesn't exist locally!")

def create_remote_directory(sftp, remote_directory):
    """Create a remote directory if it does not exist."""
    try:
        sftp.chdir(remote_directory)  # Try to change to the remote directory
    except IOError:
        sftp.mkdir(remote_directory)   # Create the directory if it does not exist
        sftp.chdir(remote_directory)    # Change into the newly created directory

def remove_remote_directory(sftp, remote_directory):
    """Recursively remove a remote directory and its contents."""
    for file_attr in sftp.listdir_attr(remote_directory):
        remote_file_path = f"{remote_directory}/{file_attr.filename}"
        if stat.S_ISDIR(file_attr.st_mode):  # If it's a directory
            remove_remote_directory(sftp, remote_file_path)  # Recursively remove subdirectories
        else:
            sftp.remove(remote_file_path)  # Remove files
    sftp.rmdir(remote_directory)  # Finally, remove the empty directory

def check_directory_exists(sftp, remote_directory,serialNumber):
    """Check if a remote directory exists."""
    try:
        sftp.stat(remote_directory)  # Try to retrieve directory attributes
        return True
    except FileNotFoundError:
        print("Component with serial number",serialNumber,"not found on proxmox!")
        return False

def scp_transfer(proxmox_auth, args, meta_data,test_type):
    host = proxmox_auth["host"]
    port = proxmox_auth["port"]
    user = proxmox_auth["user"]
    password = proxmox_auth["password"]

    comp_info = meta_data["type"]+"/"+meta_data["serialNumber"]
    remote_path = "/mnt/proxmox/images/itk_testing/"+comp_info
    nested_remote_path = remote_path + "/" + test_type

    for arg_key, value in args.items():
       key = arg_key

    try:
        # Initialize the SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the host
        ssh.connect(hostname=host, port=port, username=user, password=password)
        
        files = []
        if "/" in args[key][0]:
            for image in args[key]:
                g = image.split("/")
                files.append(g[-1])
        
        # Open an SCP session
        with ssh.open_sftp() as sftp:
            #Create directory for component
            create_remote_directory(sftp,remote_path)
            create_remote_directory(sftp,nested_remote_path)
            for image,file in zip(args[key],files):
            # Upload the local file to the remote server
                
                remote_file_path = nested_remote_path + "/" + file
                print(f"Uploading {image} to {user}:{host}:{remote_file_path}")
                sftp.put(image, remote_file_path)

        
        print("Uploaded images.")

        # Close the connection
        ssh.close()
        total_remote_path = str(user)+"@"+str(host)+":"+nested_remote_path
    
    except Exception as e:
        print(f"An error occurred: {e}")
       
    
    return total_remote_path



def curl_image_post(args,meta_data,test_type, url="https://loopback.app.hep.okstate.edu:443/uploads", verbose=True):
    
    """
    Uploads an image to the given URL using curl.
    
    Args:
        image_path (str or Path): Path to the image file.
        url (str): The endpoint to POST the image to.
        verbose (bool): If True, print curl's output.
    
    Returns:
        int: The return code from curl (0 = success).
    """
    query_string = "?subdir="
    comp_info = meta_data["type"]+"/"+meta_data["serialNumber"]
    remote_path = "/itk_testing/"+comp_info
    nested_remote_path = remote_path + "/" + test_type

    url = url + query_string + nested_remote_path
    
    for key, value in args.items():
        files = value if isinstance(value, list) else [value]

        for file_path in files:
            file_path = Path(file_path)

            # 🧠 Check if it's a directory
            if file_path.is_dir():
                # If it's a folder, loop through all files inside
                for inner_file in file_path.glob('*'):
                    if inner_file.is_file():  # Only upload actual files
                        print("\nUploading file to server:", inner_file)
                        curl_command = [
                            "curl", "-X", "POST", "-k",
                            url,
                            "-F", f"file=@{inner_file}"
                        ]
                        result = subprocess.run(curl_command, capture_output=not verbose, text=True)
            else:
                # It's a single file
                print("Uploading file to server:", file_path)
                curl_command = [
                    "curl", "-X", "POST", "-k",
                    url,
                    "-F", f"file=@{file_path}"
                ]
                result = subprocess.run(curl_command, capture_output=not verbose, text=True)
    
    if not verbose:
        print(result.stdout)
        if result.stderr:
            print("stderr:", result.stderr)
    
    return nested_remote_path

def curl_image_delete(meta_data, url="https://loopback.app.hep.okstate.edu:443/upload", verbose=True):
 
    comp_info = meta_data["type"]+"/"+meta_data["serialNumber"]
    remote_path = "itk_testing/"+comp_info

    query = "?path="
    url = url + query + remote_path

    print("deleting component at ",url)
    
    curl_command = [
        "curl",
        "-X", "DELETE", "-k",
        url
    ]
    
    result = subprocess.run(curl_command, capture_output=not verbose, text=True)
    
    if not verbose:
        print(result.stdout)
        if result.stderr:
            print("stderr:", result.stderr)
    #nested_remote_path = nested_remote_path.replace("%2F","/")
    #return nested_remote_path

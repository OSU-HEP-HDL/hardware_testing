import logging
import paramiko
from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import get_comp_info
from modules.mongo_db import insert_property_names, remove_remote_directory, check_directory_exists
from pathlib import Path

# Set up logging directory and file
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "sync.log"

# Configure logger
logger = logging.getLogger("pixal.sync")
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

# Avoid duplicate handlers if rerun
if not logger.handlers:
    logger.addHandler(file_handler)

def sync_local_db(itk_client, mongo_client):
    db = mongo_client["local"]["itk_testing"]

    search_filter = {
        "filterMap": {
            "institute": "OSU"
        }
    }

    itk_existing_components = itk_client.get("listComponents", json=search_filter)
    
    itk_sn = []
    for comp in itk_existing_components:
        if comp['state'] == 'deleted':
            continue
        if comp['serialNumber'] is None:
            continue
        itk_sn.append(comp['serialNumber'])

    mongo_inv = db.find()
    mongo_sn = [inv['_id'] for inv in mongo_inv]

    logger.info(f"Total number of components on the production database: {len(itk_sn)}")
    logger.info(f"Total number of components on the local database: {len(mongo_sn)}")

    unique_to_itk = set(itk_sn) - set(mongo_sn)
    unique_to_mongo = set(mongo_sn) - set(itk_sn)
    print(unique_to_itk)
    #logger.info(f"Total unique components to the production database: {unique_to_itk}")
    #logger.info(f"Total unique components to the local database: {unique_to_mongo}")

    if unique_to_itk:
        print("The production database and the local database are not synced.")
        answer = input("Would you like to sync the local database with the production database? (y/n): ")
        if answer.lower() != 'y':
            logger.info("Exiting...")
            return
        logger.info("Syncing local database with production database...")

    try:
        logger.info("Deleting locally unique components...")
        for item in unique_to_mongo:
            if db.find_one({"_id": item}) is not None:
                db.delete_one({"_id": item})

        updated_mongo_sn = [inv['_id'] for inv in db.find()]
        logger.info(f"New total number of components on the local database: {len(updated_mongo_sn)}")
        logger.info(f"Total components deleted: {len(mongo_sn) - len(updated_mongo_sn)}")
        logger.info("Local components deleted successfully.")
    except ValueError:
        logger.info("Local database already synced.")

    logger.info("Creating components unique to production database on local database...")
    for item in unique_to_itk:
        if db.find_one({"_id": item}) is not None:
            logger.info(f"Component with serial number {item} already exists locally.")
            continue
        if item is None:
            continue
        
        comp_info = get_comp_info(itk_client, item)
        #print(comp_info)
        project = comp_info['serialNumber'][3]
        subproject = comp_info['serialNumber'][3:5]

        comp_filter = {
            "project": project,
            "code": "IS_TYPE0"
        }

        component_template = itk_client.get('generateComponentTypeDtoSample', json=comp_filter)

        purpose, type_combination, flavor, vendor, alternative_id = insert_property_names(comp_info)

        updated_component = {
            **component_template,
            "subproject": subproject,
            "institution": "OSU",
            "type": comp_info["componentType"],
            "serialNumber": comp_info["serialNumber"],
            "stage": comp_info['currentStage'],
            "properties": {
                **component_template['properties'],
                "PURPOSE": purpose,
                "TYPE_COMBINATION": type_combination,
                "FLAVOR": flavor,
                "VENDOR": vendor,
                "ALTERNATIVE_IDENTIFIER": alternative_id
            },
            "_id": comp_info["serialNumber"]
        }

        logger.info(f"Updated component: {updated_component}")
        db.insert_one(updated_component)

    logger.info("Components created locally successfully." if unique_to_itk else "No components to create locally.")


def remove_component_proxmox(proxmox_auth, comp_dict):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=proxmox_auth["host"],
        port=proxmox_auth["port"],
        username=proxmox_auth["user"],
        password=proxmox_auth["password"]
    )

    sftp = ssh.open_sftp()

    for item in comp_dict:
        comp_info = f"{item['type']}/{item['serialNumber']}"
        remote_path = f"/mnt/proxmox/images/itk_testing/{comp_info}"
        success = False
        try:
            if check_directory_exists(sftp, remote_path, item['serialNumber']):
                remove_remote_directory(sftp, remote_path)
                success = True
        except ValueError:
            logger.warning(f"Component with serial number {item['serialNumber']} not found on proxmox.")

        if success:
            logger.info(f"Component {comp_info} deleted on proxmox successfully.")

    sftp.close()
    ssh.close()


def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    sync_local_db(itkdb_client, mongodb_client)


if __name__ == '__main__':
    main()

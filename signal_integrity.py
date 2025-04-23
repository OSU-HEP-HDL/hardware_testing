from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb, authenticate_user_proxmox
from modules.reception_module import enter_serial_numbers, get_comp_info, get_template,enquiry,update_test_type,upload_attachments,check_file_size
from modules.mongo_db import upload_results_locally, curl_image_post
import itkdb
import shutil
import argparse
import csv
import datetime
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("result pdf",help="PDF of signal integrity results.")
args = vars(parser.parse_args())


def upload_signal_integrity_test(client,template,meta_data):

    component = client.get("getComponent", json={"component": meta_data["serialNumber"]})  
    
    print("Did the test pass? (y or n)")
    inp = input("\nAnswer:")
    if inp.lower() in ["y", "yes"]:
       passed = True
       problems = False
    elif inp.lower() in ["n", "no"]:
       passed = False
       problems = True
    
    runNumber = 0
    if len(component["tests"]) == 0:
      print("WARNING: No Visual Inspection test with this component")
      runNumber = str(len(component["tests"]) + 1)
    else:
      for x in component["tests"]:
          if x['code'] == "SIGNAL_INTEGRITY":
            runNumber = len(x["testRuns"])
      runNumber = str(runNumber + 1)

    test_results ={
     **template,
     'component': meta_data['serialNumber'],
     'institution': meta_data['institution'],
     'runNumber': runNumber,
     'passed': passed,
     'problems': problems,
     'properties':{'OPERATOR': meta_data['user']['userIdentity']}
      }
    
    print("You are about to upload test results for the signal integrity test, are you sure? (y or n)")
    inp = input("\n")
    if inp == "y" or inp == "yes":
      client.post("uploadTestRunResults",json = test_results)
      print("Signal Integrity test successfully uploaded!")
    else:
      print("Results not posted!")

    return test_results


def main():
    eos = True
    itkdb_client = authenticate_user_itkdb(eos)
    mongodb_client = authenticate_user_mongodb()

    if not enquiry(args["results"]):
      print("No folder argument included! Exiting...")
      exit()
    attachment = args['pdf']
    single = True
    test_type = "SIGNAL_INTEGRITY"
    serial_number = enter_serial_numbers(single)
    meta_data = get_comp_info(itkdb_client,serial_number)
    template = get_template(itkdb_client,meta_data,test_type)
    update_test_type(itkdb_client,mongodb_client,meta_data,test_type)

    test_results = upload_signal_integrity_test(itkdb_client,template,meta_data)
    upload_attachments(itkdb_client,attachment,meta_data,test_type)

    local_path = curl_image_post(args,meta_data,test_type)
    test_results["File_Location"] = local_path
    upload_results_locally(mongodb_client,test_results,serial_number,test_type)


if __name__ == '__main__':
  main()
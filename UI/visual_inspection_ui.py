from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb, authenticate_user_proxmox
from modules.reception_module import enter_serial_numbers,get_comp_info,get_template,enquiry, upload_attachments, update_test_type,check_file_size
from modules.mongo_db import upload_results_locally,scp_transfer
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("images",nargs="*",help="Add visual inspection photos to upload to the production database")
args = vars(parser.parse_args())

def upload_reception_results(client,meta_data,template):
  ''' Check to see if reception has occured before'''
  component = client.get("getComponent", json={"component": meta_data["serialNumber"]})  

  if len(component["tests"]) == 0:
      runNumber = str(len(component["tests"]) + 1)
  else:
      for x in component["tests"]:
         if x['code'] == "VISUAL_INSPECTION":
            runNumber = len(x["testRuns"])
      runNumber = str(runNumber + 1)

  while True:
     try:
        print("Has the",meta_data["type"],"passed the Visual Inspection test? (y or n)")
        ans = input("\nAnswer: ")
        if ans == "yes" or ans == "y":
           passed = True
           problems = False
           defect = "None"

        elif ans == "no" or ans == "n":
           passed = False
           problems = True

           defect_list = ["Bad Solder","Torn"]
           choices = ["list","manual"]
           print("Would you like to choose the reason from a list or enter it manually?")
           for k, v in enumerate(choices):
              print(f"For {v}, press {k}")
           while True:
              try:  
                selection = input("\nChoice: ")
                if choices[int(selection)] in choices:
                  if int(selection) == 0:
                    while True:
                       try:
                          print("Choose reason from the list.")
                          for k, v in enumerate(defect_list):
                            print(f"For {v}, press {k}")
                          defect_num = input("\nReason: ")
                          defect = defect_list[int(defect_num)]
                          break
                       except IndexError:
                          print("Invalid input. Please choose from the list.")

                  elif int(selection) == 1:
                     print("Manually enter the defect")
                     defect = input("\n")
                else:
                  raise ValueError
                break
              except ValueError:
                 print("Invalid input. Please select from the given choices.")
                  
        break
     except ValueError:
        print("Invalid input. Yes (y) or No (n)")
    
  test_results ={
     **template,
     'component': meta_data['serialNumber'],
     'institution': meta_data['institution'],
     'runNumber': runNumber,
     'passed': passed,
     'problems': problems,
     'properties':{'OPERATOR': meta_data['user']['userIdentity']},
                   'results':{'DEFECT_TYPE': defect}
                   
  }

  print("You are about to upload test results for the Visual Inspection test, are you sure? (y or n)")
  inp = input("\n")
  if inp == "y" or inp == "yes":
     upload = True
     client.post("uploadTestRunResults",json = test_results)
     print("New test run successfully uploaded!")
  else:
     upload = False
     print("Results not posted!")
   
  return test_results, upload
    
def main():
    eos = check_file_size(args)
    itkdb_client = authenticate_user_itkdb(eos)
    mongodb_client = authenticate_user_mongodb()
    proxmox_auth = authenticate_user_proxmox()
    single = True
    test_type = "VISUAL_INSPECTION"
    serial_number = enter_serial_numbers(single)
    meta_data = get_comp_info(itkdb_client,serial_number)
    template = get_template(itkdb_client,meta_data,test_type)

    results, upload = upload_reception_results(itkdb_client,meta_data,template)
    
    if enquiry(args["images"]) and upload == True:
      print("Image arguements included. Starting attachment upload.")
      upload_attachments(itkdb_client,args,meta_data,test_type)
      image_path = scp_transfer(proxmox_auth,args,meta_data,test_type)
    if upload == True:
      results["File_Location"] = image_path
      upload_results_locally(mongodb_client,results,serial_number,test_type)
    else:
       print("Not uploading results locally")


if __name__ == '__main__':
  main()
from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import enter_serial_numbers,get_comp_info,get_template,enquiry
import itkdb
import shutil
import argparse
import os
import sys
import re


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
     client.post("uploadTestRunResults",json = test_results)
     print("New test run successfully uploaded!")
  else:
     print("Results not posted!")
   
  return test_results
    

def upload_attachments(client,images,meta_data):
   component = client.get("getComponent", json={"component": meta_data["serialNumber"]})  

   for x in component["tests"]:
      if x['code'] == "VISUAL_INSPECTION":
         numInsp = len(x["testRuns"])
         testRun = x["testRuns"]

   # This is in case any argument is a in a different directory
   altered_image_list =[]

   if "/" in images["images"][0]:
      for image in images["images"]:
         g = image.split("/")
         glen = len(g)
         img_name = g[glen-1]
         shutil.copy2(image, img_name)
         altered_image_list.append(img_name)
   
   image_list = []

   if "/" in images["images"][0]:
      for image in altered_image_list:
         shutil.copy(image,itkdb.data)
         image_list.append(itkdb.data / image)
         os.remove(image)

   else:
      for image in images["images"]:
         shutil.copy(image,itkdb.data)
         image_list.append(itkdb.data / image)

   data_list = []
   for img in image_list:
      data_list.append({
         "testRun": testRun[numInsp-1]["id"],
         "title": "Visual Inpection photos",
         "description": "Photos of the visual inspection test",
         "type": "file",
         "url": img
      })

   attachment_list = []
   for img in image_list:
      attachment_list.append({"data": (img.name, img.open("rb"), "image/jpg")})

   print("You are about to upload",len(image_list), "images to the visual inspection test with run number",numInsp,", do you want to continue? (y or n)")
   ans = input("Answer: ")
   if str(ans) == "y" or str(ans) == "yes":
      for data, attachment in zip(data_list, attachment_list):
         client.post("createTestRunAttachment",data=data,files=attachment)
      print("Attachment(s) successfully uploaded!")
   else:
      print("Not uploading photos")

def upload_results_locally(client,results,serial_number):
   print("Uploading Visual Inspection results locally...")
   db = client["local"]["itk_testing"]
   try:
      if db.find_one({"_id": serial_number}) is None:
         raise ValueError
      else:
         result = {"$set":{
                     "tests":{
                        "VISUAL_INSPECTION": results
               }
            }
         }
         db.update_one({"_id": serial_number},result)
         print("Uploaded results locally!")
   except ValueError:
      print("Component with serial number",serial_number,"doesn't exist locally!")
      
   
def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    single = True
    test_type = "VISUAL_INSPECTION"
    serial_number = enter_serial_numbers(single)
    meta_data = get_comp_info(itkdb_client,serial_number,args)
    template = get_template(itkdb_client,meta_data,test_type)
    results = upload_reception_results(itkdb_client,meta_data,template)

    if enquiry(args["images"]):
      print("Image arguements included. Starting attachment upload.")
      upload_attachments(itkdb_client,args,meta_data)
    upload_results_locally(mongodb_client,results,serial_number)


if __name__ == '__main__':
  main()
from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import get_comp_info, enter_serial_numbers
from modules.mongo_db import insert_property_names
import itkdb
import shutil
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input",nargs="*",help="attachments to add to test")
args = vars(parser.parse_args())

def upload_additional_attachments(client,attch,meta_data,test_type):
   component = client.get("getComponent", json={"component": meta_data["serialNumber"]})  

   for x in component["tests"]:
      if x['code'] == test_type:
         numInsp = len(x["testRuns"])
         testRun = x["testRuns"]

   # This is in case any argument is a in a different directory
   altered_attch_list =[]
   for arg_key, value in attch.items():
       key = arg_key
   if "/" in attch[key][0]:
      for image in attch[key]:
         g = image.split("/")
         glen = len(g)
         img_name = g[glen-1]
         shutil.copy2(image, img_name)
         altered_attch_list.append(img_name)
   
   attch_list = []

   if "/" in attch[key][0]:
      for atch in altered_attch_list:
         shutil.copy(atch,itkdb.data)
         attch_list.append(itkdb.data / atch)
         os.remove(atch)

   else:
      for atch in attch[key]:
         shutil.copy(atch,itkdb.data)
         attch_list.append(itkdb.data / atch)

   data_list = []
   for atch, title in zip(attch_list,altered_attch_list):
      data_list.append({
         "testRun": testRun[numInsp-1]["id"],
         "title": title,
         "description": "Attachment for"+test_type,
         "type": "file",
         "url": atch
      })

   attachment_list = []
   for atch in attch_list:
      attachment_list.append({"data": (atch.name, atch.open("rb"), "image/csv")})

   print("You are about to upload",len(attachment_list), "attachments to " +test_type+" test with run number",numInsp,", do you want to continue? (y or n)")
   ans = input("Answer: ")
   if str(ans) == "y" or str(ans) == "yes":
      for data, attachment in zip(data_list, attachment_list):
         client.post("createTestRunAttachment",data=data,files=attachment)
      print("Attachment(s) successfully uploaded!")
   else:
      print("Not uploading photos")

def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    single = True
    serial_number = enter_serial_numbers(single)
    meta_data = get_comp_info(itkdb_client,serial_number)

    test_options = ["VISUAL_INSPECTION","CONNECTIVITY","SIGNAL_INTEGRITY"]
    print("\nChoose which stage for attachments:")
    for k, v in enumerate(test_options):
        print(f"For {v}, press {k}")
    while True:
        try:
            selection = input("\nInput Selection: ")
            option = test_options[int(selection)]
            break
        except (ValueError, IndexError):
            print("Invalid Input. Try again.")
    print(f"Selected {option}\n")
    upload_additional_attachments(itkdb_client,args,meta_data,option)
if __name__ == '__main__':
  main()

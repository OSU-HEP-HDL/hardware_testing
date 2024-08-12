from modules.db_utils import authenticate_user_itkdb
from modules.reception_module import enter_serial_numbers,get_comp_info
import datetime
import json


def get_reception_template(client,meta_data):
   ind=0
   for test in meta_data["testTypes"]:
      if str(test) == "VISUAL_INSPECTION":
         break
      ind += 1
   rec_filter = {
      'project': meta_data['project'],
      'componentType': meta_data['componentType'],
      'code': meta_data['testTypes'][ind]
   }
   test_template = client.get("generateTestTypeDtoSample",json=rec_filter)
   
   return test_template

def upload_reception_results(client,meta_data,template):
  ''' Check to see if reception has occured before'''
  component = client.get("getComponent", json={"component": meta_data["serialNumber"]})  

  if len(component["tests"]) == 0:
      runNumber = str(len(component["tests"]) + 1)
  else:
      for x in component["tests"]:
         print(x['testRuns'])
         if x['code'] == "VISUAL_INSPECTION":
            runNumber = len(x["testRuns"])
      runNumber = str(runNumber + 1)
      print(runNumber)

  while True:
     try:
        print("Has the",meta_data["type"],"passed the Visual Inspection test?")
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
    
  #print(template)
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
  print(test_results)
  print("You are about to upload test results for the Visual Inspection test, are you sure? (y or n)")
  inp = input("\n")
  if inp == "y" or inp == "yes":
     client.post("uploadTestRunResults",json = test_results)
  else:
     print("Results not posted. Exiting")
    

def main():
    itkdb_client = authenticate_user_itkdb()
    #mongodb_client = authenticate_user_mongodb()
    single = True
    serial_number = enter_serial_numbers(single)
    meta_data = get_comp_info(itkdb_client,serial_number)
    template = get_reception_template(itkdb_client,meta_data)
    upload_reception_results(itkdb_client,meta_data,template)
    #Upload photos / attachments

if __name__ == '__main__':
  main()
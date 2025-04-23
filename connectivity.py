from modules.db_auth import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import enter_serial_numbers, get_comp_info, get_template, update_test_type, upload_attachments
from modules.mongo_db import upload_results_locally, curl_image_post
from modules.utilities import enquiry, csv_to_pdf
import shutil
import argparse
import csv
import datetime

parser = argparse.ArgumentParser()
parser.add_argument("file",nargs="*",help="CIRRIS result file. PDF or CSV")
args = vars(parser.parse_args())

def get_csv_results(args):
  result = "not in file"
  wire_resistance = "not in file"
  short_test_resistance = "not in file"
  operator = "not in file"
  cable_number = "not in file"
  error_results = []
  measure_results = []

  error_table = False
  measure_table =False
  
  with open(args['file'][0]) as csv_file:
    reader = csv.reader(csv_file)
    for row in reader:
      if not row: 
        continue

      '''Obtain single line results from csv'''  
      if "Final Test Result:" in str(row):
        result = row[1]
      if "Wire Resistance" in str(row):
        wire_resistance = row[1]
      if "Shorts Test Resistance" in str(row):
        short_test_resistance = row[1]
      if "Operator" in str(row):
        operator = row[1]
      if "Cable Number" in str(row):
        cable_number = row[1]

      '''Obtain tables of information from csv'''
      if "Measured Values" in str(row):
        error_table = False
        measure_table = True

      if error_table == True:
        row_len = len(row)
        error_results.append(row[row_len-1])

      if "Error Details" in str(row):
        error_table = True

      if measure_table == True:
        if "Measured Values" in str(row):
          continue
        if "Not tested" in str(row):
          measure_results.append("Not Tested")
          continue
        measure_results.append(row)
        
  if "Failed" in str(result):
    passed = False
    hv_passed = False
    lv_passed = False
  else:
    passed = True
    hv_passed = True
    lv_passed = None

  results = {
    "PASSED": passed,
    "HV_PASS": hv_passed,
    "LV_PASS": lv_passed,
    "wire_resistance": wire_resistance,
    "short_test_resistance": short_test_resistance,
    "operator": operator,
    "cable_number": cable_number,
    "error_results": error_results,
    "measure_results": measure_results
  }
  return results

def upload_connectivity_test(client,template,meta_data,results):
    
    component = client.get("getComponent", json={"component": meta_data["serialNumber"]})  

    runNumber = 0
    if len(component["tests"]) == 0:
      print("WARNING: No Visual Inspection test with this component")
      runNumber = str(len(component["tests"]) + 1)
    else:
      for x in component["tests"]:
          if x['code'] == "CONNECTIVITY_TEST":
            runNumber = len(x["testRuns"])
      runNumber = str(runNumber + 1)
    
    if results["PASSED"] == True:
      problems = False
    else:
      problems = True

    test_results ={
     **template,
     'component': meta_data['serialNumber'],
     'institution': meta_data['institution'],
     'runNumber': runNumber,
     'passed': results['PASSED'],
     'problems': problems,
     'properties':{'OPERATOR': meta_data['user']['userIdentity'],
                   'results':{'PASSED': results['PASSED'], 'HV_PASS': results['HV_PASS'], 'LV_PASS': results['LV_PASS']},}
      }
                  
    print("You are about to upload test results for the HV Connectivity test, are you sure? (y or n)")
    inp = input("\nanswer:")
    if inp == "y" or inp == "yes":
      client.post("uploadTestRunResults",json = test_results)
      print("Connectivity test successfully uploaded!")
    else:
      print("Results not posted!")
    return test_results

def main():
    eos = True
    single = True
    test_type = "CONNECTIVITY"
    itkdb_client = authenticate_user_itkdb(eos)
    mongodb_client = authenticate_user_mongodb()
    is_csv = False

    if not enquiry(args["file"]):
      print("No file included! Exiting...")
      exit()

    results = {}

    if args["file"][0].endswith(".csv"):
      print("CSV file detected")
      is_csv = True
      results = get_csv_results(args)

    if args["file"][0].endswith(".pdf"):
      print("Did the test pass? (y or n)")
      ans = input("\nanswer: ")
      if ans.lower() == "y" or ans.lower() == "yes":
        passed = True
      else:
        passed = False
      results["PASSED"] = passed
      if passed == True:
        
        print("Did it run the HV test? (y or n)")
        ans = input("\nanswer: ")
        if ans.lower() == "y" or ans.lower() == "yes":
          print("Did it pass the HV test? (y or n)")
          ans = input("\nanswer: ")
          if ans.lower() == "y" or ans.lower() == "yes":
            hv_passed = True
          else:
            hv_passed = False
        else:
          hv_passed = None
        
        print("Did it run a LV test? (y or n)")
        ans = input("\nanswer: ")
        if ans.lower() == "y" or ans.lower() == "yes":
          print("Did it pass the LV test? (y or n)")
          ans = input("\nanswer: ")
          if ans.lower() == "y" or ans.lower() == "yes":
            lv_passed = True
          else:
            lv_passed = False
        else:
          lv_passed = None
        
      else:
        hv_passed = None
        lv_passed = None
      results["LV_PASS"] = lv_passed
      results["HV_PASS"] = hv_passed

    serial_number = enter_serial_numbers(single)
    meta_data = get_comp_info(itkdb_client,serial_number)
    template = get_template(itkdb_client,meta_data,test_type)

    update_test_type(itkdb_client,mongodb_client,meta_data,test_type)

    if is_csv == True:
      print("Input is CSV. Converting to PDF...")
      csv_to_pdf(args["file"][0])
      print("PDF created!")
      attachments_path = args["file"][0].replace(".csv",".pdf")
    else:
      attachments_path = args["file"][0]
    
    # Database upload
    test_results = upload_connectivity_test(itkdb_client,template,meta_data,results)
    upload_attachments(itkdb_client, attachments_path, meta_data, test_type)
    
    # Local upload
    upload_results_locally(mongodb_client,test_results,serial_number,test_type)
    attachment = {"file": attachments_path}
    curl_image_post(attachment,meta_data,test_type)
    

if __name__ == '__main__':
  main()
from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import enter_serial_numbers, get_comp_info, get_template,enquiry,update_test_type
from modules.mongo_db import upload_results_locally
import itkdb
import shutil
import argparse
import csv
import datetime

parser = argparse.ArgumentParser()
parser.add_argument("csv",nargs="*",help="CIRRIS result CSV")
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
  
  with open(args['csv'][0]) as csv_file:
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
        

  results = {
    "result": result,
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
    
    '''Clean up the empty spaces'''
    error_results = []
    for res in results["error_results"]:
      if str(res) == ' ':
        continue
      error_results.append((res))
      #print(res)
    measure_results = []
    for res in results["measure_results"]:
      if str(res) == ' ':
        continue
      measure_results.append(str(res))

    if str(results["result"]).strip() == "Failed":
      result = False
      problems = True
    else:
      result = True
      problems = False

    print(error_results)
    test_results ={
     **template,
     'component': meta_data['serialNumber'],
     'institution': meta_data['institution'],
     'runNumber': runNumber,
     'passed': result,
     'problems': problems,
     'properties':{'OPERATOR': meta_data['user']['userIdentity'],
                   'CABLE_NUMBER': int(results['cable_number']),
                   'WIRE_RESISTANCE': results['wire_resistance'],
                   'SHORT_TEST_RESISTANCE': results['short_test_resistance']},
                   'results': { 'PASSED': result,
                                'ERROR_DETAILS': error_results,
                                'MEASURED_VALUES': measure_results
                              }
      }
                  
    print("You are about to upload test results for the HV Connectivity test, are you sure? (y or n)")
    inp = input("\n")
    if inp == "y" or inp == "yes":
      client.post("uploadTestRunResults",json = test_results)
      print("Connectivity test successfully uploaded!")
    else:
      print("Results not posted!")
    return test_results

def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    if not enquiry(args["csv"]):
      print("No CSV included! Exiting...")
      exit()
    result_list = get_csv_results(args)
    single = True
    test_type = "CONNECTIVITY"
    serial_number = enter_serial_numbers(single)
    meta_data = get_comp_info(itkdb_client,serial_number)
    template = get_template(itkdb_client,meta_data,test_type)
    update_test_type(itkdb_client,meta_data,test_type)
    test_results = upload_connectivity_test(itkdb_client,template,meta_data,result_list)
    upload_results_locally(mongodb_client,test_results,serial_number,test_type)
    

if __name__ == '__main__':
  main()
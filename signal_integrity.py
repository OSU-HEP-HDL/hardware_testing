from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import enter_serial_numbers, get_comp_info, get_template,enquiry,update_test_type,upload_attachments
from modules.mongo_db import upload_results_locally
import itkdb
import shutil
import argparse
import csv
import datetime
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("results",nargs="*",help="Folder containing signal integrity results (input using wildcard. Ex. 'folder'/*)")
args = vars(parser.parse_args())

def sort_results(args):
    results = args['results']

    ''' Parse through args to separate results '''
    attachments = []
    impedance_images = []
    reflection_images = []
    data_loss_images = []
    eye_diagram_images = []
    value_array = []
    
    ''' sort images'''
    
    for result in results:
      if "csv" in str(result):
        attachments.append(result) 
      if "s4p" in str(result):
        attachments.append(result) 
      if "impedance" in str(result):
        impedance_images.append(result)
      if "reflection" in str(result):
        reflection_images.append(result)
      if "loss" in str(result):
        data_loss_images.append(result)
      if "ED.png" in str(result):
        eye_diagram_images.append(result)
      
      ''' Get values from csv of values '''

      if "values" in str(result):
         with open(result) as csv_file:
            reader = csv.reader(csv_file)
            count = 0
            
            ''' count the number of differential pairs '''
            for row in reader:
               if "D" in row[0]:
                  count = count+1
            csv_file.seek(0)

            rows = []
            for row in reader:
               rows.append(row)
            w, h = count, 9 # Defined by how many none empty rows between differential values
            sorted_values = [[0 for x in range(h)] for y in range(w)]  
            ''' Saving csv values into a 2D array to make it easier to sort'''
            for i in range(count):
               diff = False
               c = 0
               for p in range(len(rows)):
                  if "D"+str(i) in rows[p][0]:
                     diff = True
                  elif "D"+str(i+1) in rows[p][0]:
                     diff = False
                     continue
                  if diff == True:
                     if rows[p][2] == '':
                        continue
                     sorted_values[i][c] = rows[p]
                     c = c+1

    ''' Get designed impedance values'''
    w, h = count, 1 
    dimp_values = [[0 for x in range(h)] for y in range(w)]  
    for i in range(count):
       for p in range(len(sorted_values[0])):
         if "designed" in str(sorted_values[i][p][1]):
            dimp_values[i][0] = float(sorted_values[i][p][2])
    ''' Get measured impedance values '''
    mimp_values = [[0 for x in range(h)] for y in range(w)]  
    for i in range(count):
       for p in range(len(sorted_values[0])):
         if "measured" in str(sorted_values[i][p][1]):
            mimp_values[i][0] = float(sorted_values[i][p][2])
    ''' Get Data Loss values '''
    num_dl = 4
    w, h = count, num_dl
    dl_values = [[0 for x in range(h)] for y in range(w)]  
    for i in range(count):
       for p in range(len(sorted_values[0])):
         if "0.5" in str(sorted_values[i][p][1]):
            dl_values[i][0] = float(sorted_values[i][p][2])
         if "1.0" in str(sorted_values[i][p][1]):
            dl_values[i][1] = float(sorted_values[i][p][2])
         if "1.5" in str(sorted_values[i][p][1]):
            dl_values[i][2] = float(sorted_values[i][p][2])
         if "2.0" in str(sorted_values[i][p][1]):
            dl_values[i][3] = float(sorted_values[i][p][2])
    ''' Get Eye Diagram Values '''
    num_ed = 3
    w, h = count, num_ed
    ed_values = [[0 for x in range(h)] for y in range(w)]
    for i in range(count):
       for p in range(len(sorted_values[0])):
         if "jitter" in str(sorted_values[i][p][1]):
            ed_values[i][0] = float(sorted_values[i][p][2])
         if "height" in str(sorted_values[i][p][1]):
            ed_values[i][1] = float(sorted_values[i][p][2])
         if "width" in str(sorted_values[i][p][1]):
            ed_values[i][2] = float(sorted_values[i][p][2])    

    #dimp_values = np.array(dimp_values)
    ''' Store everything so it looks pretty '''
    values = {
       'designed_impedance': dimp_values,
       'measured_impedance': mimp_values,
       'data_loss': dl_values,
       'eye_diagram': ed_values
    }

    images = [impedance_images,data_loss_images,eye_diagram_images,reflection_images]
    
    return values, images, attachments      
   

def upload_signal_integrity_test(client,template,meta_data,values,images):

    component = client.get("getComponent", json={"component": meta_data["serialNumber"]})  
    
    runNumber = 0
    if len(component["tests"]) == 0:
      print("WARNING: No Visual Inspection test with this component")
      runNumber = str(len(component["tests"]) + 1)
    else:
      for x in component["tests"]:
          if x['code'] == "SIGNAL_INTEGRITY":
            runNumber = len(x["testRuns"])
      runNumber = str(runNumber + 1)
    
    mimpa = []
    for imp in values['measured_impedance']:
       mimpa.append(imp)
    dimpa = []
    for imp in values['designed_impedance']:
       dimpa.append(imp)
    dla = []
    for dl in values['data_loss']:
       dla.append(dl)
    eda = []
    for ed in values['eye_diagram']:
       eda.append(ed)

    test_results ={
     **template,
     'component': meta_data['serialNumber'],
     'institution': meta_data['institution'],
     'runNumber': runNumber,
     'passed': True,
     'problems': False,
     'properties':{'OPERATOR': meta_data['user']['userIdentity']},
                   'results': { 'MEASURED_IMPEDANCE': mimpa,
                                'DESIGNED_IMPEDANCE': dimpa,
                                'DATA_LOSS_VALUES': dla,
                                'EYE_DIAGRAM_VALUES': eda
                              }
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
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    if not enquiry(args["results"]):
      print("No folder argument included! Exiting...")
      exit()
    values,images, attachments = sort_results(args)
    single = True
    test_type = "SIGNAL_INTEGRITY"
    serial_number = enter_serial_numbers(single)
    meta_data = get_comp_info(itkdb_client,serial_number)
    template = get_template(itkdb_client,meta_data,test_type)
    update_test_type(itkdb_client,meta_data,test_type)
    test_results = upload_signal_integrity_test(itkdb_client,template,meta_data,values,images)
    upload_attachments(itkdb_client,args,meta_data,test_type)
    upload_results_locally(mongodb_client,test_results,serial_number,test_type)


if __name__ == '__main__':
  main()
from modules.db_utils import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import enter_serial_numbers, get_comp_info, get_template,enquiry
from modules.mongo_db import upload_results_locally
import itkdb
import shutil
import argparse
import csv
import datetime

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
      if "ED" in str(result):
        eye_diagram_images.append(result)
    
      ''' Get values from csv '''
      if "values" in str(result):
        with open(result) as csv_file:
            # RESET READING POSITION ###
            reader = csv.reader(csv_file)
            count = 0
            values = {
                    'imp_designed': 0,
                    'imp_measured': 0,
                    'dl_05_ghz': 0,
                    'dl_10_ghz': 0,
                    'dl_15_ghz': 0,
                    'dl_20_ghz': 0,
                    'ed_jitter': 0,
                    'ed_height': 0,
                    "ed_width": 0 
                    }
            ''' count the number of differential pairs '''
            for row in reader:
                if "D" in row[0]:
                   count = count+1
                   print(count)
          
            for row in reader:
                print("weeeee")
            for i in range(count):
                print(i)
                print("D"+str(i))
                for row in reader:
                    cd = 9
                    print(cd)
                    print(row[0])
                    if "D"+str(i) in row[0]:
                       cd = 9
                       print('here')
                    if "designed impedance" in (row[1]):
                       values['imp_designed'] = row[2]
                       cd = cd -1
                    if "measured impedance" in (row[1]):
                       values['imp_measured'] = row[2]
                       cd = cd -1
                    if "0.5" in (row[1]):
                       values['dl_05_ghz'] = row[2]
                       cd = cd -1
                    if "1.0" in (row[1]):
                       values['dl_10_ghz'] = row[2]
                       cd = cd -1
                    if "1.5" in str(row[1]):
                       values['dl_05_ghz'] = row[2]
                       cd = cd -1
                    if "2.0" in str(row[1]):
                       values['dl_05_ghz'] = row[2]
                       cd = cd -1
                    if "jitter" in str(row[1]):
                       values['ed_jitter'] = row[2]
                       cd = cd -1
                    if "height" in str(row[1]):
                       values['ed_height'] = row[2]
                       cd = cd -1
                    if "width" in str(row[1]):
                       values['ed_width'] = row[2]
                       cd = cd -1
                    print("cd",cd)

def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    sort_results(args)
    if not enquiry(args["results"]):
      print("No folder argument included! Exiting...")
      exit()
    single = True
    test_type = "SIGNAL_INTEGRITY"
    serial_number = enter_serial_numbers(single)
    meta_data = get_comp_info(itkdb_client,serial_number)
    template = get_template(itkdb_client,meta_data,test_type)
    print(args)
    print(template)
    #pload_results_locally(mongodb_client,test_results,serial_number,test_type)


if __name__ == '__main__':
  main()
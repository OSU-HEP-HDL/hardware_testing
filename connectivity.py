from modules.db_utils import authenticate_user_itkdb
from modules.reception_module import enter_serial_numbers,get_comp_info
import itkdb
import shutil
import argparse
import csv

parser = argparse.ArgumentParser()
parser.add_argument("csv",nargs="*",help="CIRRIS result CSV")
args = vars(parser.parse_args())

def get_csv_results(args):
  result = "not in file"
  error_results = []
  measure_results = []

  error_table = False
  measure_table =False
  
  with open(args['csv'][0]) as csv_file:
    reader = csv.reader(csv_file)
    for row in reader:
      if not row: 
        continue

      if "Final Test Result:" in str(row):
        result = row[1]
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
        

  return result, error_results, measure_results


def main():
    itkdb_client = authenticate_user_itkdb()
    #mongodb_client = authenticate_user_mongodb()
    get_csv_results(args)



if __name__ == '__main__':
  main()
from modules.db_utils import authenticate_user_itkdb
from modules.reception_module import enter_serial_numbers,get_comp_info
import itkdb
import shutil
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("csv",nargs="*",help="CIRRIS result CSV")
args = vars(parser.parse_args())

def main():
    itkdb_client = authenticate_user_itkdb()
    #mongodb_client = authenticate_user_mongodb()



if __name__ == '__main__':
  main()
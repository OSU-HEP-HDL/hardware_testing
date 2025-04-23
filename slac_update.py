from modules.db_auth import authenticate_user_itkdb, authenticate_user_mongodb
from modules.reception_module import update_test_type,enter_serial_numbers,get_comp_info


def main():
    itkdb_client = authenticate_user_itkdb()
    mongodb_client = authenticate_user_mongodb()
    single = True
    serial_number = enter_serial_numbers(single)
    meta_data = get_comp_info(itkdb_client,serial_number)
    slac_options = ["SHIPPING_TO_SLAC","RECEPTION_SLAC"]
    print("\nChoose which SLAC stage to update to:")
    for k, v in enumerate(slac_options):
        print(f"For {v}, press {k}")
    while True:
        try:
            selection = input("\nInput Selection: ")
            option = slac_options[int(selection)]
            break
        except (ValueError, IndexError):
            print("Invalid Input. Try again.")
    print(f"Selected {option}\n")
    update_test_type(itkdb_client,mongodb_client,meta_data,option)
    

    

if __name__ == '__main__':
  main()
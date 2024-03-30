from db_utils import authenticate_user_mongodb

client = authenticate_user_mongodb()

#TODO Define the criteria list
criteria_list = ["Is the item damaged? (yes/no): ", "Is the item dirty? (yes/no): ", "Is the item missing parts? (yes/no): "]


def get_response(criteria):
    # Returns user input for the given criteria
    response = input(criteria).strip().lower()
    return response


def get_status(responses):
    # Determines the status of the item based on the responses
    # NOTE: defaults to FAIL
    # If any of the responses are "yes" or "y", the status is "FAIL"
    # If no responses are "yes" or "y", the status is "PASS"
    status = "FAIL"
    for k, v in responses.items():
        if "yes" in v or "y" in v:
            status = "FAIL"
        else:
            status = "PASS"
    return status

def main():
    responses = {}
    # dictionary to store responses
    for criteria in criteria_list:
        response = get_response(criteria)
        if response in ["yes", "y", "no", "n"]: # Validates input
            responses[criteria] = response
        else:
            print("Invalid Input. Try again.")
            break

    status = get_status(responses)
    result = responses.copy()
    result["status"] = status
    # mydb = client["visual_test"]
    # mycol = mydb["inspections"]
    # x = mycol.insert_one(result)
    data_enrty = client["visual_test"]["inspections"].insert_one(result)

if __name__ == "__main__":
    main()
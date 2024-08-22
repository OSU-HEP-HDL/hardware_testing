def insert_property_names(component):

    comp_purpose = component["properties"]["PURPOSE"]
    if int(comp_purpose) == 0:
        purpose = "pre-production"
    elif int(comp_purpose) == 1:
        purpose = "production"
    elif int(comp_purpose) == 9:
        purpose = "dummy"
    
    comp_type_combination = component["properties"]["TYPE_COMBINATION"]
    if int(comp_type_combination) == 0:
        type_combination = "barrel-triplet"
    elif int(comp_type_combination) == 1:
        type_combination = "barrel-quad"
    elif int(comp_type_combination) == 2:
        type_combination = "ring-triplet"
    elif int(comp_type_combination) == 3:
        type_combination = "ring-quad"
    elif int(comp_type_combination) == 4:
        type_combination = "ring-both"
    
    comp_vendor = component["properties"]["VENDOR"]
    if int(comp_vendor) == 0:
        vendor = "Altaflex"
    elif int(comp_vendor) == 1:
        vendor = "PFC"
    elif int(comp_vendor) == 2:
        vendor = "Cirexx"
    elif int(comp_vendor) == 3:
        vendor = "EPEC"
    elif int(comp_vendor) == 4:
        vendor = "Vector"
    elif int(comp_vendor) == 5:
        vendor = "Summit"
    
    return purpose, type_combination, vendor

def upload_results_locally(client,results,serial_number,test_type):
   print("Uploading test results locally...")
   db = client["local"]["itk_testing"]
   try:
       if db.find_one({"_id": serial_number}) is None:
           raise ValueError
       elif 'tests' not in db.find_one({"_id": serial_number}):
           result = {"$set":{
               "tests":{
                 test_type: results
               }
             }
           }
           db.update_one({"_id": serial_number},result)
           print("Uploaded results locally!")
       else:
           key = "tests."+test_type
           result = {"$set":{
               key:results
               
             }
           }
           db.update_one({"_id": serial_number},result)
           print("Uploaded results locally!")
 
   except ValueError:
      print("Component with serial number",serial_number,"doesn't exist locally!")
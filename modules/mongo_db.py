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

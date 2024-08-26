# hardware_testing
Tools for performing hardware tests and uploading to databases.

# Setup
It is recommended that you install the required libraries in a virtual environment such as [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html).

To follow with this setup, create an environment called ```testing``` by running.
(Some features of OpenHTF do not work in python>3.9.)
```
virtualenv testing --python 3.9
```

Now using the startup script will activate your environment and ensure that the dependencies are installed.

```
source setup.sh
```

Create an environment file to store keys called ```.env```.
It should have the format
```
ITKDB_ACCESS_CODE1="password1"
ITKDB_ACCESS_CODE2="password2"

USERNAME="mongodb_user"
PASSWORD="mongodb_password"
LOCAL_ADDRESS="mongodb_address:port"
```

If setup is ran successfully, ```setup.sh``` should not be needed to be reran, even in a new shell. **NOTE:** After setup, your login credentials can be found in the ```.env```. You can edit this file to alter any credentials if there was a mistake made previously. Also, **YOUR CREDENTIALS ARE NOT HIDDEN, KEEP YOUR PERSONAL FILE SAFE!**

To connect to MongoDB, you need to be a part of the OSU network. If you're working from outside the network, you'll need to use Cisco (or another VPN). Instructions on how to set this up can be found here: https://it.okstate.edu/services/osuvpn/
# Running Scripts
Currently there are only three scripts that connect to the ITk database and the local database. 
```
register_components.py
remove_components.py
visual_inspection.py
```
The ```serial_number_generator.py``` is an offline SN generator. This is not needed to be ran to register components.

## Registering Components
Assuming setup has worked properly, you can now register components by:
```
python register_components.py
```
This script walks you through a menu about the component or components you're registering. If everything in the menu is answered properly, it'll output and use the ATLAS serial number(s) for both databases. 

When prompted about the component number, there are two options: 
1. the code parses through existing components with ATLAS serial you've entered and tells you how many currently exist and how many exist with your chosen flavor. It then prompots you if you want to start the component number where the latest number left off. 

2. You can also manually enter a number (not recommended).

Once you answer the prompt on the vendor, your component(s) will be registered with the ITk database. 

### Local Database
The registering to the local database happens **automatically** after it successfully uploads to the ITk databse. This is to ensure both databases are synced up with the components. The script does parse through the local database to ensure there are no duplicates. 

## Removing Components
To remove components, run:
```
python remove_components.py
```
This script can remove single components or batches of components. You can either manually enter the serial number(s) or go through the menu that the ```register_components.py``` offers. Prior to component(s) removal, it does parse through the ITk database to ensure all enquired components exist. 

### Local Database
Once components are removed from the ITk database, they are removed **automatically** from the local database to ensure both are synced with components. 

## Visual Inspection
To upload the results of the visual inspection test, run:
```
python visual_inspection.py image*.png
```
This script takes the inspection images as arguements. This can be a single image, multiple images (* works for tuple input), or no arguements (include no images).
You'll be prompted to manually input a single serial number for the component you've tested. If the test is passed, the results and its images are uploaded to the ITk database. 
If the component did not pass the test. You are asked for the reason, you can either manually enter this or choose from a list. If a common defect is not on the list, please tell me and I can add it. 

### Local Database
The results are **automatically** uploaded to the local database. The local database used for the components uses MongoDB which does not work for images, **IN PROGRESS:** urls are uploaded in their place linking the file shared system that store these images. The test result can be found under the key {'tests':'VISUAL_INSPECTION'}

## Connectivity Test
To upload the test results for the connectivity test, run:
```
python connectivity.py [CIRRUS output csv]
```
This script requires a csv produced by the CIRRUS tester as an argument. This script currently stores the test result, user, wire info, plus all the table information regardless of passing for failing. 

### Local Database
The results are **automatically** uploaded to the local database and can be found under the {'tests': 'CONNECTIVITY_TEST'}

# hardware_testing
Tools for performing hardware tests and uploading to databases.

In order to run these scripts, the user must have an account with the ITk database. https://itkpd-test.unicorncollege.cz/

A tutorial on these scripts can be found at https://github.com/OSU-HEP-HDL/hardware_database_tutorial
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
The main test stand workflow scripts are:
```
register_components.py
visual_inspection.py
connectivity.py
signal_integrity.py
```
Within the `utilites` folder, the following useful scripts can be found:
```
remove_component.py
serial_number_generator.py
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
python utilities/remove_components.py
```
This script can remove single components or batches of components. You can either manually enter the serial number(s) or go through the menu that the ```register_components.py``` offers. Prior to component(s) removal, it does parse through the ITk database to ensure all enquired components exist. 

### Local Database
Once components are removed from the ITk database, they are removed **automatically** from the local database to ensure both are synced with components. 

## Visual Inspection
To upload the results of the visual inspection test, run:
```
python visual_inspection.py image_folder/*.png
```
This script takes the inspection images as arguements. This can be a single image, multiple images (* works for tuple input), or no arguements (include no images).
You'll be prompted to manually input a single serial number for the component you've tested. If the test is passed, the results and its images are uploaded to the ITk database. 

If the component did not pass the test. You are asked for the reason, you can either manually enter this or choose from a list. If a common defect is not on the list, please tell me and I can add it. 

### Local Database
The results are **automatically** uploaded to the local database. The local database used for the components uses MongoDB which does not work for images, **IN PROGRESS:** urls are uploaded in their place linking the file shared system that store these images. The test result can be found under the key {'tests':'VISUAL_INSPECTION'}

## Connectivity Test
To upload the test results for the connectivity test, run:
```
python connectivity.py CIRRUS_output.csv
```
This script requires a csv produced by the CIRRUS tester as an argument. The data structure for this test is as follows (contains dummy values):

| **Properties**              | **Values** |
| --------------------------- | ---------- |
| Cable Number                |     1      |
| Operator Name               |  Jane Doe  |
| Short Test Resistance (kOhm)|  10 kOhm   |
| Wire Resistance (Ohm)       |  10.0 Ohm  |
| Error Details               | [" Instruction Detail"," Net NC: SHORT J1-010 to J1-012 J3-007", ...] |
| Passed                      | False      |
| Measured Values             | ["Not Tested","Not Tested","Not Tested","Not Tested",] |

Error Details and Measure Values are tables taken directly from the CIRRUS csv output.

### Local Database
The results are **automatically** uploaded to the local database and can be found under the local.itk_testing.'serialNumber'[{'tests': 'CONNECTIVITY_TEST'}]

## Signal Integrity Test
To run the test:
```
python signal_integrity.py results_folder/*
```
This test requires a folder with the results from the signal integrity test. All files within this folder will be uploaded as attachments to the test. Currently, the desired parameters that are saved need to be saved by hand in a csv. To save the images to the test, just ensure that they are contained within the result folder.

Data Structure:

The data is structured in 2D arrays. The first dimension index refers to each differential pair and the second dimension are those pair's values. For example:
```
[[3.0,4.0,5.0,6.0],[3.1,4.1,5.1,6.1],[3.2,4.2,5.2,6.2]]
```
Here, the ```[3.0,4.0,5.0,6.0]``` refers to the first differential pair, ```[3.1,4.1,5.1,6.1]``` refers to the second, and so on. 
Each value refers to a specific parameter as seen in the table.


|                        | Differential Pair 1 | Differential Pair 2 | ... |
| ---------------------- | ------------------- | ------------------- | --- |
| **Measured Impedance** |          1.0        |          1.1        | ... |
| **Designed Impedance** |          2.0        |          2.1        | ... |
|     **Data Loss**      |                     |                     |     |
|         0.5 GHz        |         3.0         |          3.1        | ... |
|         1.0 GHz        |         4.0         |          4.1        | ... |
|         1.5 GHz        |         5.0         |          5.1        | ... |
|         2.0 GHz        |         6.0         |          6.1        | ... |
| **Eye Diagram Values** |                     |                     |     |
|        Jitter          |         7.0         |          7.1        | ... |
|        Height          |         8.0         |          8.1        | ... |
|        Width           |         9.0         |          9.1        | ... |


### Local Database
The results are **automatically** uploaded to the local database and can be found under the local.itk_testing.'serialNumber'[{'tests': 'SIGNAL_INTEGRITY'}]


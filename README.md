# hardware_testing
Tools for performing hardware tests and uploading to databases.

In order to run these scripts, the user must have an account with the ITk database. https://itkpd-test.unicorncollege.cz/

A tutorial on these scripts can be found at https://github.com/OSU-HEP-HDL/hardware_database_tutorial (out of date)

>[!IMPORTANT]
>If you're reading this for your onboarding task, follow these IMPORTANT alerts. 
>
>The reason I'm having this process as an onboarding task is to give you some idea of the workflow that we, as a software team, are working on. These scripts have been editted and are used as the backbone of the UI and our ML projects are focused on increasing the efficiency of this testing process. 

# Setup
First, clone the main branch of this repository. The `setup.sh` script that's included will make a virtual environment with all the needed packages.

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

All attachments that are larger than 64kB are uploaded to EOS. This is done automatically and can still be seen on the production database.
# Running Scripts
The main test stand workflow scripts are:
```
register_components.py
visual_inspection.py
connectivity.py
signal_integrity.py
```
Some utility scripts are included:
```
remove_component.py
serial_number_generator.py
upload_attachment.py
slac_update.py
```
The ```serial_number_generator.py``` is an offline SN generator. This is not needed to be ran to register components.
A further discussion on these scripts can be found in the **Utility Scripts** section below.

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

>[!IMPORTANT]
>Most selections for component creation doesn't matter when making **Dummy** components. The **most** important one however is when prompted the type of componente (Prototype, Pre-Production, Production, Dummy). Ensure to hit **Dummy**. There are combindations that do not exist and will restart the script. To avoid this, I recommend just using most 0 selections. Do not enter a batch (say no to a batch). Just use the latest number that's listed when shown. Once the component is registered, copy the serial number as you will be asked to use it for the other scripts.

### Local Database
The registering to the local database happens **automatically** after it successfully uploads to the ITk databse. This is to ensure both databases are synced up with the components. The script does parse through the local database to ensure there are no duplicates. 

## Visual Inspection
To upload the results of the visual inspection test, run:
```
python visual_inspection.py image_folder/*.png
```
This script takes the inspection images as arguements. This can be a single image, multiple images (* works for tuple input), or no arguements (include no images).
You'll be prompted to manually input a single serial number for the component you've tested. If the test is passed, the results and its images are uploaded to the ITk database. 

If the component did not pass the test. You are asked for the reason, you can either manually enter this or choose from a list. If a common defect is not on the list, please tell me and I can add it. 

>[!IMPORTANT]
>In the folder `/testFiles`, there are example results to upload to your dummy components. You can use these as arguments, `python visual_inspection.py testFiles/visualInsp`. Say yes to the component passing the test.

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

>[!IMPORTANT]
>Just upload the pdf `python connectivity.py testFiles/connectivityFiles/l1_barrel_example.pdf`.

### Local Database
The results are **automatically** uploaded to the local database and can be found under the local.itk_testing.'serialNumber'[{'tests': 'CONNECTIVITY_TEST'}]

## Signal Integrity Test
To run the test:
```
python signal_integrity.py results_folder/*
```
The results from the signal integrity test are now being combined and formatted into a pdf report. This pdf report will be uploaded as a result attachment to the component. An example of the report can be found within the `/testFiles/signalInt` folder.

>[!IMPORTANT]
>To upload the test results to your dummy component: `python signal_integrity.py testFiles/connectivityFiles/20UPIPG1400036_report.pdf`


### Local Database
The results are **automatically** uploaded to the local database and can be found under the local.itk_testing.'serialNumber'[{'tests': 'SIGNAL_INTEGRITY'}]

## Utility Scripts

Four utility scripts are included.
```
remove_component.py
serial_number_generator.py
upload_attachment.py
slac_update.py
```

### Removing Components
To remove components, run:
```
python remove_components.py
```
This script can remove single components or batches of components. You can either manually enter the serial number(s) or go through the menu that the ```register_components.py``` offers. Prior to component(s) removal, it does parse through the ITk database to ensure all enquired components exist. 

>[!IMPORTANT]
>When you successfully take your dummy component all the way through the testing process. Please remove it! When prompted for the reason of deletion, just type "dummy" :D

#### Local Database
Once components are removed from the ITk database, they are removed **automatically** from the local database to ensure both are synced with components. 

### Upload Extra Attachments
If there are attachments you need to upload to a test that didn't make it into the original result posting, you can run:
```
python upload_attachments.py [attachment]
```
Provide the attachment as an argument. It will ask you which test to upload to, select one, and that's it!

### Updating Stage to SLAC
The final stages for the components are ```SHIPPING_TO_SLAC``` and ```RECEPTION_SLAC```. The script that updates to these stages is:
```
python slac_update.py
```
This will ask you which stage to update to, select one, and it will update to the stage.

### Serial Number Generator
This is an offline serial number generator that goes through the same menu as the ```register_component.py``` script. This just outputs the associated serial number for the user to use how they see fit. **THIS SCRIPT IS NOT NEEDED FOR REGISTERING COMPONENTS**

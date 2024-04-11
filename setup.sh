#!/bin/bash
mkdir ./results
source testing/bin/activate

pip install -r requirements.txt


read -p "Enter username: " USERNAME 


read -s -p "Enter password: " PASSWORD


echo "USERNAME=$USERNAME" > .env
echo "PASSWORD=$PASSWORD" >> .env
echo "LOCAL_ADDRESS=\"docker.dhcp.okstate.edu:27017\"" >> .env
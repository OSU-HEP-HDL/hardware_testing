#!/bin/bash
mkdir ./results
mkdir ./labels
source testing/bin/activate

pip install -r requirements.txt


read -p "Enter username: " USERNAME 
read -s -p "Enter password: " PASSWORD
read -s -p "Enter ITKDB_ACCESS_CODE1: " ITKDB_ACCESS_CODE1
read -s -p "Enter ITKDB_ACCESS_CODE2: " ITKDB_ACCESS_CODE2


echo "USERNAME=$USERNAME" >> .env
echo "PASSWORD=$PASSWORD" >> .env
echo "LOCAL_ADDRESS=\"docker.dhcp.okstate.edu:27017\"" >> .env
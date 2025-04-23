#!/bin/bash
# Exit on error
set -e

echo "🔧 Creating virtual environment in .venv/"
python3 -m venv .venv

echo "🐍 Activating virtual environment"
source .venv/bin/activate

echo "⬆️  Upgrading pip"
pip install --upgrade pip

echo "📦 Installing requirements"
pip install -r requirements/requirements.txt
echo "source .venv/bin/activate"

read -p "Enter username: " USERNAME 
read -s -p "Enter password: " PASSWORD
read -s -p "Enter ITKDB_ACCESS_CODE1: " ITKDB_ACCESS_CODE1
read -s -p "Enter ITKDB_ACCESS_CODE2: " ITKDB_ACCESS_CODE2


echo "USERNAME=$USERNAME" >> .env
echo "PASSWORD=$PASSWORD" >> .env
echo "ITKDB_ACCESS_CODE1=$ITKDB_ACCESS_CODE1" >> .env
echo "ITKDB_ACCESS_CODE2=$ITKDB_ACCESS_CODE2" >> .env
echo "ITKDB_ACCESS_SCOPE=openid https://itkpd-test.unicorncollege.cz" >> .env
echo "ITKDB_ACCESS_AUDIENCE=https://itkpd-test.unicorncollege.cz" >> .env
echo "ITKDB_AUTH_URL=https://uuidentity.plus4u.net/uu-oidc-maing02/bb977a99f4cc4c37a2afce3fd599d0a7/oidc/" >> .env
echo "ITKDB_API_URL=https://itkpd-test.unicorncollege.cz/" >> .env
echo "ITKDB_CASSETTE_LIBRARY_DIR=tests/integration/cassettes" >> .env
echo "LOCAL_ADDRESS=\"docker.dhcp.okstate.edu:27017\"" >> .env
echo "LOCAL_PROXMOX_HOST="10.206.65.222"" >> .env
echo "LOCAL_PROXMOX_USER="smb"" >> .env
echo "LOCAL_PROXMOX_PASSWORD="osuhep"" >> .env
echo "LOCAL_PROXMOX_PORT="22"" >> .env
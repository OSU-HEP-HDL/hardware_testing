#!/bin/bash
# Exit on error
set -e

# Determine if the system is macOS
IS_MAC=false
if [[ "$(uname)" == "Darwin" ]]; then
    IS_MAC=true
fi

prompt_input() {
    local prompt="$1"
    local varname="$2"
    local silent="$3"

    if $IS_MAC; then
        # macOS fallback (no -p or -s support)
        if [[ "$silent" == "true" ]]; then
            echo -n "$prompt"
            stty -echo
            read "$varname"
            stty echo
            echo ""
        else
            echo -n "$prompt"
            read "$varname"
        fi
    else
        # Modern Bash (Linux or newer Bash on macOS)
        if [[ "$silent" == "true" ]]; then
            read -s -p "$prompt" "$varname"
            echo ""
        else
            read -p "$prompt" "$varname"
        fi
    fi
}

echo "🔧 Creating virtual environment in .venv/"
python3 -m venv .venv

echo "🐍 Activating virtual environment"
source .venv/bin/activate

echo "⬆️  Upgrading pip"
pip install --upgrade pip

echo "📦 Installing requirements"
pip install -r requirements/requirements.txt

# Prompting for credentials
prompt_input "Enter username: " USERNAME false
prompt_input "Enter password: " PASSWORD true
prompt_input "Enter ITKDB_ACCESS_CODE1: " ITKDB_ACCESS_CODE1 true
prompt_input "Enter ITKDB_ACCESS_CODE2: " ITKDB_ACCESS_CODE2 true

# Create .env file
{
echo "USERNAME=$USERNAME"
echo "PASSWORD=$PASSWORD"
echo "ITKDB_ACCESS_CODE1=$ITKDB_ACCESS_CODE1"
echo "ITKDB_ACCESS_CODE2=$ITKDB_ACCESS_CODE2"
echo "ITKDB_ACCESS_SCOPE=openid https://itkpd-test.unicorncollege.cz"
echo "ITKDB_ACCESS_AUDIENCE=https://itkpd-test.unicorncollege.cz"
echo "ITKDB_AUTH_URL=https://uuidentity.plus4u.net/uu-oidc-maing02/bb977a99f4cc4c37a2afce3fd599d0a7/oidc/"
echo "ITKDB_API_URL=https://itkpd-test.unicorncollege.cz/"
echo "ITKDB_CASSETTE_LIBRARY_DIR=tests/integration/cassettes"
echo "LOCAL_ADDRESS=\"docker.dhcp.okstate.edu:27017\""
echo "LOCAL_PROXMOX_HOST=\"10.206.65.222\""
echo "LOCAL_PROXMOX_USER=\"smb\""
echo "LOCAL_PROXMOX_PASSWORD=\"osuhep\""
echo "LOCAL_PROXMOX_PORT=\"22\""
} >> .env
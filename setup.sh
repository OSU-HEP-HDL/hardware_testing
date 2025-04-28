#!/bin/bash
# Exit on error
set -e
rm -f .env

# Detect OS
IS_MAC=false
IS_WINDOWS=false

case "$(uname -s)" in
    Darwin)
        IS_MAC=true
        ;;
    Linux)
        # No change, assume normal Linux
        ;;
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
        IS_WINDOWS=true
        ;;
    *)
        echo "Unsupported OS: $(uname -s)"
        exit 1
        ;;
esac

# Function to prompt for input
prompt_input() {
    local prompt="$1"
    local varname="$2"
    local silent="$3"

    if $IS_MAC || $IS_WINDOWS; then
        # macOS or Windows bash fallback (no reliable -p or -s support)
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
        # Modern Linux
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
if $IS_WINDOWS; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

echo "⬆️  Upgrading pip"
pip install --upgrade pip

echo "📦 Installing requirements"
pip install -r requirements/requirements.txt

# Prompting for credentials
prompt_input "Enter username: " INPUT_USERNAME false
prompt_input "Enter password: " PASSWORD true
prompt_input "Enter ITKDB_ACCESS_CODE1: " ITKDB_ACCESS_CODE1 true
prompt_input "Enter ITKDB_ACCESS_CODE2: " ITKDB_ACCESS_CODE2 true

# Create .env file
{
echo "USERNAME=$INPUT_USERNAME"
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

echo "✅ Setup complete!"

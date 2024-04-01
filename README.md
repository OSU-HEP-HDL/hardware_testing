# hardware_testing
Tools for performing hardware tests and uploading to databases.

# Setup
It is recommended that you install the required libraries in a virtual environment such as [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html).

To follow with this setup, create an environment called ```testing``` by running.
```
virtualenv testing
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

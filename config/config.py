"""Configuration options
Load credentials from this file, or environment variables, or docker secrets.
For notes on configuration and deployment options, see CONFIG_README.md
"""

from get_docker_secret import get_docker_secret

# Optionally customize with your credentials
MY_ENVIRONMENT = 'some-server.lexisnexis.com'
MY_PROJECT_ID = 'your-user@email.com'
MY_USERNAME = 'your-user@wsk'
MY_PASSWORD = 'your-password'

# Do not change
LN_ENVIRONMENT = get_docker_secret('ln_environment', default=MY_ENVIRONMENT)
LN_PROJECT_ID = get_docker_secret('ln_project_id', default=MY_PROJECT_ID)
LN_USERNAME = get_docker_secret('ln_username', default=MY_USERNAME)
LN_PASSWORD = get_docker_secret('ln_password', default=MY_PASSWORD)

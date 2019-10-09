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

MY_OATH_ID = 'your-oath-id'
MY_OATH_SECRET = 'your-oath-secret'

# Do not change
LN_ENVIRONMENT = get_docker_secret('ln_environment', default=MY_ENVIRONMENT)
LN_PROJECT_ID = get_docker_secret('ln_project_id', default=MY_PROJECT_ID)
LN_USERNAME = get_docker_secret('ln_username', default=MY_USERNAME)
LN_PASSWORD = get_docker_secret('ln_password', default=MY_PASSWORD)

LN2_OAUTH_ID = get_docker_secret('ln2_oauth_id', default=MY_OAUTH_ID)
LN2_OAUTH_SECRET = get_docker_secret('ln2_oauth_secret', default=MY_OAUTH_SECRET)

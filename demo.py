# v0.10
# Dependencies: OpenSSL installed (to handle https/SSL), requests module
# Notes: The requests module handles most of the heavy lifting
#       This will loop through all results in a query, 50 at a time,
#       saving individual JSON files to the same directory as the script

# Modified for Docker, 10/24

import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime  # used to name json files
from os import environ
from time import sleep

# import json

from get_docker_secret import get_docker_secret


#  Place entire query string inside these quotes. (e.g. "'Edwin Willers'")
query = ""

#  Place entire query string inside these quotes.
filter = ""

# OAuth credentials.
client_id = get_docker_secret(
    "CHOMP_LN_CLIENT_ID", default=environ.get("CHOMP_LN_CLIENT_ID")
)
secret = get_docker_secret(
    "CHOMP_LN_SECRET_KEY", default=environ.get("CHOMP_LN_SECRET_KEY")
)

############# Begin Function Definitions #############


def get_token(client_id, secret):
    """Gets Authorizaton token to use in other requests."""
    auth_url = "https://auth-api.lexisnexis.com/oauth/v2/token"
    payload = (
        "grant_type=client_credentials&scope=http%3a%2f%2f" "oauth.lexisnexis.com%2fall"
    )
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(
        auth_url, auth=HTTPBasicAuth(client_id, secret), headers=headers, data=payload
    )
    json_data = r.json()
    return json_data["access_token"]


def build_url(content="News", query="", skip=0, expand="Document", top=50, filter=None):
    """Builds the URL part of the request to Web Services API."""
    if filter != None:  # Filter is an optional parameter
        api_url = (
            "https://services-api.lexisnexis.com/v1/"
            + content
            + "?$expand="
            + expand
            + "&$search="
            + query
            + "&$skip="
            + str(skip)
            + "&$top="
            + str(top)
            + "&$filter="
            + filter
        )
    else:
        api_url = (
            "https://services-api.lexisnexis.com/v1/"
            + content
            + "?$expand="
            + expand
            + "&$search="
            + query
            + "&$skip="
            + str(skip)
            + "&$top="
            + str(top)
        )
    return api_url


def build_header(token):
    """Builds the headers part of the request to Web Services API."""
    headers = {
        "Accept": "application/json;odata.metadata=minimal",
        "Connection": "Keep-Alive",
        "Host": "services-api.lexisnexis.com",
    }
    headers["Authorization"] = "Bearer " + token
    return headers


def get_result_count(json_data):
    """Gets the number of results from @odata.count in the response"""
    return json_data["@odata.count"]


def time_now():
    """Gets current time to the second."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d-%H%M%S")


############# End Function Defnitions #############

############# Begin business logic #############

token = get_token(client_id, secret)  # 1 token will work for multiple requests
request_headers = build_header(token)
skip_value = 0  # Sets starting skip
top = 50  # Adjusts the number of results to return

while True:
    request_url = build_url(
        content="News",
        query=query,
        skip=skip_value,
        expand="Document",
        top=top,
        filter=None,
    )  # Filter is set to filter=None here. Change to filter=filter to use the filter specified above
    r = requests.get(request_url, headers=request_headers)

    with open(
        str(time_now()) + ".json", "w"
    ) as f_out:  # Creates a file with the current time as the file name.
        f_out.write(r.text)

    skip_value = skip_value + top
    json_data = r.json()
    if skip_value > get_result_count(
        json_data
    ):  # Check to see if all the results have been looped through
        break

    sleep(12)  # Limit 5 requests per minute (every 12 seconds)

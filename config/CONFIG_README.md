# Config README

For each variable, config checks if a Docker 'secret' is mounted in-container;
it then checks if an equivalent environment variable exists;
finally it falls back to the default values defined directly in config.py.

The simplest possible configuration is standalone (changing this file);
more complex configuration setups with are also described below. They are
ordered from least to greatest complexity.


## Standalone


### Standalone with custom file

To run as a standalone program, customize the `my_` variables in config.py
with your LexisNexis WSK credentials.


### Standalone with custom environment

In the shell, define these environment variables:

    LN_ENVIRONMENT=some-server.lexisnexis.com
    LN_PROJECT_ID=your-user@email.com
    LN_USERNAME=your-user@wsk
    LN_PASSWORD=your-password

...then run the program. It will load credentials from the environment.


## Docker


### Docker with environment variables

To run as a Docker container, pass credentials as environment variables
which have been set in all caps in the shell environment, e.g. 

    LN_PASSWORD=your-password

This can be done with `docker run` arguments:

    docker run \
        --env LN_ENVIRONMENT=some-server.lexisnexis.com \
        --env LN_PROJECT_ID=your-user@email.com \
        --env LN_USERNAME=your-user@wsk \
        --env LN_PASSWORD=your-password \

...or from a list file:

    docker run --env-file ./env.list jeremydouglass/we1s-collector

...or by defining the environment variables in a (private!) Dockerfile

    FROM jeremydouglass/we1s-collector
    ENV LN_ENVIRONMENT=some-server.lexisnexis.com \
        LN_PROJECT_ID=your-user@email.com \
        LN_USERNAME=your-user@wsk \
        LN_PASSWORD=your-password \

        --env-file ./env.list ubuntu bash

...note that in this case your Docker image is also insecure.


### Docker swarm: secrets

To run as a container in a Docker swarm, first create your secrets:

    printf "some-server.lexisnexis.com" | docker secret create ln_environment -
    printf "your-user@email.com"        | docker secret create ln_project_id -
    printf "your-user@wsk"              | docker secret create ln_username -
    printf "your-password"              | docker secret create ln_password -

Once secrets are created, either:

1. launch a  docker service with access to those secrets, or
2. deploy a swarm stack that defines access to those secrets.


#### Option 1. `docker service` with secrets

Then launch as a service that uses those secrets:

    docker service create \
        --name we1s-collector \
        --secret ln_environment \
        --secret ln_project_id \
        --secret ln_username \
        --secret ln_password \
        --publish published=8081,target=8081 \
        jeremydouglass/we1s-collector:latest

...or add them to a running service:

    docker service update \
        --secret ln_environment \
        --secret ln_project_id \
        --secret ln_username \
        --secret ln_password \
        we1s-collector


#### Option 2. `docker stack deploy` with secrets

An alternative is to specify the secrets in a docker-compose.yml file (v3.1+)
and launch with `docker stack deploy`.

    version: "3.1"
    services:
      we1s-collector:
        image: jeremydouglass/we1s-collector
        secrets:
          - ln_environment
          - ln_project_id
          - ln_username
          - ln_password
    secrets:
      ln_environment:
        external: true
      ln_project_id:
        external: true
      ln_username:
        external: true
      ln_password:
        external: true

Instead of loading secrets that were created beforehand, you can also load
create them directly from the filesystem where docker-compose is run:

    secrets:
      ln_environment:
        file: ./ln_environment.txt
      ln_project_id:
        file: ./ln_project_id.txt
      ln_username:
        file: ./ln_username.txt
      ln_password:
        file: ./ln_password.txt

> **Portainer users**: Note if you are using Portainer that `docker swarm init`
> must be running on the host before submitting the compose file through the
> Stacks menu -- otherwise Portainer will use compose, not swarm, and version
> 3.1 files are not supported.

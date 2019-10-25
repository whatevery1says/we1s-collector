# we1s-collector

The collector is a system for searching, paging, and ingesting article data from new sources (with a current focus on sources from the Lexis-Nexis web-services kit API). Its interface to Lexis-Nexis is built on a fork of the Yale DH Lab “lexis-nexis-wsk,” a Python package with convenience wrappers for accessing Lexis Nexis WSK API.

It consists of wrappers and utilities for processing queries into collections of news article metadata, with a "bagify" feature to transform article content into word lists. Input may be a comma-delimited lists of query jobs; output is into WE1S schema JSON files (one per article), and may be batch-packaged into zip files. It comes with a command line batch-query interface, `searchcmd.py`, and a single-query interface, `search.py`.

This software was developed for WE1S (WhatEvery1Says) for studying collections of news articles.

Requires WSK API credentials issued by LexisNexis in order to submit queries.

Python 3-based. Uses the LexisNexis Web Services Kit (WSK) via the Yale DHLab [lexis-nexis-wsk](https://github.com/YaleDHLab/lexis-nexis-wsk). Other requirements are listed in `requirements.txt`


## local install

1. Download or `git clone https://github.com/whatevery1says/we1s-collector.git`
2. From directory, install required python 3 packages with:

      pip -r requirements.txt

3. Edit `config/config.py` and add credentials


### run a query set

Run a query set with the built-in test file:

     searchcmd.py -q queries.csv

Here are the usage details from `searchcmd.py --help`:

    WSK command line interface for WE1S (WhatEvery1Says)
    usage examples:
        python searchcmd.py -o ../wskoutput -q queries.csv
        ./searchcmd.py -o ../wskoutput -q queries.csv
    
    optional arguments:
      -h, --help            show this help message and exit
      -b, --bagify
      -o OUTPATH, --outpath OUTPATH
                            output path, e.g. "../output"
      -q QUERIES, --queries QUERIES
                            specify query file path, e.g. queries.csv
      -z, --zip             zip the json output

Query files are comma-separated-value (.csv) files with a header row and one query defined per row.

    source_title,source_id,keyword_string,begin_date,end_date,result_filter
    Chicago Daily Herald,163823,body(plural(humanities)) or hlead(plural(humanities)),2017-01-01,2017-01-31,humanities
    BBC Monitoring: International Reports,10962,body(plural(humanities)) or hlead(plural(humanities)),2017-01-01,2017-01-31,humanities
    The Guardian (London),138620,body(plural(arts)) or hlead(plural(arts)),2017-01-01,2017-01-15,the arts
    TVEyes - BBC 1 Wales,402024,body(plural(humanities)) or hlead(plural(humanities)),2017-01-01,2017-01-31,humanities
    Washington Post,8075,body(liberal PRE/1 plural(arts)) or hlead(liberal PRE/1 plural(arts)),2017-01-01,2017-01-31,liberal arts
    
The fields are:

-  `source_title`
    A human readable label for the source / publication, to be used in file names and metadata.
-  `source_id`  
    The LexisNexis WSK source id number, to be used in the query.
-  `keyword_string`  
    The search query string. This string may include keywords and WSK search operators such as `hlead()`, `plural()`, `PRE/1` et cetera.
-  `begin_date`  
    Beginning of the seach date range, in YYYY-MM-DD format.
-  `end_date`  
    End of the seach date range, in YYYY-MM-DD format.
-  `result_filter`
    Optional post-processing filter string. Results which do not contain this literal string are returned, but filtered into the `(no-exact-matches)` result group.

The default query filename is `queries.csv` -- you may edit the existing `queries.csv` or create new `.csv` files with the required header columns and process those files using the `-q` argument.


## Docker

This repository comes with a Dockerfile for installing as a Docker container on a generic virtual machine running Debian Linux with Python 3.6. The container image may be built locally, or it may be from from a pre-built image available from Docker Hub.


### adding credentials to Docker

Note that in order to submit queries, the container must have valid credentials for the WSK API. These can be added:

1. before a local build, by editing the `config/config.py` file before building the image
2. when launching a container, by passing `--env` arguments to the `docker run` command 
3. after entering a running container, by editing the `/app/config/config.py` file inside the container.
4. by running the container in a swarm and defining and mounting credentials as "Docker secrets".

For more details on these options, see: `config/CONFIG_README.md`


### run from Docker local build

1. Download or `git clone https://github.com/whatevery1says/we1s-collector.git`

2. From directory, build the image:

      docker build we1s-collector .

3. Run a container from the image.

      docker run we1s-collector --name we1s-collector
   
4. Enter the shell of the running container

      docker exec -it we1s-collector /bin/bash

5. Run a test query set:

     cd /app
     searchcmd.py -q queries.csv


### run from Docker remote image

1. Run a container from an image hosted on Docker Hub: 

      docker run whatevery1says/we1s-collector:latest --name we1s-collector

2. Enter the shell of the running container

      docker exec -it we1s-collector /bin/bash

3. Run a test query set:

     cd /app
     searchcmd.py -q queries.csv

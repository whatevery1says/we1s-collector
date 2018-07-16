# wskutils

Install with:

> pip -r requirements.txt

Rename `config.py--EXAMPLE` to `config.py` and add credentials.

Create a sample query list CSV file `queries.csv` with header row and one query per row, e.g.:

    source_title,source_id,keyword_string,begin_date,end_date
    Chicago Daily Herald,163823,liberal arts,2017-01-01,2017-02-01
    Chicago Daily Herald,163823,plural (humanities),2017-01-01,2017-02-01
    Los Angeles Times,8006,liberal arts,2017-01-01,2017-02-01
    Los Angeles Times,8006,plural (humanities),2017-01-01,2017-02-01

Run with:

> python search.py

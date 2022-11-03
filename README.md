# nifti2database

## Usage
```
usage: nifti2database [-h] -i DIR [DIR ...] [-o DIR] [--connect | --prepare] [--config_file FILE] [--credentials FILE] [-v]

    Parse nifti and json sidecare paramters and export them into a database for easy query.
    

Required arguments:
  -i DIR [DIR ...], --in_dir DIR [DIR ...]
                        Nifti directories that will be parsed.
                        This directory is usually in xnat/archive.
                        This argument accepts several paths. You can use syntax such as /path/to/nii/2021_*

Optional arguments:
  -h, --help            show this help message and exit
  -o DIR, --out_dir DIR
                        Output directory, receiving the log file.
  --connect             Use psycopg2.connect() to execute SQL 'INSERT' request (default)
  --prepare             Do not connect and write all SQL 'INSERT' lines in an output file
  --config_file FILE    If you want to use non-coded sequences such as new Products, WIP or C2P,
                        you can provide a config file.
                        Default location is ~/niix2bids_config_file/siemens.py
                        If default location is not present, try to use the template file 
                        located in [niix2bids]/config_file/siemens.py
  --credentials FILE    [nifti2database] will by default look for a credential json files 
                        located here : ~/credentials_nifti2database.json 
                        Otherwise, the user can provide it's path using this argument 
                        The file should lool like this :  
                        { 
                            "user": "username", 
                            "password": "********", 
                            "database": "mydatabase", 
                            "host": "ip_adress/host_name", 
                            "port": "5432", 
                            "schema: "myschema", 
                            "table: "mytable" 
                           ["sslmode": "disable"] 
                           ["gssencmode": "disable"] 
                        } 
                        !!! fields in [brackets] are optional, it depends on the server config 
                        
  -v, --version         show program's version number and exit

nifti2database version = 3.0.0
```

## Installation

### Python version & other dependencies 

#### Python version

`python >= 3.10` Tested on `3.10`

#### Package dependencies
- `pandas` # for DataFrame
- `nibabel` # to read nifti header
- `psycopg2-binary` # postgresql connection
- `niix2bids` # decision tree of the nifti & json fields
- `Flask` # for API using HTTP

## PostgreSQL
Some notes/commands for initialization of the test database, schema and table are in [db_scripts](db_scripts)

### How to

#### Recommended setup

Use [conda](https://docs.conda.io/en/latest/miniconda.html) to create a new python environment.

**Standard**

```shell
conda create --name nifti2database python=3.10
conda activate nifti2database
pip install git+https://github.com/benoitberanger/nifti2database
```

**Developer**

If you want to install in "developer" mode using the Git local repository, clone the repo before, then change the installation line :

```shell
cd /path/to/mydir/
git clone https://github.com/benoitberanger/nifti2database
conda create --name nifti2database python=3.10
conda activate nifti2database
pip install -e nifti2database/
```


#### **NOT** recommended installation procedure

`pip install git+https://github.com/benoitberanger/nifti2database`  
The installation might crash because of wrong dependency management.

## Known issues

`pip install nifti2database` is not possible yet. I did not register this packaged on https://pypi.org.


# Perform SQL requests

## Software
https://dbeaver.io/  
DBeaver can connect to a database, have a script editor to execute requests in 1 click and display the result

## Demo

[sample_request.sql](sample_request.sql)

Example :

```pgsql
-- count different resolution for mprage
select distinct dict->'Resolution', count(*)  from xdat_search.nifti_json
where dict->>'PulseSequenceName'='tfl' and jsonb_typeof(dict->'InversionTime')='number'
group by dict->'Resolution' order by count desc;
```

|resolution|count|
|----------|-----|
|[1, 1, 1]|15827|
|[1.2, 1.25, 1.25]|2013|
|[1.1, 1.102, 1.102]|1473|
|[0.8, 0.8, 0.8]|1276|
|[1.1, 1.094, 1.094]|906|
|[1.1, 1, 1]|717|
|[1.2, 1.055, 1.055]|371|
|[0.7, 0.7, 0.7]|346|
|[0.9, 0.889, 0.889]|238|
|[1.2, 1, 1]|226|
|[1.2, 0.938, 0.938]|76|
|[0.5, 0.5, 0.5]|73|
|[0.6, 0.602, 0.602]|73|
|[0.82, 0.82, 0.8]|72|
|[1, 0.977, 0.977]|63|
|[0.602, 0.602, 0.6]|23|
|[0.802, 0.802, 0.8]|22|
|[0.9, 0.898, 0.898]|19|
|[0.9, 0.896, 0.896]|18|
|[0.9, 0.903, 0.903]|18|

## Python script to send request
[template_request.py](template_request.py)

# API

## Flask
[Flask](https://flask.palletsprojects.com/) is used to build an API using HTTP

### Syntax
```json
{"args":"<same args as the CLI>"}
```
In the `args` field, just use the same arguments as the CLI. Such as :
```json
{"args":"-i /path/to/data --credentials /path/to/credentials.json"}
```

### is it running ?
`GET` request at the root `https://ipaddress:port/` will send a back a message : `API is running`  
`GET` request at  `https://ipaddress:port/help` will send back the help of the CLI

## Docker
[Docker](https://docs.docker.com/) is used as container

### Build
```bash
docker build -f Dockerfile -t nifti2database .
```

### Run
**!!! incomplete command !!!** :
```bash
docker run -p 5000:5000 nifti2database
```
The command misses mounting points :
- to the credential JSON file
- to the data directory

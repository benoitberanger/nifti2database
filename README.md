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

nifti2database version = 2.0.0
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

## PostgreSQL
Some notes/commands for initialization of the test database, schema and table are in [db_scripts](db_scripts)

### How to

#### Recommended setup

Use [conda](https://docs.conda.io/en/latest/miniconda.html) to create a new python environment.

**Standard**

```
conda create --name nifti2database python=3.10
conda activate nifti2database
pip install git+https://github.com/benoitberanger/nifti2database
```

**Developer**

If you want to install in "developer" mode using the Git local repository, clone the repo before, then change the installation line :

```
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

[sample_request.sql]()


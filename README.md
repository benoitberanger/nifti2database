# nifti2database


## Background


## Usage
```

```

## Limitations


## Installation

### Python version & other dependencies 

#### Python version

`python >= 3.9` Tested on `3.9`

#### Package dependencies
- `setuptools`
- `pandas`
- `nibabel`


### How to

#### Recommended setup

Use [conda](https://docs.conda.io/en/latest/miniconda.html) to create a new python environment.

**Standard**

```
conda create --name nifti2database_python3.9
conda activate nifti2database_python3.9
pip install git+https://github.com/benoitberanger/nifti2database
```

**Developer**

If you want to install in "developer" mode using the Git local repository, clone the repo before, then change the installation line :

```
cd /path/to/mydir/
git clone https://github.com/benoitberanger/nifti2database
conda create --name nifti2database_python3.9
conda activate nifti2database_python3.9
pip install -e nifti2database/
```


#### **NOT** recommended installation procedure

`pip install git+https://github.com/benoitberanger/nifti2database`  
The installation might crash because of wrong dependencies' management. Check [Known issues](https://github.com/benoitberanger/nifti2database#known-issues) section.


## Known issues

`pip install nifti2database` is not possible yet. I did not register this packaged on https://pypi.org.



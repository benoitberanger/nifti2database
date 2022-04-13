import setuptools  # for the setup, i.e. generate the script that enables CLI

with open('nifti2database/metadata.py', 'r') as fp:
    line = fp.readline()                      # read first line, which is "__version__ = '0.0.1'"
    __version__ = line.split()[2].strip("'")  # extract version number

with open('README.md', 'r') as f:
    long_description = f.readlines()

setuptools.setup(
    name="nifti2database",
    version=__version__,
    author='Benoit Beranger',
    author_email='benoit.beranger@icm-institute.org',
    url='https://github.com/benoitberanger/nifti2database.git',
    description='nifti2database',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='GPL3',
    packages=setuptools.find_packages(),
    python_requires='>=3.9',
    install_requires=[
        "pandas",
        "nibabel",
    ],
    entry_points={
        'console_scripts': [
            'nifti2database = nifti2database.cli:main'
        ]
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GLP3",
        "Operating System :: OS Independent",
    ),
    keywords='MRI nifti database',
    zip_safe=False
)

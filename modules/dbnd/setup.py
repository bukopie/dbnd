from os import path

import setuptools

from setuptools.config import read_configuration


BASE_PATH = path.dirname(__file__)
CFG_PATH = path.join(BASE_PATH, "setup.cfg")

config = read_configuration(CFG_PATH)

# A list of vendored packages
dbnd_vendors_list = [
    "cachetools",
    "hjson",
    "cloudpickle",
    "pendulum==1.4.4",
    "tabulate",
    "marshmallow==2.18.0",
    "croniter>=0.3.30,<0.4",
    "protobuf==3.13.0",
    "psutil>=4.2.0,<5.7.0",  # extracted use to vendorized_psutil.py
]

setuptools.setup(
    name="dbnd",
    package_dir={"": "src"},
    install_requires=[
        "tzlocal",
        "six",
        "more-itertools",
        "attrs!=21.1.0",  # yanked version, breaks dbnd
        "pyyaml",  # yaml support in targets
        "pytz",  # python time zone for pendulum library
        "pytzdata",  # python time zone for pendulum library
        "requests>=2.18.0",  # API TRACKING
        "configparser<3.6.0,>=3.5.0",  # same versions as Airflow -- Moved library to _vendor
        "pygments>=2.6.1",
        # backward compatible python
        'typing;python_version<"3.7"',  # Standalone pkg is incompatible with 3.7 and not required
        "python-dateutil",
        "sqlparse",
        # WARNING! Keep install_requires in sync with dbnd.requirements.txt file:
        # use dbnd.requirements.txt file generated by `make dist-python`
    ],
    extras_require={
        ':sys_platform=="win32"': ["colorama"],
        "tests": [
            "qtconsole==4.7.7",
            "numpy<1.20",  # 1.20 has compatibility issue with HDF5 marshalling. Fix is in progress
            "coverage",
            "pytest==4.5.0",  # 4.6.0 requires pluggy 0.12
            "pytest-cov==2.9.0",
            "pluggy==0.11.0",  # 0.12 has import_metadata, fails on py2
            "zope.interface",
            "mock",
            "pandas<2.0.0,>=0.17.1",  # airflow supports only this version
            "tox==3.12.1",
            "matplotlib==3.3.0",
            "tables==3.5.1",
            "feather-format",
            "pyarrow",
            # conflict with pandas version on new openpyxl: got invalid input value of type <class 'xml.etree.ElementTree.Element'>, expected string or Element
            "openpyxl==2.6.4",
            "scikit-learn",
            "wheel",  # for fat_wheel tests
        ],
        "jupyter": [
            "nbconvert",
            "nbformat",
            "jupyter",
            "traitlets>=4.2,<5.0.0",  # required by jupyter, fix py37 compatibility
            "IPython",
            "jupyter_contrib_nbextensions",
        ],
    },
    entry_points={"console_scripts": ["dbnd = dbnd:dbnd_main"]},
)

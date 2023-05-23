import json
import requests
import pandas as pd
from pandas import read_csv
from pandas import read_excel
import os
import pathlib
from datetime import datetime
from datetime import timedelta
from src.schema_merge import *
from collections import OrderedDict
from src.xls_to_json import *
from copy import deepcopy
import openpyxl
from src.download_xwalk import *

#### Load the credentials from GitHub
PERSONAL_TOKEN = os.environ.get("ACCESS_TOKEN")
credentials = os.environ.get("GSUITE_CREDENTIALS")
REPO = ['gtsueng/DDE-CrossWalks']

#### Load additional configurations
test = False

#### Load the paths
script_path = pathlib.Path(__file__).parent.absolute()

#### Check for new crosswalks
check_repo(REPO, PERSONAL_TOKEN,script_path,test)
check_crosswalks_list(script_path,credentials)
check_crosswalks_conversion(script_path)

#### Update the schemas
schema_path = os.path.join(script_path,'schema')
update_schema(schema_path)

#### Run the xls to json conversions
#convert_crosswalks(script_path)
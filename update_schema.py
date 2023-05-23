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


#### Load the paths
script_path = pathlib.Path(__file__).parent.absolute()

#### Update the schemas
schema_path = os.path.join(script_path,'schema')
update_schema(schema_path)

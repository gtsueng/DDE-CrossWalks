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

#### Update the schemas
script_path = pathlib.Path(__file__).parent.absolute()
data_path = os.path.join('script_path','schema')
update_schema(data_path)

#### Run the xls to json conversions
convert_crosswalks(script_path)
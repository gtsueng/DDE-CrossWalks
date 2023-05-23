import os
import json
import pandas as pd
import requests
from datetime import datetime
import openpyxl
from io import BytesIO as BytesIO
from src.xls_to_json import *

#### Handle spreadsheets from google
def parse_g_sheet_url(gsheeturl):
    baseurl = 'https://docs.google.com/spreadsheets/d/'
    tmpurl = gsheeturl.replace(baseurl,'')
    tmpurlcontent = tmpurl.split('/')
    spreadsheetId = tmpurlcontent[0]
    return spreadsheetId

def load_g_cred(parent_path):
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
    from pydrive2.auth import ServiceAccountCredentials
    gauth = GoogleAuth()
    scope = ['https://www.googleapis.com/auth/drive']
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials), scope)
    return gauth

def load_g_sheet_data(parent_path, gsheeturl):
    gauth = load_g_cred(parent_path)
    spreadsheetID = parse_g_sheet_url(gsheeturl)
    url = f"https://docs.google.com/spreadsheets/export?id={spreadsheetID}&exportFormat=xlsx"
    res = requests.get(url, headers={"Authorization": "Bearer " + str(gauth.attr['credentials'].access_token)})
    data_file = res.content
    return data_file

#### Handle spreadsheets saved in GitHub
def load_github_data(githuburl):
    url = f"{githuburl}?raw=true"
    res = requests.get(url)
    data_file = res.content
    return data_file

#### Handle spreadsheets saved elsewhere
def load_xls_data(otherurl):
    res = requests.get(url)
    data_file = res.content
    return data_File

#### Pull basic metadata from spreadsheet
def get_xwalk_meta(parent_path, inputurl):
    if 'github' in inputurl:
        data_file = load_github_data(inputurl)
        xwalk_dict = {'url':inputurl, 'urlType':'GitHub'}
    elif 'google' in inputurl:
        data_file = load_g_sheet_data(parent_path, inputurl)
        xwalk_dict = {'url':inputurl, 'urlType':'Gsheet'}
    else:
        try:
            data_file = load_xls_data(otherurl)
        except:
            data_file = None
        xwalk_dict = {'url':inputurl, 'urlType':'Other'}
    if data_file != None:
        try:
            try:
                values = pd.read_excel(data_file,sheet_name='metaInfo',header=0,index_col=None)
            except:
                data_stream = BytesIO(data_file)
                values = pd.read_excel(data_stream,sheet_name='metaInfo',header=0,index_col=None)
        except:
            try:
                values = pd.read_excel(data_file,sheet_name='metaInfo',header=0,index_col=None,engine="openpyxl")
            except:
                data_stream = BytesIO(data_file)
                values = pd.read_excel(data_stream,sheet_name='metaInfo',header=0,index_col=None,engine="openpyxl")                
        fileid = values['value'].loc[values['property']=='identifier']
        version = values['value'].loc[values['property']=='dateModified']
        xwalk_dict['identifier'] = fileid.iloc[0]
        xwalk_dict['version'] = version.iloc[0]
    return xwalk_dict, data_file


def download_spreadsheet(parent_path,url):
    if 'xlsx' in url:
        extension = '.xlsx'
    elif 'google' in url:
        extension = '.xlsx'
    else:
        extension = '.xls'
    xwalk_dict, data_file = get_xwalk_meta(parent_path, url)
    identifier = xwalk_dict['identifier']
    if data_file != None:
        with open(os.path.join(parent_path,'crosswalks',f"{identifier}{extension}"), 'wb') as output:
            output.write(data_file)
    else:
        print('unable to parse data from provided url')


def get_json_version(parent_path,data_file):
    tmpjson = json.load(open(os.path.join(parent_path,'jsoncrosswalks',data_file),'rb'))
    dateModified = tmpjson['dateModified']
    jsonversion = datetime.strptime(dateModified,"%Y-%m-%d")
    return jsonversion  

def get_xls_version(data_file):
    try:
        xwalkmeta = pd.read_excel(data_file,sheet_name='metaInfo',header=0,index_col=0)
    except:
        xwalkmeta = pd.read_excel(data_file,sheet_name='metaInfo',header=0,index_col=0,engine="openpyxl")
    xwalkdict = xwalkmeta.to_dict()
    dateModified = xwalkdict['value']['dateModified']
    if isinstance(dateModified,str):
        xls_version = datetime.strptime(dateModified.replace('"','').replace("'",""),"%Y-%m-%d")
    else:
        xls_version = dateModified
    return xls_version


def compare_versions(version1,version2):
    if version1 > version2:
        newer = version1
    else: #otherwise version 2 is either newer or the same, so just keep it
        newer = version2
    return newer


#### Check if the json_crosswalks folder is up-to-date

def check_crosswalks_conversion(parent_path):
    crosswalks_path = os.path.join(parent_path,'crosswalks')
    json_crosswalks_path = os.path.join(parent_path,'jsoncrosswalks')
    saved_crosswalks_list = os.listdir(crosswalks_path)
    json_crosswalks_list = os.listdir(json_crosswalks_path)
    ## For each item in crosswalks df
    for eachfile in saved_crosswalks_list:
        filename = eachfile.replace('.xls','.json').replace('.xlsx','.json')
     ### Check if the file already exists
        if filename in json_crosswalks_list:
            jsonversion = get_json_version(parent_path,filename)
            xlsversion = get_xls_version(os.path.join(parent_path,'crosswalks',eachfile))
            ### If it does, check if the version is up-to-date
            if jsonversion < xlsversion:
                ### If the jsonversion is older than the xls version, run the conversion
                convert_a_crosswalk(parent_path,eachfile)
        ### If it doesn't exist, run the conversion             
        else:
            convert_a_crosswalk(parent_path,eachfile) 
            

#### Check if items in crosswalks list are in the crosswalks folder
def check_crosswalks_list(parent_path):
    try:
        crosswalksdf = pd.read_csv(os.path.join(parent_path,'crosswalkslist.txt'),delimiter='\t',header=0, parse_dates=['version'])
    except:
        crosswalksdf = pd.read_csv(os.path.join(parent_path,'crosswalkslist.txt'),delimiter='\t',header=0)
    crosswalks_path = os.path.join(parent_path,'crosswalks')
    saved_crosswalks_list = os.listdir(crosswalks_path)
    ## For each item in crosswalks df
    crosswalk_list = crosswalksdf['identifier'].tolist()
    for identifier in crosswalk_list:
        tmp = crosswalksdf.loc[crosswalksdf['identifier']==identifier]
        txtversion = tmp.iloc[0]['version']
        txturl = tmp.iloc[0]['url']
        ### Check if the file already exists
        if (f"{identifier}.xls" in saved_crosswalks_list) or (f"{identifier}.xlsx" in saved_crosswalks_list):
            ### If it does, check if the version is up-to-date
            try:
                xlsversion = get_xls_version(os.path.join(parent_path,'crosswalks',f"{identifier}.xls"))
            except:
                xlsversion = get_xls_version(os.path.join(parent_path,'crosswalks',f"{identifier}.xlsx"))                
            newer = compare_versions(txtversion,xlsversion)
            ## if the one listed in the textfile is newer, download it
            if newer == txtversion:
                download_spreadsheet(parent_path,txturl)
        else:
            ### If it doesn't exist or is not up-to-date, download it
            download_spreadsheet(parent_path,txturl)

            
#### Functions for GitHub issue parsing

## Double-check to ensure it's a crosswalk submission
def check_status(eachissue):
    if eachissue['state'] == 'open':
        update_flag = True
    else:
        update_flag = False
    return update_flag

def check_labels(eachissue):
    labels = []
    for eachlabel in eachissue['labels']:
        labels.append(eachlabel['name'])
    if 'crosswalk submission' in labels:
        label_check = True
    else:
        label_check = False
    return label_check

## Parse a mapping submitted via GitHub issue form
def parse_mapping_submission(eachissue):
    md_result = eachissue['body']
    no_response = md_result.replace("_No response_","N/A")
    no_space = no_response.replace(' ','')
    no_space = no_space.replace('\n\n\n','\n\n').replace('\n\n','\n')
    dict_result = {}
    linelist = no_space.split('\n')
    i=0
    while i < len(linelist):
        if '###' in linelist[i]:
            dict_result[linelist[i].replace('###','')] = linelist[i+1]
        i=i+2
    dict_result['version'] = datetime.strptime(dict_result['version'],'%m/%d/%Y')
    try:
        dict_result.pop('ContactDetails')
    except:
        pass
    return dict_result

## Update a list based on a GitHub issue
def check_an_issue(parent_path,eachissue,test=False):
    label_check = check_labels(eachissue)
    update_flag = check_status(eachissue)
    if (label_check == True) and (update_flag == True):
        try:
            dict_result = parse_mapping_submission(eachissue)
            parse_success = True
        except:
            dict_result = {}
            parse_success = False
    else:
        parse_success = False
    ## If an issue was successfully parsed, check if it's already in the csv file
    if parse_success == True:
        try:
            crosswalklist = pd.read_csv(os.path.join(parent_path,'crosswalkslist.txt'),delimiter='\t',header=0,parse_dates=['version'])
        except:
            crosswalklist = pd.read_csv(os.path.join(parent_path,'crosswalkslist.txt'),delimiter='\t',header=0)

        all_crosswalks = crosswalklist['identifier'].tolist()
        ## Is the crosswalk already in the list?
        if dict_result['identifier'] in all_crosswalks:
            ## if it is, which version is newer?
            tmpdf = crosswalklist.loc[crosswalklist['identifier'] == dict_result['identifier']]
            prevdf = crosswalklist.loc[crosswalklist['identifier'] != dict_result['identifier']]
            listversion = tmpdf.iloc[0]['version']
            issueversion = dict_result['version']
            if issueversion > listversion:
                ## If the version in the issue is newer than the version in the list, update the list
                issuedf = pd.DataFrame([dict_result])
                crosswalklist = pd.concat((prevdf,issuedf))
                print('file updated')
            else:
                print('issue version is older')
        else:
            #print(dict_result["identifier"]," not yet in: ",all_crosswalks, ", now adding it")
            issuedf = pd.DataFrame([dict_result])
            crosswalklist = pd.concat((crosswalklist,issuedf),ignore_index=True)
            print("crosswalklist updated")
        if test == False:
            crosswalklist.to_csv(os.path.join(parent_path,'crosswalkslist.txt'),sep='\t',header=True,index=False)
        else:
            print('test completed')
           
        

def check_repo(REPO, PERSONAL_TOKEN,parent_path,test=False):
    i = 0
    while i < len(REPO):
        headers = {'Authorization': 'token %s' % PERSONAL_TOKEN }
        params_payload = { 'state' : 'open', 'labels' : 'crosswalk submission' , 'sort' : 'updated'} 
        ISSUES_FOR_REPO_URL = 'https://api.github.com/repos/%s/issues' % REPO[i]
        r = requests.get(ISSUES_FOR_REPO_URL, params=params_payload, headers=headers) 
        repo_issues = json.loads(r.text)
        for eachissue in repo_issues:
            check_an_issue(parent_path,eachissue,test)               
        # Check for more pages using the 'Link' header
        if 'Link' in r.headers:
            while check == True:
                # Create overview regarding the different Links, usually previous, first, last and next
                data = {}
                for links in r.headers['Link'].split(","):
                    raw = links.split(";")
                    data[raw[1][6:6+4]] = raw[0].strip()

                if "next" in data:
                    newlink = data["next"][1:-1]
                    r = requests.get(newlink, headers=headers)
                    print("Now processing page: " + newlink)
                    write_issues(r)
                    if data["next"] == data["last"]:
                        check = False
                        print("Done with Repository: " + REPO[i])
                else:
                    check = False
                    print("Done with Repository: " + REPO[i])
        else:
            print("Done with Repository: " + REPO[i])

        i=i+1
            

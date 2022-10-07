import json
import requests
import pandas as pd
from pandas import read_csv
import os
import pathlib
from biothings_schema import Schema


def get_raw_url(url):
    if 'raw' not in url:
        rawrawurl = url.replace('github.com','raw.githubusercontent.com')
        if 'main' in rawrawurl:
            rawurl = rawrawurl.replace('/blob/main/','/main/')
    else:
        rawurl = url
    return(rawurl)

def generate_base_dict():
    crosswalks = {
        "@context": {
            "schema": "http://schema.org/",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "owl": "http://www.w3.org/2002/07/owl/",
            "crosswalks": "https://discovery.biothings.io/view/crosswalks/"            
        },
        "@graph":[]
    }
    return(crosswalks)


def pool_graph_data(data_path,local=False):
    schema_list = ['CrossWalk.json','DataTransformer.json','Property.json']
    source_site = 'https://github.com/gtsueng/DDE-CrossWalks/blob/main/schema/'
    classlist = []
    propertylist = []
    for eachfile in schema_list:
        if local==False:
            rawurl = get_raw_url(f"{source_site}{eachfile}")
            r = requests.get(rawurl)
            tmpdict = json.loads(r.text)
        elif local==True:
            with open(os.path.join(data_path,eachfile),'r') as infile:
                tmpdict = json.load(infile)
                
        for eachhit in tmpdict['@graph']:
            if eachhit['@type'] == 'rdf:Property':
                propertylist.append(eachhit)
            else:
                classlist.append(eachhit)
    return(classlist,propertylist)


def clean_duplicate_classes(classlist):
    classlistid = [x['@id'] for x in classlist]
    duplicates = [i for i in set(classlistid) if classlistid.count(i) > 1]
    nondupes = [x for x in classlistid if x not in duplicates]
    cleanclassgraph = []
    if len(duplicates)>0:  ## There are duplicate classes to clean up
        for x in classlist:
            if x["@id"] in nondupes:
                cleanclassgraph.append(x)
            for eachclass in duplicates: ## Keep only the one that has $validation
                if x["@id"]==eachclass:
                    if "$validation" in x.keys():
                        cleanclassgraph.append(x)
    else:  ## There are no duplicate classes to clean up
        for x in classlist:
            if x["@id"] in nondupes:
                cleanclassgraph.append(x)         
    return(cleanclassgraph)

def clean_duplicate_properties(propertylist):            
    propertylistid = [x['@id'] for x in propertylist]
    duplicates = [i for i in set(propertylistid) if propertylistid.count(i) > 1]
    nondupes = [x for x in propertylistid if x not in duplicates]
    cleanpropsgraph = []
    dupepropsgraph = []
    if len(duplicates)>0:  ## There are duplicate properties to clean up
        for x in propertylist:
            if x['@id'] in nondupes:
                cleanpropsgraph.append(x)
            else:
                dupepropsgraph.append(x)
        dupepropsdf = pd.DataFrame(dupepropsgraph)
        for eachprop in duplicates:
            tmpdf = dupepropsdf.loc[dupepropsdf['@id']==eachprop].copy()
            domainlist = []
            domainlist = [y for y in tmpdf["schema:domainIncludes"] if y not in domainlist]
            #### Get the row with the least number of NaNs (ie- the row with the most properties) to serve as the base property
            tmpdict = tmpdf.iloc[0].to_dict()
            tmpdict["schema:domainIncludes"]=domainlist #### Set the domainIncludes list
            cleanpropsgraph.append(tmpdict)       
    else:
        for x in propertylist:
            if x["@id"] in nondupes:
                cleanpropsgraph.append(x) 
    return(cleanpropsgraph)  

def merge_specs(data_path,local=False):
    classlist,propertylist = pool_graph_data(data_path,local)
    cleanclassgraph = clean_duplicate_classes(classlist)
    cleanpropsgraph = clean_duplicate_properties(propertylist)
    crosswalks = generate_base_dict()
    graphlist = []
    for i in range(len(cleanclassgraph)):
        graphlist.append(cleanclassgraph[i])
    for j in range(len(cleanpropsgraph)):
        graphlist.append(cleanpropsgraph[j])
    crosswalks['@graph'] = graphlist
    return(crosswalks)

def validate_and_export(data_path,crosswalks):
    try:
        sc = Schema(crosswalks, base_schema=["schema.org"])
        sc.validation
        with open(os.path.join(data_path,'MetadataCrossWalk.json'),'w') as outfile:
            outfile.write(json.dumps(crosswalks,indent=2))
    except:
        print('validation failed')

        
def update_schema(data_path):
    local = True
    crosswalks = merge_specs(data_path,local)
    validate_and_export(data_path,crosswalks)


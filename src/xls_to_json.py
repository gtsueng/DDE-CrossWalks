import pandas as pd
from pandas import read_excel
import json
import os
from datetime import datetime
from collections import OrderedDict
import pathlib
from copy import deepcopy

def generate_context_list(contextdf):
    context_dict = {}
    for i in range(len(contextdf)):
        contextdf.fillna('null',inplace=True)
        tmpnamespace = contextdf.iloc[i]['namespace']
        tmpuri = contextdf.iloc[i]['@context']
        context_dict[str(tmpnamespace)]=str(tmpuri)
    clean_context = dict((k, v) for k, v in context_dict.items() if v!='null')
    if "schema" not in list(clean_context.keys()):
        clean_context["schema"] = "https://schema.org/"
    if "owl" not in list(clean_context.keys()):
        clean_context["owl"] = "http://www.w3.org/2002/07/owl/"
    if "rdf" not in list(clean_context.keys()):
        clean_context["rdf"] = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    if "rdfs" not in list(clean_context.keys()):
        clean_context["rdfs"] = "http://www.w3.org/2000/01/rdf-schema#"
    return clean_context

def clean_citations(schemaObject):
    citationdf = schemaObject[['citation.@type','citation.name','citation.url']].copy()
    citationdf.rename(columns={'citation.@type':'@type','citation.name':'name','citation.url':'url'},inplace=True)
    citejson = citationdf.to_dict(orient='records')
    schemaObject['citation'] = [x for x in citejson]
    schemaObject.drop(columns = ['citation.@type','citation.name','citation.url'], axis=1,inplace=True)
    return schemaObject

def load_authors(data_file):
    author_info = read_excel(data_file,sheet_name='authorInfo',header=0,index_col=None)
    author_object = author_info.to_dict(orient="records")
    return author_object

def load_funding(data_file):
    funding_info = read_excel(data_file,sheet_name='fundingInfo',header=0,index_col=None)
    if len(funding_info)>0:
        funder_info = funding_info[['funder.@type','funder.name']].copy()
        funder_info.rename(columns={'funder.@type':'@type','funder.name':'name'}, inplace=True)
        funder_dict_list = funder_info.to_dict(orient="records")
        funding = funding_info[['@type','identifier']].copy()
        funding['funder'] = [x for x in funder_dict_list]
        fundingdict = funding.to_dict(orient="records")
    else:
        fundingdict = {}
    return fundingdict

def load_schema_objects(data_file):
    schemaObjects = read_excel(data_file,sheet_name='schemaObjects',header=0,index_col=None)
    schemaObjects['version'] = schemaObjects.apply(lambda row: clean_up_dates(row['version']), axis=1)
    schemaContext = schemaObjects[['namespace','@context']].copy()
    context_dict = generate_context_list(schemaContext)
    schemaObjects = clean_citations(schemaObjects)
    schemaOriginObjects = schemaObjects.loc[schemaObjects['objectType']=='schemaOriginObject'].copy()
    schemaTargetObjects = schemaObjects.loc[schemaObjects['objectType']=='schemaTargetObject'].copy()
    schemaOriginObjects.drop(['namespace','@context','objectType'],axis=1,inplace=True)
    schemaTargetObjects.drop(['namespace','@context','objectType'],axis=1,inplace=True)
    schemaOriginList = schemaOriginObjects.to_dict(orient="records")
    schemaTargetList = schemaTargetObjects.to_dict(orient="records")
    try:
        schemaUsageObjects = schemaObjects.loc[schemaObjects['objectType']=='schemaUsageObject'].copy()    
        schemaUsageObjects.drop(['namespace','@context','objectType'],axis=1,inplace=True)
        schemaUsageList = schemaUsageObjects.to_dict(orient="records")
    except:
        schemaUsageList = None
    idlist = schemaObjects['identifier'].unique().tolist()
    return schemaOriginList, schemaTargetList, schemaUsageList, context_dict, idlist

def merge_schema_objects(schemaOriginList,schemaTargetList):
    schemalist = []
    for x in schemaOriginList:
        schemalist.append(x)
    for y in schemaTargetList:
        schemalist.append(y)
    return schemalist

def load_schema_usage_objects(schemaUsageList):
    schemalist = []
    for z in schemaUsageList:
        schemalist.append(z)
    return schemalist
    
def clean_up_dates(propvalue):
    if type(propvalue)==str:
        tmppropvalue = propvalue.strip('"')
        cleanpropvalue = tmppropvalue.strip("'")
    elif isinstance(propvalue,datetime):
        cleanpropvalue = datetime.strftime(propvalue,"%Y-%m-%d")
    else:
        cleanpropvalue = propvalue
    return cleanpropvalue

def parse_nestedProps(data_file):
    nestedProps = read_excel(data_file,sheet_name='nestedProps',header=0,index_col=None)
    nestedProps.fillna("null",inplace=True)
    proplist = nestedProps['property'].unique().tolist()
    propdict = {}
    for eachprop in proplist:
        tmpdf = nestedProps.loc[nestedProps['property']==eachprop].copy()
        tmpdf.drop('property',axis=1,inplace=True)
        tmpdict = tmpdf.to_dict(orient="records")
        cleandict = []
        for eachdict in tmpdict:
            cleandict.append(dict((k, v) for k, v in eachdict.items() if v!="null"))
        propdict[eachprop] = cleandict
    return propdict

#### value string formatting functions
def format_iri_as_id(example_iri):
    iri_list = example_iri.split(',')
    tmplist = []
    for each_iri in iri_list:
        iri_dict = {"@id":each_iri}
        tmplist.append(iri_dict)
    return tmplist   

def get_last_element(nestedname):
    namelist = nestedname.split('.')
    if len(namelist)>1:
        last_element = namelist[-1]
    if len(namelist)==1:
        last_element = namelist[0]
    if len(namelist)==0:
        last_element = nestedname
    return last_element

#### property functions
def add_type(propertydf):
    propertydf['@type'] = "schema:Property"
    return propertydf

def cleanup_domain_range(propertydf):
    try:
        propertydf['rangeIncludes'] = propertydf.apply(lambda row: format_iri_as_id(row['rangeIncludes']), axis=1)
    except:
        pass
    try:
        propertydf['domainIncludes'] = propertydf.apply(lambda row: format_iri_as_id(row['domainIncludes']), axis=1)
    except:
        pass
    return propertydf

def idlist_to_renamedf(idlist):
    renamedf = {}
    for eachid in idlist:
        renamedf[eachid] = 'property'
    return renamedf

def generate_isPartOf_info(propertydf,idlist):
    partid = [col for col in propertydf.columns if col in idlist]
    tmpdict = {'@id': partid[0]}
    return tmpdict

def clean_up_source_id(propertydf,idlist):
    partdict = generate_isPartOf_info(propertydf,idlist)
    renamedf = idlist_to_renamedf(idlist)
    propertydf.rename(columns=renamedf,inplace=True)
    propertydf['isPartOf'] = [partdict for x in propertydf['property']]
    return propertydf

def clean_up_prop_names(propertydf):
    propertydf.rename(columns = {'property':'nestedName'},inplace=True)
    propertydf['name'] = propertydf.apply(lambda row: get_last_element(row['nestedName']), axis=1)
    return propertydf

def clean_up_props(propertydf,idlist):
    propertydf = clean_up_source_id(propertydf,idlist)
    propertydf = clean_up_prop_names(propertydf)
    propertydf = cleanup_domain_range(propertydf)
    return propertydf

    
def generate_prop_included(data_file,idlist):
    proplist = read_excel(data_file,sheet_name='propertyList',header=0,index_col=None)
    proplist.dropna(axis=1, how='all', inplace=True)
    same_cols = [col for col in proplist.columns if 'sameAs' in col]
    source_cols = [col for col in proplist.columns if 'sameAs' not in col]
    sourcedf = proplist[source_cols].copy()
    sourcedf = clean_up_props(sourcedf,idlist)
    samedf = proplist[same_cols].copy()
    samedf.rename(columns=lambda s: s.replace("sameAs.", ""), inplace=True)
    samedf = clean_up_props(samedf,idlist)
    samedict = samedf.to_dict(orient="records")
    sourcedf['sameAs'] = samedict
    propdictlist = sourcedf.to_dict(orient="records")
    return propdictlist
    

def convert_xls_xwalk(data_file):
    author_object = load_authors(data_file)
    funding_object = load_funding(data_file)
    schemaOriginList, schemaTargetList, schemaUsageList, context_dict, idlist = load_schema_objects(data_file)
    propdict = parse_nestedProps(data_file)
    includedprops = generate_prop_included(data_file,idlist)
    xwalkmeta = read_excel(data_file,sheet_name='metainfo',header=0,index_col=0)
    xwalkmeta.dropna(inplace=True)
    xwalkdict = xwalkmeta.to_dict()
    xwalkclean = OrderedDict(xwalkdict['value'])
    xwalkclean['@context'] = context_dict
    xwalkclean['@type'] = 'crosswalks:MetadataCrosswalk'
    xwalkclean['author'] = author_object
    if len(funding_object)>0:
        xwalkclean['funding'] = funding_object
    xwalkclean['hasPart'] = merge_schema_objects(schemaOriginList,schemaTargetList)
    xwalkclean['datePublished'] = clean_up_dates(xwalkclean['datePublished'])
    xwalkclean['dateModified'] = clean_up_dates(xwalkclean['dateModified'])
    try:
        xwalkclean['isBasedOn'] = propdict['isBasedOn']
    except:
        pass
    try:
        xwalkclean['isBasisFor'] = propdict['isBasisFor']
    except:
        pass
    xwalkclean['includesProperty'] = includedprops
    if schemaUsageList != None:
        xwalkclean['isPartOf'] = load_schema_usage_objects(schemaUsageList)
    return xwalkclean


def invert_mappings(property_list):
    inverted_prop_list = []
    for eachprop in property_list:
        newprop = eachprop.pop('sameAs')
        newprop['sameAs'] = eachprop
        inverted_prop_list.append(newprop)
    return inverted_prop_list


def generate_inverted_crosswalk(xwalkclean):
    property_list = xwalkclean['includesProperty']
    inverted_props = invert_mappings(property_list)
    original_id = xwalkclean['identifier']
    new_id = 'inverted_'+original_id
    invertedxwalk = deepcopy(xwalkclean)
    invertedxwalk['identifier'] = new_id
    invertedxwalk['includesProperty']=inverted_props
    return(invertedxwalk)



def convert_crosswalks(script_path):
    data_path = os.path.join(script_path,'crosswalks')
    export_path = os.path.join(script_path,'jsoncrosswalks')
    data_files = os.listdir(data_path)
    for filename in data_files:
        data_file = os.path.join(data_path,filename)
        export_file = os.path.join(export_path,filename.replace('xls','json'))
        inverted_export_file = os.path.join(export_path,filename.replace('.xls','_inverted.json'))
        try:
            xwalkjson = convert_xls_xwalk(data_file)
            with open(export_file,'w') as outfile:
                jsonfile = json.dumps(xwalkjson, indent=2)
                outfile.write(jsonfile)
            invertedxwalk = generate_inverted_crosswalk(xwalkjson)
            with open(inverted_export_file,'w') as outfile:
                jsonfile = json.dumps(invertedxwalk, indent=2)
                outfile.write(jsonfile)
        except:
            print("failed to convert: ",filename)   


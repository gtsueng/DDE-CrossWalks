## List of Notebooks

The following notebooks and their descriptions are included in this repository:

1. Generate_crosswalks.ipynb : This notebook contains scripts for identifying child classes given an input class and then creating the crosswalks metadata info table using information from 2 child classes. The property table is generated in a different notebook. This notebook also contains scripts for generating default metadata info tables for NDE mappings
2. generate_dde_default_prop_tables.ipynb : This notebook contains scripts for generating default property definition tables for a given class. It has been used for generating the default NDE property definition tables which have been used for draft NDE mappings
3. merge_schemas.ipynb : This notebook contains scripts for merging different classes of the metadata crosswalks schema into one jsonschema/JSONLD file. It is for the generation of the schema file itself for registration in the DDE.
4. Using_Crosswalks.ipynb : This notebooks contains example python scripts for using a metadata crosswalk json file: eg- finding all the properties that map to a given property, etc.
5. validate_schema.ipynb : This notebook has scripts to validate a metadata crosswalk data file against the metadata crosswalk json schema
6. xls_2_json.ipynb : This notebook contains scripts for converting a template metadata crosswalk xls or xlsx file to JSON Schema/JSON-LD formatting.
7. Download_Crosswalk.ipynb: This notebook contains scripts for downloading and maintaining crosswalks 

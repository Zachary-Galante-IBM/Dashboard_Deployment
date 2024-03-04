#Import Libraries
import dash
from dash import Dash, html, Input, Output, ctx,dcc
from dash.dependencies import Output, Input
import dash_bootstrap_components as dbc
from natsort import natsort_keygen
import plotly
import plotly.graph_objects as go
import jupyter_dash as jd
import pandas as pd
pd.options.mode.chained_assignment = None
pd.options.display.max_columns = None
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import numpy as np
from datetime import date, timedelta
date_today = date.today().strftime("%m/%d/%Y")
import calendar
import os
cwd = os.getcwd()
import json
import re
from auth_dash import AppIDAuthProviderDash
import datetime
#import client data
#setting up the API with the COS
# Constants for IBM COS values
COS_ENDPOINT = "https://s3.us-east.cloud-object-storage.appdomain.cloud" # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
COS_API_KEY_ID = "jUd1NEp9jsSKKOdGAStVi2muc3WegqA44HCD_ax_W1R_" # eg "W00YixxxxxxxxxxMB-odB-2ySfTrFBIQQWanc--P3byk"
COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/6003dba678e9a506528e0dc3dad11d75:b75750b4-68a2-4113-af62-16c1e6e10bca::" # eg "crn:v1:bluemix:public:cloud-object-storage:global:a/3bf0d9003xxxxxxxxxx1c3e97696b71c:d6f04d83-6c4f-4a62-a165-696756d63903::"
# Create resource
cos = ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_INSTANCE_CRN,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)
# Using the API to connect to the COS
def get_item(bucket_name, item_name):
    print("Retrieving item from bucket: {0}, key: {1}".format(bucket_name, item_name))
    try:
        file = cos.Object(bucket_name, item_name).get()
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve file contents: {0}".format(e))
    return file

######### FOR CLOUD DEPLOYMENT ########
# getting the contents of the file from the COS
client_data = get_item('oidash-app','All_2023_data.csv')
client_data = client_data['Body'].read()
# writing to a csv and then loading into a pandas DataFrame
with open('All_2023_data.csv','wb') as file:
    file.write(client_data)
# New Monthly Data
jan_data = get_item('oidash-app','Jan24.csv')
jan_monthly_data = jan_data['Body'].read()
with open('Jan24.csv','wb') as file:
    file.write(jan_monthly_data)
feb_data = get_item('oidash-app','Feb24.csv')
feb_monthly_data = feb_data['Body'].read()
with open('Feb24.csv','wb') as file:
    file.write(feb_monthly_data)
######################################## """

all_data = pd.read_csv('All_2023_data.csv')
cloud_columns = list(all_data.columns)
if 'Unnamed: 0' in cloud_columns:
    all_data.drop(columns = ['Unnamed: 0'], inplace = True)
jan_data_loaded = pd.read_csv('Jan24.csv',  encoding='UTF-16', sep='\t',on_bad_lines='skip')
feb_data_loaded = pd.read_csv('Feb24.csv',  encoding='UTF-16', sep='\t',on_bad_lines='skip')
jan_data_loaded['Date'] = pd.to_datetime(jan_data_loaded['Month'])
feb_data_loaded['Date'] = pd.to_datetime(feb_data_loaded['Month'])
all_data['Date'] = pd.to_datetime(all_data['Month'])
all_data = pd.concat([all_data, jan_data_loaded, feb_data_loaded])
earliest_date = all_data['Date'].min() # earliest date 
most_recent_date = all_data['Date'].max() # the most recent date 

# get the dictionaries and write them to JSON files
red = get_item('oidash-app','red.json')
red = red['Body'].read()
with open('red.json','wb') as file:
    file.write(red)
orange = get_item('oidash-app','orange.json')
orange = orange['Body'].read()
with open('orange.json','wb') as file:
    file.write(orange)
green = get_item('oidash-app','green.json')
green = green['Body'].read()
with open('green.json','wb') as file:
    file.write(green)


#clients = pd.read_csv('clients_defects_june_23.csv')

#clients.drop(columns = clients.columns[0], inplace = True)
#client_focus_list = pd.read_csv('graph2_data_june_23.csv')
#client_focus_list.drop(columns = client_focus_list.columns[0], inplace = True)
#client_focus_list.drop(columns = ['c_color'], inplace = True)

# changing some column names for uniformity
#clients["Product name"]=clients["Product Name"]
#clients["Product"]=clients["Product Name"]
#clients["client"]=clients["Client"]
DASH_URL_BASE_PATHNAME = "/dashboard/"
auth = AppIDAuthProviderDash(DASH_URL_BASE_PATHNAME)
app = dash.Dash(__name__, server = auth.flask, url_base_pathname = DASH_URL_BASE_PATHNAME, external_stylesheets=[dbc.themes.MINTY, dbc.icons.FONT_AWESOME])
#==========================================================================================================================================
#Import Dictionaries - Used for calculating the color for EOS status
#RED: products and related versions that have reached end of support
with open('red.json', 'r') as f:
  red = json.load(f)
f.close()
#ORANGE: products and related versions that are approaching end of support within 12 months
with open('orange.json', 'r') as f:
  orange = json.load(f)
f.close()
#GREEN: products and related versions that are approaching end of support within 12 months
with open('green.json', 'r') as f:
  green = json.load(f)
f.close()
# changing how some specific products are represented in the dictionary 
if 'PowerVM VIOS Enterprise Edition' in list(red.keys()):
    red['PowerVM / VIOS'] = red['PowerVM VIOS Enterprise Edition'] 
    del red['PowerVM VIOS Express Edition']
if 'PowerVM VIOS Enterprise Edition' in list(green.keys()):
    green['PowerVM / VIOS'] = green['PowerVM VIOS Enterprise Edition'] 
    del green['PowerVM VIOS Enterprise Edition']
if 'PowerVM VIOS Enterprise Edition' in list(orange.keys()):
    orange['PowerVM / VIOS'] = orange['PowerVM VIOS Enterprise Edition'] 
    del orange['PowerVM VIOS Enterprise Edition']
if 'IBM QRadar' in list(red.keys()):
    red['IBM QRadar on Cloud'] = red['IBM QRadar'] 
    del red['IBM QRadar']
if 'IBM QRadar' in list(green.keys()):
    green['IBM QRadar on Cloud'] = green['IBM QRadar'] 
    del green['IBM QRadar']
if 'IBM QRadar' in list(orange.keys()):
    orange['IBM QRadar on Cloud'] = orange['IBM QRadar'] 
    del orange['IBM QRadar']
if 'Content Manager OnDemand for z/OS' in list(red.keys()):
    red['Content Manager OnDemand'] = red['Content Manager OnDemand for z/OS'] 
    del red['Content Manager OnDemand for z/OS']
if 'Content Manager OnDemand for z/OS' in list(green.keys()):
    green['Content Manager OnDemand'] = green['Content Manager OnDemand for z/OS']  
    del green['Content Manager OnDemand for z/OS']
if 'Content Manager OnDemand for z/OS' in list(orange.keys()):
    orange['Content Manager OnDemand'] = orange['Content Manager OnDemand for z/OS']  
    del orange['Content Manager OnDemand for z/OS']
# Tivoli Management Services for z/OS
if 'IBM Tivoli Management Services on z/OS' in list(red.keys()):
    red['Tivoli Management Services for z/OS'] = red['IBM Tivoli Management Services on z/OS'] 
    del red['IBM Tivoli Management Services on z/OS']
if 'IBM Tivoli Management Services on z/OS' in list(green.keys()):
    green['Tivoli Management Services for z/OS'] = green['IBM Tivoli Management Services on z/OS']  
    del green['IBM Tivoli Management Services on z/OS']
if 'IBM Tivoli Management Services on z/OS' in list(orange.keys()):
    orange['Tivoli Management Services for z/OS'] = orange['IBM Tivoli Management Services on z/OS']  
    del orange['IBM Tivoli Management Services on z/OS']
orange['Integrated Analytics Systems'] = orange['IBM Integrated Analytics System']
orange['Integrated Analytics Systems'].append('1.0.x')
if 'IBM Integrated Analytics System' in list(green.keys()):
    green['IBM Integrated Analytics System'] = green['IBM Integrated Analytics System'].append('1.0.x')
if 'IBM Planning Analytics Local' in list(green.keys()):
    green['IBM Planning Analytics Local'].append('2.0.9.x')
if 'IBM Sterling Connect:Direct for z/OS' in list(green.keys()):
    green['Sterling Connect Direct for z/OS'] = green['IBM Sterling Connect:Direct for z/OS']  
    del green['IBM Sterling Connect:Direct for z/OS']
if 'Tivoli Netcool/OMNIbus' in list(red.keys()):
    red['Netcool/OMNIbus'] = red['Tivoli Netcool/OMNIbus']
if 'Tivoli Netcool/Impact' in list(red.keys()):
    red['Netcool/Impact'] = red['Tivoli Netcool/Impact']    
    #del green['IBM Sterling Connect:Direct for z/OS']
#if 'Tivoli Netcool/OMNIbus' in list(red.keys()):
 #   red['Netcool/OMNIbus'].append(red['Tivoli Netcool/OMNIbus'])
#if 'Tivoli Netcool/OMNIbus' in list(green.keys()):
 #   green['Netcool/OMNIbus'].append(green['Tivoli Netcool/OMNIbus'])
#if 'Tivoli Netcool/OMNIbus' in list(orange.keys()):
 #   orange['Netcool/OMNIbus'].append(orange['Tivoli Netcool/OMNIbus'])
if 'IBM Cloud Pak for Data' in list(green.keys()):
    green['IBM Cloud Pak for Data'].extend([f'4.{i}.x' for i in range(30)])
if 'IBM SevOne Network Performance Management' in list(green.keys()):
    green['IBM SevOne Network Performance Management'].extend([f'6.{i}.x' for i in range(30)])
if 'Cloudera Data Platform Private Cloud Plus Add-on with IBM' in list(red.keys()):
    red['Cloudera CDP Private Cloud'] = red['Cloudera Data Platform Private Cloud Plus Add-on with IBM']
if 'Cloudera Data Platform Private Cloud Plus Add-on with IBM' in list(orange.keys()):
    orange['Cloudera CDP Private Cloud'] = orange['Cloudera Data Platform Private Cloud Plus Add-on with IBM']
if 'Cloudera Data Platform Private Cloud Plus Add-on with IBM' in list(green.keys()):
    green['Cloudera CDP Private Cloud'] = green['Cloudera Data Platform Private Cloud Plus Add-on with IBM']
if 'IBM Aspera Faspex' in list(red.keys()):
    red['Aspera'] = red['IBM Aspera Faspex']
if 'IBM Aspera Faspex' in list(green.keys()):
    green['Aspera'] = green['IBM Aspera Faspex']
if 'IBM Aspera Faspex' in list(orange.keys()):
    orange['Aspera'] = orange['IBM Aspera Faspex']

 #   red['Netcool/OMNIbus'].append(red['Tivoli Netcool/OMNIbus'])
#if 'Tivoli Netcool/OMNIbus' in list(green.keys()):
 #   green['Netcool/OMNIbus'].append(green['Tivoli Netcool/OMNIbus'])
#if 'Tivoli Netcool/OMNIbus' in list(orange.keys()):
 #   orange['Netcool/OMNIbus'].append(orange['Tivoli Netcool/OMNIbus'])

    
    
    #==========================================================================================================================================
# Supporting Functions

def calc_color(x):
    """---------------------------------------------------------------------------------
    Description:Function used in association with graph 2 to calculate scatter plot colors based on EOS status
    Parameters: x (Pandas Series) - df element containing columns 'Product Name' and 'Product Version'
    Return: (string) - color associated with product version EOS status
    Comments: Uses dictionaries 'red' and 'orange' to determine colors based on EOS status
    ---------------------------------------------------------------------------------"""
    prod_string=x["Product Name"]
    version=str(x['Product Version']).lower()
    # for instances where the product name is the EXACT same 
    if prod_string in red and version in red[prod_string]:#if product in red and version in red
        return "red"
    elif prod_string in orange and version in orange[prod_string]:#if product in orange and version in orange
        return "orange"
    elif prod_string in green and version in green[prod_string]:#if product in green and version in green
        return "green"
    elif version == None or version == " " or version == "" or version == "NaN" or version == "nan":
        return "blue" 



    #if exact product name not found, check if products exist in string. Ex: 'MQ' in 'IBM MQ'
    else:
        # go through all product names in all dictionaries to see if it is part of a string
        orange_products = []
        for oname in orange:
            if prod_string in oname:
                orange_products.append(oname)
        if len(orange_products) > 0:
            shortest_name = detect_shortest_string(orange_products, prod_string)
            orange_product_versions = [i.lower() for i in orange[shortest_name]]
            if prod_string in shortest_name and version in orange_product_versions:#if string contains a product
                return "orange"
            elif prod_string in shortest_name and version[:-1] + 'x' in orange_product_versions:
                return "orange"    
            elif prod_string in shortest_name and re.sub(r"\.[^\.]*$","",version)+ '.x' in orange_product_versions:
                return "orange"
            elif prod_string in shortest_name and version + '.0' in orange_product_versions:
                return "orange"
            elif prod_string in shortest_name:
                for detected_version in orange_product_versions:
                    if '.' in detected_version and '.' in version:
                        if version.split('.')[0:2] == detected_version.split('.')[0:2]:
                            return 'orange'
            for i in orange_product_versions:
                if 'x' in i:
                    # checks if there is any numerical version
                    prod_name = i.replace('x', '[0-9]+')
                    if re.search(prod_name, version):
                        return "orange"
                    elif version == i.replace('.x', ''):
                        return "orange"
                    elif version + '.0.x' == i:
                        return 'orange'
                    elif ('.x.x' in i) and ('.' in version):
                        versions_split = i.split('.x')
                        provided_versions_split = version.split('.')
                        if versions_split[0] == provided_versions_split[0]:
                            return 'orange'
      
        red_products = []
        for rname in red:
            if prod_string in rname:
                red_products.append(rname)
        # gets the shortest name that contains the name of the IBM product 
        if len(red_products) > 0:
            shortest_name = detect_shortest_string(red_products, prod_string)
            red_product_versions = [i.lower() for i in red[shortest_name]]
            if prod_string in shortest_name and version in red_product_versions:
                return "red"
            elif prod_string in shortest_name and version[:-1] + 'x' in red_product_versions:
                return 'red'
            elif prod_string in shortest_name and re.sub(r"\.[^\.]*$","",version)+ '.x' in red_product_versions:
                return "red"
            elif prod_string in shortest_name and version + '.0' in red_product_versions:
                return "red"
            elif prod_string in shortest_name and version + '.0.0' in red_product_versions:
                return "red"
            elif prod_string in shortest_name:
                for detected_version in red_product_versions:
                    if '.' in detected_version and '.' in version:
                        if version.split('.')[0:2] == detected_version.split('.')[0:2]:
                            return 'red' 
            for i in red_product_versions:
                if 'x' in i:
                    # checks if there is any numerical version
                    prod_name = i.replace('x', '[0-9]+')
                    if re.search(prod_name, version):
                        return "red"
                    elif version == i.replace('.x', ''):
                        return "red"
                    elif version + '.0.x' == i:
                        return 'red'
                    elif ('.x.x' in i) and ('.' in version):
                        versions_split = i.split('.x')
                        provided_versions_split = version.split('.')
                        if versions_split[0] == provided_versions_split[0]:
                            return 'red'
            
        green_products = []    
        for gname in green:
            if prod_string in gname:
                green_products.append(gname)
        if len(green_products) > 0:
            shortest_name = detect_shortest_string(green_products, prod_string)
            green_product_versions = [i.lower() for i in green[shortest_name]]
            if prod_string in shortest_name and version in green_product_versions:
                return "green"
            elif prod_string in shortest_name and version[:-1] + 'x' in green_product_versions:
                return 'green'
            elif prod_string in shortest_name and re.sub(r"\.[^\.]*$","",version)+ '.x' in green_product_versions:
                return "green"
            elif prod_string in shortest_name and version + '.0' in green_product_versions:
                return "green"
            elif prod_string in shortest_name:
                for detected_version in green_product_versions:
                    if '.' in detected_version and '.' in version:
                        if version.split('.')[0:2] == detected_version.split('.')[0:2]:
                            return 'green'
            for i in green_product_versions:
                if 'x' in i:
                    # checks if there is any numerical version
                    prod_name = i.replace('x', '[0-9]+')
                    if re.search(prod_name, version):
                        return "green"
                    elif version == i.replace('.x', ''):
                        return "green"
                    elif version + '.0.x' == i:
                        return 'green'
                    elif ('.x.x' in i) and ('.' in version):
                        versions_split = i.split('.x')
                        provided_versions_split = version.split('.')
                        if versions_split[0] == provided_versions_split[0]:
                            return 'green'
        return "blue" 
def detect_shortest_string(LIST,prod_string):
    if prod_string + ' Standard Edition' in LIST:
        return prod_string + ' Standard Edition'
    elif 'IBM ' + prod_string in LIST:
        return 'IBM ' +prod_string 
    best_match = 0
    loc = None
    for index, string in enumerate(LIST):
        percent_match = len(prod_string) / len(string)
        if percent_match > best_match:
            best_match = percent_match
            loc = index
    return LIST[loc]
def clean_versions(txt):
    """---------------------------------------------------------------------------------
    Description:Function used in association with graph 2 to clean the text of version annotations
    Parameters: txt (str) - a string relating to the version of IBM products
    Return: new_txt(str) - new string value stripped of punctuation from left and right sides, and limited to 4 values
    ---------------------------------------------------------------------------------"""
    items = [',','.',';',':']
    new_txt = str(txt)
    for item in items:
        new_txt = new_txt.rstrip(item).lstrip(item)

    if new_txt.count('.') > 3:
        new_txt = txt
        while new_txt[-1] != '.':
            new_txt = new_txt[:-1]#remove extra characters
        new_txt = new_txt[:-1]#remove final decimal
    elif new_txt == 'nan':
        new_txt = ' '
    return new_txt
def blank_zero(total):
    """---------------------------------------------------------------------------------
    Description:Function used in association with graphs 1 and 3 to display blank totals for values of 0
    Parameters: total (float) - a float value representing the current totals of bar plots based on legend filters
    Return: new_total(str) - new string value of graph totals where 0 is replaced with blank
    ---------------------------------------------------------------------------------"""
    new_total = ""
    temp = int(total)
    if temp != 0:
        new_total = str(temp)
    return new_total
def update_color(df):
    """---------------------------------------------------------------------------------
    Description: Cleans up the versions in the graph showing N/A
    - Any version to the right of a red version is assumed red
    - Any version to the right of an orange version is assumed orange
    - For now, it makes sense to color green anything that is not red or orange
    Parameters: df (DataFrame) - DataFrame with the version and the current color represented
    Return: df(DataFrame) - A DataFrame that has the colors updated from the logic
    ---------------------------------------------------------------------------------"""
    red_index = None
    orange_index = 0
    for index, color in enumerate(df.color):
        if color == 'orange':
            if orange_index == 0:
                orange_index = index
        if color == 'red':
            red_index = index
            break
    # if you have an orange and no red --> Set the remaining ones to orange
    if orange_index and red_index == None:
        df['color'][orange_index:] = 'orange'
    # if you have an orange and red --> Set the values between to be orange
    elif orange_index and red_index:
        df['color'][orange_index:red_index] = 'orange'
    if red_index:
        df['color'][red_index:] = 'red'  
    return df

def string_replace(summary):
#---------------------------------------------------------------------------------
#Description:Function used in association with graph 2 to clean df data
#Parameters: summary (pandas df) - df element containing columns 'Product Name' and 'Product Version'
#Return: Summary (pandas df) - clean df of user input
#---------------------------------------------------------------------------------
    nine = ['91','91942','v9942','9942','92951','88'] #strings to replace with character '9'
    for word in nine:
        summary["Product Version"]=summary["Product Version"].str.replace(word, '9')
    #strings to replace with blank character
    blank = ["other","Other","Spectrum Scale Extended Edition","Spectrum Scale Extended Support","Spectrum Scale Standard Edition",
            "C:D ","v","00","\(.*\)$","\[.*\]$", "Not Sure", "Unknown", " ", '-',':5/','[a-zA-Z]*','\([^()]*\)','\[[^()]*\]','20220430']
    for word in blank:
        summary["Product Version"]=summary["Product Version"].str.replace(word, '')
    summary["Product Version"]=summary["Product Version"].str.replace('Windows', 'Win')
    summary["Product Version"]=summary["Product Version"].str.replace('Liberty', 'Lib')
    summary["Product Version"]=summary["Product Version"].str.replace('1011010', '10')
    
    return summary

def graph_data_prep(selected_client, data, graph_num,  start_interval = None):
    from natsort import natsort_keygen
    """
    Processes data used to populate graphs used 
    
    Keyword Arguments:
    selected_client -- The name of the client selected
    data -- The dataset passed in. This should be the raw data from EPM
    graph_num -- The graph number that the data will be used for (1,2 or 3)
    start_interval -- Start interval of how far back to look for data (default None)
    
    Returns:
    client_defects_data -- DataFrame with case info describing the severity level and type of question
    
    """
    filtered_data_by_client = data[data['Global Buying Group Name'] == selected_client]
    filtered_data_by_client['Date'] = pd.to_datetime(filtered_data_by_client['Month'])
    latest_date = filtered_data_by_client['Date'].max() # the most recent date 
    # filtering based off input from the buttons
    if start_interval:
        start_date = latest_date - start_interval
        data_filtered_by_date = filtered_data_by_client[(filtered_data_by_client['Date'] <= latest_date) & (filtered_data_by_client['Date'] >= start_date)]
    else:
        data_filtered_by_date = filtered_data_by_client
    data_filtered_by_date['Initial Severity'] = data_filtered_by_date['Initial Severity'].astype(float).astype(int)

    if (graph_num == 1) or (graph_num == 3): # processes the data to be used for the 1st and 3rd graphs 
        # now can start processing data 
        tickets_by_sev =data_filtered_by_date.groupby(['Global Buying Group Name','Product Name', 'Initial Severity']).size().unstack(fill_value=0).reset_index(level=[0,1])
        present_sevs = list(tickets_by_sev.columns)[2:]

        # adding tickets together to get a total 
        tickets_by_sev['total'] = tickets_by_sev[present_sevs].sum(axis = 1)
        for column in present_sevs:
            tickets_by_sev[f'Sev{int(float(column))}'] = tickets_by_sev[column]
        present_cols = list(tickets_by_sev.columns)
        desired_cols = ['Global Buying Group Name', 'Product Name', 'total', 'Sev1', 'Sev2', 'Sev3', 'Sev4', 'Defects', 'How To']
        cols_to_drop = []
        for column_name in present_cols:
            if column_name not in desired_cols:
                cols_to_drop.append(column_name)
        if len(cols_to_drop) > 0:
            tickets_by_sev.drop(columns = cols_to_drop, inplace = True )

        # getting data on defects by product 
        defects_data = data_filtered_by_date.groupby(['Global Buying Group Name','Product Name', 'Is Defect']).size().unstack(fill_value=0).reset_index(level=[0,1])

        # merging the two DataFrames together to get complete data 
        client_defects_data = pd.merge(tickets_by_sev, defects_data,  how='left', left_on=['Global Buying Group Name','Product Name'],
                               right_on = ['Global Buying Group Name','Product Name'])
        if 1 in list(client_defects_data.columns):
            client_defects_data["Defects"]=client_defects_data[1]
        if 0 in list(defects_data.columns):
            client_defects_data["How To"]=client_defects_data[0]

        client_defects_data.rename(columns = {'Global Buying Group Name' : 'Client', 'Product' : 'Product Name'})

        sev_levels = ['Sev1', 'Sev2', 'Sev3', 'Sev4', 'Defects', 'How To']
        current_sevs = list(client_defects_data.columns)
        missing_sevs = np.setdiff1d(sev_levels, current_sevs)
        sevs_to_add = list(missing_sevs)
        for sev in sevs_to_add:
            client_defects_data[sev] = [0] * len(client_defects_data)
    
    if graph_num == 2: #processes the data needed for graph 2 
        filtered_by_date_cleaned = string_replace(data_filtered_by_date)
        filtered_by_date_sub = filtered_by_date_cleaned[["Year","Month","Case Number","Product Version","Product Name","Initial Severity","Parent Id","Is Defect","Defect Number","Customer Name","Customer Id","Global Buying Group Name","Parent Case Number"]]
        filtered_by_date_sub= filtered_by_date_sub[filtered_by_date_sub['Parent Case Number'].isnull()]
        filtered_by_date_sub['Initial Severity']=filtered_by_date_sub['Initial Severity'].astype(str).str.replace('.0', '', regex=False)
        filtered_by_date_sub.loc[filtered_by_date_sub["Product Name"].str.contains("InfoSphere Information Server"), "Product Name"] = 'IBM InfoSphere Information Server'
        filtered_by_date_sub.loc[filtered_by_date_sub["Product Name"].str.contains("Hortonworks Data Platform for IBM"), "Product Name"] = 'Hortonworks Data Platform'
        filtered_by_date_sub['color'] = filtered_by_date_sub.apply(calc_color,axis=1).tolist()#find color/support status
        
        # product name and version grouped 
        product_info_grouped = filtered_by_date_sub.groupby(['Global Buying Group Name','Product Name','Product Version']).size().reset_index(name='counts')
        
        # sort by product version 
        product_info_grouped.sort_values(['Global Buying Group Name','Product Name','Product Version'], ascending=[True,True,False], inplace=True, na_position='last', 
                    ignore_index=False, key=natsort_keygen())
        
        color = ['blue'] * len(product_info_grouped)
        product_info_grouped['c_color'] = color
        version_nums = product_info_grouped.groupby(['Global Buying Group Name','Product Name']).cumcount()+1
        product_info_grouped['version_number'] = version_nums

        product_info_grouped = product_info_grouped.rename(columns = {'Global Buying Group Name' : 'client'})
        product_info_grouped['color'] = product_info_grouped.apply(calc_color,axis=1).tolist()#find color/support status

        client_defects_data = product_info_grouped

    return client_defects_data        
#==========================================================================================================================================
#graph creation

geo_dropdown = dcc.Dropdown(options=all_data['Global Buying Group Name'].unique(),value='METLIFE')

global legend1#keep track of which items in legend are selected upon update for graph 1
legend1 = [True,True,True,True]

global legend2#keep track of which items in legend are selected upon update for graph 2
legend2 = [True,True,True,True]

global legend3#keep track of which items in legend are selected upon update for graph 2
legend3 = [True,True]

download_component = dcc.Download()

@app.callback(
    Output(component_id='graph-one', component_property='figure'),
    #Output(component_id= 'date_label', component_property= 'value'),
    Input(component_id=geo_dropdown, component_property='value'),
    Input('graph-one', 'restyleData'),#user input to detect interaction of legend
    Input('Sort-1', 'n_clicks'),
    Input('Totals-1', 'n_clicks'),
    Input('button_6months', 'n_clicks'), # buttons to represent the date range
    Input('button4_3months', 'n_clicks'),
    Input('button_1year', 'n_clicks')
)
def update_graph1(selected_client, click, sort_button, totals_button, button_6months,  button_1year, button4_3months):
    """
    returns a bar graph of product open tickets and their severity
    for selected client represented by values 1-4
    """
    #check for legend action and update global variable
    if str(click)!="None":
        num = click[1][0]
        vis = click[0]['visible'][0]
        if vis == "True":
            legend1[num] = True
        else: legend1[num] = vis

    # logic for the date buttons and filters data accordingly
    # gets all data in the specified date range
    interval_start = None
    if 'button_6months' == ctx.triggered_id:
        interval_start = timedelta(days = 182) # data for last 6 months 
    elif 'button_1year' == ctx.triggered_id:
        interval_start = timedelta(days = 365) # data for last 1 year 
    elif 'button4_3months' == ctx.triggered_id:
        interval_start = timedelta(days = 91) # data for the last 3 months 
    else:
        interval_start = None 

    # get the most recent date for the graph label 
    ##if most_recent_date.month ==  12:
      #  most_recent_month = 1
    end_date_month = calendar.month_name[most_recent_date.month]

    if (interval_start!= timedelta(days = 365)) and (interval_start != None):
        start_date = most_recent_date  - interval_start
        start_month = calendar.month_name[start_date.month ] 
        date_label = f'{start_month} {start_date.year} through {end_date_month} {most_recent_date.year}'
    else:
        earliest_month = calendar.month_name[earliest_date.month ] 
        date_label = f'{earliest_month} {earliest_date.year} through {end_date_month} {most_recent_date.year}'

    graph1_processed_data = graph_data_prep(selected_client= selected_client, data = all_data, graph_num = 1, start_interval=interval_start)

    #create custom annotations based on legend status
    first = True
    for i in range(len(legend1)):
        val = str(i+1)
        if legend1[i] == True and first == True:
            totals = graph1_processed_data["Sev" + val].fillna(0)
            first = False
        elif legend1[i] == True:
            totals = totals + graph1_processed_data["Sev"+val].fillna(0)

    #create base graph
    x= graph1_processed_data['Product Name']

    html_totals = graph1_processed_data["total"]

    fig1 = go.Figure()
    for i in range(1,5):
        fig1.add_trace(go.Bar(x=x, y=graph1_processed_data['Sev' + str(i)], name='Severity ' + str(i),text= graph1_processed_data['Sev' + str(i)],textposition='inside'))
    #graph adjustments
    fig1.update_layout(
        barmode='stack', xaxis={'categoryorder': 'category ascending'},
        height=800, width =800 + 13*len(x),
        legend=dict(yanchor="top", y=1, xanchor="left", x=0, orientation="h", traceorder='normal'),
        title={# Only appears for the HTML download
            'text': f'Tickets Opened by Severity for {selected_client} from {date_label}',
            'y':0.97,
            'x':0,
            'xanchor': 'left',
            'yanchor': 'top'})
    #html download annotations
    html_total_labels = [{"x": x, "y": total+5, "text": blank_zero(total), "showarrow": False} for x, total in zip(x, html_totals)]
    #dashboard annotations
    total_labels = []
    if first != True: total_labels = [{"x": x, "y": total+5, "text": blank_zero(total), "showarrow": False} for x, total in zip(x, totals)]

    #buttons for html download
    fig1.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                yanchor= 'bottom',
                xanchor= 'left',
                active=0,
                x=0,
                y=1,
                buttons=list([
                         dict(label="Sort",
                            method="relayout",
                            args=["xaxis", {'categoryorder':'category ascending'}],
                            args2=["xaxis", {'categoryorder':'total descending'}]),
                         dict(label="Totals",
                            method="relayout",
                            args=["annotations",html_total_labels],
                            args2=["annotations", []])])
            )
        ])
    #reset graph legend filters on reupdate
    total_visible = 0
    for i in range(len(legend1)):
        fig1.data[i].visible = legend1[i]
        if fig1.data[i].visible != True:
            total_visible += 1

    #convert to html for download
    fig1.write_html(graph_one)

    #Sort: Alternate between alphabetical and totals sort
    if sort_button % 2 == 0: fig1.update_layout(xaxis={'categoryorder': 'category ascending'})
    else: fig1.update_layout(xaxis={'categoryorder': 'total descending'})
    #Totals: Alternate between text on/off
    if totals_button % 2 == 0:fig1.update_layout(annotations=[])
    else: fig1.update_layout(annotations=total_labels)

    #hide title and buttons for dashboard view as dash versions used instead
    fig1.update_layout(title=None, updatemenus=[dict(visible = False)],legend=dict(yanchor="bottom", y=1, xanchor="left", x=0, orientation="h", traceorder='normal'),)

    return fig1

@app.callback(
    Output(component_id='graph-two', component_property='figure'),#graph to be returned and displayed in HTML
    Input(component_id=geo_dropdown, component_property='value'),#value of client selcted form dropdown
    Input('graph-two', 'restyleData'),#user input to detect interaction of legend
    Input('Versions', 'n_clicks'),#versions button and number of clicks
    Input('button_6months', 'n_clicks'), # buttons to represent the date range
    Input('button4_3months', 'n_clicks'),
    Input('button_1year', 'n_clicks')
)
def update_graph2(selected_client, click, versions_button, button_6months,  button_1year, button4_3months):
    """
    Returns a scatter plot graph of open tickets based on
    ticket count and color coordinated based on End of Support
    Status. Such that Green is in support, Yellow approaching
    EOS within 12 months, Red reached EOS and blue is unknown
    """
    #Filter data
    #filtered_clients = client_focus_list[client_focus_list['client'] == selected_client]
    #filtered_clients['Product Version'] = filtered_clients['Product Version'].apply(clean_versions)
    #filtered_clients.loc[filtered_clients["Product Name"].str.contains("InfoSphere Information Server"), "Product Name"] = 'IBM InfoSphere Information Server'
    #filtered_clients.loc[filtered_clients["Product Name"].str.contains("Hortonworks Data Platform for IBM"), "Product Name"] = 'Hortonworks Data Platform'
    #filtered_clients['color'] = filtered_clients.apply(calc_color,axis=1).tolist()#find color/support status

    """summary_new = pd.DataFrame()
    products = np.unique(filtered_clients['Product Name'])
    for product in products:
        product_df = filtered_clients[filtered_clients['Product Name'] == product]
        summary_new = pd.concat([summary_new, update_color(product_df)])
    # changes all remaining blues to green
    #summary_new.replace({'color' : {'blue' : 'green'}}, inplace = True )"""
    # *********************************************************************
    # This section was being used to imclude the missing products that are displayed in graphs 1 and 3, but not 2
    """current_products = set(summary_new['Product Name'])
    graph1_data = clients[clients['client'] == selected_client]
    graph1_products = set(graph1_data['Product Name'])
    missing_products = list(graph1_products.difference(current_products))
    if len(missing_products) > 0:
        new_data = []
        for missing_product in missing_products:
            product_info = graph1_data[graph1_data['Product Name'] == missing_product]
            product_info['total'] = product_info["Sev1"].fillna(0)+product_info["Sev2"].fillna(0)+product_info["Sev3"].fillna(0)+product_info["Sev4"].fillna(0).round(0)
            new_data.append([selected_client, missing_product, 'N/A Version', product_info['total'].iloc[0], 1, 'blue', 'blue'])
        missing_product_data = pd.DataFrame(new_data, columns = list(summary_new.columns))
        summary_new = pd.concat([summary_new, missing_product_data])

    filtered_clients = summary_new """

    interval_start = None
    if 'button_6months' == ctx.triggered_id:
        interval_start = timedelta(days = 182) # data for last 6 months 
    elif 'button_1year' == ctx.triggered_id:
        interval_start = timedelta(days = 365) # data for last 1 year 
    elif 'button4_3months' == ctx.triggered_id:
        interval_start = timedelta(days = 91) # data for the last 3 months  
    else:
        interval_start = None 

    end_date_month = calendar.month_name[most_recent_date.month]

    if (interval_start!= timedelta(days = 365)) and (interval_start != None):
        start_date = most_recent_date  - interval_start
        start_month = calendar.month_name[start_date.month ] 
        date_label = f'{start_month} {start_date.year} through {end_date_month} {most_recent_date.year}'
    else:
        earliest_month = calendar.month_name[earliest_date.month ] 
        date_label = f'{earliest_month} {earliest_date.year} through {end_date_month} {most_recent_date.year}'


    graph2_processed_data = graph_data_prep(selected_client= selected_client, data = all_data, graph_num = 2,  start_interval=interval_start)

    #seperate into traces by EOS status
    colors = {'green': 'In Support','orange':"End of Support Within 12 Months",'red': "End of Support",'blue':'N/A Version'}
    traces,prod = [],[]

    #create graph base
    fig2 = go.Figure()
    graph2_processed_data['Product Version'] = graph2_processed_data['Product Version'].apply(clean_versions)
    y = 0
    for color,eos in colors.items():
        trace = (graph2_processed_data.loc[graph2_processed_data['color'] == color].reset_index())
        y += len(trace["Product Name"])
        traces.append(trace)
        prod.append(trace["Product Name"].drop_duplicates())
        text = "Version: " + trace["Product Version"].fillna("") +"<br>Count: "+ trace["counts"].astype(str)
        temp = go.Scatter(x=trace["version_number"], y=trace["Product Name"],name=eos, text=text,mode='markers')
        fig2.add_trace(temp)

    counts = (graph2_processed_data["Product Name"].value_counts().max())
    #update graph orientation
    fig2.update_layout(
        xaxis=dict(title='Latest Product Version to Oldest',range=(0.5,counts + 0.5)),
        yaxis=dict(title='IBM Product',categoryorder='category descending',dtick=1),
        showlegend=True,
        height = 400 + 7*y,
        legend=dict(yanchor="bottom", y=1, xanchor="right", x=1, orientation="h", itemsizing='constant'),
        title = f'Open Tickets by Product Version for Summary of {selected_client} from {date_label}'
    )
    fig2.update_traces(textfont_size=10)

    #Set base color and size for scatter points
    i = 0
    for trace in traces:
        col = list(colors)[i]
        fig2.data[i].marker.color = [col] * len(traces[i])
        fig2.data[i].marker.opacity = 0.55
        s = [10] * len(trace)
        for j in range(len(s)):
            s[j] = 7 + trace['counts'][j]/graph2_processed_data['counts'].max() * 18
        fig2.data[i].marker.size = s
        i+=1

    #read user click actions
    if str(click)!="None":
        num = click[1][0]
        vis = click[0]['visible'][0]
        if vis == "True":
            legend2[num] = True
        else: legend2[num] = vis
        fig2.data[num].visible = legend2[num]
    #create specific annotations based on legend filters
    total_prod = []
    total_df = []
    for i in range(len(legend2)):
        fig2.data[i].visible = legend2[i]
        if legend2[i] != 'legendonly':
            total_prod.append(prod[i])
            total_df.append(traces[i])

    combined_prod,combined_df = pd.DataFrame(),pd.DataFrame()
    #avoid error of concat empty list
    if total_prod == []:
        total_prod = prod
        total_df = traces
        version_labels = []

    combined_prod = pd.concat(total_prod).drop_duplicates()#only show products of visble traces
    combined_df = pd.concat(total_df).drop_duplicates()#only show annotations of visible traces

    #version annotations for dashboard
    version_labels = [{"x": x, "y": y, "text": clean_versions(txt), "showarrow": False, "font": {"size":10}} for x, y, txt in zip(combined_df["version_number"], combined_df["Product Name"],combined_df["Product Version"])]
    #version annotations for html download
    html_version_labels = [{"x": x, "y": y, "text": clean_versions(txt), "showarrow": False, "font": {"size":10}} for x, y, txt in zip(graph2_processed_data["version_number"], graph2_processed_data["Product Name"],graph2_processed_data["Product Version"])]

    #buttons for html download only (turned off on dashboard)
    fig2.update_layout(
        updatemenus=[
            dict(
            type="buttons",
            buttons=[
                #This is the WIP Version ID button, shows versions that are not correct
                dict(label="Version ID",
                    method="relayout",
                    args=["annotations",[]],
                    args2=["annotations", html_version_labels]),
            ],
            direction="right",
            x=0, y=1,
            yanchor="bottom",
            xanchor="left",
            )
        ]
    )
    #convert to html for download
    fig2.write_html(graph_two)

    #update annotations for legend filters
    fig2.update_layout(yaxis=dict(title='IBM Product',categoryorder='category descending',ticklabelstep = 1,tickvals = combined_prod)),

    #if button clicked flip boolean value
    if versions_button % 2 == 0: fig2.update_layout(annotations=[])
    else: fig2.update_layout(annotations=version_labels)

    #remove title and buttons as they are replaced with dash options
    fig2.update_layout(title=None,updatemenus=[dict(visible = False)])

    return fig2
@app.callback(
    Output(component_id='graph-three', component_property='figure'),#graph shown in HTML
    Input(component_id=geo_dropdown, component_property='value'),#client dropdown selection
    Input('graph-three', 'restyleData'),#user input to detect interaction of legend
    Input('Sort-2', 'n_clicks'),#sort button and number of clicks
    Input('Totals-2', 'n_clicks'),#totals button and number of clicks
    Input('button_6months', 'n_clicks'), # buttons to represent the date range
    Input('button4_3months', 'n_clicks'),
    Input('button_1year', 'n_clicks')
)
def update_graph3(selected_client,click,sort_button,totals_button, button_6months,  button_1year, button4_3months):
    """
    Returns Bar graph of open tickets based on product count
    and categorized by Defect or How to Questions.
    """
    #check for legend action and update global variable
    if str(click)!="None":
        num = click[1][0]
        vis = click[0]['visible'][0]
        if vis == "True":
            legend3[num] = True
        else: legend3[num] = vis



    interval_start = None
    if 'button_6months' == ctx.triggered_id:
        interval_start = timedelta(days = 182) # data for last 6 months 
    elif 'button_1year' == ctx.triggered_id:
        interval_start = timedelta(days = 365) # data for last 1 year
    elif 'button4_3months' == ctx.triggered_id:
        interval_start = timedelta(days = 91) # data for the last 3 months 
    else:
        interval_start = None 
    
    end_date_month = calendar.month_name[most_recent_date.month]

    if (interval_start!= timedelta(days = 365)) and (interval_start != None):
        start_date = most_recent_date  - interval_start
        start_month = calendar.month_name[start_date.month ] 
        date_label = f'{start_month} {start_date.year} through {end_date_month} {most_recent_date.year}'
    else:
        earliest_month = calendar.month_name[earliest_date.month ] 
        date_label = f'{earliest_month} {earliest_date.year} through {end_date_month} {most_recent_date.year}'


    graph3_processed_data = graph_data_prep(selected_client= selected_client, data = all_data, graph_num = 1, start_interval=interval_start)


    #create base graph
    x=graph3_processed_data['Product Name']
    fig3 = go.Figure(go.Bar(x=x, y=graph3_processed_data['How To'], name='How To Questions',text=graph3_processed_data['How To'],textposition='inside'))
    fig3.add_trace(go.Bar(x=x, y=graph3_processed_data['Defects'], name='Defects',text=graph3_processed_data['Defects'],textposition='inside'))

    #update graph layout
    fig3.update_layout(
        barmode='stack', xaxis={'categoryorder': 'category ascending'},
        height=800,width =800 + 13*len(x),
        legend=dict(yanchor="top", y=1, xanchor="left", x=0, orientation="h"),
        title={
            'text': f'Proportion of Defects to Case Activity by Product for Summary of {selected_client} from {date_label}' ,
            'y':0.97,
            'x':0,
            'xanchor': 'left',
            'yanchor': 'top'})

    #annotations for dashboard
    graph3_processed_data["totals"]=graph3_processed_data["How To"].fillna(0)+graph3_processed_data["Defects"].fillna(0)
    #annotations for html download
    html_totals = graph3_processed_data["totals"]

    #update legend visibility based on global variale upon reupdate
    first = True
    options = ["How To","Defects"]
    for i in range(len(legend3)):
        fig3.data[i].visible = legend3[i]
        if legend3[i] == True and first == True:
            totals = graph3_processed_data[options[i]].fillna(0)
            first = False
        elif legend3[i] == True:
            totals = totals + graph3_processed_data[options[i]].fillna(0)

    #totals=filtered_clients["totals"]
    html_total_labels = [{"x": x, "y": total+5, "text": blank_zero(total), "showarrow": False} for x, total in zip(x, html_totals)]
    total_labels = []
    if first != True:total_labels = [{"x": x, "y": total+5, "text": blank_zero(total), "showarrow": False} for x, total in zip(x, totals)]

    #button only for html download
    fig3.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                yanchor= 'bottom',
                xanchor= 'left',
                active=0,
                x=0,
                y=1,
                buttons=list([
                         dict(label="Sort",
                            method="relayout",
                            args=["xaxis", {'categoryorder':'category ascending'}],
                            args2=["xaxis", {'categoryorder':'total descending'}]),
                         dict(label="Totals",
                            method="relayout",
                            args=["annotations",html_total_labels],
                            args2=["annotations", []])])
            )
        ])

    #convert graph to html for download
    fig3.write_html(graph_three)

    if sort_button % 2 == 0:
        fig3.update_layout(xaxis={'categoryorder': 'category ascending'})
    else: fig3.update_layout(xaxis={'categoryorder': 'total descending'})
    #totals: alternate between text on/off
    if totals_button % 2 == 0: fig3.update_layout(annotations=[])
    else: fig3.update_layout(annotations=total_labels)
    #remove title and buttons from html version
    fig3.update_layout(title=None,updatemenus=[dict(visible = False)],legend=dict(yanchor="bottom", y=1, xanchor="left", x=0, orientation="h"),)

    return fig3



#==========================================================================================================================================
#download button
graph_one = os.path.join(os.getcwd(), 'graph-one.html')
graph_two = os.path.join(os.getcwd(), 'graph-two.html')
graph_three = os.path.join(os.getcwd(), 'graph-three.html')


# download client data ----
@app.callback(
    Output("download-data", "data"),
    Input("download-data-button", "n_clicks"),
    Input(component_id=geo_dropdown, component_property='value'),#client dropdown selection
    prevent_initial_call=True,
)

def download_client_data(n_clicks, selected_client):
    filtered_data_by_client = all_data[all_data['Global Buying Group Name'] == selected_client]
    filtered_data_by_client['Date'] = pd.to_datetime(filtered_data_by_client['Month'])
    latest_date = filtered_data_by_client['Date'].max() # the most recent date 
    # filtering based off input from the buttons
    interval_start = None
    if 'button_6months' == ctx.triggered_id:
        interval_start = timedelta(days = 182) # data for last 6 months 
    elif 'button_1year' == ctx.triggered_id:
        interval_start = timedelta(days = 365) # data for last 1 year
    elif 'button4_3months' == ctx.triggered_id:
        interval_start = timedelta(days = 91) # data for the last 3 months 
    else:
        interval_start = None
    if 'download-data-button' == ctx.triggered_id:
        if interval_start:
            start_date = latest_date - interval_start
            data_filtered_by_date = filtered_data_by_client[(filtered_data_by_client['Date'] <= latest_date) & (filtered_data_by_client['Date'] >= start_date)]
        else:
            data_filtered_by_date = filtered_data_by_client
        cols_to_drop = ['Salesforce Record Type', 'Ticketing System', 'Origin', 'Source', 'Row Type', 'IP Partners', 'Mission Team Group', 'Is Blue Diamond', 
                        'Is CritSit', 'Dv Parent', 'Is Screened (BAIW)', 'Is Eligible (BAIW)', 'Is Cancelled (BAIW)', 'Skill Case Sort Key']
        data_filtered_by_date.drop(columns = cols_to_drop, inplace = True)
        return dcc.send_data_frame(data_filtered_by_date.to_csv, f'{selected_client}_data.csv')

# download the html report 

@app.callback(
    Output("download-html", "data"),
    Input("download-button", "n_clicks"),
    #Input(component_id=geo_dropdown, component_property='value'),#client dropdown selection
    prevent_initial_call=True,
)

def get_download_file(n_clicks):
    """
    Prepares the final html for download. All the graphs are
    written to the file system. After the final HTML is ready
    for download, this function will also clean up those temp htmls
    for each graph.

    Sends the final HTML as bytes with dcc.send_bytes.
    """
    global html_bytes
    if os.path.exists(graph_one) and os.path.exists(graph_two) and os.path.exists(graph_three):
        with open(graph_one,'rb') as p:
            graph_one_html = (p.readlines())
        # delete the html written to temp locations.
        os.remove(graph_one)

        with open(graph_two, 'rb') as p:
            graph_two_html = (p.readlines())
        # delete the html written to temp locations.
        os.remove(graph_two)

        with open(graph_three, 'rb')as p:
            graph_three_html = (p.readlines())
        # delete the html written to temp locations.
        os.remove(graph_three)

        # Convert the saved htmls into bytes type to be endoded.
        if graph_one_html and graph_two_html and graph_three_html:
            html_bytes = graph_one_html + graph_two_html + graph_three_html
            html_bytes = b''.join(html_bytes)
    return dcc.send_bytes(html_bytes, "Ticket-Analysis-Report-.html")

#==========================================================================================================================================
#grab client names for titles
@app.callback(
    Output('title1', 'children'),
    Output('title2', 'children'),
    Output('title3', 'children'),
    Input(component_id=geo_dropdown, component_property='value')
    #Input(component_id= 'date_range', component_property= 'value' )
)
def update_output(selected_client):
    """
    Returns strings of graph titles dependent on dropdown value.
    Used in HTML layout
    """
    title1 = 'Open Tickets by Product Version for Summary of ' + selected_client
    title2 = 'Open Tickets by Product Version for Summary of ' + selected_client
    title3 = 'Proportion of Defects to Case Activity by Product for Summary of ' + selected_client
    return title1, title2, title3

#==========================================================================================================================================
#HTML Layout

FA_icon = html.I(className="fa-solid fa-cloud-arrow-down me-2")
subtitle = 'Data from March 2022 through June 2023'
disclaimer = 'Disclaimer: Products without version information may appear in graphs 1 and 3, but not graph 2'
app.layout = html.Div([
    html.Div(id = "page-content"),
    dcc.Interval(id = "auth-check-interval", interval = 3600 * 1000)
])

# All of your Dash UI components go in this function.
# Your dashboard users are not able to view those UI components unless
# they are authenticated and authorized.
@app.callback(Output("page-content", "children"),
              Input("auth-check-interval", "n_intervals"))
@auth.check
def layout_components(n):
    # For example, the following function returns Dropdown and Div UI components that display information about
    # the Flask and Dash frameworks.
    return [
    # All elements from the top of the page
     html.Div([
        html.Div([
            html.H1(children='Ticket Analysis by Client'),
#            html.H2(children='Number of Tickets by Product and Severity')
        ], className='six columns'),

    ], className='row'),
    # Div elements for each graph -- Each corresponds to one graph 
    html.Div([
        html.Div([
            geo_dropdown,
            html.Br(),
            dbc.Button([FA_icon, "Download Report"], color="info", className=("m-1"), outline=True, id = 'download-button'),
            dcc.Download(id="download-html"),
            dbc.Button([FA_icon, "Download Client Data"], color="info", className=("m-1"), outline=True, id = 'download-data-button', n_clicks= 0 ),
            dcc.Download(id="download-data"),
            html.Br(),html.Br(),
            html.H3(id='title1'),
            dbc.Button('3 Months', id = 'button4_3months', n_clicks = 0, color = 'primary', outline = True),
            dbc.Button('6 Months', id = 'button_6months', n_clicks = 0, color = 'primary',  outline = True),
            dbc.Button('1 Year', id = 'button_1year', n_clicks = 0, color = 'primary', outline = True),
            dbc.Button('Sort', color="success", className=("m-1"), outline=True, id='Sort-1', n_clicks=0),
            dbc.Button('Totals', color="success", className=("m-1"), outline=True, id='Totals-1', n_clicks=0),
            dcc.Graph(id='graph-one', style={'overflowX': 'scroll'}),

        ], className='six columns'),

    ], className='row'),

    # New Div for all elements in the new 'row' of the page
    html.Div([
        html.Div([
                html.Br(),
                html.H3(id='title2'),
                html.H5(disclaimer),
                dbc.Button('Version ID', color="success", className=("m-1"), outline=True, id='Versions', n_clicks=0),
                dbc.Button('3 Months', id = 'button4_3months', n_clicks = 0, color = 'primary', outline = True),
                dbc.Button('6 Months', id = 'button_6months', n_clicks = 0, className = ('m-1'), color = 'success', outline = True),
                dbc.Button('1 Year', id = 'button_1year', n_clicks = 0, className = ('m-1'), color = 'success', outline = True),
                dcc.Graph(id='graph-two'),
        ], className='six columns'),
    ], className='row'),

    # New Div for all elements in the new 'row' of the page
    html.Div([
        html.Div([
                html.H3(id='title3'),
                dbc.Button('Sort', color="success", className=("m-1"), outline=True, id='Sort-2', n_clicks=0),
                dbc.Button('Totals', color="success", className=("m-1"), outline=True, id='Totals-2', n_clicks=0),
                dbc.Button('3 Months', id = 'button4_3months', n_clicks = 0, color = 'primary', outline = True),
                dbc.Button('6 Months', id = 'button_6months', n_clicks = 0, className = ('m-1'), color = 'success', outline = True),
                dbc.Button('1 Year', id = 'button_1year', n_clicks = 0, className = ('m-1'), color = 'success', outline = True),
                dcc.Graph(id='graph-three'),

        ], className='six columns'),
    ], className='row'),
    ]




if __name__ == "__main__":
    app.run_server(host = "0.0.0.0")

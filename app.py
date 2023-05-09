#Import Libraries
import dash
from dash import Dash, html, Input, Output, ctx,dcc
from dash.dependencies import Output, Input

import dash_bootstrap_components as dbc

import plotly
import plotly.graph_objects as go

import jupyter_dash as jd

import pandas as pd
pd.options.mode.chained_assignment = None
pd.options.display.max_columns = None

import numpy as np
import re

from datetime import date
date_today = date.today().strftime("%m/%d/%Y")

import os
cwd = os.getcwd()

import json

from auth_dash import AppIDAuthProviderDash

import ibm_boto3
from ibm_botocore.client import Config, ClientError


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
# getting the contents of the file from the COS
client_data = get_item('oidash-app','client_focus_list.csv')
client_data = client_data['Body'].read()
# writing to a csv and then loading into a pandas DataFrame
with open('client_focus_list.csv','wb') as file:
    file.write(client_data)
client_focus_list = pd.read_csv('client_focus_list.csv')

client_defects = get_item('oidash-app','clients_defects.csv')
client_defects_data = client_defects['Body'].read()
with open('clients_defects.csv','wb') as file:
    file.write(client_defects_data)
clients = pd.read_csv('clients_defects.csv')
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



clients["Product name"]=clients["Product Name"]
clients["Product"]=clients["Product Name"]
clients["client"]=clients["Client"]

DASH_URL_BASE_PATHNAME = "/dashboard/"

auth = AppIDAuthProviderDash(DASH_URL_BASE_PATHNAME)
app = dash.Dash(__name__, server = auth.flask, url_base_pathname = DASH_URL_BASE_PATHNAME, external_stylesheets=[dbc.themes.MINTY, dbc.icons.FONT_AWESOME])
#==========================================================================================================================================
#Import Dictionaries

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


#==========================================================================================================================================
#Functions

def calc_color(x):
    """---------------------------------------------------------------------------------
    Description:Function used in association with graph 2 to calculate scatter plot colors based on EOS status
    Parameters: x (Pandas Series) - df element containing columns 'Product Name' and 'Product Version'
    Return: (string) - color associated with product version EOS status
    Comments: Uses dictionaries 'red' and 'orange' to determine colors based on EOS status
    ---------------------------------------------------------------------------------"""
    prod_string=x["Product Name"]
    version=str(x['Product Version'])
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
            shortest_name = min(orange_products)
            if prod_string in shortest_name and version in orange[shortest_name]:#if string contains a product
                return "orange"
            elif prod_string in shortest_name and version[:-1] + 'x' in orange[shortest_name]:
                return "orange"    
            elif prod_string in shortest_name and re.sub(r"\.[^\.]*$","",version)+ '.x' in orange[shortest_name]:
                return "orange"    
        red_products = []
        for rname in red:
            if prod_string in rname:
                red_products.append(rname)
        # gets the shortest name that contains the name of the IBM product 
        if len(red_products) > 0:
            shortest_name = min(red_products)
            if prod_string in shortest_name and version in str(red[shortest_name]):
                return "red"
            elif prod_string in shortest_name and re.sub(r"\.[^\.]*$","",version)+ '.x' in red[shortest_name]:
                return "red"
        green_products = []    
        for gname in green:
            if prod_string in gname:
                green_products.append(gname)
        if len(green_products) > 0:
            shortest_name = min(green_products)
            if prod_string in gname and version in green[shortest_name]:
                return "green"
            elif prod_string in gname and re.sub(r"\.[^\.]*$","",version)+ '.x' in green[shortest_name]:
                return "green"    

        return "blue"  

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
#==========================================================================================================================================
#graph creation

geo_dropdown = dcc.Dropdown(options=clients['client'].unique(),value='METLIFE')

global legend1#keep track of which items in legend are selected upon update for graph 1
legend1 = [True,True,True,True]

global legend2#keep track of which items in legend are selected upon update for graph 2
legend2 = [True,True,True,True]

global legend3#keep track of which items in legend are selected upon update for graph 2
legend3 = [True,True]


@app.callback(
    Output(component_id='graph-one', component_property='figure'),
    Input(component_id=geo_dropdown, component_property='value'),
    Input('graph-one', 'restyleData'),#user input to detect interaction of legend
    Input('Sort-1', 'n_clicks'),
    Input('Totals-1', 'n_clicks')
)
def update_graph1(selected_client, click, sort_button, totals_button):
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

    #filter client data by dropdown
    filtered_clients = clients[clients['client'] == selected_client]
    filtered_clients["Sev"] = filtered_clients["Sev1"].astype(str)
    filtered_clients["totals"]=filtered_clients["Sev1"].fillna(0)+filtered_clients["Sev2"].fillna(0)+filtered_clients["Sev3"].fillna(0)+filtered_clients["Sev4"].fillna(0).round(0)
    html_totals = filtered_clients["totals"]

    #create custom annotations based on legend status
    first = True
    for i in range(len(legend1)):
        val = str(i+1)
        if legend1[i] == True and first == True:
            totals = filtered_clients["Sev" + val].fillna(0)
            first = False
        elif legend1[i] == True:
            totals = totals + filtered_clients["Sev"+val].fillna(0)

    #create base graph
    x=filtered_clients['Product']

    fig1 = go.Figure()
    for i in range(1,5):
        fig1.add_trace(go.Bar(x=x, y=filtered_clients['Sev' + str(i)], name='Severity ' + str(i),text=filtered_clients['Sev' + str(i)],textposition='inside'))
    #graph adjustments
    fig1.update_layout(
        barmode='stack', xaxis={'categoryorder': 'category ascending'},
        height=800, width =800 + 13*len(x),
        legend=dict(yanchor="top", y=1, xanchor="left", x=0, orientation="h", traceorder='normal'),
        title={#only for html download
            'text': 'Open Tickets by Severity for Summary of ' + selected_client,
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
    Input(component_id=geo_dropdown, component_property='value'),#velaue of client selcted form dropdown
    Input('graph-two', 'restyleData'),#user input to detect interaction of legend
    Input('Versions', 'n_clicks'),#versions button and number of clicks
)
def update_graph2(selected_client, click, versions_button):
    """
    Returns a scatter plot graph of open tickets based on
    ticket count and color coordinated based on End of Support
    Status. Such that Green is in support, Yellow approaching
    EOS within 12 months, Red reached EOS and blue is unknown
    """
    #Filter data
    filtered_clients = client_focus_list[client_focus_list['client'] == selected_client]
    filtered_clients['color'] = filtered_clients.apply(calc_color,axis=1).tolist()#find color/support status

    summary_new = pd.DataFrame()
    products = np.unique(filtered_clients['Product Name'])
    for product in products:
        product_df = filtered_clients[filtered_clients['Product Name'] == product]
        summary_new = summary_new.append(update_color(product_df))
    # changes all remaining blues to green
    summary_new.replace({'color' : {'blue' : 'green'}}, inplace = True )
    filtered_clients = summary_new

    #seperate into traces by EOS status
    colors = {'green': 'In Support','orange':"End of Support Within 12 Months",'red': "End of Support",'blue':'N/A Version'}
    traces,prod = [],[]

    #create graph base
    fig2 = go.Figure()
    filtered_clients['Product Version'] = filtered_clients['Product Version'].apply(clean_versions)
    y = 0
    for color,eos in colors.items():
        trace = (filtered_clients.loc[filtered_clients['color'] == color].reset_index())
        y += len(trace["Product Name"])
        traces.append(trace)
        prod.append(trace["Product Name"].drop_duplicates())
        text = "Version: " + trace["Product Version"].fillna("") +"<br>Count: "+ trace["counts"].astype(str)
        temp = go.Scatter(x=trace["version_number"], y=trace["Product Name"],name=eos, text=text,mode='markers')
        fig2.add_trace(temp)

    counts = (filtered_clients["Product Name"].value_counts().max())
    #update graph orientation
    fig2.update_layout(
        xaxis=dict(title='Latest Product Version to Oldest',range=(0.5,counts + 0.5)),
        yaxis=dict(title='IBM Product',categoryorder='category descending',dtick=1),
        showlegend=True,
        height = 400 + 7*y,
        legend=dict(yanchor="bottom", y=1, xanchor="right", x=1, orientation="h", itemsizing='constant'),
        title = 'Open Tickets by Product Version for Summary of ' + selected_client
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
            s[j] = 7 + trace['counts'][j]/filtered_clients['counts'].max() * 18
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
    html_version_labels = [{"x": x, "y": y, "text": clean_versions(txt), "showarrow": False, "font": {"size":10}} for x, y, txt in zip(filtered_clients["version_number"], filtered_clients["Product Name"],filtered_clients["Product Version"])]

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
    Input('Totals-2', 'n_clicks')#totals button and number of clicks
)
def update_graph3(selected_client,click,sort_button,totals_button):
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

    #filter date based on dropdown selection
    filtered_clients = clients[clients['client'] == selected_client]

    #create base graph
    x=filtered_clients['Product']
    fig3 = go.Figure(go.Bar(x=x, y=filtered_clients['How To'], name='How To Questions',text=filtered_clients['How To'],textposition='inside'))
    fig3.add_trace(go.Bar(x=x, y=filtered_clients['Defects'], name='Defects',text=filtered_clients['Defects'],textposition='inside'))

    #update graph layout
    fig3.update_layout(
        barmode='stack', xaxis={'categoryorder': 'category ascending'},
        height=800,width =800 + 13*len(x),
        legend=dict(yanchor="top", y=1, xanchor="left", x=0, orientation="h"),
        title={
            'text': 'Proportion of Defects to Case Activity by Product for Summary of ' + selected_client,
            'y':0.97,
            'x':0,
            'xanchor': 'left',
            'yanchor': 'top'})

    #annotations for dashboard
    filtered_clients["totals"]=filtered_clients["How To"].fillna(0)+filtered_clients["Defects"].fillna(0)
    #annotations for html download
    html_totals = filtered_clients["totals"]

    #update legend visibility based on global variale upon reupdate
    first = True
    options = ["How To","Defects"]
    for i in range(len(legend3)):
        fig3.data[i].visible = legend3[i]
        if legend3[i] == True and first == True:
            totals = filtered_clients[options[i]].fillna(0)
            first = False
        elif legend3[i] == True:
            totals = totals + filtered_clients[options[i]].fillna(0)

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
    return dcc.send_bytes(html_bytes, "Ticket-Analysis-Report.html")

#==========================================================================================================================================
#grab client names for titles
@app.callback(
    Output('title1', 'children'),
    Output('title2', 'children'),
    Output('title3', 'children'),
    Input(component_id=geo_dropdown, component_property='value'),
)
def update_output(selected_client):
    """
    Returns strings of graph titles dependent on dropdown value.
    Used in HTML layout
    """
    title1 = 'Open Tickets by Severity for Summary of ' + selected_client
    title2 = 'Open Tickets by Product Version for Summary of ' + selected_client
    title3 = 'Proportion of Defects to Case Activity by Product for Summary of ' + selected_client
    return title1, title2, title3

#==========================================================================================================================================
#HTML Layout

FA_icon = html.I(className="fa-solid fa-cloud-arrow-down me-2")
subtitle = 'Past 12 Months as of ' + date_today

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
    # New Div for all elements in the new 'row' of the page
    html.Div([
        html.Div([
            geo_dropdown,
            html.Br(),
            dbc.Button([FA_icon, "Download Report"], color="info", className=("m-1"), outline=True, id = 'download-button'),
            dcc.Download(id="download-html"),
            html.Br(),html.Br(),
            html.H3(id='title1'),
            html.H5(subtitle),
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
                html.H5(subtitle),
                dbc.Button('Version ID', color="success", className=("m-1"), outline=True, id='Versions', n_clicks=0),
                dcc.Graph(id='graph-two'),
        ], className='six columns'),
    ], className='row'),

    # New Div for all elements in the new 'row' of the page
    html.Div([
        html.Div([
                html.H3(id='title3'),
                html.H5(subtitle),
                dbc.Button('Sort', color="success", className=("m-1"), outline=True, id='Sort-2', n_clicks=0),
                dbc.Button('Totals', color="success", className=("m-1"), outline=True, id='Totals-2', n_clicks=0),
                dcc.Graph(id='graph-three'),

        ], className='six columns'),
    ], className='row'),
    ]

if __name__ == "__main__":
    app.run_server(host = "0.0.0.0")

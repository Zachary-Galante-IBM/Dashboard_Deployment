import dash
from dash import html, dcc
from dash.dependencies import Output, Input

from urllib.parse import parse_qs, unquote
from datetime import date
today = date.today()
date_today = today.strftime("%m/%d/%Y")
import plotly
import plotly.express as px
import plotly.graph_objects as go
from dash import callback_context
import jupyter_dash as jd
from jupyter_dash import JupyterDash
import dash_bootstrap_components as dbc
from dash.dependencies import State, ALL, ALLSMALLER, MATCH
from dash.exceptions import PreventUpdate
from dash import dash_table
import pandas as pd
import numpy as np

from auth_dash import AppIDAuthProviderDash

pd.options.display.max_columns = None

for p in [plotly, dash, jd, dcc, html, dbc, pd, np]:
    print(f'{p.__name__:-<30}v{p.__version__}')

clients=pd.read_excel('clients_defects.xlsx')
clients["Product name"]=clients["Product"]
clients["client"]=clients["Client"]

client_focus_list=pd.read_csv('client_focus_list.csv')

DASH_URL_BASE_PATHNAME = "/dashboard/"

auth = AppIDAuthProviderDash(DASH_URL_BASE_PATHNAME)
app = dash.Dash(__name__, server = auth.flask, url_base_pathname = DASH_URL_BASE_PATHNAME)

#==========================================================================================================================================
#Dictionaries
#==========================================================================================================================================
red = {
#---------------------------------------------------------------------------------
#products and related versions that have reached end of support
#---------------------------------------------------------------------------------
    "QRadar":["7.3.2"],
    "WebSphere Application Server":["8.0.","7.0."],
    "Hortonworks Data Platform for IBM":["3.1.5", "3.1.4", "3.1.0", "3.0.0", "2.6.5", "2.6.2", "2.6.1"],
    "Guardium Data Protection":["11.2", "11.1", "11.0"],
    "MQ":["9.0", "8.1", "8.0", "7.5", "6.0"],
    "IBM i":["7.2"],
    'Sterling B2B Integrator':["5.2.6","4.7","4,8","6.1"],
    'Sterling Transformation Extender':["10.0.0","10.0.1","10.1.1","9.0.0"],
    "AIX":["7.1","6.1"],
    'Security Verify Access':[".9.0.7"],
    "Engineering Workflow Management": ["6.0.6"],
    'DB2 Analytics Accelerator for z/OS':["7.1.","7.1.0"],
    "Cognos Analytics":["11.0.13","10.2.2"],
    "API Connect":["5.0.","4.1."],
    "App Connect Enterprise":["10.0.0.","9.0.0","8.0.0"],
    "Big SQL":["5.0.4.0"],
    "Cloudera Data Platform Private Cloud":["7.1.1","7.1.3"],
    "DataPower":["5.0.","4.1"],
    'Db2 Linux, Unix and Windows':["10.5","10.1","9.7","9.5"],
    'Hardware Management Console Application':["V9","9"],
    "FileNet Content Manager":["3.0.1","5.2.1.0","5.2.1.1"],
    "FileNet Rendition Engine" :["5.2.0"],
    "MQ":["7.5","9.0","8.1","8.0","6.0"],
    "MQ for z/OS":["9.1 LTS"],
    "PureData Analytics Systems": ["510"],
    "PowerVC": [],
    "Spectrum Scale":["4.2","5.0.2","5.0.4"],
    "SPSS Modeler": ["18.0.0.0","18.1.0.0","18.2.2.0"],
    "Sterling B2B Integrator": ["5.2.6"],
    "Sterling Connect Direct": ["Sterling Connect Direct: Win 4.7"],
    "Sterling Transformation Extender":["9.0.0"],
    "Tivoli Network Manager":["4.2.0.13","3.8.0.2","1.6.4"],
    "Z System Automation":["4.1.0"],
    "z/OS":["2.3.0","2.2.0","1.1"],
    "IBM i": ["7.2"],
    "AIX":["7.1"],
    "FileNet Content Manager":["3.0.1","5.2.1.0","5.2.1.1"]
}
#==========================================================================================================================================
orange = {
#---------------------------------------------------------------------------------
#products and related versions that are approaching end of support within 12 months
#---------------------------------------------------------------------------------
    "Sterling Connect Direct": ["Win 4.8"], 
    "Sterling Transformation Extender": ["10.0.0","10.0.1","10.1.1"],
    'QRadar': ["7.4.0","7.4.1","7.4.2","7.4.3"],
    "Tivoli OMEGAMON XE for Db2 Performance Expert":["5.4"],
    "Tivoli OMEGAMON XE for Db2 Performance Monitor":["5.4"]}

#==========================================================================================================================================
#Functions
#==========================================================================================================================================
def calc_color(x):
#---------------------------------------------------------------------------------
#Description:Function used in association with graph 2 to calculate scatter plot colors based on EOS status
#Parameters: x (Pandas Series) - df element containing columns 'Product Name' and 'Product Version'
#Return: (string) - color associated with product version EOS status
#Comments: Uses dictionaries 'red' and 'orange' to determine colors based on EOS status
#---------------------------------------------------------------------------------
    prod_string=x["Product Name"]
    version=str(x['Product Version'])
    if prod_string in red and version in red[prod_string]:#if product in red and version in red
        return "red"
    elif prod_string in orange and version in orange[prod_string]:#if product in orange and version in orange
        return "orange"
    elif version == None or version == " " or version == "" or version == "NaN" or version == "nan":
        return "grey"
    else:#if exact product name not found, check if products exist in string
        for oname in orange:#check every item from orange
            if oname in prod_string and version in orange[oname]:#if string contains a product
                return "orange"
        for rname in red:
            if rname in prod_string and version in red[rname]:
                return "red"
        
        return "green"

app.layout = html.Div([
    html.Div(id = "page-content"),
    dcc.Interval(id = "auth-check-interval", interval = 3600 * 1000)
])

geo_dropdown = dcc.Dropdown(options=clients['client'].unique(),
                            value='Metlife')

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
            html.Button('Download Report',id = 'download-button'),
            dcc.Download(id="download-graphs-html"),
            html.Br(),
            
            dcc.Graph(id='price-graph', style={'overflowX': 'scroll'}),
            
        ], className='six columns'),

    ], className='row'),
    


    # New Div for all elements in the new 'row' of the page
    html.Div([
            dcc.Graph(id='graph-two'),
        
    ], className='row'),
    
    
    # New Div for all elements in the new 'row' of the page
    html.Div([
            dcc.Graph(id='graph-three'),
        
    ], className='row'),
    ]

@app.callback(
    Output(component_id='price-graph', component_property='figure'),
    Input(component_id=geo_dropdown, component_property='value')
)
def update_graph(selected_client):
    filtered_clients = clients[clients['client'] == selected_client]
    filtered_clients["Sev"] = filtered_clients["Sev1"].astype(str)

#    line_fig = px.bar(filtered_clients,
#                       x='Product name', y='Tickets',height=600,
#                       color='Sev', text='Tickets',
#                       title=f'Open Tickets by Severity for {selected_client}')

    filtered_clients["totals"]=filtered_clients["Sev1"].fillna(0)+filtered_clients["Sev2"].fillna(0)+filtered_clients["Sev3"].fillna(0)+filtered_clients["Sev4"].fillna(0)
    filtered_clients["totals"]=filtered_clients["totals"].round(0)
    totals=filtered_clients["totals"]

    x=filtered_clients['Product']
    fig1=go.Figure(go.Bar(x=x, y=filtered_clients['Sev1'], name='Severity 1',text=filtered_clients['Sev1'],textposition='inside'))
    fig1.add_trace(go.Bar(x=x, y=filtered_clients['Sev2'], name='Severity 2',text=filtered_clients['Sev2'],textposition='inside'))
    fig1.add_trace(go.Bar(x=x, y=filtered_clients['Sev3'], name='Severity 3',text=filtered_clients['Sev3'],textposition='inside'))
    fig1.add_trace(go.Bar(x=x, y=filtered_clients['Sev4'], name='Severity 4',text=filtered_clients['Sev4'],textposition='inside'))

    fig1.update_layout(
        title='Open Tickets by Severity for Summary of ' + selected_client + '<br><sup>Past 12 Months as of ' + date_today,
        barmode='stack', xaxis={'categoryorder': 'category descending'},
        height=800,
        title_x = 0.03,
        title_y = 0.96,
        legend=dict(yanchor="top", y=1.1, xanchor="right", x=0.2, orientation="h"))
    
    total_labels = [{"x": x, "y": total+5, "text": int(total), "showarrow": False} for x, total in zip(x, totals)]
        
    fig1.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                active=0,
                x=0.042,
                y=1.12,
                buttons=list([                
                     dict(label="Sort",
                        method="relayout",
                        args=["xaxis", {'categoryorder':'total descending'}],
                        args2=["xaxis", {'categoryorder':'category ascending'}]),
                     dict(label="Totals",
                        method="relayout",
                        args=["annotations",total_labels],
                        args2=["annotations", []])     
                ]),
            )
        ])
    fig1.layout.width= 2800
   
    return fig1

@app.callback(
    Output(component_id='graph-two', component_property='figure'),
    Input(component_id=geo_dropdown, component_property='value')
)
def update_graph(selected_client):
    filtered_clients = client_focus_list[client_focus_list['client'] == selected_client]

    c = filtered_clients.apply(calc_color,axis=1).tolist()
    filtered_clients['color'] = c

    red = filtered_clients.loc[filtered_clients['color'] == 'red'].reset_index()
    green = filtered_clients.loc[filtered_clients['color'] == 'green'].reset_index()
    orange = filtered_clients.loc[filtered_clients['color'] == 'orange'].reset_index()
    grey = filtered_clients.loc[filtered_clients['color'] == 'grey'].reset_index()
    traces = [green,orange,red,grey]
    text = []
    for trace in traces:
        text.append("Version: " + trace["Product Version"].fillna("") +"<br>Count: "+ trace["counts"].astype(str))   
    #UPDATE LAYOUT
   
 #   line_fig = px.scatter(filtered_clients, x="version_number", y="Product Name",
 #       size="counts", color="Product Name", text="Product Version",    height=800,
 #       hover_name="name version")
    
    line_fig = go.FigureWidget([go.Scatter(x=green["version_number"], y=green["Product Name"],name='In Support', text=text[0],mode='markers')])
    line_fig.add_trace(go.Scatter(x=orange["version_number"], y=orange["Product Name"],name='End of Support Within 12 Months',text=text[1],mode='markers'))
    line_fig.add_trace(go.Scatter(x=red["version_number"], y=red["Product Name"],name='End of Support',text=text[2],mode='markers'))
    line_fig.add_trace(go.Scatter(x=grey["version_number"], y=grey["Product Name"],name='NA Version',text=text[3],mode='markers'))
    
    
    count = (filtered_clients["Product Name"].value_counts().max())
    line_fig.update_xaxes(range=(0.5,count + 0.5))#lengthen graph xaxis to fit max product count
    line_fig.layout.hovermode = 'closest'
    
    counts = (filtered_clients["Product Name"].value_counts().max())
 #   line_fig.update_xaxes(range=(0.5,counts + 0.5))#lengthen graph xaxis to fit max product count
    line_fig.layout.hovermode = 'closest'
    
    def strip_text(txt):
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
    
    version_labels = [{"x": x, "y": y, "text": strip_text(txt), "showarrow": False, "font": {"size":10}} for x, y, txt in zip(filtered_clients["version_number"], filtered_clients["Product Name"],filtered_clients["Product Version"])]
    
    line_fig.update_layout(
        updatemenus=[
            dict(
            type="buttons",
            buttons=[
                #This is the WIP Version ID button, shows versions that are not correct   
                dict(label="Version ID",
                    method="relayout",
                    args=["annotations",[]],
                    args2=["annotations", version_labels]),
            ],
            direction="right",
            x=1, y=1.1,
            )
        ]
    )
    line_fig.update_layout(
    #Slightly changed titles to be easier to read graph (not final)
        #title='Open Tickets by Product Version for Metlife Summary of Past 12 Months as of '+ date_today,
        xaxis=dict(title='Latest Product Version to Oldest'),
        yaxis=dict(title='IBM Product',categoryorder='category descending',dtick=1),
        showlegend=True,
        height = 1400,
        legend=dict(yanchor="top", y=1.05, xanchor="right", x=1, orientation="h"),
        title='Open Tickets by Product Version for Summary of ' + selected_client + '<br><sup>Past 12 Months as of ' + date_today,
        title_x = 0.09,
    )
    line_fig.update_traces(textfont_size=10)
    
    #Set base color and size for scatter points
    #================================================================================================================
    for i in range(4):
        col = ''
        if i == 0: col = 'green'
        elif i == 1: col = 'orange'
        elif i == 2: col = 'red'
        else: col = 'grey'
        line_fig.data[i].marker.color = [col] * len(traces[i])
        line_fig.data[i].marker.opacity = 0.5
        
    #print(len(fig2.data[0]))
    i = 0
    max_count = (filtered_clients['counts'].max())
    for trace in traces:
        scatter = line_fig.data[i]
        s = [10] * len(trace)
        for j in range(len(s)):
            s[j] = 7 + trace['counts'][j]/max_count * 18
        line_fig.data[i].marker.size = s
        i+=1
    
        # create our callback function
    #================================================================================================================
    def update_point_g2(trace, points, selector):
        c = list(trace.marker.color)
        s = list(trace.marker.size)
        for i in points.point_inds:
            c[i] = 'blue'
            s[i] = 20
            with line_fig.batch_update():
                trace.marker.color = c
                
    line_fig.data[0].on_click(update_point_g2)
    line_fig.data[1].on_click(update_point_g2)
    line_fig.data[2].on_click(update_point_g2)

    return line_fig

@app.callback(
    Output(component_id='graph-three', component_property='figure'),
    Input(component_id=geo_dropdown, component_property='value')
)
def update_graph(selected_client):
    filtered_clients = clients[clients['client'] == selected_client]

    x=filtered_clients['Product']
    line_fig = go.Figure(go.Bar(x=x, y=filtered_clients['How To'], name='How To Questions',text=filtered_clients['How To'],textposition='inside'))
    line_fig.add_trace(go.Bar(x=x, y=filtered_clients['Defects'], name='Defects',text=filtered_clients['Defects'],textposition='inside'))

    #UPDATE LAYOUT
    line_fig.update_layout(
        title='Proportion of Defects to Case Activity by Product for Summary of ' + selected_client + '<br><sup>Past 12 Months as of ' + date_today,
        title_x = 0.03,title_y=0.96,
        barmode='stack', xaxis={'categoryorder': 'category descending'},
#        annotations=total_labels,
        height=800,
        legend=dict(yanchor="top", y=1.1, xanchor="right", x=0.13, orientation="h"))
    filtered_clients["totals"]=filtered_clients["Sev1"].fillna(0)+filtered_clients["Sev2"].fillna(0)+filtered_clients["Sev3"].fillna(0)+filtered_clients["Sev4"].fillna(0)
    filtered_clients["totals"]=filtered_clients["totals"].round(0)
    totals=filtered_clients["totals"]
    total_labels = [{"x": x, "y": total+5, "text": int(total), "showarrow": False} for x, total in zip(x, totals)]    
    line_fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                active=0,
                x=0.042,
                y=1.12,
                buttons=list([
                     dict(label="Sort",
                        method="relayout",
                        args=["xaxis", {'categoryorder':'total descending'}],
                        args2=["xaxis", {'categoryorder':'category ascending'}]),
                     dict(label="Totals",
                        method="relayout",
                        args=["annotations",total_labels],
                        args2=["annotations", []]),
                ]),
            )
        ])
    
    
#    line_fig = px.bar(filtered_clients,
#                       x='Product name', y='Tickets',height=700,
#                       color='Sev', text='Tickets',
#                       title=f'Proportion of Defects to Case Activity by Product for {selected_client}')
    
    line_fig.layout.width= 2800
    return line_fig

if __name__ == "__main__":
    app.run_server(host = "0.0.0.0")

import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash

import plotly
import dash_table
from dash.dependencies import Input, Output, State

import pandas as pd
import numpy as np

import datetime
import operator
import os

import base64
import io

import chart_studio.plotly as py
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
pio.templates.default = "plotly_white"

app = dash.Dash()
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
application = app.server

app.layout = html.Div([

                html.Div([
                    html.H1(children='Control Chart Generator',style={'textAlign': 'center'}),
                    
                    html.Div(children='Data Charting Tool for CSV Files'
                             ', Data aggregation (H-Hour, D-Day, W-Week, M-Month, Q-Quarter, Y-Year), Example 4H = Every 4 Hours',
                             style={'textAlign': 'center','vertical-align': 'top'}),
                        
                    html.H3("Upload Files"),
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files')
                        ]),
                        style={
                            'width': '95%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px',

                        },
                        multiple=False),
                
                    html.Div([
                        
                        html.Div([
                            html.Label('Select Data to Graph'),
                            dcc.Dropdown(id='y-data',
                                        multi = False,
                                        placeholder='Filter Column'),
                            
                            html.Label('Select Date Range for Graph',style={'display':'table-cell'}),
                            dcc.DatePickerRange(
                                id='date',
                                style={'font-family':'Trebuchet MS, sans-serif','font-size':'small'}
                            ),
                            
                        ],
                        style={'width':'25%','display': 'inline-block','padding-top':'20px','vertical-align': 'top'}
                        ),
                        
                        html.Div([
                            html.Label('Lower Specification Limit',style={'display':'table-cell'}),
                            dcc.Input(id='lsl',
                                      value=0,type='number',
                                      placeholder='low spec limit',style={'display':'table-cell'}),
                            
                            html.Label('Upper Specification Limit',style={'display':'table-cell'}),
                            dcc.Input(id='usl',
                                      value=0,type='number',
                                      placeholder='upper spec limit',style={'display':'table-cell'})

                        ],
                        style={ 'display': 'inline-block','padding-left':'20px','padding-top':'20px','vertical-align': 'top'}
                        ),
                    
                        html.Div([                                          
                            html.Label('Y-Axis Lower Limit',style={'display':'table-cell'}),
                            dcc.Input(id='y_low',
                                      value=0,type='number',
                                      placeholder='lower y limit',style={'display':'table-cell'}),
                            
                            html.Label('Y-Axis Upper Limit',style={'display':'table-cell'}),
                            dcc.Input(id='y_high',
                                      value=0,type='number',
                                      placeholder='upper y limit',
                                      style={'display':'table-cell'},
                                      )

                        ],
                        style={'display':'inline-block','padding-left': '20px','padding-top':'20px','vertical-align': 'top'}
                                
                        ),
                    
                        html.Div([                      
                            html.Label('Input Data Aggregation',style={'display':'table-cell'}),
                            dcc.Input(id='agg',
                                value='all',type='text',
                                placeholder='input aggregration, type all for all',style={'display':'table-cell'}),
                        ],
                        style={'display':'inline-block','padding-left': '20px','padding-top':'20px','vertical-align': 'top'}
                        ),
                        
                        html.Div([
                            html.Label('Select Y-Axis Type'),
                            dcc.RadioItems(id='ytype',
                                options=[
                                {'label': 'Linear', 'value': 'linear'},
                                {'label': 'Logarithmic', 'value': 'log'}
                                ]                                
                                ),
                        ],
                        style={'display':'inline-block','padding-left': '20px','padding-top':'20px','vertical-align': 'top'}
                        ), 
                            
                    ],
                    style={'display':'inline-block','padding-left': '20px','padding-top':'20px','vertical-align': 'top'}    
                    ),
                            
                    html.Div([
                       dcc.Graph(id='graph-data')
                        ]),

                ]),
                html.Div(id='df0', style={'display': 'none'}),
                html.Br(),
                html.Div(dash_table.DataTable(id='table'))

            ],
            style={'font-family':'Trebuchet MS, sans-serif','border':'3px outset','padding':'10px','background-color':'#f5f5f5'}
            )

# Functions

# file upload function
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),index_col=0)
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(
                io.BytesIO(decoded),index_col=0)

    except Exception as e:
        print(e)
        return None

    return df

#callback table creation
@app.callback(Output('df0', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename')
              ])

def update_output(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        df.index = pd.to_datetime(df.index)
        if df is not None:
            return df.to_json(orient='split')
        else:
            return [{}]
    else:
        return [{}]

#callback update options of filter dropdown
@app.callback(Output('y-data', 'options'),
              [Input('df0', 'children')])

def update_filter_column_options(data):
    
        df = pd.read_json(data,orient='split') # <- problem! dff stays empty even though table was uploaded

        return [{'label': i, 'value': i} for i in sorted(list(df))]

@app.callback(Output(component_id='graph-data',component_property='figure'),
    [Input(component_id='y-data',component_property='value'),
     Input(component_id='usl',component_property='value'),
     Input(component_id='lsl',component_property='value'),
     Input(component_id='y_low',component_property='value'),
     Input(component_id='y_high',component_property='value'),
     Input(component_id='date',component_property='start_date'),
     Input(component_id='date',component_property='end_date'),
     Input(component_id='agg',component_property='value'),
     Input(component_id='df0', component_property='children'),
     Input(component_id='ytype', component_property='value')
    ]
)

def create_timeseries(y_data,us_lim,ls_lim,y_lower,y_upper,start,end,agg,data,ytype):
    
    dff = pd.read_json(data,orient='split')
    
    if agg != 'all':
        df = dff.loc[start:end].resample(agg).mean()
    else:
        df = dff.loc[start:end]
    
    df_usl = pd.DataFrame(index=df.index,data=np.ones(len(df.index))*us_lim)
    df_lsl = pd.DataFrame(index=df.index,data=np.ones(len(df.index))*ls_lim)
    
    df_high = df[(df[y_data]>us_lim)]
    df_low = df[(df[y_data]<ls_lim)]
    df_good = df[(df[y_data]<us_lim) & (df[y_data]>ls_lim)]
    
    df_mean = df[y_data].mean()
    df_std = df[y_data].std()
    
    df_cpk = min((df_mean-ls_lim)/(3*df_std),(us_lim-df_mean)/(3*df_std))
    
    df_ucl = pd.DataFrame(index=df.index,data=np.ones(len(df.index))*(df_mean+3*df_std))
    
    df_lcl = pd.DataFrame(index=df.index,data=np.ones(len(df.index))*(df_mean-3*df_std))
    
    df_mean2 = pd.DataFrame(index=df.index,data=np.ones(len(df.index))*df_mean)
    
    return {
        'data': [

            go.Scatter(
                x=df.index,y=df[y_data],mode='lines',name='Trend Line',
                line={'width': 1, 'color': 'black'}
            ),
            go.Scatter(
                x=df_usl.index,y=df_usl[0],mode='lines',name='Upper Spec Limit',
                line={'width': 1, 'color': 'black','dash':'dash'}
            ),
            go.Scatter(
                x=df_lsl.index,y=df_lsl[0],mode='lines',name='Lower Spec Limit',
                line={'width': 1, 'color': 'black','dash':'dash'}            
            ),
            go.Scatter(
            x=df_mean2.index,y=df_mean2[0],mode='lines',name='Mean',
                line={'width': 1, 'color': 'green'}
            ),
            go.Scatter(
                x=df_ucl.index,y=df_ucl[0],mode='lines',name='Upper Control Limit',
                line={'width': 1, 'color': 'red'}            
            ),
            go.Scatter(
                x=df_lcl.index,y=df_lcl[0],mode='lines',name='Lower Control Limit',
                line={'width': 1, 'color': 'red'}            
            ),
            go.Scatter(
                x=df_good.index,y=df_good[y_data],mode='markers',name='Within Spec Limits',
                marker={'size': 10,'color':'black','opacity': 0.5,
                'line': {'width': 0.5, 'color': 'black'}
                       }
            ),          
            go.Scatter(
                x=df_high.index, y=df_high[y_data],mode='markers',name='High',
                marker={'size': 10,'color':'red','opacity': 0.5,
                'line': {'width': 0.5, 'color': 'black'}
                       }
            ),      
            
            go.Scatter(
                x=df_low.index,y=df_low[y_data],mode='markers',name='Low',
                marker={'size': 10,'color':'blue','opacity': 0.5,
                'line': {'width': 0.5, 'color': 'black'}
                        }
            ),
         ],

            'layout': go.Layout({
                'title':'Process Control (Cpk) = '+str(np.round(df_cpk,1)),                               
                'xaxis':{
                    'title': 'Date and Time','mirror':True,'ticks':'outside','showline':True
                },
                'yaxis':{
                    'title': y_data, 'range':[y_lower,y_upper],'mirror':True,'ticks':'outside','showline':True,'type':ytype
                }
            })
        }

if __name__ == '__main__':
    app.run_server(port=8080)




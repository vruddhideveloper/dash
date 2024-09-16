import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go

# Initialize the Dash app
app = dash.Dash(__name__)

# Assume we have a CSV file named 'data.csv'
df = pd.read_csv('data.csv')

# Calculate additional columns for the second table
df['T3-T2'] = df['T3'] - df['T2']
df['T4-T3'] = df['T4'] - df['T3']
df['T5-T4'] = df['T5'] - df['T4']
df['T5-T2'] = df['T5'] - df['T2']

# Define the layout
app.layout = html.Div([
    html.H1("Dashboard", style={'textAlign': 'center', 'color': '#2c3e50', 'font-family': 'Arial, sans-serif'}),
    
    html.Div([
        html.H2("Table 1", style={'color': '#34495e'}),
        dash_table.DataTable(
            id='table1',
            columns=[{"name": i, "id": i} for i in ['ts_Amps', 'ts_tcp_recv', 'ts_thr_recv', 'ts_converted', 'ts_written']],
            data=df.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'font-family': 'Arial, sans-serif'
            },
            style_header={
                'backgroundColor': '#3498db',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f2f2f2'
                }
            ]
        )
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ecf0f1', 'borderRadius': '10px'}),
    
    html.Div([
        html.H2("Table 2", style={'color': '#34495e'}),
        dash_table.DataTable(
            id='table2',
            columns=[{"name": i, "id": i} for i in ['T1', 'T2', 'T3', 'T4', 'T5', 'T3-T2', 'T4-T3', 'T5-T4', 'T5-T2']],
            data=df.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'font-family': 'Arial, sans-serif'
            },
            style_header={
                'backgroundColor': '#e74c3c',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f2f2f2'
                }
            ]
        )
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ecf0f1', 'borderRadius': '10px'})
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime
import os

# Initialize the Dash app
app = dash.Dash(__name__)

# Custom CSS for the app
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .toggle-button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s, transform 0.1s;
                font-size: 16px;
                font-weight: bold;
            }
            .toggle-button:hover {
                background-color: #2980b9;
            }
            .toggle-button:active {
                transform: scale(0.98);
            }
            .table-container {
                height: 300px;
                overflow-y: auto;
            }
            .table-container table {
                width: 100%;
            }
            .table-container thead {
                position: sticky;
                top: 0;
                background-color: #f8f9fa;
                z-index: 1;
            }
            .histogram-card {
                display: flex;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
                margin: 20px;
                padding: 20px;
            }
            .histogram-plot {
                flex: 3;
            }
            .histogram-stats {
                flex: 1;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                font-size: 18px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Function to load data based on selected date
def load_data(date):
    filename = f"{date}.csv"
    try:
        df = pd.read_csv(filename)
        df['T2'] = pd.to_datetime(df['T2'])
        df['T2_seconds'] = df['T2'].dt.floor('S')
        
        # Ensure latency columns are in nanoseconds
        latency_columns = ['T2-T1', 'T3-T2', 'T4-T3', 'T5-T4', 'T5-T2']
        for col in latency_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                print(f"Warning: Column {col} not found in the CSV file.")
        
        return df
    except FileNotFoundError:
        return pd.DataFrame()  # Return empty DataFrame if file not found

# Get list of available dates from CSV files
available_dates = [f.split('.')[0] for f in os.listdir() if f.endswith('.csv') and f[0].isdigit()]
initial_date = max(available_dates) if available_dates else datetime.now().strftime("%Y-%m-%d")

# Initial data load
df = load_data(initial_date)

# Define the layout
app.layout = html.Div([
    html.H1("Performance Dashboard", style={'textAlign': 'center', 'color': '#2c3e50', 'font-family': 'Helvetica, Arial, sans-serif', 'margin-bottom': '30px'}),
    
    html.Div([
        dcc.DatePickerSingle(
            id='date-picker',
            date=initial_date,
            display_format='YYYY-MM-DD',
            style={'margin': '10px'}
        ),
        html.Button('Toggle View', id='toggle-view', n_clicks=0, className='toggle-button'),
    ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'backgroundColor': '#ecf0f1', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}),

    html.Div(id='content-container')
], style={'backgroundColor': '#f5f6fa', 'padding': '20px', 'minHeight': '100vh'})

@app.callback(
    Output('content-container', 'children'),
    [Input('date-picker', 'date'),
     Input('toggle-view', 'n_clicks')]
)
def update_dashboard(selected_date, n_clicks):
    df = load_data(selected_date)
    
    if df.empty:
        return html.Div("No data available for the selected date.", style={'textAlign': 'center', 'marginTop': '20px', 'color': '#e74c3c', 'fontSize': '18px'})

    t2_counts = df['T2_seconds'].value_counts().sort_index()
    t2_df = pd.DataFrame({'Timestamp': t2_counts.index.strftime('%H:%M:%S'), 'Count': t2_counts.values})

    t2_hist = px.bar(t2_df, x='Timestamp', y='Count', 
                     title='Number of Records per T2 Second',
                     labels={'Timestamp': 'T2 Timestamp (HH:MM:SS)', 'Count': 'Number of Records'},
                     color='Count', color_continuous_scale=px.colors.sequential.Viridis)

    t2_hist.update_layout(
        xaxis_title='T2 Timestamp (HH:MM:SS)',
        yaxis_title='Number of Records',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Helvetica, Arial, sans-serif", size=14),
        margin=dict(l=50, r=50, t=80, b=50),
        title=dict(font=dict(size=24))
    )

    t2_hist.update_traces(marker_line_color='rgb(8,48,107)', marker_line_width=1.5)
    t2_hist.update_xaxes(tickangle=45, tickmode='array', tickvals=t2_df['Timestamp'])

    latency_metrics = ['T5-T4', 'T4-T3', 'T3-T2', 'T2-T1', 'T5-T2']

    if n_clicks % 2 == 0:
        return [
            html.Div([
                html.H2("Performance Metrics", style={'color': '#34495e', 'textAlign': 'center', 'fontSize': '24px'}),
                html.Div([
                    dash_table.DataTable(
                        id='table1',
                        columns=[{"name": i, "id": i} for i in ['ts_Amps', 'ts_tcp_recv', 'ts_thr_recv', 'ts_converted', 'ts_written']],
                        data=df.to_dict('records'),
                        page_size=5,
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'font-family': 'Helvetica, Arial, sans-serif'
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
                ], className='table-container')
            ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H2("Timing Metrics", style={'color': '#34495e', 'textAlign': 'center', 'fontSize': '24px'}),
                html.Div([
                    dash_table.DataTable(
                        id='table2',
                        columns=[{"name": i, "id": i} for i in ['OptionEMMId', 'UnderlyingEMMId', 'T2-T1', 'T3-T2', 'T4-T3', 'T5-T4', 'T5-T2', 'Insert/Update']],
                        data=df.to_dict('records'),
                        page_size=5,
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'font-family': 'Helvetica, Arial, sans-serif'
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
                ], className='table-container')
            ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'})
        ]
    else:
        return html.Div([
            html.H2("Data Analysis", style={'color': '#34495e', 'textAlign': 'center', 'fontSize': '28px'}),
            html.Div([
                html.H3("T2 Timestamp Analysis (Second Precision)", style={'color': '#34495e', 'textAlign': 'center', 'fontSize': '22px'}),
                dcc.Graph(figure=t2_hist)
            ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'}),
            html.Div([
                html.H3("Latency Analysis", style={'color': '#34495e', 'textAlign': 'center', 'fontSize': '22px'}),
                dcc.Dropdown(
                    id='latency-dropdown',
                    options=[{'label': metric, 'value': metric} for metric in latency_metrics],
                    value=latency_metrics[0],
                    style={'width': '50%', 'margin': '10px auto'}
                ),
                html.Div(id='latency-histogram-card', className='histogram-card')
            ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'}),
            html.Div([
                html.H3("Insert/Update Analysis", style={'color': '#34495e', 'textAlign': 'center', 'fontSize': '22px'}),
                html.Div([
                    dcc.Dropdown(
                        id='insert-update-dropdown',
                        options=[
                            {'label': 'Insert', 'value': 'I'},
                            {'label': 'Update', 'value': 'U'}
                        ],
                        value='I',
                        style={'width': '45%', 'display': 'inline-block', 'marginRight': '5%'}
                    ),
                    dcc.Dropdown(
                        id='latency-metric-dropdown',
                        options=[{'label': metric, 'value': metric} for metric in latency_metrics],
                        value='T5-T4',
                        style={'width': '45%', 'display': 'inline-block'}
                    ),
                ], style={'marginBottom': '20px'}),
                html.Div(id='insert-update-histogram-card', className='histogram-card')
            ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'})
        ])

@app.callback(
    Output('latency-histogram-card', 'children'),
    [Input('latency-dropdown', 'value'),
     Input('date-picker', 'date')]
)
def update_latency_histogram(selected_metric, selected_date):
    df = load_data(selected_date)
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=df[selected_metric], name=selected_metric))
    fig.update_layout(
        title=dict(text=f'{selected_metric} Latency Distribution', font=dict(size=22)),
        xaxis_title=dict(text='Latency (ns)', font=dict(size=16)),
        yaxis_title=dict(text='Frequency', font=dict(size=16)),
        showlegend=False,
        font=dict(family="Helvetica, Arial, sans-serif", size=14),
        margin=dict(l=50, r=50, t=100, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    
    return [
        html.Div([
            dcc.Graph(figure=fig)
        ], className='histogram-plot'),
        html.Div([
            html.H4("Statistics", style={'fontSize': '24px', 'marginBottom': '20px'}),
            html.P(f"Min: {df[selected_metric].min():.2f} ns", style={'fontSize': '18px'}),
            html.P(f"Mean: {df[selected_metric].mean():.2f} ns", style={'fontSize': '18px'}),
            html.P(f"Median: {df[selected_metric].median():.2f} ns", style={'fontSize': '18px'}),
            html.P(f"Max: {df[selected_metric].max():.2f} ns", style={'fontSize': '18px'})
        ], className='histogram-stats')
    ]

@app.callback(
    Output('insert-update-histogram-card', 'children'),
    [Input('insert-update-dropdown', 'value'),
     Input('latency-metric-dropdown', 'value'),
     Input('date-picker', 'date')]
)

def update_insert_update_histogram(selected_type, selected_metric, selected_date):
    df = load_data(selected_date)
    
    filtered_df = df[df['Insert/Update'] == selected_type]
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=filtered_df[selected_metric], name=f'{selected_type} {selected_metric}'))
    fig.update_layout(
        title=dict(text=f'{selected_type} {selected_metric} Latency Distribution', font=dict(size=22)),
        xaxis_title=dict(text='Latency (ns)', font=dict(size=16)),
        yaxis_title=dict(text='Frequency', font=dict(size=16)),
        showlegend=False,
        font=dict(family="Helvetica, Arial, sans-serif", size=14),
        margin=dict(l=50, r=50, t=100, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    
    return [
        html.Div([
            dcc.Graph(figure=fig)
        ], className='histogram-plot'),
        html.Div([
            html.H4("Statistics", style={'fontSize': '24px', 'marginBottom': '20px'}),
            html.P(f"Min: {filtered_df[selected_metric].min():.2f} ns", style={'fontSize': '18px'}),
            html.P(f"Mean: {filtered_df[selected_metric].mean():.2f} ns", style={'fontSize': '18px'}),
            html.P(f"Median: {filtered_df[selected_metric].median():.2f} ns", style={'fontSize': '18px'}),
            html.P(f"Max: {filtered_df[selected_metric].max():.2f} ns", style={'fontSize': '18px'})
        ], className='histogram-stats')
    ]

if __name__ == '__main__':
    app.run_server(debug=True)

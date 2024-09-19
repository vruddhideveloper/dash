import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime
import os
import dask.dataframe as dd
import vaex
from flask_caching import Cache

# Initialize the Dash app
app = dash.Dash(__name__)

# Setup caching
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})
TIMEOUT = 60 * 60  # 1 hour

# Custom CSS for the app (unchanged)
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Your existing styles here */
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
@cache.memoize(timeout=TIMEOUT)
def load_data(date):
    filename = f"{date}.csv"
    try:
        # Use Dask for out-of-memory computations
        df = dd.read_csv(filename)
        
        # Convert to Vaex DataFrame for faster processing
        df = vaex.from_pandas(df.compute())
        
        # Perform necessary data transformations
        df['T2'] = df['T2'].astype('datetime64')
        df['T2_seconds'] = df['T2'].dt.floor('1s')
        df['T2_formatted'] = df['T2'].dt.strftime('%H:%M:%S.%f')
        
        # Ensure latency columns are in nanoseconds
        latency_columns = ['T2-T1', 'T3-T2', 'T4-T3', 'T5-T4', 'T5-T2']
        for col in latency_columns:
            if col in df.column_names:
                df[col] = df[col].astype('float64')
            else:
                print(f"Warning: Column {col} not found in the CSV file.")
        
        return df
    except FileNotFoundError:
        return vaex.from_pandas(pd.DataFrame())  # Return empty DataFrame if file not found

# Get list of available dates from CSV files
available_dates = [f.split('.')[0] for f in os.listdir() if f.endswith('.csv') and f[0].isdigit()]
initial_date = max(available_dates) if available_dates else datetime.now().strftime("%Y-%m-%d")

# Initial data load
df = load_data(initial_date)

# Define the layout (unchanged)
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
    
    if df.shape[0] == 0:
        return html.Div("No data available for the selected date.", style={'textAlign': 'center', 'marginTop': '20px', 'color': '#e74c3c', 'fontSize': '18px'})

    # Sample data for faster processing
    sample_size = min(100000, df.shape[0])
    df_sample = df.sample(n=sample_size)

    t2_counts = df_sample['T2_seconds'].value_counts()
    t2_df = pd.DataFrame({'Timestamp': t2_counts.index.strftime('%H:%M:%S'), 'Count': t2_counts.values})

    t2_hist = px.bar(t2_df, x='Timestamp', y='Count', 
                     title='Number of Records per T2 Second (Sampled)',
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
                        columns=[{"name": i, "id": i} for i in ['ts_Amps', 'ts_tcp_recv', 'ts_thr_recv', 'ts_converted', 'ts_written'], {"name": "T2", "id": "T2_formatted"},],
                        data=df_sample.to_pandas_df().to_dict('records'),
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
                        data=df_sample.to_pandas_df().to_dict('records'),
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
                        value='I',  # Set default value to 'I' for Insert
                        style={'width': '100%', 'marginBottom': '20px'}
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
@cache.memoize(timeout=TIMEOUT)
def update_latency_histogram(selected_metric, selected_date):
    df = load_data(selected_date)
    
    # Sample data for faster processing
    sample_size = min(100000, df.shape[0])
    df_sample = df.sample(n=sample_size)

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=df_sample[selected_metric].values, name=selected_metric))
    fig.update_layout(
        title=dict(text=f'{selected_metric} Latency Distribution (Sampled)', font=dict(size=22)),
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
            html.P(f"Min: {df_sample[selected_metric].min():.2f} ns", style={'fontSize': '18px'}),
            html.P(f"Mean: {df_sample[selected_metric].mean():.2f} ns", style={'fontSize': '18px'}),
            html.P(f"Median: {df_sample[selected_metric].median():.2f} ns", style={'fontSize': '18px'}),
            html.P(f"Max: {df_sample[selected_metric].max():.2f} ns", style={'fontSize': '18px'})
        ], className='histogram-stats')
    ]

@app.callback(
    Output('insert-update-histogram-card', 'children'),
    [Input('insert-update-dropdown', 'value'),
     Input('date-picker', 'date')]
)
@cache.memoize(timeout=TIMEOUT)
def update_insert_update_histogram(selected_type, selected_date):
    df = load_data(selected_date)
    
    # Sample data for faster processing
    sample_size = min(100000, df.shape[0])
    df_sample = df.sample(n=sample_size)
    
    filtered_df = df_sample[df_sample['Insert/Update'] == selected_type]
    selected_metric = 'T5-T4'  # Fixed to T5-T4
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=filtered_df[selected_metric].values, name=f'{selected_type} {selected_metric}'))
    fig.update_layout(
        title=dict(text=f'{selected_type} {selected_metric} Latency Distribution (Sampled)', font=dict(size=22)),
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

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime, timedelta
import os

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

# Function to load data based on selected date
def load_data(date):
    filename = f"{date}.csv"
    try:
        df = pd.read_csv(filename)
        df['T2'] = pd.to_datetime(df['T2'])
        df['T2_seconds'] = df['T2'].dt.floor('S')
        
        # Calculate latency columns
        for col in ['T1', 'T2', 'T3', 'T4', 'T5']:
            df[col] = pd.to_datetime(df[col])
        df['T5-T4'] = (df['T5'] - df['T4']).dt.total_seconds() * 1000  # Convert to milliseconds
        df['T4-T3'] = (df['T4'] - df['T3']).dt.total_seconds() * 1000
        df['T3-T2'] = (df['T3'] - df['T2']).dt.total_seconds() * 1000
        df['T2-T1'] = (df['T2'] - df['T1']).dt.total_seconds() * 1000
        df['T5-T2'] = (df['T5'] - df['T2']).dt.total_seconds() * 1000
        
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
        dcc.Dropdown(
            id='timestamp-dropdown',
            options=[],
            placeholder="Select a specific timestamp",
            style={'width': '300px', 'margin': '10px'}
        ),
        html.Button('Toggle View', id='toggle-view', n_clicks=0, 
                    style={'margin': '10px', 'padding': '10px', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer', 'transition': 'background-color 0.3s'}),
    ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'backgroundColor': '#ecf0f1', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}),

    html.Div(id='content-container')
], style={'backgroundColor': '#f5f6fa', 'padding': '20px', 'minHeight': '100vh'})

@app.callback(
    [Output('timestamp-dropdown', 'options'),
     Output('content-container', 'children')],
    [Input('date-picker', 'date'),
     Input('timestamp-dropdown', 'value'),
     Input('toggle-view', 'n_clicks')]
)
def update_dashboard(selected_date, selected_timestamp, n_clicks):
    df = load_data(selected_date)
    
    if df.empty:
        return [], html.Div("No data available for the selected date.", style={'textAlign': 'center', 'marginTop': '20px', 'color': '#e74c3c', 'fontSize': '18px'})

    timestamp_options = [{'label': ts, 'value': ts} for ts in df['T2_seconds'].dt.strftime('%H:%M:%S').unique()]
    
    if selected_timestamp:
        df = df[df['T2_seconds'].dt.strftime('%H:%M:%S') == selected_timestamp]

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
        font=dict(family="Helvetica, Arial, sans-serif"),
        margin=dict(l=50, r=50, t=50, b=50),
    )

    t2_hist.update_traces(marker_line_color='rgb(8,48,107)', marker_line_width=1.5)
    t2_hist.update_xaxes(tickangle=45, tickmode='array', tickvals=t2_df['Timestamp'])

    # Create latency histograms
    latency_metrics = ['T5-T4', 'T4-T3', 'T3-T2', 'T2-T1', 'T5-T2']
    latency_hists = []

    for metric in latency_metrics:
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=df[metric], name=metric, marker_color='#3498db'))
        fig.update_layout(
            title=f'{metric} Latency Distribution',
            xaxis_title='Latency (ms)',
            yaxis_title='Frequency',
            showlegend=False,
            font=dict(family="Helvetica, Arial, sans-serif"),
            margin=dict(l=50, r=50, t=50, b=50),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        fig.add_annotation(x=0.5, y=1.15, 
                           text=f'Avg: {df[metric].mean():.2f} ms, Min: {df[metric].min():.2f} ms, Max: {df[metric].max():.2f} ms',
                           showarrow=False, xref='paper', yref='paper',
                           font=dict(size=12))
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
        latency_hists.append(dcc.Graph(figure=fig, style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}))

    if n_clicks % 2 == 0:
        return timestamp_options, [
            html.Div([
                html.H2("Performance Metrics", style={'color': '#34495e', 'textAlign': 'center'}),
                dash_table.DataTable(
                    id='table1',
                    columns=[{"name": i, "id": i} for i in ['ts_Amps', 'ts_tcp_recv', 'ts_thr_recv', 'ts_converted', 'ts_written']],
                    data=df.to_dict('records'),
                    style_table={'height': '300px', 'overflowY': 'auto'},
                    page_size=10,
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
            ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H2("Timing Metrics", style={'color': '#34495e', 'textAlign': 'center'}),
                dash_table.DataTable(
                    id='table2',
                    columns=[{"name": i, "id": i} for i in ['T1', 'T2', 'T3', 'T4', 'T5', 'T2-T1', 'T3-T2', 'T4-T3', 'T5-T4', 'T5-T2']],
                    data=df.to_dict('records'),
                    style_table={'height': '300px', 'overflowY': 'auto'},
                    page_size=10,
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
            ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'})
        ]
    else:
        return timestamp_options, html.Div([
            html.H2("Data Analysis", style={'color': '#34495e', 'textAlign': 'center'}),
            html.Div([
                html.Div([
                    html.H3("T2 Timestamp Analysis (Second Precision)", style={'color': '#34495e', 'textAlign': 'center'}),
                    dcc.Graph(figure=t2_hist)
                ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'}),
                html.Div(latency_hists, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around'})
            ])
        ])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

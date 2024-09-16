import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
from datetime import datetime

# Initialize the Dash app
app = dash.Dash(__name__)

# Function to load data based on selected date
def load_data(date):
    filename = f"{date}.csv"
    try:
        df = pd.read_csv(filename)
        df['T2'] = pd.to_datetime(df['T2'])
        df['T2_seconds'] = df['T2'].dt.floor('S')
        return df
    except FileNotFoundError:
        return pd.DataFrame()  # Return empty DataFrame if file not found

# Initial data load
initial_date = datetime.now().strftime("%Y-%m-%d")
df = load_data(initial_date)

# Define the layout
app.layout = html.Div([
    html.H1("Dashboard", style={'textAlign': 'center', 'color': '#2c3e50', 'font-family': 'Arial, sans-serif'}),
    
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
                    style={'margin': '10px', 'padding': '10px', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'borderRadius': '5px'}),
    ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}),

    html.Div(id='content-container')
])

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
        return [], html.Div("No data available for the selected date.", style={'textAlign': 'center', 'marginTop': '20px'})

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
    )

    t2_hist.update_traces(marker_line_color='rgb(8,48,107)', marker_line_width=1.5)
    t2_hist.update_xaxes(tickangle=45, tickmode='array', tickvals=t2_df['Timestamp'])

    if n_clicks % 2 == 0:
        return timestamp_options, [
            html.Div([
                html.H2("Table 1", style={'color': '#34495e'}),
                dash_table.DataTable(
                    id='table1',
                    columns=[{"name": i, "id": i} for i in ['ts_Amps', 'ts_tcp_recv', 'ts_thr_recv', 'ts_converted', 'ts_written']],
                    data=df.to_dict('records'),
                    style_table={'height': '300px', 'overflowY': 'auto'},
                    page_size=5,
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
                    columns=[{"name": i, "id": i} for i in ['T1', 'T2', 'T3', 'T4', 'T5', 'T2-T1', 'T3-T2', 'T4-T3', 'T5-T4', 'T5-T2']],
                    data=df.to_dict('records'),
                    style_table={'height': '300px', 'overflowY': 'auto'},
                    page_size=5,
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
        ]
    else:
        return timestamp_options, html.Div([
            html.H2("T2 Timestamp Analysis (Second Precision)", style={'color': '#34495e', 'textAlign': 'center'}),
            dcc.Graph(figure=t2_hist)
        ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ecf0f1', 'borderRadius': '10px'})

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

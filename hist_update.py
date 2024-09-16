import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px

# Initialize the Dash app
app = dash.Dash(__name__)

# Assume we have a CSV file named 'data.csv'
df = pd.read_csv('data.csv')

# Prepare data for T2 histogram
# Convert T2 to datetime and then round to seconds
df['T2'] = pd.to_datetime(df['T2'])
df['T2_seconds'] = df['T2'].dt.floor('S')

# Count occurrences of each second
t2_counts = df['T2_seconds'].value_counts().sort_index()
t2_df = pd.DataFrame({'Timestamp': t2_counts.index.strftime('%H:%M:%S'), 'Count': t2_counts.values})

# Create new histogram for T2
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

# Adjust x-axis to show all labels
t2_hist.update_xaxes(tickangle=45, tickmode='array', tickvals=t2_df['Timestamp'])

# Define the layout
app.layout = html.Div([
    html.H1("Dashboard", style={'textAlign': 'center', 'color': '#2c3e50', 'font-family': 'Arial, sans-serif'}),
    
    html.Div([
        html.Button('Toggle View', id='toggle-view', n_clicks=0, 
                    style={'margin': '10px', 'padding': '10px', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'borderRadius': '5px'}),
    ], style={'textAlign': 'center'}),

    html.Div(id='content-container')
])

@app.callback(
    Output('content-container', 'children'),
    Input('toggle-view', 'n_clicks'),
    State('content-container', 'children')
)
def toggle_content(n_clicks, current_content):
    if n_clicks % 2 == 0:
        return [
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
                    columns=[{"name": i, "id": i} for i in ['T1', 'T2', 'T3', 'T4', 'T5', 'T2-T1', 'T3-T2', 'T4-T3', 'T5-T4', 'T5-T2']],
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
        ]
    else:
        return html.Div([
            html.H2("T2 Timestamp Analysis (Second Precision)", style={'color': '#34495e', 'textAlign': 'center'}),
            dcc.Graph(figure=t2_hist)
        ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ecf0f1', 'borderRadius': '10px'})

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

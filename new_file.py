import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

app = dash.Dash(__name__)


df = pd.read_csv('data.csv')

colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

bar_fig = go.Figure(data=[
    go.Bar(name='T2-T1', x=df.index, y=df['T2-T1'], marker_color=colors[0]),
    go.Bar(name='T3-T2', x=df.index, y=df['T3-T2'], marker_color=colors[1]),
    go.Bar(name='T4-T3', x=df.index, y=df['T4-T3'], marker_color=colors[2]),
    go.Bar(name='T5-T4', x=df.index, y=df['T5-T4'], marker_color=colors[3]),
    go.Bar(name='T5-T2', x=df.index, y=df['T5-T2'], marker_color=colors[4])
])

bar_fig.update_layout(
    title='Time Differences Comparison',
    xaxis_title='Data Point',
    yaxis_title='Time Difference',
    barmode='group',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)

hist_fig = px.histogram(
    df, 
    x=['T2-T1', 'T3-T2', 'T4-T3', 'T5-T4', 'T5-T2'], 
    nbins=20, 
    title='Distribution of Time Differences',
    labels={'value': 'Time Difference', 'variable': 'Measurement'},
    color_discrete_sequence=colors
)

hist_fig.update_layout(
    xaxis_title='Time Difference',
    yaxis_title='Frequency',
    bargap=0.2,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)


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
            html.H2("Time Difference Analysis", style={'color': '#34495e', 'textAlign': 'center'}),
            dcc.Graph(figure=bar_fig),
            dcc.Graph(figure=hist_fig)
        ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#ecf0f1', 'borderRadius': '10px'})

if __name__ == '__main__':
    app.run_server(debug=True)

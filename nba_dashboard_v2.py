import plotly.express as px
import pandas as pd
import numpy as np

from pathlib import Path

#import plotly.graph_objects as go
#from plotly.subplots import make_subplots

from pathlib import Path
from dash import Dash, dcc, html, Input, Output
import dash_daq as daq

currentfolder = Path("C:/Users/blake/OneDrive/Documents/Alex/job stuff/Personal Projects/NBA/")
filepath = currentfolder / "23Players.xlsx"
data = pd.read_excel(filepath)


app = Dash(__name__)

# start by making a dictionary of all players in each team, each team is the key, player lists are the items
# order the teams alphabetically and players alphabetically
all_teams = {}
for tm in sorted(data.Tm.unique()):
    all_teams[tm] = sorted(list(data.loc[data['Tm'] == tm, 'Player']))

# list of all the stats you can choose
stats = ['FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'eFG%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']


# other ideas: have a slider of minutes per game so you can see stats just of the most played players
# get rid of player selection, have a radioItems selection for teams to see all players from all those teams
app.layout = html.Div([
    html.H1('NBA Dashboard', style = {"text-align": "center"}),

    dcc.Checklist(
        list(all_teams.keys()),
        ['ATL'],
        inline = True,
        id = 'team_checklist'
    ),
    html.Hr(),
    dcc.RangeSlider(
        0, 48, 
        value = [5,48],
        id = 'minutes_slider'
    ),
    html.Hr(),
    dcc.Checklist(
        stats, 
        ['PTS', 'AST', 'BLK'], 
        inline = True, 
        id = 'stats_checklist'
    ),
    # also want a toggle to adjust for per 48
    html.Hr(),
    daq.ToggleSwitch(
        label = "Toggle for per 48 stats",
        labelPosition = 'bottom',
        color = 'blue',
        id = 'per48_toggle'
    ),
    html.Hr(),
    # this is our final graph displaying individual players of each team ranked in certain stats
    dcc.Graph(id="player_plot", figure = {}),

    # want to display all teams on same graph with different stats choices
    # need to download team totals information
    # need to figure out how to display two seperate graphs
    # need t ofigure out which stats are valid options
    html.Hr(),
    html.Div(
        children = [
            dcc.Dropdown(
                stats,
                value = 'PTS',
                id = 'x-axis'
            )
        ],
        style=dict(width='50%')
    ),
    html.Div(
        children = [
            dcc.Dropdown(
                stats,
                value = 'eFG%',
                id = 'y-axis'
            )
        ],
        style=dict(width='50%')
    )
])


# final callback to display everything
@app.callback(
    Output('player_plot', 'figure'),
    Input('team_checklist', 'value'),
    Input('minutes_slider', 'value'),
    Input('stats_checklist', 'value'),
    Input('per48_toggle', 'value')
)
def set_display_children(selected_teams, minutes_limits, selected_stats, per48):
    # next step adding dropdowns to choose which data to be displayed
    # add radioitems for columns to selct what stats you want to look at
    # make vertical scatter lines showing players performance within each time

    data2 = data.copy()
    
    min_mins = minutes_limits[0]
    max_mins = minutes_limits[1]

    # subset the data to only selected teams and selected minutes
    team_df = data2.copy().query("Tm in @selected_teams")
    team_df = team_df.query("MP > @min_mins & MP <= @max_mins")
    team_df.reset_index(drop = True, inplace = True)
    
    # melt the dataframe
    id_columns = ['Player', 'Tm', 'MP']
    stats_columns = selected_stats
    melted_df = pd.melt(team_df, id_columns, stats_columns, var_name = 'stat', value_name = 'raw_value')

    # bit of a problem in that per48 only makes sense for certain stats, whereas makes no sense for percentage stats
    # add in per48_value column and find the maximums for each category
    melted_df['per48_value'] = 48*melted_df['raw_value']/melted_df['MP']
    
    # find the max raw values and max per48 values for each category as dictionaries
    max_48_vals = {s: melted_df[melted_df.stat == s].per48_value.max() for s in stats_columns}
    max_raw_vals = {s: melted_df[melted_df.stat == s].raw_value.max() for s in stats_columns}
    
    # add in scaled columns for raw and per48 stats to better display all categories on same graph
    melted_df['scaled_48_value'] = [100*i/j for i,j in zip(melted_df['per48_value'], melted_df['stat'].map(max_48_vals))] 
    melted_df['scaled_raw_value'] = [100*i/j for i,j in zip(melted_df['raw_value'], melted_df['stat'].map(max_raw_vals))] 

    yaxis = 'scaled_raw_value'
    if per48:
        yaxis = 'scaled_48_value'

    fig = px.scatter(
        melted_df,
        x = 'stat',
        y = yaxis,
        size = 'MP',
        size_max=10,
        color_discrete_map={'2':'red', '1':'blue'},
        custom_data=['Player','raw_value', 'per48_value', 'MP']
    ).update_layout(
        showlegend=False,
        yaxis = {'visible': False},
        xaxis = {'title': None, 'showticklabels': True}
    ).update_traces(hovertemplate='%{customdata[0]}' +
                                  '<br>%{x} per game: %{customdata[1]}' +
                                  '<br>%{x} per 48: %{customdata[2]:.1f}' +
                                  '<br>Minutes: %{customdata[3]}' +
                                  '<extra></extra>') 

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)

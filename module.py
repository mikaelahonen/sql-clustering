import config as c

#Analysis
import numpy as np
import pandas as pd

#Plotly
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.graph_objs as go

#Generate time series from 0 ... observations_n
def generate_initial_data():

    #Generate the time column
    time_series = np.arange(c.observations_n)

    #Create cluster breakpoints
    np.random.seed(11)
    cluster_breakpoints = np.sort(np.random.randint(c.observations_n, size=c.clusters_n-1))
    cluster_breakpoints = np.insert(cluster_breakpoints, 0, 0)
    print("Cluster breakpoints: {}".format(cluster_breakpoints))
    
    #Create cluster partitions
    cluster_id = np.repeat(0, c.observations_n)
    cluster_id[cluster_breakpoints] = 1
    cluster_id = np.cumsum(cluster_id)
    
    #Create starting heat
    cluster_start_heat = np.repeat(np.nan, c.observations_n)
    cluster_start_heat[cluster_breakpoints] = np.random.randint(low=c.start_heat_min, high=c.start_heat_max, size=c.clusters_n)
    
    #Create the data frame
    df = pd.DataFrame({c.col_time: time_series, c.col_cluster_id: cluster_id, c.col_start_heat: cluster_start_heat})
    
    #Rank inside the cluster
    df[c.col_cluster_rank] = df.groupby(c.col_cluster_id)[c.col_cluster_id].rank().astype(int)
    
    #Initial temperature
    cluster_firsts = np.where(df[c.col_cluster_rank]==1)
    df[[c.col_start_heat]] = df[[c.col_start_heat]].fillna(method='ffill')
    
    return df

#Always increasing
def generate_engine_heat_1(df_arg, col_engine_heat='engine_heat'):
    
    df = df_arg.copy()
    
    col_heat_delta = 'heat_delta_temp'
    col_heat_cum = 'heat_cum_temp'
    
    #Create heat delta and give a cluster specific factor
    df[col_heat_delta] = np.random.random(size=df.shape[0]) * df[c.col_cluster_rank]**0.5
    
    #Cumulative sum of heat deltas by cluster id
    df[col_heat_cum] = df.groupby(c.col_cluster_id)[col_heat_delta].cumsum()
    
    #Engine heat at given moment is cumulative sum plus start heat
    df[col_engine_heat] = df[c.col_start_heat] + df[col_heat_cum]
    
    #Drop temporary columns
    df.drop([col_heat_delta, col_heat_cum], inplace=True, axis=1)
    
    return df

#The combination is always increasing
def generate_engine_heat_2(df_arg, col_1='engine_heat_1', col_2='engine_heat_2'):
    
    df = df_arg.copy()
    
    #Create temporary column names
    delta_1 = 'heat_delta_temp_1'
    delta_2 = 'heat_delta_temp_2'
    cum_1 = 'heat_cum_temp_1'    
    cum_2 = 'heat_cum_temp_2'
    
    #Create heat delta and give a cluster specific factor    
    df[delta_1] = (np.random.random(size=df.shape[0])-0.3) * df[c.col_cluster_rank]**0.5
    df[delta_2] = (np.random.random(size=df.shape[0])-0.4)
    
    #Ensure that sum is always more than zero
    df[delta_2] = np.where((df[delta_2]+df[delta_1])<0, -1 * df[delta_1] + 0.05, df[delta_2])
    
    #Cumulative sum of heat deltas by cluster id
    df[cum_1] = df.groupby(c.col_cluster_id)[delta_1].cumsum()
    df[cum_2] = df.groupby(c.col_cluster_id)[delta_2].cumsum()
    
    #Engine heat at given moment is cumulative sum plus start heat
    df[col_1] = df[c.col_start_heat] + df[cum_1]
    df[col_2] = df[c.col_start_heat] + df[cum_2]
    
    #Drop temporary columns
    df.drop([delta_1, delta_2, cum_1, cum_2], inplace=True, axis=1)
    
    return df

#Plot clusters in regular scatter plot
def plot_heat_2d(df, col_y='engine_heat', plot_title="Cluster plot"):
    
    #Tooltip for cluster id and cluster rank
    if c.col_cluster_rank in df.columns:
        label_text = "Cluster id: " + df[c.col_cluster_id].astype(str) + "<br>Cluster rank: " +  df[c.col_cluster_rank].astype(str)
    #If the cluster rank is unknown, omit it
    else:
        label_text = "Cluster id: " + df[c.col_cluster_id].astype(str)
    
    fig = go.Figure()
    
    fig.add_scatter(
        x=df[c.col_time],
        y=df[col_y],
        text=label_text,
        mode='markers',
        marker={
            'color': df[c.col_cluster_id],
            'colorscale': 'Rainbow',
        }
    )
    
    fig.update_layout(
        title=go.layout.Title(text=plot_title),
        xaxis=go.layout.XAxis(
            title=go.layout.xaxis.Title(text=c.col_time)
        ),
        yaxis=go.layout.YAxis(
            title=go.layout.yaxis.Title(text=col_y)
        )
    )
    
    iplot(fig)
    
#Visualize time and two engine heat variables in a 3D scatter plot
def plot_heat_3d(df, col_y='engine_heat_1', col_z='engine_heat_2', plot_title="3D Plot"):
    
    series_1 = go.Scatter3d(
        x=df[c.col_time],
        y=df[col_y],
        z=df[col_z],
        text="Cluster id: " + df[c.col_cluster_id].astype(str) + "<br>Cluster rank: " +  df[c.col_cluster_rank].astype(str),
        mode='markers',
        marker={
            'size': 5,
            'color': df[c.col_cluster_id],
            'opacity': 0.8,
            'colorscale': 'Rainbow',
            'symbol': 'circle'
        }
              
    )
    
    layout = go.Layout(
        title=plot_title,
        margin=dict(
            l=0,
            r=0,
            b=0,
            t=50
        ),
        scene = dict(
            xaxis = dict(title=c.col_time),
            yaxis = dict(title=col_y),
            zaxis = dict(title=col_z),
        ),
    )
    
    fig = go.Figure(data=[series_1], layout=layout)
    
    iplot(fig)
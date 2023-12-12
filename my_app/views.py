import os
import json
import dash
import flask
import random
import numpy as np
import requests
import networkx as nx
from .graph import Graph, random_walk
from collections import deque
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from dash import Dash, dcc, html, State, dash_table
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
from django.views.decorators.csrf import ensure_csrf_cookie

# initialize dash app and geodataframe
app = DjangoDash("drug-interaction")
shp_file = gpd.read_file("./my_app/World_Countries_Generalized.zip").drop(
    ["SHAPE_Leng", "SHAPE_Area", "FID", "COUNTRYAFF"], axis=1
)

# check if FDA API key is found
FDA_KEY = os.environ["FDA_KEY"]
print("FDA key found") if FDA_KEY else print("fda key not found")

# layout for the dash app
app.layout = html.Div(
    [
        # input box and drop down menu
        html.Div("Please enter a series of drug names, separated by comma:"),
        html.Div([dcc.Input(id="query", type="text", style={"height": "20px", "width": "270px"}),
                  html.Div("", style={'height': "10px"}),
                  html.Div("Please select a specific type of information to display"),
                  dcc.Dropdown(["Patient Sex", "Age of onset", "Report nation", "Reaction type"],
                               "Patient Sex",  id="dd",
                               style={"height": "35px", "width": "270px", "display": "inline-block"})],
                style = {"display": "flex", "flex-direction": "column",}),
        # status string
        html.Div(id="status-div", style={"color": "blue", "height": "20px"}),
        html.Button("Submit", id="submit-btn", n_clicks=0),
        # graph container
        html.Div(
            [
                html.Div(dcc.Graph(id="drug-network"), style={"width": "49%"}),
                html.Div(
                    html.Div(
                        [
                            dcc.Graph(id="drill-down", style={"height": "49%"}),
                        ]
                    ),
                    style={"width": "49%"},
                ),
            ],
            style={
                "display": "flex",
                "flex-direction": "row",
                "justify-content": "space-between",
            },
        ),
    ],
    id="graph-container",
)

# django view
@ensure_csrf_cookie
def index(request):
    """handle django view function

    Parameters
    ----------
    request : 
        request object

    Returns
    -------
        Rendered django template
    """
    context = {}
    return render(request, "index.html", context)

# callback for network graph
@app.callback(
    dash.dependencies.Output("drug-network", "figure"), # network graph
    dash.dependencies.Output("status-div", "children"), # status string
    dash.dependencies.Input("submit-btn", "n_clicks"),  # click counter - n_clicks
    dash.dependencies.Input("dd", "value"),  # dropdown value - query
    State("query", "value"),  # query string - text
    prevent_initial_call=True,
)
def update_graph(n_clicks, query, text):
    """Update the drug network graph based on user input

    Takes the `Input` callbacks supplied in the annotation as arguments
    and return the network graph and a status string

    Parameters
    ----------
    n_clicks : 
        Number of times the "submit" button is clicked 
    query : 
        Value that the users select from the dropdown menu
    text : 
        User query string

    Returns
    -------
        The network graph, 
    """
    if n_clicks >= 1:
        try:
            print(f"query string is: {text}")
            # get RxCUI and interaction data
            cui_name_pair = getRxNorm(text)
            interaction = getInteractionData(list(cui_name_pair.keys()))
            # build interaction graph
            graph = getInteractionGraph(interaction)
            return (
                buildGraphVisualization(graph),
                "Graph built successfully",
            )
        except ValueError:
            # if the user only enter one drug
            return dcc.Graph(), "Please enter at least two drug names"
        except KeyError as e:
            print(e)
            # if there is no interaction found for users' input drug
            return dcc.Graph(), "No interaction is found for this group of drugs!"
    return dash.no_update, ""


@app.callback(
    Output("drill-down", "figure"),
    Input("drug-network", "clickData"), # click data from the network graph - click_data
    Input("dd", "value"), # drop-down selection - dropdown
)
def update_drilldown(click_data, dropdown):
    """Update the adverse event drill down graph based on user input

    Parameters
    ----------
    click_data : 
        The vertex that the user clicks on
    dropdown : 
        The dropdown value that the user selects

    Returns
    -------
        The drill down graph
    """
    try:
        # get the CUI number being clicked on
        cui_clicked = click_data["points"][0]["text"].split("<br>")[0].split(": ")[1]
        openFda = getOpenFda(cui_clicked)
    except:
        # when the user clicks on the edge scatter points
        pass
    if dropdown == "Patient Sex":
        # patient sex - bar graph
        # construct dicionary with data to plot (k: v = sex: count)
        plot_dict = openFda["sex"]
        fig = px.bar(x=plot_dict.keys(), y=plot_dict.values(), color=plot_dict.keys())
        fig.update_layout(
            title=f"Gender distribution of adverse events for {cui_clicked}"
        )
        return fig
    elif dropdown == "Age of onset":
        # age of onset - bar graph
        # construct dicionary with data to plot (k: v = Age : count)
        plot_dict = openFda["age_onset"]
        fig = px.bar(x=plot_dict.keys(), y=plot_dict.values(), color=plot_dict.keys())
        fig.update_layout(
            xaxis_range=[0, 100],
            xaxis_title="Age",
            yaxis_title="Count",
            title=f"Distribution of age of adverse event onset for {cui_clicked}",
        )
        fig.update(layout_coloraxis_showscale=False)
        return fig
    elif dropdown == "Report nation":
        # report nation - choropleth mapping
        # use geopandas geodataframe
        plot_data = (
            gpd.GeoDataFrame(openFda["reporting_country"])
            .merge(shp_file, how="inner", left_on="term", right_on="ISO")
            .drop(["term", "AFF_ISO"], axis=1)
        )
        # index needs to be ISO, geometry needs to be set too
        plot_data = plot_data.set_geometry("geometry").set_index("ISO")
        # plot
        fig = px.choropleth(
            plot_data,
            geojson=plot_data.geometry,
            locations=plot_data.index,
            color="count",
        )
        fig.update_layout(title=f"Reporting country distribution for {cui_clicked}")
        return fig
    elif dropdown == "Reaction type":
        # reaction type - bar graph
        # construct dicionary with data to plot (k: v = reaction type: count)
        plot_dict = {
            i["term"].capitalize(): i["count"] for i in openFda["reaction_type"]
        }
        plot_dict = sorted(plot_dict.items(), key=lambda x: x[1], reverse=True)
        plot_dict = {i[0]: i[1] for i in plot_dict}
        n = 15
        fig = px.bar(x=list(plot_dict.keys())[:n], y=list(plot_dict.values())[:n])
        fig.update(layout_coloraxis_showscale=False, layout_showlegend=False)
        fig.update_layout(
            title_text=f"Top 15 Adverse Reactions of {cui_clicked}",
            xaxis_title="Adverse Reaction",
            yaxis_title="Count",
        )
        return fig



def getRxNorm(query_str):
    """Get data from the RxNorm API 

    Takes the user input string and return a dictionary with RxCUI 
    as keys and drug names as values. Caches data to the `cache.json` file. 
    The cached data will be used if the user enters the same drug names. 
    `cache.json` has structure: `{user_input: {RxCUI: drug_name, ...}}`

    Parameters
    ----------
    query_str : 
        Users' input string with drug names separated by commas

    Returns
    -------
        A dictionary with RxCUI as keys and drug names as values

    Raises
    ------
    ValueError
        When users enter less than two drug names
    """
    query_str = [i.strip().lower() for i in query_str.split(",")]
    if len(query_str) < 2:
        raise ValueError("Please enter at least two drug names")
    cui_name = {}  # dictionary to store cui to drug_name mapping
    with open("./my_app/cache.json", "r") as json_file:
        cache = json.load(json_file)

    for q in query_str:
        if q in cache.keys():
            # if data is in cache
            print("data found in cache")
            cui_name.update(cache[q])  # update cui_name with cached data
        else:
            # if data is not in cache, fetch new data
            print("Fetching new data")
            response = requests.get(
                f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={q}"
            ).json()
            new_data = {}  # temporary dictionary to store new API data
            try:
                for i in response["drugGroup"]["conceptGroup"]:
                    if "conceptProperties" in i:
                        for j in i["conceptProperties"]:
                            new_data[j["rxcui"]] = j["name"]
                cache[q] = new_data  # update cache with new data for q
                cui_name.update(new_data)  # update cui_name with new API data
            except KeyError:
                pass

    # Update the cache file only once after processing all queries
    with open("./my_app/cache.json", "w") as f:
        json.dump(cache, f)

    return cui_name


def getOpenFda(cui):
    """Get data from the OpenFDA API

    Parameters
    ----------
    cui : 
        RxCUI Code numbers

    Returns
    -------
        A dictionary containing the results
    """
    BASE_URL = f"https://api.fda.gov/drug/event.json?api_key={FDA_KEY}&search=patient.drug.openfda.rxcui"
    results = {}
    # sex
    # 0 is unknown, 1 is male, 2 is female, baba is you
    content = requests.get(f"{BASE_URL}:%22{cui}%22&count=patient.patientsex").json()
    sex_dict = {0: "unknown", 1: "male", 2: "female"}
    results["sex"] = {sex_dict[i["term"]]: i["count"] for i in content["results"]}

    # age of onset
    content = requests.get(
        f"{BASE_URL}:%22{cui}%22&count=patient.patientonsetage"
    ).json()
    results["age_onset"] = {i["term"]: i["count"] for i in content["results"]}

    # reporting country
    results["reporting_country"] = requests.get(
        f"{BASE_URL}:%22{cui}%22&count=primarysourcecountry.exact"
    ).json()["results"]

    # reaction type
    results["reaction_type"] = requests.get(
        f"{BASE_URL}:%22{cui}%22&count=patient.reaction.reactionmeddrapt.exact"
    ).json()["results"]
    return results


def getInteractionData(cui_list):
    """Get drug interaction data from NIH Drug interaction data

    Parameters
    ----------
    cui_list : 
        A list of RxCUI numbers

    Returns
    -------
        The json response from the NIH API
    """
    max_len = 50 if len(cui_list) >= 50 else len(cui_list) # max len is 50
    cui_list = random.choices(cui_list, k=max_len) # choose max of 50 CUI from list
    cui_str = "+".join(cui_list) # join CUI with +
    content = requests.get(
        f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={cui_str}"
    ).json()
    return content


def getInteractionGraph(interaction):
    """Construct a graph from interaction data

    Parameters
    ----------
    interaction : 
        The json response from the NIH API

    Returns
    -------
        A graph object conforming to the graph structure described
        in the document and `graph.py` 
    """
    graph = Graph()
    # access fullInteractionType nested in fullInteractionTypeGroup
    for i in interaction["fullInteractionTypeGroup"]:
        for j in i["fullInteractionType"]:
            graph.add_edge(
                j["minConcept"][0]["rxcui"],
                j["minConcept"][0]["name"],
                j["minConcept"][1]["rxcui"],
                j["minConcept"][1]["name"],
                i["sourceName"], # source of info is in outer group
                j["interactionPair"][0]["severity"],
                j["interactionPair"][0]["description"],
            )
    return graph


def buildGraphVisualization(graph):
    """Build a visualization of the graph using plotly

    Parameters
    ----------
    graph : 
        The graph constructed by the getInteractionGraph() function

    Returns
    -------
        A plotly graph object
    """
    def point_generator(x0, x1, y0, y1, qty, ht):
        """Helper function to generate multiple midpoints for edges

        This allows users to hover over any given points on 
        the edges and see the hovertext

        Adapted from: https://stackoverflow.com/questions/74607000
        (Used np.linspace to increase performance of computing points and added comments)

        Parameters
        ----------
        x0 :
            Starting point on the x coordinate
        x1 :
            Ending point on the x coordinate
        y0 :
            Starting point on the y coordinate
        y1 :
            Ending point on the y coordinate
        qty :
            Number of points to generate
        ht :
            Hover text to display (duplicated `qty` times)

        Returns
        -------
            A tuple of lists
            ptx : points for x-axis
            pty : points for y-axis
            pth : duplicated hover text
        """
        # generate duplicate hovertext
        pth = [ht] * qty
        # calculate all middle points + start and end (x-axis)
        ptx = np.linspace(x0, x1, qty + 2).tolist() 
        # calculate all middle points + start and end (y-axis)
        pty = np.linspace(y0, y1, qty + 2).tolist()
        ptx.pop(0); ptx.pop() # pop first and last for x (to avoid the origin)
        pty.pop(0); pty.pop() # pop first and last for y (to avoid the origin)
        return ptx, pty, pth

    def nxGraph(drug_graph):
        """helper function to convert the given drug graph to a networkx graph

        Parameters
        ----------
        drug_graph : 
            The graph constructed by the getInteractionGraph() function

        Returns
        -------
            A networkx graph object
        """
        G = nx.Graph()
        # loop over vertices in the graph as vertex
        for vertex in drug_graph.vert_list.values():
            # add node to networkx graph
            G.add_node(vertex.id)
            for neighbor in vertex.connectedTo:
                # add edge to networkx graph
                # can use kwargs to add additional info to the graph
                G.add_edge(
                    vertex.id,
                    neighbor.id,
                    severity=vertex.connectedTo[neighbor].severity, # include severity info
                    additional_info=vertex.connectedTo[neighbor].additional_info, # inclide additional info
                )
        return G

    # convert to networkx graph
    G = nxGraph(graph)

    # generate positions for each node for visualization
    pos = nx.spring_layout(G)

    # extract edge coordinates from the positions
    edge_x, edge_y = [], []
    m2x, m2y, m2t = [], [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]] # get x coord
        x1, y1 = pos[edge[1]] # get y coord
        edge_x.extend([x0, x1, None])  #  None is for a break between lines
        edge_y.extend([y0, y1, None])
        
        # edge hovertext definition
        info = (
            f"RxCUI: {edge[0]}, {edge[1]}<br>"
            + f"Severity: {G.get_edge_data(edge[0], edge[1])['severity']}<br>"
            + f"Rationale: {G.get_edge_data(edge[0], edge[1])['additional_info']}"
        )

        # generate multiple midpoints (15) for edges
        # (allows users to hover over any given point on edge to see hovertext)
        ptsx, ptsy, ptsh = point_generator(x0, x1, y0, y1, 15, info)
        m2x.extend(ptsx)
        m2y.extend(ptsy)
        m2t.extend(ptsh)

    # create visible line for edges
    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="text",
        mode="lines",
    )

    # create invisible lines for edges for hovertext
    mnode_trace = go.Scatter(
        x=m2x,
        y=m2y,
        mode="markers",
        showlegend=False,
        hovertemplate="%{hovertext}<extra></extra>",
        hovertext=m2t,
        marker=go.scatter.Marker(opacity=0),
    )

    # extract node coordinates and labels
    node_x, node_y, node_text = [], [], [] # init lists for coords and text
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    # scatter for nodes
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(showscale=False, color="blue", size=10, line_width=2),
    )
    
    # node hovertext definition
    n_adjacencies, n_text = [], []
    for node, adjacencies in enumerate(G.adjacency()):
        print(adjacencies[0])
        print(adjacencies[1])
        n_adjacencies.append(len(adjacencies[1]))
        n_text.append(
            f"RxCUI: {adjacencies[0]}<br>"
            + f"Drug name: {graph.vert_list[adjacencies[0]].name}<br>"
            + f"# of connections: {str(len(adjacencies[1]))}<br>"
            + f"# of average shortest path # to other vertices: {str(random_walk(graph.vert_list.keys(), graph, adjacencies[0]))}"
        )

    # pass hovertext and color into the node trace
    node_trace.marker.color = n_adjacencies
    node_trace.text = n_text

    annots = []
    for node, (x, y) in pos.items():
        annots.append(
            dict(x=x, y=y - 0.1, xref="x", yref="y", text=node, showarrow=False)
        )

    # Create a Plotly figure
    fig = go.Figure(
        data=[edge_trace, node_trace, mnode_trace],
        layout=go.Layout(
            title="Drug interactions graph",
            titlefont_size=16,
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=annots,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    # update fig layout to allow click and hover callbacks + minor styling
    fig.add_trace(edge_trace)
    fig.update_layout(clickmode="event+select")
    fig.update_layout(height=700)
    fig.update_traces(marker_size=20)
    return fig


# references:
# 1. https://realpython.com/django-hosting-on-heroku/#step-7-deploy-your-django-project-to-heroku
# 2. https://docs.djangoproject.com/en/4.2/intro/tutorial01/
# 3. https://stackoverflow.com/questions/74607000/python-networkx-plotly-how-to-display-edges-mouse-over-text
# 4. https://plotly.com/python/network-graphs/

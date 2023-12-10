import os
import json
import dash
import flask
import random
import requests
import networkx as nx
from .graph import Graph
from .forms import DrugForm
from collections import deque
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from dash import Dash, dcc, html, State
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
from django.views.decorators.csrf import ensure_csrf_cookie


app = DjangoDash("drug-interaction")
shp_file = gpd.read_file("./my_app/World_Countries_Generalized.zip").drop(
    ["SHAPE_Leng", "SHAPE_Area", "FID", "COUNTRYAFF"], axis=1
)


app.layout = html.Div(
    [
        html.Div("Dash application"),
        dcc.Input(id="query", type="text"),
        html.Div(id="status-div", style={"color": "blue", "height": "20px"}),
        html.Div(
            dcc.Dropdown(
                ["Patient Sex", "Age of onset", "Report nation", "4", "5", "6"],
                "Patient Sex",
                id="dd",
            )
        ),
        html.Button("Submit", id="submit-btn", n_clicks=0),
        # html.Div(id='dd-test', style={"height":"20px", "width":"100px"}),
        html.Div(
            [
                html.Div(dcc.Graph(id="drug-network"), style={"width": "49%"}),
                html.Div(dcc.Graph(id="drill-down"), style={"width": "49%"}),
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


@ensure_csrf_cookie
def index(request):
    greeting_list = ["hello", "bye"]

    # get user option
    if request.method == "POST":
        form = DrugForm(request.POST)
        if form.is_valid():
            # Process form data
            print("form is valid")
            request.session["dash_data"] = form.cleaned_data
            # use functions
            cui_name_pair = getRxNorm(form.cleaned_data["drug"])
            interaction = getInteractionData(list(cui_name_pair.keys()))
            # assembleVisual(buildGraphVisualization(interaction))
            context = {
                "form": form,
                "cached": cui_name_pair,
                "dash-data": json.dumps(form.cleaned_data),
                "graph": buildGraphVisualization(interaction),
                "interaction_data": json.dumps(interaction),
            }
            return render(request, "index.html", context)
    else:
        form = DrugForm()
    context = {"greetings": greeting_list, "only_one": greeting_list[1], "form": form}
    return render(request, "index.html", context)


@app.callback(
    dash.dependencies.Output("drug-network", "figure"),
    dash.dependencies.Output("status-div", "children"),
    dash.dependencies.Input("submit-btn", "n_clicks"),  # click counter - n_clicks
    dash.dependencies.Input("dd", "value"),  # dropdown value - query
    State("query", "value"),  # query string - text
    prevent_initial_call=True,
)
def update_graph(n_clicks, query, text):
    """draws the drug interaction graph"""
    if n_clicks >= 1:
        try:
            print(f"query string is: {text}")
            cui_name_pair = getRxNorm(text)
            interaction = getInteractionData(list(cui_name_pair.keys()))
            return buildGraphVisualization(interaction), "Graph built successfully"
        except ValueError:
            return dcc.Graph(), "Please enter at least two drug names"
        except KeyError:
            return dcc.Graph(), "No interaction is found for this group of drugs!"
    return dash.no_update


@app.callback(
    Output("drill-down", "figure"),
    Input("drug-network", "clickData"),
    Input("dd", "value"),
)
def update_drilldown(click_data, dropdown):
    """updates the drilldown graph"""
    try:
        cui_clicked = click_data["points"][0]["text"].split("<br>")[0].split(": ")[1]
        openFda = getOpenFda(cui_clicked)
    except:
        # when the user clicks on the edge scatter points
        pass
    print(cui_clicked)
    if dropdown == "Patient Sex":
        plot_dict = openFda["sex"]
        fig = px.bar(x=plot_dict.keys(), y=plot_dict.values(), color=plot_dict.keys())
        fig.update_layout(title=f'Gender distribution of adverse events for {cui_clicked}')
        return fig
    elif dropdown == "Age of onset":
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
        plot_data = (
            gpd.GeoDataFrame(openFda["reporting_country"])
            .merge(shp_file, how="inner", left_on="term", right_on="ISO")
            .drop(["term", "AFF_ISO"], axis=1)
        )
        plot_data = plot_data.set_geometry("geometry").set_index("ISO")
        fig = px.choropleth(
            plot_data,
            geojson=plot_data.geometry,
            locations=plot_data.index,
            color="count",
        )
        fig.update_layout(title=f'Reporting country distribution for {cui_clicked}')
        return fig
    elif dropdown == "Reaction type":
        pass


def getRxNorm(query_str):
    query_str = [i.strip().lower() for i in query_str.split(",")]
    if len(query_str) < 2:
        raise ValueError("Please enter at least two drug names")
    cui_name = {}  # dictionary to store cui to drug_name mapping
    with open("./my_app/cache.json", "r") as json_file:
        cache = json.load(json_file)

    for q in query_str:
        if q in cache.keys():
            print("data found in cache")
            cui_name.update(cache[q])  # update cui_name with cached data
        else:
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
    BASE_URL = "https://api.fda.gov/drug/event.json?search=patient.drug.openfda.rxcui"
    results = {}
    # sex
    # 0 unknown, 1 male, 2 female
    content = requests.get(f"{BASE_URL}:%22{cui}%22&count=patient.patientsex").json()
    sex_dict = {0: "unknown", 1: "male", 2: "female"}
    results["sex"] = {sex_dict[i["term"]]: i["count"] for i in content["results"]}
    del content

    #
    content = requests.get(
        f"{BASE_URL}:%22{cui}%22&count=patient.patientonsetage"
    ).json()
    results["age_onset"] = {i["term"]: i["count"] for i in content["results"]}

    results["hospitalization"] = ...
    results["report_date"] = ...

    results["reporting_country"] = requests.get(
        f"{BASE_URL}:%22{cui}%22&count=primarysourcecountry.exact"
    ).json()["results"]
    results["reaction_type"] = ...
    return results


def getInteractionData(cui_list):
    max_len = 50 if len(cui_list) >= 50 else len(cui_list)
    cui_list = random.choices(cui_list, k=max_len)
    cui_str = "+".join(cui_list)
    content = requests.get(
        f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={cui_str}"
    ).json()
    return content


def buildGraphVisualization(interaction):
    # Function to create a NetworkX graph from your graph structure

    def queue(a, b, qty):
        """either x0 and x1 or y0 and y1, qty of points to create"""
        q = deque()
        q.append((0, qty - 1))  # indexing starts at 0
        pts = [0] * qty
        pts[0] = a
        pts[-1] = b  # x0 is the first value, x1 is the last
        while len(q) != 0:
            left, right = q.popleft()  # remove working segment from queue
            center = (left + right + 1) // 2  # creates index values for pts
            pts[center] = (pts[left] + pts[right]) / 2
            if right - left > 2:  # stop when qty met
                q.append((left, center))
                q.append((center, right))
        return pts

    def collector(x0, x1, y0, y1, qty, ht):
        """line segment end points, how many midpoints, hovertext"""
        pth = [ht] * qty
        ptx = queue(x0, x1, qty + 2)  # add 2 because the origin will be in the list
        pty = queue(y0, y1, qty + 2)
        ptx.pop(0)
        ptx.pop()  # pop first and last (the nodes)
        pty.pop(0)
        pty.pop()  # pop first and last (the nodes)
        return ptx, pty, pth

    def nxGraph(drug_graph):
        G = nx.Graph()
        for vertex in drug_graph.vert_list.values():
            G.add_node(vertex.id)
            for neighbor in vertex.connectedTo:
                G.add_edge(
                    vertex.id,
                    neighbor.id,
                    severity=vertex.connectedTo[neighbor].severity,
                    additional_info=vertex.connectedTo[neighbor].additional_info,
                )
        return G

    graph = Graph()
    for i in interaction["fullInteractionTypeGroup"]:
        for j in i["fullInteractionType"]:
            graph.add_edge(
                j["minConcept"][0]["rxcui"],
                j["minConcept"][0]["name"],
                j["minConcept"][1]["rxcui"],
                j["minConcept"][1]["name"],
                i["sourceName"],
                j["interactionPair"][0]["severity"],
                j["interactionPair"][0]["description"],
            )

    # Convert graph to a NetworkX graph
    G = nxGraph(graph)

    # Generate positions for each node using NetworkX
    pos = nx.spring_layout(G)

    # Extracting edge coordinates from the positions
    edge_x = []
    edge_y = []
    m2x, m2y, m2t = [], [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])  # Add None to create a break between lines
        edge_y.extend([y0, y1, None])

        info = (
            f"RxCUI: {edge[0]}, {edge[1]}<br>"
            + f"Severity: {G.get_edge_data(edge[0], edge[1])['severity']}<br>"
            + f"Rationale: {G.get_edge_data(edge[0], edge[1])['additional_info']}"
        )

        ptsx, ptsy, ptsh = collector(x0, x1, y0, y1, 15, info)
        m2x.extend(ptsx)
        m2y.extend(ptsy)
        m2t.extend(ptsh)

    # Create a trace for edges
    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="text",
        mode="lines",
    )

    mnode_trace = go.Scatter(
        x=m2x,
        y=m2y,
        mode="markers",
        showlegend=False,
        hovertemplate="%{hovertext}<extra></extra>",
        hovertext=m2t,
        marker=go.scatter.Marker(opacity=0),
    )

    # Extracting node coordinates and labels
    node_x = []
    node_y = []
    node_text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    # Create a trace for nodes
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(showscale=False, color="blue", size=10, line_width=2),
    )

    n_adjacencies = []
    n_text = []

    for node, adjacencies in enumerate(G.adjacency()):
        n_adjacencies.append(len(adjacencies[1]))
        n_text.append(
            f"RxCUI: {adjacencies[0]}<br>"
            + f"Drug name: {graph.vert_list[adjacencies[0]].name}<br>"
            + f"# of connections: {str(len(adjacencies[1]))}"
        )

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
            title="<br>Drug interactions graph",
            titlefont_size=16,
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=annots,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

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

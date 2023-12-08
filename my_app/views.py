import requests
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import DrugForm
from .graph import Graph
import plotly.graph_objects as go
import networkx as nx
import json 
import random
import os

@ensure_csrf_cookie
def index(request):
    greeting_list = ["hello", "bye"]

    # get user option
    if request.method == "POST":
        form = DrugForm(request.POST)
        if form.is_valid():
            # Process form data
            print("form is valid")
            drug = form.cleaned_data['drug']
            sex = form.cleaned_data['sex']
            age_onset = form.cleaned_data['age_onset']
            hospitalization = form.cleaned_data['hospitalization']
            report_date = form.cleaned_data['report_date']
            reporting_country = form.cleaned_data['reporting_country']
            reaction_type = form.cleaned_data['reaction_type']

            print(drug, age_onset)
            # use functions 
            cui_name_pair = getRxNorm(drug)
            interaction = getInteractionData(list(cui_name_pair.keys()))

            context = {
               'form': form,
               'cached': cui_name_pair,
               'graph': buildGraphVisualization(interaction),
               }

            return render(request, "index.html", context)

    else: 
        form = DrugForm()

    context = {"greetings": greeting_list, 
               "only_one": greeting_list[1], 
               'form': form}
    
    return render(request, "index.html", context)

def getRxNorm(query_str):
    query_str = [i.strip().lower() for i in query_str.split(',')]
    cui_name = {}  # dictionary to store cui to drug_name mapping
    with open("./my_app/cache.json", 'r') as json_file:
        cache = json.load(json_file)
    
    for q in query_str:
        if q in cache.keys(): 
            print("data found in cache")
            cui_name.update(cache[q])  # update cui_name with cached data
        else: 
            print("Fetching new data")
            response = requests.get(f'https://rxnav.nlm.nih.gov/REST/drugs.json?name={q}').json()
            new_data = {}  # temporary dictionary to store new API data
            try:
                for i in response['drugGroup']['conceptGroup']:
                    if 'conceptProperties' in i:
                        for j in i['conceptProperties']:
                            new_data[j['rxcui']] = j['name']
                cache[q] = new_data  # update cache with new data for q
                cui_name.update(new_data)  # update cui_name with new API data
            except KeyError:
                pass

    # Update the cache file only once after processing all queries
    with open("./my_app/cache.json", "w") as f:
        json.dump(cache, f)

    return cui_name

def getOpenFda(cui, sex, age_onset, hospitalization, report_date, reporting_country, reaction_type):
    results = {}
    # TODO: parse data
    if sex: 
        results['sex'] = ...
    if age_onset:
        results['age_onset'] = ...
    if hospitalization:
        results['hospitalization'] = ...
    if report_date:
        results['report_date'] = ...
    if reporting_country:
        results['reporting_country'] = ...
    if reaction_type:
        results['reaction_type'] = ...
    return results

def getInteractionData(cui_list):
    max_len = 50 if len(cui_list) >= 50 else len(cui_list)
    cui_list = random.choices(cui_list, k=max_len)
    cui_str = '+'.join(cui_list)
    content = requests.get(f'https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={cui_str}').json()
    return content


def buildGraphVisualization(interaction):
    # Function to create a NetworkX graph from your graph structure
    def create_networkx_graph(drug_graph):
        G = nx.Graph()
        for vertex in drug_graph.vert_list.values():
            G.add_node(vertex.id)
            for neighbor in vertex.connectedTo:
                G.add_edge(vertex.id, neighbor.id)
        return G
    
    graph = Graph()
    for i in interaction['fullInteractionTypeGroup']:
        for j in i['fullInteractionType']:
            graph.add_edge(
                j['minConcept'][0]['rxcui'],
                j['minConcept'][0]['name'],
                j['minConcept'][1]['rxcui'],
                j['minConcept'][1]['name'],
                i['sourceName'],
                j['interactionPair'][0]['severity'],
                j['interactionPair'][0]['description']
            )


    # Convert your graph to a NetworkX graph
    G = create_networkx_graph(graph)

    # Generate positions for each node using NetworkX
    pos = nx.spring_layout(G)

    # Extracting edge coordinates from the positions
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])  # Add None to create a break between lines
        edge_y.extend([y0, y1, None])

    # Create a trace for edges
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

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
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=False,
            color='blue',
            size=10,
            line_width=2))

    n_adjacencies = []
    n_text = []

    for node, adjacencies in enumerate(G.adjacency()):
        n_adjacencies.append(len(adjacencies[1]))
        n_text.append('# of connections: '+str(len(adjacencies[1])))

    node_trace.marker.color = n_adjacencies
    node_trace.text = n_text

    # Create a Plotly figure
    fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title='<br>Drug interactions graph',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[ dict(
                        text="Drug network graph",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002 ) ],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))

    return fig.to_html()



# references:
# 1. https://realpython.com/django-hosting-on-heroku/#step-7-deploy-your-django-project-to-heroku
# 2. https://docs.djangoproject.com/en/4.2/intro/tutorial01/

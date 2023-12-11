from graph import Graph
import requests
import json
import networkx as nx
import matplotlib.pyplot as plt

# get data
content = requests.get(
    "https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis=207106+152923+656659+828557+828555+209387+1738139"
).json()

# build graph
graph = Graph()
for i in content['fullInteractionTypeGroup']:
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


# use 2 level nested dict
# 1: from rxcui: [from name, level 2 dict]
# 2: to rxcui: [to name, source, severity, additional info]
graph_json = {}
for i in graph.vert_list:
    for j in graph.vert_list[i].connectedTo:
        graph_json[i] = [ # from rxcui
            graph.vert_list[i].name,  # from rx name
            {
                j.id: [ # to rxcui
                    graph.vert_list[j.id].name,  # to rx name
                    graph.vert_list[i].connectedTo[j].source,  # source of info
                    graph.vert_list[i].connectedTo[j].severity, # severity of interaction
                    graph.vert_list[i].connectedTo[j].additional_info, # additional info abt. interaction
                ] for j in graph.vert_list[i].connectedTo # have to account for all connections
            },
        ]

# dump to json
with open("graph.json", "w") as f:
    json.dump(graph_json, f)

del graph_json

with open("graph.json", "r") as f:
    graph_json = json.load(f)

new_graph = Graph()

# i - key, v - list of value (0 is from rxcui, 1 is interaction)
for i, v in zip(graph_json.keys(), graph_json.values()):
    # get interaction from v
    # j is to rxcui, k is to interaction data
    # k 0 : to name
    # k 1 : source
    # k 2 : severity
    # k 3 : additional info
    for j, k in zip(v[1].keys(), v[1].values()):
        new_graph.add_edge(
            i,
            v[0],
            j,
            k[0],
            k[1],
            k[2],
            k[3],
        )

# check to see if the graph is working
def create_networkx_graph(g):
    G = nx.Graph()
    for vertex in g.vert_list.values():
        for edge in vertex.connectedTo.values():
            G.add_edge(edge.src.id, edge.dest.id)

    pos = nx.spring_layout(G)  # positions for all nodes
    nx.draw(G, pos, with_labels=True)
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.title("Example Drug graph")
    plt.show()
    return G

g = create_networkx_graph(new_graph)
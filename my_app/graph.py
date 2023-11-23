"""Definition for graph, edge, and vertex"""

class Edge:
    def __init__(self, src, dest, source, severity, additional_info):
        self.src = src # source
        self.dest = dest # destination 
        self.source = source  # source of info
        self.severity = severity  # severity of interaction
        self.additional_info = additional_info  # description of interaction

    def __str__(self):
        return f"{self.src.id} and {self.dest.id} has interaction \"{self.additional_info}\"\n"

class Vertex:
    def __init__(self, value, name):
        self.id = value # RxNorm CUI
        # TODO: Name
        self.name = name
        # TODO: User choices - implemented patient sex agg. only
        # self.reaction_sex = reaction_sex

        self.connectedTo = {}  # Key: Vertex, Value: Edge

    def __str__(self):
        return f"{''.join([str(edge) for edge in self.connectedTo.values()])}"

    def add_neighbor(self, nbr, edge):
        self.connectedTo[nbr] = edge

class Graph:
    def __init__(self):
        self.vert_list = {}  # vertices
        self.num_vertices = 0

    def add_vertex(self, key, name):
        self.num_vertices += 1
        new_vertex = Vertex(key, name)
        self.vert_list[key] = new_vertex
        return new_vertex

    def add_edge(self, f, f_name, t, t_name, source, severity, additional_info):
        # vertex
        if f not in self.vert_list:
            self.add_vertex(f, f_name)
        if t not in self.vert_list:
            self.add_vertex(t, t_name)

        # edge
        edge = Edge(self.vert_list[f], self.vert_list[t], source, severity, additional_info)
        self.vert_list[f].add_neighbor(self.vert_list[t], edge)
        # If the graph is undirected, you might also want to add the reverse edge:
        reverse_edge = Edge(self.vert_list[t], self.vert_list[f], source, severity, additional_info)
        self.vert_list[t].add_neighbor(self.vert_list[f], reverse_edge)

# Example usage
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

print(graph.vert_list["207106"])
"""Definition for graph, edge, and vertex"""
from collections import deque
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
        # construct undirected graph
        reverse_edge = Edge(self.vert_list[t], self.vert_list[f], source, severity, additional_info)
        self.vert_list[t].add_neighbor(self.vert_list[f], reverse_edge)

def bfs(graph, start, end):
    visited = set()
    # use deque to hold start vertex and distance 
    queue = deque([(start, 0)])

    while queue:
        current_id, distance = queue.popleft()
        if current_id == end:
            return distance

        if current_id not in visited:
            visited.add(current_id)
            current = graph.vert_list[current_id]
            for neighbor in current.connectedTo:
                if neighbor.id not in visited:
                    queue.append((neighbor.id, distance + 1))

    return None # no paths found
"""
Exampel usage: 
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
print(bfs(graph, "828555", "209387"))
"""
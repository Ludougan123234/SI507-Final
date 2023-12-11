"""Definition for graph, edge, and vertex"""
from collections import deque
from math import inf
import random
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
    if start == end:
        return 0
    
    visited = set()
    # use deque to hold start vertex and distance 
    queue = deque([(start, 0)])

    while queue:
        cur_id, path = queue.popleft()
        if cur_id == end:
            return path

        if cur_id not in visited:
            visited.add(cur_id)
            current = graph.vert_list[cur_id]
            for neighbor in current.connectedTo:
                if neighbor.id not in visited:
                    queue.append((neighbor.id, path + 1))

    return 0 # no paths found

def weight_avg(n, avg_old, distance):
    """Helper function to compute weighted average

    Parameters
    ----------
    n : float
        current iteration number
    avg_old : float
        Cumulative average
    distance : float
        New distance computed based on the `opt1()` function

    Returns
    -------
    float
        The weighted average of the path length
    """
    return ((n * avg_old) + distance) / (n + 1)

def random_walk(drug_li, drug_graph, user_choice):
    n = 0  # actor counter
    avg_diff = inf
    avg_old = 0
    avg_all = []
    drug_li = list(drug_li)

    while avg_diff > 0.01:
        # choose actor randomly
        chosen = []
        random_act = random.choice(drug_li)
        if random_act not in chosen:
            chosen.append(random_act)
            # calculate distance from BK to actor
            distance = bfs(drug_graph, start=user_choice, end=random_act)
            # get list length for actor path
            # distance = len(distance) - 1
            if distance > 0:
                avg = weight_avg(n, avg_old, distance)
                avg_all.append(avg)
                avg_diff = abs(avg - avg_old)
                # print(f"distance: {distance}, avg: {avg}, avg_diff: {avg_diff}")
                avg_old = avg
                n += 1
    return sum(avg_all) / len(avg_all)


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
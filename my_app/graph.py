"""Contains definitions for graphs, vertex, and edge"""

class Edge:
    def __init__(self, src, dest, weight=0, additional_info=None):
        self.src = src
        self.dest = dest
        self.weight = weight
        self.additional_info = additional_info

    def __str__(self):
        return f"Edge from {self.src.id} to {self.dest.id} with weight {self.weight} and info {self.additional_info}"

class Vertex:
    def __init__(self, value):
        self.id = value
        self.connectedTo = {}  # Key: Vertex, Value: Edge

    def __str__(self):
        return f"{self.id} is connected to {', '.join([str(edge) for edge in self.connectedTo.values()])}"

    def add_neighbor(self, nbr, edge):
        self.connectedTo[nbr] = edge

class Graph:
    def __init__(self):
        self.vert_list = {}  # vertices
        self.num_vertices = 0

    def add_vertex(self, key):
        self.num_vertices += 1
        new_vertex = Vertex(key)
        self.vert_list[key] = new_vertex
        return new_vertex

    def add_edge(self, f, t, weight=0, additional_info=None):
        if f not in self.vert_list:
            self.add_vertex(f)
        if t not in self.vert_list:
            self.add_vertex(t)
        
        edge = Edge(self.vert_list[f], self.vert_list[t], weight, additional_info)
        self.vert_list[f].add_neighbor(self.vert_list[t], edge)
        # undirected graph
        reverse_edge = Edge(self.vert_list[t], self.vert_list[f], weight, additional_info)
        self.vert_list[t].add_neighbor(self.vert_list[f], reverse_edge)
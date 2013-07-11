import cPickle as pickle
import copy

from google.appengine.ext import db


class Edge():

    """Represents an edge between two nodes with four attributes -
    start node ID, end node ID, link quality and neighbor link quality.

    """

    def __init__(self, from_node, to_node, lq, nlq, link_type=''):
        self.from_node = from_node
        self.to_node = to_node
        self.lq = lq
        self.nlq = nlq
        self.link_type = link_type

    def get_weight(self):

        """Returns the weight, i.e. the ETX value, for an instance of this class.

        """
        
        return float(1 / (float(self.lq) * float(self.nlq)))
    
    def __eq__(self, other_edge):
        if (self.from_node == other_edge.from_node and self.to_node == other_edge.to_node and
            self.lq == other_edge.lq and self.nlq == other_edge.nlq):
            return True
        return False
    
    def __cmp__(self, other_edge):
        if self.get_weight() == other_edge.get_weight():
            return 0
        if self.get_weight() < other_edge.get_weight():
            return -1
        return 1
    
    def __str__(self):
        return self.from_node + ' -> ' + self.to_node + ' ' + str(self.get_weight())

class Node:
    
    def __init__(self, name):
        self.name = name
        
    def __str__(self):
        return self.name
    
class NetworkGraph():
    
    """Implements a graph based on an adjacency matrix."""
    
    def __init__(self, adjacency_matrix_arg=None, time_arg='Unknown', date_arg='Unknown'):
        if adjacency_matrix_arg is None:
            self.adjacency_matrix = {}
        else:
            self.adjacency_matrix = adjacency_matrix_arg
        self.all_nodes = set([])
        self.predecessors = {}
        self.timestamp_time = time_arg
        self.timestamp_date = date_arg
        self.backbone_nodes = set([])
        
    def add_edge(self, from_node, to_node, lq, nlq, link_type=''):

        """Add an entry for from_node and to_node."""

        if from_node not in self.adjacency_matrix:
            self.adjacency_matrix[from_node] = {}
        edge = Edge(from_node, to_node, lq, nlq, link_type)
        (self.adjacency_matrix[from_node])[to_node] = edge
        
        # Add nodes to list of nodes
        self.all_nodes.add(from_node)
        self.all_nodes.add(to_node)
        
    def get_edge(self, node1, node2):

        """Returns the edge between node1 and node2 or None if there is
        no such edge.

        """

        if node1 in self.adjacency_matrix:
            inner = self.adjacency_matrix[node1]
            if node2 in inner:
                return inner[node2]
        return None

    def remove_edge(self, edge):

        """Removes an edge from the graph."""
        
        (self.adjacency_matrix[edge.from_node]).pop(edge.to_node)

    def get_shortest_paths(self, start_node, end_node=None):

        """Implements Dijkstra algorithm to calculate the shortest paths
        for a given node start_node to all other nodes.
        Returns a set of lists of the form
        [other_node, distance_to_other_node, path_between_them].
        If the parameter end_node is given, the algorithm will come to an end
        when end_node has been reached and return the distance of the shortest path
        between start_node and end_node.

        """
        
        distances = {}
        nodes = self.get_all_nodes()

        #Initialization
        distances[start_node] = 0
        self.predecessors[start_node] = None
        for node in nodes:
            if node != start_node:
                # float('infinity') returns the largest floating point value.
                # Could create problems on some platforms.

                distances[node] = float('infinity')
                self.predecessors[node] = None

        while len(nodes) > 0:
            candidates = nodes.intersection(distances.keys())
            min_distance = float('infinity')
            min_dist_node = None
            for candidate in candidates:
                if distances[candidate] <= min_distance:
                    min_distance = distances[candidate]
                    min_dist_node = candidate
            # If an end node was given, return the minimal distance.
            if min_dist_node == end_node:
                return min_distance
            nodes.remove(min_dist_node)
            for node in nodes:
                if(self.get_edge(min_dist_node, node) is not None):
                    if distances[node] > distances[min_dist_node] + self.get_edge(min_dist_node, node).get_weight():
                        distances[node] = distances[min_dist_node] + self.get_edge(min_dist_node, node).get_weight()
                        self.predecessors[node] = min_dist_node

        distances_set = []

        for other_node in distances.keys():
            distances_set.append([other_node, distances[other_node], self.get_shortest_path_by_nodes(start_node, other_node)])

        return distances_set

    def get_shortest_path_by_nodes(self, start_node, end_node):

        """Return the shortest path between two nodes as a list."""

        path = []

        path.append(end_node)
        temp_node = self.predecessors[end_node]
        
        while temp_node != start_node and temp_node is not None:
            path.append(temp_node)
            temp_node = self.predecessors[temp_node]
        
        path.append(start_node)
        path.reverse()

        return path
    
    def is_connected(self):
        
        """Checks if the graph is connected. Uses depth first search."""
        
        graph_nodes = self.get_all_nodes()
        
        start_node = (list(self.get_all_nodes()))[0]
        visited_nodes = []
        
        self.depth_first_search(start_node, visited_nodes)
         
        # Check if graph is still connected...
        for graph_node in graph_nodes:
            if not graph_node == start_node and not graph_node in visited_nodes:
                # Graph is not connected
                return False
            
        return True
    
    def depth_first_search(self, start_node, visited_nodes):
        
        """Recursive depth first search for a given start_node.
        When this method is called from outside, the parameter visited_nodes
        must be passed [] as a value. 
        
        """
        
        node_stack = self.get_all_adjacent_nodes(start_node)
        while len(node_stack) > 0:
            neighbor_node = node_stack.pop()
            if not neighbor_node in visited_nodes:
                visited_nodes.append(neighbor_node)
                self.depth_first_search(neighbor_node, visited_nodes)
    
    def get_all_edges(self):

        """Returns a list of all edges for an instance of this class."""

        edges = []
        for node1 in self.adjacency_matrix.keys():
            inner = self.adjacency_matrix[node1]
            for node2 in inner.keys():
                edges.append(inner[node2])
        return edges
    
    def get_all_nodes(self):
        
        """Returns a set of all nodes for an instance of this class."""
        
        return copy.deepcopy(self.all_nodes)
    
    def get_all_edges_by_node(self, node):
        
        """Returns all edges for a given node "node" in the form (other_node, edge_to_other_node). If there are
        no connections for a given node or the node has not been found, [] will be returned."""
        
        allConnections = []
        if node in self.adjacency_matrix:
            inner = self.adjacency_matrix[node]
        else:
            return []
        for key in inner:
            allConnections.append((key, inner[key]))
        return allConnections
    
    def get_all_adjacent_nodes(self, node):
        
        """Returns all nodes adjacent to a given node."""
        
        adjacent_nodes = []
        connections = self.get_all_edges_by_node(node)
        for connection in connections:
            adjacent_nodes.append(connection[0])
        return adjacent_nodes
    
    def get_median(self):
        
        """Calculates the median for all edge weights."""
        
        weights = []
        edges = self.get_all_edges()
        if len(edges) == 0:
            return
        for edge in edges:
            weights.append(edge.get_weight())
        weights.sort()
        position = len(weights) / 2
        if (len(weights) % 2) != 0:
            return weights[position]
        median = float(weights[position] + weights[position - 1]) / 2.0
        return median
    
    def get_arithmetic_mean(self):
        
        """Calculates the arithmetic mean for all edge weights."""
        
        _sum = 0.0
        edges = self.get_all_edges()
        if len(edges) == 0:
            return
        for edge in edges:
            _sum += edge.get_weight()
        return float(_sum) / float(len(edges))
    
    def get_median_for_node(self, node):
        
        """Calculates the median for the links of a given node."""
        
        weights = []
        edges = self.get_all_edges_by_node(node)
        
        if len(edges) == 0:
            return None
        
        for _, edge in edges:
            weights.append(edge.get_weight())
        
        weights.sort()
        
        position = len(weights) / 2
        
        if (len(weights) % 2) != 0:
            return weights[position]
        
        median = float(weights[position] + weights[position - 1]) / 2.0
        
        return median
    
    def get_arithmetic_mean_for_node(self, node):
        
        """Calculates the arithmetic mean for the links of a given node."""
        
        _sum = 0.0
        edges = self.get_all_edges_by_node(node)
        
        if len(edges) == 0:
            return None
        
        for _, edge in edges:
            _sum += edge.get_weight()
        
        return float(_sum) / float(len(edges))
    
    def set_time_and_date(self, t_time, t_date):
        
        """Sets time and date extracted from the time stamp file."""
        
        self.timestamp_time = t_time
        self.timestamp_date = t_date
    
    def create_dot_representation(self):
        
        """Returns a string that describes the graph in Dot format."""
        
        edges = self.get_all_edges()
        dot_string = 'graph{'
        for edge in edges:
            dot_string += '\"' + edge.from_node + '\"' + '--' + '\"' + edge.to_node + '\"[label=\"' + str(edge.get_weight()) + '\"];' + '\n'
        dot_string += '}'
        return dot_string
    
    def get_model(self, type='NetworkGraphModel'):
        
        """Returns an instance of class NetworkGraphModel."""
        
        # Serialize attribute 'adjacency_matrix' in order to store it as a Text attribute
        adjacency_matrix_serialized = pickle.dumps(self.adjacency_matrix)
    
        # Serialize attribute 'backbone_nodes' in order to store it as a Text attribute
        backbone_nodes_serialized = pickle.dumps(self.backbone_nodes)
        
        # Serialize attribute 'all_nodes' in order to store it as a Text attribute
        all_nodes_serialized = pickle.dumps(self.all_nodes)
        
        if type == 'NetworkGraphModel':
        
            return NetworkGraphModel(adjacency_matrix=adjacency_matrix_serialized, backbone_nodes=backbone_nodes_serialized,
                                     all_nodes=all_nodes_serialized, timestamp_time=self.timestamp_time, 
                                     timestamp_date=self.timestamp_date)
            
        else:
            
            return ModifiedNetworkGraphModel(adjacency_matrix=adjacency_matrix_serialized, backbone_nodes=backbone_nodes_serialized,
                                     all_nodes=all_nodes_serialized, timestamp_time=self.timestamp_time, 
                                     timestamp_date=self.timestamp_date)

    def add_backbone_nodes(self, backbone_nodes):
        self.backbone_nodes = backbone_nodes
        
    def add_all_nodes(self, nodes_list):
        self.all_nodes = nodes_list

    def __str__(self):
        returnString = ''
        for key1 in self.adjacency_matrix.keys():
            returnString += key1
            returnString += " -> \n \t \t"
            for key2 in self.adjacency_matrix[key1].keys():
                returnString += key2 + ' ' + str((self.adjacency_matrix[key1])[key2]) + '\n \t \t'
            returnString += '\n'
        return returnString

class NetworkGraphModel(db.Model):
    """Serves as a model for the NetworkGraph class. It should be created 
    from an instance of the NetworkGraph class.
    
    """
    
    adjacency_matrix = db.TextProperty(required=True)
    backbone_nodes = db.TextProperty(required=True)
    all_nodes = db.TextProperty(required=True)
    timestamp_time = db.StringProperty(required=True)
    timestamp_date = db.StringProperty(required=True)
    
    def recreate_network_graph(self):
        
        # De-serialize adjacency matrix
        adjacency_matrix_deserialized = pickle.loads(str(self.adjacency_matrix))
                
        # De-serialize list of backbone nodes
        backbone_nodes_deserialized = pickle.loads(str(self.backbone_nodes))     
                
        # De-serialize list of all nodes
        all_nodes_deserialized = pickle.loads(str(self.all_nodes))
                
        ret_network_graph = NetworkGraph(adjacency_matrix_arg=adjacency_matrix_deserialized, time_arg=self.timestamp_time,
                                         date_arg=self.timestamp_date)
    
        ret_network_graph.add_backbone_nodes(backbone_nodes_deserialized)

        ret_network_graph.add_all_nodes(all_nodes_deserialized)

        return ret_network_graph

# This model is only created to distinguish the original graph
# from the modified ones.
class ModifiedNetworkGraphModel(NetworkGraphModel):
    
    pass

if __name__ == '__main__':
    network_graph = NetworkGraph()
    network_graph.add_edge('a', 'b', 1.0, 1.0 / 3.0)
    network_graph.add_edge('a', 'c', 1.0, 1.0 / 8.0)
    network_graph.add_edge('b', 'd', 1.0, 1.0)
    network_graph.add_edge('b', 'e', 1.0, 1.0 / 5.0)
    network_graph.add_edge('c', 'b', 1.0, 1.0 / 2.0)
    network_graph.add_edge('c', 'f', 1.0, 1.0 / 7.0)
    network_graph.add_edge('d', 'e', 1.0, 1.0)
    network_graph.add_edge('e', 'f', 1.0, 1.0 / 3.0)
    

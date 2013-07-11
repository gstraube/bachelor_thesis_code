import copy
import logging

class NodeSelector:
    
    """Provides methods to select a subset of all nodes that will be considered for channel assignment."""
    
    def __init__(self, network_graph, min_links=0, min_neighbors=0):
        self.network_graph = network_graph
        self.selected_nodes = set([])
        self.min_links = min_links
        self.min_neighbors = min_neighbors
        
    def select_by_links(self):
        """Select all nodes whose number of links is at least min_links."""
        
        if self.min_links == 0:
            return self.network_graph.get_all_nodes()
        
        selected_nodes_by_links = []
        nodes = self.network_graph.get_all_nodes()
        for node in nodes:
            edges = self.network_graph.get_all_edges_by_node(node)
            if len(edges) >= self.min_links:
                selected_nodes_by_links.append(node)
                
        return selected_nodes_by_links
    
    def select_by_neighbors(self):
        """Select all nodes whose number of 2 hop neighbors is at least the value 
        of min_neighbors.
        
        """
        
        if self.min_neighbors == 0:
            return self.network_graph.get_all_nodes()
        
        selected_nodes_by_neighbors = []
        nodes = self.network_graph.get_all_nodes()
        
        for node in nodes:
            direct_neighbors = self.network_graph.get_all_adjacent_nodes(node)
            two_hop_neighbors = []
            for direct_neighbor in direct_neighbors:
                two_hop_neighbors.extend(self.network_graph.get_all_adjacent_nodes(direct_neighbor))
            if len(two_hop_neighbors) >= self.min_neighbors:
                selected_nodes_by_neighbors.append(node)
                
        return selected_nodes_by_neighbors
    
    def __filter_backbone_nodes(self):
        backbone_nodes = self.network_graph.backbone_nodes
        selected_nodes_copy = copy.copy(self.selected_nodes)
        for selected_node in selected_nodes_copy:
            if selected_node in backbone_nodes:
                self.selected_nodes.remove(selected_node)
        
    def select_nodes(self):
        """Select nodes according to different criteria and compute the intersection."""
        
        selected_nodes_by_links = set(self.select_by_links())
        selected_nodes_by_neighbors = set(self.select_by_neighbors())
        
        self.selected_nodes = selected_nodes_by_links.intersection(selected_nodes_by_neighbors)
        
        # Filter out all backbone nodes
        self.__filter_backbone_nodes()
        
        return list(self.selected_nodes)

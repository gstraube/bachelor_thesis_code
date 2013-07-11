import unittest

from google.appengine.ext import db
from google.appengine.ext import testbed

from network_graph import NetworkGraph, Edge

from node_selection import NodeSelector
from channel_assignment import ChannelAssignmentModel, EvaluationModel

class NetworkGraphTestCase(unittest.TestCase):
    
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        
        self.network_graph = NetworkGraph()
        self.network_graph.add_edge('a', 'b', 1.0, 1.0 / 3.0)
        self.network_graph.add_edge('a', 'c', 1.0, 1.0 / 8.0)
        self.network_graph.add_edge('a', 'd', 1.0, 1.0 / 9.0)
        self.network_graph.add_edge('b', 'd', 1.0, 1.0)
        self.network_graph.add_edge('b', 'e', 1.0, 1.0 / 5.0)
        self.network_graph.add_edge('c', 'b', 1.0, 1.0 / 2.0)
        self.network_graph.add_edge('c', 'f', 1.0, 1.0 / 7.0)
        self.network_graph.add_edge('d', 'e', 1.0, 1.0)
        self.network_graph.add_edge('e', 'f', 1.0, 1.0 / 3.0)
        
    def tearDown(self):
        self.testbed.deactivate()
        
    def testGetShortestPaths(self):
        shortest_paths = self.network_graph.get_shortest_paths('a')
        self.assertEqual(6, len(shortest_paths))
        self.assertTrue(['a', 0, ['a', 'a']] in shortest_paths)
        self.assertTrue(['b', 3, ['a', 'b']] in shortest_paths)
        self.assertTrue(['c', 8, ['a', 'c']] in shortest_paths)
        self.assertTrue(['d', 4, ['a', 'b', 'd']] in shortest_paths)        
        self.assertTrue(['e', 5, ['a', 'b', 'd', 'e']] in shortest_paths)       
        self.assertTrue(['f', 8, ['a', 'b', 'd', 'e', 'f']] in shortest_paths) 
        
        distance = self.network_graph.get_shortest_paths('a', 'd')        
        self.assertEqual(4, distance)
        
        distance = self.network_graph.get_shortest_paths('b', 'f')        
        self.assertEqual(5, distance)
        
        distance = self.network_graph.get_shortest_paths('c', 'd')        
        self.assertEqual(3, distance)
        
        distance = self.network_graph.get_shortest_paths('a', 'b')        
        self.assertEqual(3, distance)
        
        
    def testGetMedian(self):
        self.assertEqual(3, self.network_graph.get_median())
    
    def testGetArithmeticMean(self):
        self.assertEqual(4.333333333333333, self.network_graph.get_arithmetic_mean())
    
    def testGetEdge(self):
        self.assertTrue(Edge('a', 'b', 1.0, 1.0 / 3.0) == self.network_graph.get_edge('a', 'b'))
        self.assertTrue(Edge('a', 'c', 1.0, 1.0 / 8.0) == self.network_graph.get_edge('a', 'c'))
        self.assertTrue(Edge('b', 'd', 1.0, 1.0 / 1.0) == self.network_graph.get_edge('b', 'd'))
        self.assertTrue(Edge('b', 'e', 1.0, 1.0 / 5.0) == self.network_graph.get_edge('b', 'e'))
        self.assertTrue(Edge('d', 'e', 1.0, 1.0 / 1.0) == self.network_graph.get_edge('d', 'e'))
        self.assertTrue(Edge('c', 'b', 1.0, 1.0 / 2.0) == self.network_graph.get_edge('c', 'b'))
        self.assertTrue(Edge('c', 'f', 1.0, 1.0 / 7.0) == self.network_graph.get_edge('c', 'f'))
        self.assertTrue(Edge('e', 'f', 1.0, 1.0 / 3.0) == self.network_graph.get_edge('e', 'f'))
        self.assertEqual(None, self.network_graph.get_edge('a', 'e'))
        self.assertEqual(None, self.network_graph.get_edge('q', 'd'))
    
    def testGetAllEdges(self):
        edges = self.network_graph.get_all_edges()
        self.assertEqual(9, len(edges))
        self.assertTrue(Edge('a', 'b', 1.0, 1.0 / 3.0) in edges)
        self.assertTrue(Edge('a', 'c', 1.0, 1.0 / 8.0) in edges)
        self.assertTrue(Edge('a', 'd', 1.0, 1.0 / 9.0) in edges)
        self.assertTrue(Edge('b', 'd', 1.0, 1.0 / 1.0) in edges)
        self.assertTrue(Edge('b', 'e', 1.0, 1.0 / 5.0) in edges)
        self.assertTrue(Edge('d', 'e', 1.0, 1.0 / 1.0) in edges)
        self.assertTrue(Edge('c', 'b', 1.0, 1.0 / 2.0) in edges)
        self.assertTrue(Edge('c', 'f', 1.0, 1.0 / 7.0) in edges)
        self.assertTrue(Edge('e', 'f', 1.0, 1.0 / 3.0) in edges)
    
    def testGetAllNode(self):
        nodes = self.network_graph.get_all_nodes()
        self.assertEqual(6, len(nodes))
        self.assertTrue('a' in nodes)
        self.assertTrue('b' in nodes)
        self.assertTrue('c' in nodes)
        self.assertTrue('d' in nodes)
        self.assertTrue('e' in nodes)
        self.assertTrue('f' in nodes)
    
    def testGetAllConnectionsByNode(self):
        connections = self.network_graph.get_all_edges_by_node('a')
        self.assertEqual(3, len(connections))
        self.assertTrue(('b', Edge('a', 'b', 1.0, 1.0 / 3.0)) in connections)
        self.assertTrue(('c', Edge('a', 'c', 1.0, 1.0 / 8.0)) in connections)
        self.assertTrue(('d', Edge('a', 'd', 1.0, 1.0 / 9.0)) in connections)
        
        connections = self.network_graph.get_all_edges_by_node('b')
        self.assertEqual(2, len(connections))
        self.assertTrue(('d', Edge('b', 'd', 1.0, 1.0 / 1.0)) in connections)
        self.assertTrue(('e', Edge('b', 'e', 1.0, 1.0 / 5.0)) in connections)
        
        connections = self.network_graph.get_all_edges_by_node('c')
        self.assertEqual(2, len(connections))
        self.assertTrue(('b', Edge('c', 'b', 1.0, 1.0 / 2.0)) in connections)
        self.assertTrue(('f', Edge('c', 'f', 1.0, 1.0 / 7.0)) in connections)
        
        connections = self.network_graph.get_all_edges_by_node('d')
        self.assertEqual(1, len(connections))
        self.assertTrue(('e', Edge('d', 'e', 1.0, 1.0 / 1.0)) in connections)
        
        connections = self.network_graph.get_all_edges_by_node('e')
        self.assertEqual(1, len(connections))
        self.assertTrue(('f', Edge('e', 'f', 1.0, 1.0 / 3.0)) in connections)
        
        connections = self.network_graph.get_all_edges_by_node('f')
        self.assertEqual(0, len(connections))
                
    def testAverageValuesByNode(self):
        self.assertEqual(8, self.network_graph.get_median_for_node('a'))
        self.assertEqual(6.666666666666667, self.network_graph.get_arithmetic_mean_for_node('a'))
    
        self.assertEqual(3.0, self.network_graph.get_median_for_node('b'))
        self.assertEqual(3.0, self.network_graph.get_arithmetic_mean_for_node('b'))
    
        self.assertEqual(4.5, self.network_graph.get_median_for_node('c'))
        self.assertEqual(4.5, self.network_graph.get_arithmetic_mean_for_node('c'))
        
        self.assertEqual(1.0, self.network_graph.get_median_for_node('d'))
        self.assertEqual(1.0, self.network_graph.get_arithmetic_mean_for_node('d'))
        
        self.assertEqual(3.0, self.network_graph.get_median_for_node('e'))
        self.assertEqual(3.0, self.network_graph.get_arithmetic_mean_for_node('e'))
        
        self.assertEqual(3.0, self.network_graph.get_median_for_node('e'))
        self.assertEqual(3.0, self.network_graph.get_arithmetic_mean_for_node('e'))
        
        self.assertEqual(None, self.network_graph.get_median_for_node('f'))
        self.assertEqual(None, self.network_graph.get_arithmetic_mean_for_node('f'))
    
    def testDatastorePersisting(self):
        network_graph_model = self.network_graph.get_model()
        network_graph_model.put()
                
        query = db.GqlQuery("SELECT * FROM NetworkGraphModel")
        network_graph_model = query.get()
        
        self.assertNotEqual(None, network_graph_model)
        self.network_graph = network_graph_model.recreate_network_graph()

        # Re-run tests        
        self.testGetAllConnectionsByNode()
        self.testGetAllEdges()
        self.testGetAllNode()
        self.testGetArithmeticMean()
        self.testGetEdge()
        self.testGetMedian()
        self.testGetShortestPaths()

class NodeSelectorTest(unittest.TestCase):
    
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        
        self.network_graph = NetworkGraph()
        self.network_graph.add_edge('a', 'b', 1.0, 1.0 / 3.0)
        self.network_graph.add_edge('a', 'c', 1.0, 1.0 / 8.0)
        self.network_graph.add_edge('b', 'd', 1.0, 1.0)
        self.network_graph.add_edge('b', 'e', 1.0, 1.0 / 5.0)
        self.network_graph.add_edge('c', 'b', 1.0, 1.0 / 2.0)
        self.network_graph.add_edge('c', 'f', 1.0, 1.0 / 7.0)
        self.network_graph.add_edge('d', 'e', 1.0, 1.0)
        self.network_graph.add_edge('e', 'f', 1.0, 1.0 / 3.0)

    def tearDown(self):
        self.testbed.deactivate()
        
    def testFilterByLinks(self):
        node_selector = NodeSelector(self.network_graph, min_links=2)
        node_selector.select_nodes()
        selected_nodes = node_selector.selected_nodes
        self.assertEqual(3, len(selected_nodes))
        self.assertTrue('a' in selected_nodes)
        self.assertTrue('b' in selected_nodes)
        self.assertTrue('c' in selected_nodes)
        
    def testFilterByNeighbors(self):    
        node_selector = NodeSelector(self.network_graph, min_neighbors=3)
        node_selector.select_nodes()
        selected_nodes = node_selector.selected_nodes
        self.assertEqual(1, len(selected_nodes))
        self.assertTrue('a' in selected_nodes)

class ChannelAssignmentTest(unittest.TestCase):
    
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        
        self.network_graph = NetworkGraph()
        self.network_graph.add_edge('a', 'b', 1.0, 1.0 / 3.0)
        self.network_graph.add_edge('a', 'c', 1.0, 1.0 / 8.0)
        self.network_graph.add_edge('b', 'd', 1.0, 1.0)
        self.network_graph.add_edge('b', 'e', 1.0, 1.0 / 5.0)
        self.network_graph.add_edge('c', 'b', 1.0, 1.0 / 2.0)
        self.network_graph.add_edge('c', 'f', 1.0, 1.0 / 7.0)
        self.network_graph.add_edge('d', 'e', 1.0, 1.0)
        self.network_graph.add_edge('e', 'f', 1.0, 1.0 / 3.0)

    def tearDown(self):
        self.testbed.deactivate()
        
    def testModifiedNetworkModel(self):
        network_graph_model = self.network_graph.get_model()
        
        network_graph_model.put()
        
        channel_assignment_model = ChannelAssignmentModel(channel_assignment='(0, 0, 0)')
        
        channel_assignment_model.put()
        
        modified_network_model = EvaluationModel(network_graph=network_graph_model,
                                                      channel_assignment=channel_assignment_model,
                                                      num_removed_edges = 5)

        modified_network_model.put()
        
        query = db.GqlQuery("SELECT * FROM EvaluationModel")
        
        modified_network_model = query.get()
        
        network_graph_model = modified_network_model.network_graph
        network_graph = network_graph_model.recreate_network_graph()
        
        nodes = network_graph.get_all_nodes()
        
        self.assertEqual(6, len(nodes))
        self.assertTrue('a' in nodes)
        self.assertTrue('b' in nodes)
        self.assertTrue('c' in nodes)
        self.assertTrue('d' in nodes)
        self.assertTrue('e' in nodes)
        self.assertTrue('f' in nodes)

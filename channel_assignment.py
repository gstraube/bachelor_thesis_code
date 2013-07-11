from __future__ import with_statement
import logging
import random

from google.appengine.ext import db
from mapreduce import operation as op
from mapreduce import context

from network_graph import NetworkGraphModel
from io_handler import InputReader
from node_selection import NodeSelector

class ChannelAssignmentModel(db.Model):
    
    channel_assignment = db.TextProperty(required=True)
    
class NamesToNumbersModel(db.Model):
    
    names_to_numbers = db.TextProperty(required=True)

# Subclassing db.Expando allows for adding dynamic properties
class EvaluationModel(db.Expando):
    
    network_graph = db.ReferenceProperty(NetworkGraphModel, required=True)
    channel_assignment = db.ReferenceProperty(ChannelAssignmentModel, required=True)
    
class ChannelAssignmentValidator:

    def __init__(self, channel_assignment, improvement_rate_lower, improvement_rate_upper):
        self.channel_assignment = channel_assignment
        
        self.improvement_rate_lower = float(improvement_rate_lower)
        self.improvement_rate_upper = float(improvement_rate_upper)
        
        input_reader = InputReader()
        self.network_graph = input_reader.read_graph()

        names_to_numbers_entity = input_reader.read_entity('NamesToNumbersModel')
        self.names_to_numbers = eval(names_to_numbers_entity.names_to_numbers)
        self.selected_nodes = self.names_to_numbers.keys()                                   
    
        self.num_removed_edges = 0

    def __filter_edges(self):
        edges = self.network_graph.get_all_edges()
        
        for edge in edges:
            
            # Backbone or cable links need not to be considered.
            if not edge.link_type == 'Backbone link' and not edge.link_type == 'Cable link':
                
                # If the node has not been selected, a default channel
                # will be assumed.
                
                # Get node number according to the mapping of names to numbers.
                if edge.from_node in self.selected_nodes:
                    from_node_number = self.names_to_numbers[edge.from_node]
                    from_node_channel = self.channel_assignment[from_node_number]
                else:
                    from_node_channel = 0
                    
                # Get channel according to the channel assignment.
                if edge.to_node in self.selected_nodes:
                    to_node_number = self.names_to_numbers[edge.to_node]
                    to_node_channel = self.channel_assignment[to_node_number]
                else:
                    to_node_channel = 0
                    
                # Remove edge if the adjacent nodes have been assigned different edges.
                if from_node_channel != to_node_channel:
                    self.network_graph.remove_edge(edge)
                    self.num_removed_edges += 1
                else:
                    # Enhance link quality values for an edge in the modified network graph. 
                    # Link quality is augmented by a random value between upper and lower bound. 
                    # in the variable improvement_rate (except when it already equals 1.0).
                    # This is to account for improvements due to interference reduction.

                    lower_bound = self.improvement_rate_lower / 100.0
                    upper_bound = self.improvement_rate_upper / 100.0
                    
                    factor = 1.0 + random.uniform(lower_bound, upper_bound)
                    
                    if edge.lq < 1.0:
                        edge.lq = edge.lq * factor
                        if edge.lq > 1.0:
                            edge.lq = 1.0
                    
    def validate_channel_assignment(self):
        
        """Checks if a channel assignment is valid."""
        
        # Remove edges dropping out according to the channel assignment.
        self.__filter_edges()
        
        # Check if the graph is still connected (main criterion for validity).
        if self.network_graph.is_connected():
            return True
        
        return False    
        
class AverageValuesEvaluator:
    
    """Evaluate a given channel assignment by calculating arithmetic means and medians 
    for a certain set of values.

    """
    
    def __init__(self, network_graph, channel_assignment, num_removed_edges):
        
        self.network_graph = network_graph
        self.channel_assignment = channel_assignment
        self.num_edges = len(self.network_graph.get_all_edges())
        self.num_removed_edges = num_removed_edges
    
    def evaluate_channel_assignment(self):
        
        self.etx_median = self.network_graph.get_median()
        self.etx_arithmetic_mean = self.network_graph.get_arithmetic_mean()
        
class ETXClassesEvaluator:
    
    """Evaluate a given channel assignment by categorizing nodes into 
    classes according to the ETX values of their outgoing links.
    
    """

    def __init__(self, network_graph, channel_assignment, num_removed_edges,
                 num_classes, upper_bound):
        
        self.network_graph = network_graph
        self.channel_assignment = channel_assignment
        self.num_edges = len(self.network_graph.get_all_edges())
        self.num_removed_edges = num_removed_edges
    
        self.etx_classes = []    
        self.ascended_nodes = 0
        self.relegated_nodes = 0
        
        self.__initialize_etx_classes(num_classes, upper_bound)
    
    def __initialize_etx_classes(self, num_classes, upper_bound):
            
        lower_bound = 1.0
    
        step = (float(upper_bound) - 1.0) / float(num_classes - 1)
            
        for rank in range(int(num_classes) - 1):
            self.etx_classes.append((lower_bound, lower_bound + step, rank))
            lower_bound = lower_bound + step        
            
        self.etx_classes.append((lower_bound, float('infinity'), rank + 1))
    
    def __get_rank(self, etx_value):
    
        for etx_class in self.etx_classes:
                
            if etx_class[0] < etx_value <= etx_class[1]: 
                    
                # Return rank
                return etx_class[2]
        
    def evaluate_channel_assignment(self):
    
        input_reader = InputReader()
        original_network_graph = input_reader.read_graph()
    
        nodes = self.network_graph.get_all_nodes()
        
        for node in nodes:
            original_etx_value = original_network_graph.get_median_for_node(node)
            etx_value = self.network_graph.get_median_for_node(node)
            
            # Has the node been ranked better or worse? Do not account for unchanged
            # ranks.
            if self.__get_rank(etx_value) < self.__get_rank(original_etx_value):
                self.ascended_nodes += 1
            elif self.__get_rank(etx_value > self.__get_rank(original_etx_value)):
                self.relegated_nodes += 1

class ChannelAssignmentInitializer:

    def __init__(self, selected_nodes, num_channels):
        
        """Initializes values and calls methods for preparing the mapreduce
        execution.
        
        """
        
        self.selected_nodes = selected_nodes
        self.names_to_numbers = {}
        self.num_channels = num_channels
        
        self.__map_names_to_numbers()
        
    def __map_names_to_numbers(self):
        
        """Assigns a number for each node name in the set of
        selected nodes.
        
        """
        
        # Sort nodes to create an order.
        self.selected_nodes.sort()
        
        # Assign ascending numbers for the set 
        # of selected nodes.
        num_index = 0
        for node in self.selected_nodes:
            self.names_to_numbers[node] = num_index
            num_index += 1
    
def product(*args, **kwds):
    
    """Calculates the Cartesian product. 
    Source: http://docs.python.org/library/itertools.html#itertools.product.
    
    """
    
    # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
    # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
    pools = map(tuple, args) * kwds.get('repeat', 1)
    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)
    
def create_channel_assignments(entity):
    
    # Get network graph
    
    logging.info('Creating channel assignments')
    
    network_graph = entity.recreate_network_graph()
    
    # Get parameter values
    
    ctx = context.get()
    params = ctx.mapreduce_spec.mapper.params

    min_links = int(params['min_links'])
    min_neighbors = int(params['min_neighbors'])
    num_channels = int(params['num_channels'])
    
    node_selector = NodeSelector(network_graph, min_links, min_neighbors)    
    selected_nodes = node_selector.select_nodes()
    
    logging.info('Number of selected nodes: ' + str(len(selected_nodes)))
    
    channel_assignment_initializer = ChannelAssignmentInitializer(selected_nodes, num_channels)
    names_to_numbers = channel_assignment_initializer.names_to_numbers
    names_to_numbers_entity = NamesToNumbersModel(names_to_numbers=str(names_to_numbers))
    names_to_numbers_entity.put()
    
    num_nodes = len(names_to_numbers)
    
    for combination in product(range(num_channels), repeat=num_nodes):
        ca_entity = ChannelAssignmentModel(channel_assignment=str(combination))
        ca_entity.put()
    
def validate_and_evaluate(entity):
    
    """This method is called by mapreduce. It receives a channel assignment as input (in the form of an instance
    of the ChannelAssignmentModel model class) then validates and evaluates it if it's a valid assignment.
    
    """
    
    global num_valid_assignments
    
    ctx = context.get()
    params = ctx.mapreduce_spec.mapper.params
    
    # Get improvement rate lower and upper bound.
    improvement_rate_lower = float(params['improvement_rate_lower'])
    improvement_rate_upper = float(params['improvement_rate_upper'])
    
    # Build tuple from text property.
    channel_assignment = eval(entity.channel_assignment)
    
    # Prepare Datastore entries. Each channel assignment is put in the Datastore so that
    # mapreduce can iterate over all assignments.
    channel_assignment_validator = ChannelAssignmentValidator(channel_assignment,
                                                              improvement_rate_lower,
                                                              improvement_rate_upper)
    
    # Check if the channel assignment is valid.
    is_valid = channel_assignment_validator.validate_channel_assignment()
    
    if is_valid:
        
        graph = channel_assignment_validator.network_graph
        graph_entity_key = graph.get_model(type='ModifiedNetworkGraphModel').put()
        
        num_removed_edges = channel_assignment_validator.num_removed_edges

        # Instantiation of evaluator
        evaluator_arg = params['evaluator']
        
        if evaluator_arg == 'channel_assignment.AverageValuesEvaluator':
            
            evaluator = AverageValuesEvaluator(graph, 
                                               channel_assignment,
                                               num_removed_edges)
            
            logging.debug('AverageValuesEvaluator has been chosen.')
            
        elif evaluator_arg == 'channel_assignment.ETXClassesEvaluator':
            
            num_classes = float(params['num_classes'])
            upper_bound = float(params['upper_bound'])
            
            evaluator = ETXClassesEvaluator(graph, 
                                            channel_assignment,
                                            num_removed_edges,
                                            num_classes,
                                            upper_bound)
            
            logging.debug('ETXClassesEvaluator has been chosen.')
            
        # If the parameter value could not be recognized, 
        # an instance of AverageValuesEvaluator class is 
        # assigned as default.
        else:
            evaluator = AverageValuesEvaluator(graph, 
                                               channel_assignment,
                                               num_removed_edges)
            logging.debug('Unrecognized parameter. AverageValuesEvaluator will be chosen as default.')
        
        evaluator.evaluate_channel_assignment()

        evaluation_entity = EvaluationModel(network_graph=graph_entity_key,
                                            channel_assignment=entity.key(),
                                            num_removed_edges=num_removed_edges
                                            )
        
        if isinstance(evaluator, AverageValuesEvaluator):    
        
            evaluation_entity.etx_median = evaluator.etx_median  
            evaluation_entity.etx_arithmetic_mean = evaluator.etx_arithmetic_mean  
            
        elif isinstance(evaluator, ETXClassesEvaluator):
    
            evaluation_entity.ascended_nodes = evaluator.ascended_nodes
            evaluation_entity.relegated_nodes = evaluator.relegated_nodes
            evaluation_entity.difference = evaluator.ascended_nodes - evaluator.relegated_nodes
    
        else:

            # In case of new evaluator classes, this
            # code section needs to be updated.
            
            pass
            
        evaluation_entity.put()
        
def clear_datastore(entity):
    
    yield op.db.Delete(entity)
    
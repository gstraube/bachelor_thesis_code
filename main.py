import os
import time
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from network_graph import NetworkGraph
from io_handler import InputReader, FileModel

import channel_assignment #@UnusedImport 
import node_selection #@UnusedImport
from kml_export import KMLExporter

network_graph = NetworkGraph()


class MainPage(webapp.RequestHandler):
    
    def get(self):
                
        parse_graph()
        
        self.response.headers['Content-Type'] = 'text/html'
        
        nodes_count = len(network_graph.get_all_nodes())
        edges = network_graph.get_all_edges()
        timestamp_time = network_graph.timestamp_time
        timestamp_date = network_graph.timestamp_date
        statistics = (network_graph.get_median(), network_graph.get_arithmetic_mean())
        
        template_values = {'nodes_count' : nodes_count,
                           'edges' : edges, 
                           'time' : timestamp_time, 
                           'date' : timestamp_date,
                           'statistics' : statistics}
        
        path = os.path.join(os.path.dirname(__file__), 'html', 'index.html')
        
        self.response.out.write(template.render(path, template_values))


class ShortestPaths(webapp.RequestHandler):
    
    """Displays shortest paths for one node to all other nodes."""
    
    def get(self):
                
        parse_graph()
        
        self.response.headers['Content-Type'] = 'text/html'
        
        node = self.request.get('node')
        
        start = time.time()
        distances = network_graph.get_shortest_paths(node)
        end = time.time()
        duration = end - start
        
        timestamp_time = network_graph.timestamp_time
        timestamp_date = network_graph.timestamp_date
        
        template_values = {'node' : node, 'distances' : distances, 'time' : timestamp_time, 
                           'date' : timestamp_date, 'duration' : duration}
        
        path = os.path.join(os.path.dirname(__file__), 'html', 'shortest_paths.html')
        self.response.out.write(template.render(path, template_values))
        
class EvaluationOverview(webapp.RequestHandler):
    
    """Overview of all evaluations ranked by a criterion."""
    
    def get(self):
        
        self.response.headers['Content-Type'] = 'text/html'
        
        inputReader = InputReader()
        
        # Fetch one entity of type EvaluationModel to determine which evaluator class
        # is in use
        
        sample_entity = inputReader.read_entity('EvaluationModel')
        
        if hasattr(sample_entity, 'etx_median'):
            
            template_file = 'evaluation_overview.html'
            order_attr = 'etx_median ASC'
        
        else:
            
            template_file = 'evaluation_overview_classes.html'
            order_attr = 'difference DESC'
        
        evaluation_entities = inputReader.read_all_entities('EvaluationModel', order_attr)
        
        template_values = {'evaluations' : evaluation_entities}
        
        path = os.path.join(os.path.dirname(__file__), 'html', template_file)
        
        self.response.out.write(template.render(path, template_values))
        
class EvaluationDetails(webapp.RequestHandler):
    
    """Details for an evaluation chosen from evaluation overview."""
    
    def get(self):
        
        parse_graph()
        
        self.response.headers['Content-Type'] = 'text/html'
        
        inputReader = InputReader()
        
        entity_key = self.request.get('key')
        evaluation_entity = inputReader.read_entity('EvaluationModel', key=entity_key)
        
        ca_entity = evaluation_entity.channel_assignment
        
        ca = eval(ca_entity.channel_assignment)
    
        names_to_numbers_entity = inputReader.read_entity('NamesToNumbersModel')
        names_to_numbers = eval(names_to_numbers_entity.names_to_numbers)
            
        colored_nodes = []
        
        for node in network_graph.get_all_nodes():
            
            if node in names_to_numbers.keys():
                node_number = names_to_numbers[node]
                node_channel = ca[node_number]
                if node_channel == 0:
                    node_channel_description = 'Default channel'
                else:
                    node_channel_description = 'Channel ' + str(node_channel)
            
            elif node in network_graph.backbone_nodes:
                node_channel = '-'
                node_channel_description = 'Backbone node'
            
            else:
                node_channel = 0
                node_channel_description = 'Default channel'
        
            colored_nodes.append((node, node_channel_description, node_channel))
            
        template_values = {'nodes' : colored_nodes}
        
        path = os.path.join(os.path.dirname(__file__), 'html', 'evaluation_details.html')
        
        self.response.out.write(template.render(path, template_values))
          
class UploadHandler(webapp.RequestHandler):
    
    """The user can upload a time stamp file along with a list of backbone nodes and
    cable links.
    
    """
    
    def get(self):
        
        path = os.path.join(os.path.dirname(__file__), 'html', 'upload_file.html')
        
        template_values = {}
        
        self.response.out.write(template.render(path, template_values))
    
    def post(self):
        
        uploaded_timestamp = self.request.get('timestamp_file')
        uploaded_timestamp_entity = FileModel(file=uploaded_timestamp, name='time_stamp')
        uploaded_timestamp_entity.put()
        
        uploaded_backbone_nodes = self.request.get('backbone_nodes')
        uploaded_backbone_nodes_entity = FileModel(file=uploaded_backbone_nodes,
                                                   name='backbone_nodes')
        uploaded_backbone_nodes_entity.put()
        
        uploaded_cable_links = self.request.get('cable_links')
        uploaded_cable_links_entity = FileModel(file=uploaded_cable_links,
                                                name='cable_links')
        uploaded_cable_links_entity.put()
        
        uploaded_ip_to_coordinates = self.request.get('ip_to_coordinates')
        uploaded_ip_to_coordinates_entity = FileModel(file=uploaded_ip_to_coordinates,
                                                name='ip_to_coordinates')
        
        uploaded_ip_to_coordinates_entity.put()
        
        self.redirect('/')
        
class NetworkGraphHandler(webapp.RequestHandler):
    
    def get(self):
 
        inputReader = InputReader()
        
        entity_key = self.request.get('key') 
        evaluation_entity = inputReader.read_entity('EvaluationModel', key=entity_key)
        
        modified_network_graph = evaluation_entity.network_graph.recreate_network_graph()
        
        nodes_count = len(modified_network_graph.get_all_nodes())
        edges = modified_network_graph.get_all_edges()
        
        timestamp_time = modified_network_graph.timestamp_time
        timestamp_date = modified_network_graph.timestamp_date
        
        statistics = (modified_network_graph.get_median(), modified_network_graph.get_arithmetic_mean())
        
        template_values = {'nodes_count' : nodes_count,
                           'edges' : edges, 
                           'time' : timestamp_time, 
                           'date' : timestamp_date,
                           'statistics' : statistics}
        
        path = os.path.join(os.path.dirname(__file__), 'html', 'index.html')
        self.response.out.write(template.render(path, template_values))
        
class MapHandler(webapp.RequestHandler):
    
    def get(self):
        
        entity_key = self.request.get('key')        
        
        path = os.path.join(os.path.dirname(__file__), 'html', 'map.html')
        
        template_values = {'evaluation_entity_key' : entity_key}
        
        self.response.out.write(template.render(path, template_values))

        
class KMLHandler(webapp.RequestHandler):
    
    def get(self):
        
        parse_graph()
        
        self.response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        
        inputReader = InputReader()
        
        entity_key = self.request.get('key')
        evaluation_entity = inputReader.read_entity('EvaluationModel', key=entity_key)
        
        ca_entity = evaluation_entity.channel_assignment
        
        ca = eval(ca_entity.channel_assignment)
    
        names_to_numbers_entity = inputReader.read_entity('NamesToNumbersModel')
        names_to_numbers = eval(names_to_numbers_entity.names_to_numbers)

        modified_network_graph = evaluation_entity.network_graph.recreate_network_graph()

        kml_exporter = KMLExporter(modified_network_graph, ca, names_to_numbers)
                
        kml = kml_exporter.kml

        self.response.out.write(kml)
        
def parse_graph():
    global network_graph
    
    logging.debug('Parsing graph...')
        
    input_reader = InputReader()
    network_graph = input_reader.read_graph()
        
    logging.debug('Finished parsing graph.')

# Mapping of URLs to handlers initializes instance
# of class WSGIApplication
application = webapp.WSGIApplication(
                                     [('/', MainPage), ('/shortest_paths', ShortestPaths),
                                      ('/evaluation', EvaluationOverview),
                                      ('/evaluation_details', EvaluationDetails),
                                      ('/upload_files', UploadHandler),
                                      ('/map', MapHandler),
                                      ('/kml', KMLHandler),
                                      ('/network_graph', NetworkGraphHandler)],
                                     debug=True)

def main():
    # Run instance of class WSGIApplication
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
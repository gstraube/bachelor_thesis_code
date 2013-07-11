import os
import logging

from google.appengine.ext import db

from network_graph import NetworkGraph


class FileModel(db.Model):
    
    file = db.BlobProperty(required=True)
    name = db.StringProperty(required=True)

class InputReader:
    
    def __init__(self):
        pass
    
    def read_graph(self):
        """Read in the network graph from a given time stamp file or the Datastore 
        if the graph has already been read in once. Returns an instance of class NetworkGraph.
        
        """
           
        # Query Datastore for instances of class NetworkGraph
        
        query = db.GqlQuery("SELECT * FROM NetworkGraphModel")
        network_graph_model = query.get()
        
        if network_graph_model is not None:
            logging.debug('Retrieving and recreating graph from Datastore...')
            
            # If one or more instances have been found, take the first one
            network_graph = network_graph_model.recreate_network_graph()
            
            logging.debug('Finished retrieving and recreating graph.')
            
            return network_graph
        else:
            # If there is no instance found, read graph from file
            return self.read_graph_from_file()
    
    def read_graph_from_file(self):
        network_graph = NetworkGraph()
        
        query = db.GqlQuery("SELECT * FROM %s WHERE name='%s'" % ('FileModel', 'time_stamp'))
        entity = query.get()

        if entity is not None:
            time_stamp = str(entity.file)
            time_stamp_file = None
        else:
            time_stamp_file = os.path.join(os.path.dirname(__file__), 'data', 'timestamp.txt')
            
        query = db.GqlQuery("SELECT * FROM %s WHERE name='%s'" % ('FileModel', 'backbone_nodes'))
        entity = query.get()

        if entity is not None:
            backbone_nodes = eval(entity.file)
            logging.info(backbone_nodes[0])
        else:
            backbone_nodes_file = os.path.join(os.path.dirname(__file__), 'data', 'backbone_nodes.txt')
            backbone_nodes = eval(open(backbone_nodes_file, 'r').read())
            
        query = db.GqlQuery("SELECT * FROM %s WHERE name='%s'" % ('FileModel', 'cable_links'))
        entity = query.get()

        if entity is not None:
            cable_links = eval(entity.file)
        else:
            cable_links_file = os.path.join(os.path.dirname(__file__), 'data', 'cable_links.txt')
            cable_links = eval(open(cable_links_file, 'r').read())
    
        logging.debug('Reading graph from file...')
        
        if time_stamp_file is not None:
            time_stamp = open(time_stamp_file, 'r')   
            lines = time_stamp.readlines() 
        else:
            lines = time_stamp.split('\n')

        # Extract time and date and add them 
        if len(lines) > 0:
            first_line = lines[0]
            line_words = first_line.split()
            date = line_words[0]
            time = line_words[1]
            network_graph.set_time_and_date(time, date)
            
        
        # Successively add lines of the time stamp file as edges to the network graph
        for line in lines:
            
            if line == '':
                break
            
            # Split line into strings (delimiter is space)            
            line_words = line.split()
            
            # line_words[0] - time stamp date (see above)
            # line_words[1] - time stamp time (see above)
            # line_words[2] - this_ip
            # line_words[3] - other_ip
            # line_words[4] - link quality
            # line_words[5] - neighbor link quality
            
            from_node = line_words[2]
            to_node = line_words[3]
            lq = line_words[4]
            nlq = line_words[5]
            
            # Dismiss edges where either LQ or NLQ equals zero (i.e., edges that do not exist anymore)
            if not lq == '0.000' and not nlq == '0.000':
                network_graph.add_edge(from_node, to_node, float(lq), float(nlq))
                if from_node in backbone_nodes and to_node in backbone_nodes:
                    network_graph.add_edge(from_node, to_node, float(lq), float(nlq), 'Backbone link')
                else:
                    for cable_link in cable_links:
                        is_cable_link = False
                        if from_node in cable_link and to_node in cable_link:
                            is_cable_link = True
                            network_graph.add_edge(from_node, to_node, float(lq), float(nlq), 'Cable link')
                            break
                        if is_cable_link == False:
                            network_graph.add_edge(from_node, to_node, float(lq), float(nlq))
        
        if time_stamp_file is not None:
            time_stamp.close()
        
        logging.debug('Finished reading graph from file.')
        
        # Adding list of backbone nodes to graph
        network_graph.add_backbone_nodes(backbone_nodes)
        
        # Put instance into Datastore
        logging.debug('Storing graph instance to Datastore...')
        
        network_graph_model = network_graph.get_model()
        network_graph_model.put()   
        
        logging.debug('Finished storing')
            
        return network_graph
    
    def read_entity(self, kind_name,  key=None):
        
        """Returns the entity for a given kind name and key 
        or the first entity found if no key was given.
        
        """
        
        if key is not None:
            entity = db.get(key)
        else:
            query = db.GqlQuery("SELECT * FROM %s" % kind_name)
            entity = query.get()
    
        if entity is None:
            logging.info('Could not fetch entity from Datastore')
    
        return entity
    
    def read_all_entities(self, kind_name, order=None):
        
        """Returns all entities for a given kind name."""
        
        if order is None:
            query = db.GqlQuery("SELECT * FROM %s" % kind_name)
        else:
            query = db.GqlQuery("SELECT * FROM %s ORDER BY %s" % (kind_name, order))
        
        entities = query.run()
    
        return entities
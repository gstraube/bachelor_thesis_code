import os
import xml.dom.minidom
import logging

class KMLExporter:
    
    def __init__(self, network_graph, channel_assignment, names_to_numbers):
        
        self.network_graph = network_graph
        self.channel_assignment = channel_assignment
        self.names_to_numbers = names_to_numbers
        
        input_file = os.path.join(os.path.dirname(__file__), 'data', 'ip_to_coordinates.txt')
        self.ip_to_coordinates = eval(open(input_file, 'r').read())
        
        # @attention: Color for default channel must be listed first, i.e. as element
        # with index 0
        self.color_styles = ['blueColorStyle', 'greenColorStyle', 'redColorStyle']
        
        self.color_styles_to_hex = {}
        
        self.color_styles_to_hex['blackColorStyle'] = '40000000'
        self.color_styles_to_hex['blueColorStyle'] = '40ff0000'
        self.color_styles_to_hex['greenColorStyle'] = '4000ff00'
        self.color_styles_to_hex['redColorStyle'] = '400000ff'
        
        self.kml = ''
        self.__create_kml()
        
    def __create_kml(self):
        
        kml_writer = kml('Colored links', 'Network graph')
        
        kml_writer.add_style_color('blackColorStyle', '2', self.color_styles_to_hex['blackColorStyle'])
        kml_writer.add_style_color('blueColorStyle', '2', self.color_styles_to_hex['blueColorStyle'])
        kml_writer.add_style_color('greenColorStyle', '2', self.color_styles_to_hex['greenColorStyle'])
        kml_writer.add_style_color('redColorStyle', '2', self.color_styles_to_hex['redColorStyle'])
        
        edges = self.network_graph.get_all_edges()
        
        visited_nodes = []
        
        for edge in edges:
            
            edge_color_style = ''
            
            if edge.link_type == 'Backbone link' or edge.link_type == 'Cable link':
                
                edge_color_style = 'blackColorStyle'
                
            else:
                
                if edge.from_node in self.names_to_numbers.keys():
                    
                    from_node_channel = self.channel_assignment[self.names_to_numbers[edge.from_node]]
                    
                    edge_color_style = self.color_styles[from_node_channel]
                    
                else:
                    
                    # Edges operating on the default channel will be colored blue
                    edge_color_style = self.color_styles[0]
            
            if edge.from_node in self.ip_to_coordinates:
                
                if edge.from_node not in visited_nodes:
            
                    kml_writer.add_placemark(edge.from_node, self.ip_to_coordinates[edge.from_node])
                
                    visited_nodes.append(edge.from_node)
                
                if edge.to_node in self.ip_to_coordinates:
                    
                    if edge.to_node not in visited_nodes:
                    
                        kml_writer.add_placemark(edge.to_node, self.ip_to_coordinates[edge.to_node])
                    
                        visited_nodes.append(edge.to_node)
                        
                    kml_writer.add_lineSeg([self.ip_to_coordinates[edge.from_node], 
                                            self.ip_to_coordinates[edge.to_node]], 
                                            edge_color_style)
                    
                else:
                    
                    logging.info('Could not find coordinates for node %s' % edge.to_node)
            
            else:
                
                logging.info('Could not find coordinates for node %s' % edge.from_node)
        
        self.kml = kml_writer.get_kml()
                    
class kml:
    
    def __init__(self,title,description):
        """Add KML preamble"""
        title=unicode(title)
        description=unicode(description)
        self.__doc = xml.dom.minidom.Document()
        
        kml = self.__doc.createElement('kml')
        kml.setAttribute('xmlns', 'http://www.opengis.net/kml/2.2')
        self.__doc.appendChild(kml)
           
        document = self.__doc.createElement('Document')
        kml.appendChild(document)
        
        docName = self.__doc.createElement('name')
        document.appendChild(docName)
        docName_text = self.__doc.createTextNode(title)
        docName.appendChild(docName_text)
        
        docName = self.__doc.createElement('open')
        document.appendChild(docName)
        docName_text = self.__doc.createTextNode('1')
        docName.appendChild(docName_text)
        
        docDesc = self.__doc.createElement('description')
        document.appendChild(docDesc)
        docDesc_text = self.__doc.createTextNode(description)
        docDesc.appendChild(docDesc_text)
        self.__idcounter=0
        self.__kml=document
        
    def add_style_color(self, name, width_value, color_value):
        name=unicode(name)
        
        """Add a simple Style block with a icon"""
        style = self.__doc.createElement('Style')
        style.setAttribute('id', name)
        self.__kml.appendChild(style)
        
        line_style = self.__doc.createElement('LineStyle')
        style.appendChild(line_style)

        color = self.__doc.createElement('color')
        line_style.appendChild(color)
        color_text = self.__doc.createTextNode(color_value)
        color.appendChild(color_text)
        
        width = self.__doc.createElement('width')
        line_style.appendChild(width)
        width_text = self.__doc.createTextNode(width_value)
        width.appendChild(width_text)
        
    def add_placemark(self, name, (lon, lat)):
        """Generate the KML Placemark for a given address."""
        name=name
        pm = self.__doc.createElement("Placemark")
        self.__kml.appendChild(pm)
        pname = self.__doc.createElement("name")
        pm.appendChild(pname)

        name_text = self.__doc.createTextNode(name)
        pname.appendChild(name_text)
        pt = self.__doc.createElement("Point")
        pm.appendChild(pt)
        coords = self.__doc.createElement("coordinates")
        pt.appendChild(coords)
        coords_text = self.__doc.createTextNode(lon+","+lat)
        coords.appendChild(coords_text)
            
    def add_lineSeg(self, points, style):
        pm = self.__doc.createElement("Placemark")
        
        style_url = self.__doc.createElement('styleUrl')
        pm.appendChild(style_url)
        style_url_text = self.__doc.createTextNode('#' + style)
        style_url.appendChild(style_url_text)
        
        ln = self.__doc.createElement("LineString")
        self.__idcounter+=1
        self.__kml.appendChild(pm)
        pm.appendChild(ln)
        
        coords = self.__doc.createElement("coordinates")
        ln.appendChild(coords)
        for p in points:
            lon=p[0].strip().replace(",",".")
            lat=p[1].strip().replace(",",".")
            if points.index(p) == (len(points) - 1):
                coords_text = self.__doc.createTextNode(lon+","+lat)
            else:
                coords_text = self.__doc.createTextNode(lon+","+lat+" ")
            coords.appendChild(coords_text)

    def get_kml(self):
        return self.__doc.toprettyxml(encoding='UTF-8')

* Deployen der Anwendung

Um die Anwendung zu deployen, wird das AppEngine-SDK von Google benötigt. Dieses enthält das Skript appcfg.py. Durch den Aufruf

									appcfg.py update Quellcode 

wird der Quellcode für die Anwendung deployt, deren Name in der Datei app.yaml festgelegt wurde und die im Vorfeld erstellt werden muss. Hierzu wird ein Google-Konto benötigt, dessen Zugangsdaten beim Hochladen der Anwendung abgefragt werden.

* Orderstruktur

Die Python-Quelldateien liegen im Hauptverzeichnis "Quellcode". Der Unterordner "Quellcode/data" enthält alle Dateien, die der Anwendung als Eingabe dienen und deren Aufbau unten beschrieben wird. Im Unterordner "Quellcode/html" sind die HTML-Templates zu finden. In "Quellcode/mapreduce" sind die Dateien der Mapreduce-Bibliothek enthalten.  

* Aufbau der Dateien im Ordner "Quellcode/data" 


	- timestamp.txt: Jede Zeile entspricht einem Link im Netzwerk und beinhaltet Datum, Uhrzeit, Quell-IP, Ziel-IP, Link Quality, Neighbor Link Quality (in 				     dieser Reihenfolge).

	- backbone_nodes.txt: Eine Liste von Backbone-Knoten der Form ['knoten1', 'knoten2', ..., 'knotenN'].

	- cable_links.txt: Eine Liste von Listen der Form [['a', 'b'], ['x', 'y'], ['u', 'v', 's', 't']]. Die Knoten in jedem Listeneintrag gehören zu einer 						   Kabelverbindung.

	- ip_to_coordinates: Eine Zuordnung von Knotennamen zu Koordinaten der Form {'knoten1' : ('längengrad_knoten1', 'breitengrad_knoten1'), 
																				 'knoten2' : ('längengrad_knoten2', 'breitengrad_knoten2')}

				
					 

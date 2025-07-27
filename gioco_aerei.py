import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets, QtGui, QtSvg
import numpy as np
from PyQt5.QtWidgets import QInputDialog
import random
import sys

# Nella documentazione è presente un modo più efficiente per cambiare i colori
# Quando ci saranno più aerei. Il file è "ColorazioneAerei.docx"


class CityNetwork:
    ''' Class that defines all the cities, the active cities and the current
    connections '''
    def __init__(self, all_cities):
        self.all_cities = all_cities
        self.active_cities = {}
        self.connections = {}
        
    # aggiunge una città alle città attive se è presente nell'elenco delle 
    # città disponibili. Appena aggiunta la città non è connessa a niente,
    # quindi la lista di connessioni è vuota
    def add_city(self, city_name):
        if city_name in self.all_cities and city_name not in self.active_cities:
            self.active_cities[city_name] = self.all_cities[city_name]
            self.connections[city_name] = []
            return True
        return False
    
    # connette due città. Controlla se entrambe sono nel dizionario connections,
    # ovvero le città attive, e poi controlla se non sono già connesse
    def connect(self, city1, city2):
        if city1 in self.connections and city2 in self.connections and city2 not in self.connections[city1]:
            self.connections[city1].append(city2)
            self.connections[city2].append(city1)

    def disconnect(self, city1, city2):
        if city1 in self.connections and city2 in self.connections[city1]:
            self.connections[city1].remove(city2)
            self.connections[city2].remove(city1)

class Airplane:
    def __init__(self, svg_path, start_pos, end_pos, parent, 
                 size = 15, connection = None, rotta = None, capacity = 100, 
                 passengers = {}, color = 'black'):
        self.parent = parent
        self.start = np.array(start_pos)
        self.end = np.array(end_pos)
        self.position = np.array(start_pos)
        self.size = size
        self.distance = 0
        self.direction = 1
        self.connection = connection
        self.capacity = capacity
        self.rotta = rotta
        self.passengers = passengers
        self.clicked = False
        self.color = color
        



        
        direction_vec = self.end - self.start
        self.length = np.linalg.norm(direction_vec)
        self.angle = np.degrees(np.arctan2(direction_vec[1], direction_vec[0])) + 90

        # self.item = QtSvg.QGraphicsSvgItem(svg_path)
        self.item = ClickableAirplaneItem(svg_path)
        self.item.setFlags(QtWidgets.QGraphicsItem.ItemClipsToShape)
        self.item.setCacheMode(QtWidgets.QGraphicsItem.NoCache)
        self.item.setZValue(3)
        

        bounds = self.item.boundingRect()
        scale = self.size / max(bounds.width(), bounds.height())
        self.item.setScale(scale)

        translation_value = (-bounds.width() * scale / 2, -bounds.height() * scale / 2)
        transform = QtGui.QTransform()
        transform.rotate(self.angle)
        transform.translate(*translation_value)
        self.item.setTransform(transform)
        self.set_pos(self.position)
    
    def update_color(self):
        
        plane_load = sum(self.passengers.values())/self.capacity
        color_index = min(int(plane_load*len(self.parent.airplane_colors)), 
                          len(self.parent.airplane_colors) - 1)
        self.color = self.parent.airplane_colors[color_index]
        effect = QtWidgets.QGraphicsColorizeEffect()
        effect.setColor(QtGui.QColor(self.color))
        self.item.setGraphicsEffect(effect)
                    

    def set_pos(self, pos):
        self.position = pos
        self.item.setPos(pos[0], pos[1])
        
    def update(self, speed = 0.5):
        self.distance += speed * self.direction        
        
        if self.distance >= self.length:
            self.distance = self.length
            self.direction *= -1 #inverte direzione
            self.update_transform()
            
            #aggiorna i passeggeri nelle città
            end_city = self.rotta[1]
            start_city = self.rotta[0]
            
            self.parent.network.active_cities[end_city]['pop'] += sum(self.passengers.values())
            # self.passengers = random.randint(0, self.capacity)
            self.passengers = {'A': 50}
            self.parent.network.active_cities[end_city]['pop'] -= sum(self.passengers.values())
            self.update_color()
            print(f'Rotta da {end_city} a {start_city} -> Passeggeri: {self.passengers}')

            self.parent.update_city_population_label(start_city)
            self.parent.update_city_population_label(end_city)
            if self.clicked == True:
                self.parent.on_airplane_clicked(self)
            

            
        elif self.distance <= 0:
            self.distance = 0
            self.direction *= -1  # Inverte la direzione
            self.update_transform()

            # Scarica passeggeri alla città di origine
            end_city = self.rotta[0]
            start_city = self.rotta[1]
            self.parent.network.active_cities[end_city]['pop'] += sum(self.passengers.values())
            # self.passengers = random.randint(0, self.capacity)
            self.passengers = {'C': 50}
            self.parent.network.active_cities[end_city]['pop'] -= sum(self.passengers.values())
            self.update_color()
            print(f'Rotta da {end_city} a {start_city} -> Passeggeri: {self.passengers}')
    
            self.parent.update_city_population_label(start_city)
            self.parent.update_city_population_label(end_city)
            if self.clicked == True:
                self.parent.on_airplane_clicked(self)
    

            
        t = self.distance / self.length if self.length else 1
        new_pos = (1 - t) * self.start + t * self.end
        self.set_pos(new_pos)
        
    
    def update_transform(self):
        transform = QtGui.QTransform()
        transform.rotate(self.angle + (180 if self.direction == -1 else 0))
        bounds = self.item.boundingRect()
        scale = self.item.scale()
        transform.translate(-bounds.width() * scale / 2, -bounds.height() * scale / 2)
        self.item.setTransform(transform)

    

class ClickableAirplaneItem(QtSvg.QGraphicsSvgItem):
    clicked = QtCore.pyqtSignal(object)

    def mousePressEvent(self, event):
        self.clicked.emit(self)
        event.accept()



# class ClickableLine(QtCore.QObject, QtWidgets.QGraphicsLineItem):
#     clicked = QtCore.pyqtSignal(object)  # emette se stessa quando cliccata

#     def __init__(self, p1, p2, city1, city2, pen=None):
#         QtCore.QObject.__init__(self)
#         QtWidgets.QGraphicsLineItem.__init__(self)
#         self.setLine(p1[0], p1[1], p2[0], p2[1])
        
#         self.city1 = city1
#         self.city2 = city2
#         self.setPen(pg.mkPen(color=(100, 100, 100), width=2))
#         self.setZValue(0.5)
#         self.setAcceptHoverEvents(True)
#         self.setFlag(self.ItemIsSelectable, True)

#     def mousePressEvent(self, event):
#         self.clicked.emit(self)

class ClickableLine:
    def __init__(self, city1, city2, p1, p2, on_click_callback):
        self.city1 = city1
        self.city2 = city2
        self.line_item = QtWidgets.QGraphicsLineItem(p1[0], p1[1], p2[0], p2[1])
        self.line_item.setPen(pg.mkPen(color=(100, 100, 100), width=2))
        self.line_item.setZValue(1)
        self.line_item.setAcceptHoverEvents(True)

        # Callback da richiamare al click
        self.on_click_callback = on_click_callback

        # Attacca evento di clic
        self.line_item.mousePressEvent = self._on_mouse_press

    def _on_mouse_press(self, event):
        if callable(self.on_click_callback):
            self.on_click_callback(self)
        event.accept()



class AirplaneGame:
    def __init__(self):
        self.app = pg.mkQApp()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        
        self.plane_size = 50
        self.city_size = 30
        self.airplane_colors = ['#024E1B', '#006B3E', '#FFE733', '#FFAA1C',
                                '#FF8C01', '#ED2938']

        self.win = pg.GraphicsLayoutWidget(show=True, title='Gioco aerei volanti')
        self.plot = self.win.addPlot()
        self.plot.setAspectLocked(True)

        self.all_cities = {
            'A': {'pos': (100, 200), 'pop': 5000, 'pas': {'B': 10, 'C': 20}},
            'B': {'pos': (500, 800), 'pop': 7000, 'pas': {'A': 80, 'C': 50}},
            'C': {'pos': (700, 400), 'pop': 3000, 'pas': {'A': 50}},
            'D': {'pos': (900, 900), 'pop': 9000, 'pas': {'A': 50}},
            'E': {'pos': (300, 600), 'pop': 4500, 'pas': {'A': 50}},
            'F': {'pos': (800, 200), 'pop': 3500, 'pas': {'A': 50}},
            'G': {'pos': (600, 100), 'pop': 2500, 'pas': {'A': 50}},
            'H': {'pos': (400, 700), 'pop': 6000, 'pas': {'A': 50}},
        }
        
        self.active_city_label = []
        
        
        self.network = CityNetwork(self.all_cities)
        for city in ['A', 'B', 'C']:
            self.network.add_city(city)
        
        
        self.city_scatter = pg.ScatterPlotItem(
            pos = [m['pos'] for m in self.network.active_cities.values()],
            data = list(self.network.active_cities.keys()),
            size = self.city_size,
            brush = pg.mkBrush('dodgerblue'),
            pen = pg.mkPen('black')
        )
        self.city_scatter.setZValue(1)
        self.plot.addItem(self.city_scatter)

        self.pen_dashed = pg.mkPen(color = (128, 128, 128), width = 1, 
                                   style = QtCore.Qt.DashLine)
        self.lines = []
        self.texts = {}

        for name, city_info in self.network.active_cities.items():
            self.add_city_label(name, city_info)

        self.active_planes = []
        self.animation_speed = 5

        self.animation_timer = QtCore.QTimer()
        self.animation_timer.setInterval(30)
        self.animation_timer.timeout.connect(self.animate)

        self.add_city_timer = QtCore.QTimer()
        self.add_city_timer.timeout.connect(self.add_city)
        self.add_city_timer.start(10000)

        self.city_scatter.sigClicked.connect(self.on_city_clicked)
        self.plot.scene().sigMouseClicked.connect(self.on_plot_clicked)
        self.win.closeEvent = self.closeEvent

    def add_city_label(self, city_name, city_info):
        pos = city_info['pos']
        pop = city_info['pop']
        label = ""
        html_info = """<font size="3">
                    {city_name}<br>Population: {pop}
                    </font>
        """.format(city_name = city_name, pop = pop)
        text = pg.TextItem(label, anchor=(0.4, 0.1), color = 'black', html = html_info)
        text.setPos(*pos)
        text.setZValue(2)
        self.plot.addItem(text)
        self.texts[city_name] = text
    
    def update_city_population_label(self, city_name):
        if city_name in self.texts:
            pop = self.network.active_cities[city_name]['pop']
            html_info = f"""<font size="3">
                            {city_name}<br>Population: {pop}
                            </font>
            """
            self.texts[city_name].setHtml(html_info)


    def add_city(self):
        remaining = [k for k in self.all_cities if k not in self.network.active_cities]
        if not remaining:
            self.add_city_timer.stop()
            return
        new_city = random.choice(remaining)
        if self.network.add_city(new_city):
            new_city_info = self.network.active_cities[new_city]
            self.city_scatter.addPoints(pos = [new_city_info['pos']], data = [new_city])
            self.add_city_label(new_city, new_city_info)
    
    def load_plane(self, plane):
        start_city, end_city = plane.rotta
        places_left = plane.capacity - sum(plane.passengers.values())
        city_pas = self.network.active_cities[start_city]['pas']
        ordered_city_pas = dict(sorted(city_pas.items(), key = lambda item:item[1], reverse = True))
        while (places_left > 0) and (ordered_city_pas != {}):
            first_city = list(ordered_city_pas.keys())[0] #first city in ordered city -> most passengers
            n_pas_first = ordered_city_pas[first_city]
            if n_pas_first < places_left:
                plane.passengers[first_city] = n_pas_first
                ordered_city_pas.pop(first_city)
                places_left = plane.capacity - sum(plane.passengers.values())
            else:
                plane.passengers[first_city] = places_left
                ordered_city_pas[first_city] = ordered_city_pas[first_city] - places_left
                places_left = plane.capacity - sum(plane.passengers.values())


    def on_city_clicked(self, scatter, points):
        if not points:
            return
        city_name = points[0].data()
        if not city_name:
            return
        start = self.network.active_cities[city_name]['pos']
        options = ["Creare una linea di connessione"] if not self.network.connections.get(city_name) else ["Far partire un aereo", "Creare una linea di connessione", "Eliminare una linea di connessione"]
        choice, ok = QtWidgets.QInputDialog.getItem(None, f"Azioni per città {city_name}", "Scegli un'azione:", options, 0, False)
        if not ok:
            return
        if choice == "Far partire un aereo":
            possible = self.network.connections[city_name] #cities connected with city_name
            dest_city, ok =  QtWidgets.QInputDialog.getItem(None, "Scegli destinazione", "Città di destinazione:", possible, 0, False)
            if not ok:
                return 
            
            end = self.network.active_cities[dest_city]['pos']
            conn = tuple(sorted([city_name, dest_city]))
            rotta_aereo = [city_name, dest_city]
            
            plane = Airplane('airplane.svg', start, end, size = self.plane_size,
                             connection = conn, rotta = rotta_aereo,
                             parent = self)
            # plane.passengers = random.randint(0, plane.capacity)
            self.load_plane(plane)
            print(plane.passengers)
            plane.update_color()
            
            self.network.active_cities[city_name]['pop'] -= sum(plane.passengers.values())
            self.update_city_population_label(city_name)
            plane.item.clicked.connect(self.on_airplane_clicked)
            self.plot.addItem(plane.item)
            # Collegamento click sull’aereo alla funzione principale
            plane.item.mousePressEvent = lambda event, p = plane: self.on_airplane_clicked(p)
            self.active_planes.append(plane)
            print(f"Aereo da {city_name} a {dest_city}, capacità: {plane.capacity}, passeggeri: {plane.passengers}")
            if not self.animation_timer.isActive():
                self.animation_timer.start()
                
        elif choice == "Creare una linea di connessione":
            possible = [k for k in self.network.active_cities.keys() if k != city_name and k not in self.network.connections[city_name]]
            if not possible:
                return
            dest_city, ok = QtWidgets.QInputDialog.getItem(None, "Scegli destinazione", "Città di destinazione:", possible, 0, False)
            if not ok:
                return
            end = self.network.active_cities[dest_city]['pos']
            self.network.connect(city_name, dest_city)
            
            line = pg.PlotCurveItem(x=[start[0], end[0]], y=[start[1], end[1]],
                                    pen = self.pen_dashed)
            line.setZValue(0.5)
            # line = ClickableLine(city_name, dest_city, start, end, 
            #                      on_click_callback=self.on_connection_clicked)
            self.plot.addItem(line)
            self.lines.append(line)


        elif choice == "Eliminare una linea di connessione":
            if not self.network.connections[city_name]:
                return
            dest_city, ok = QtWidgets.QInputDialog.getItem(None, "Scegli collegamento da eliminare", "Città collegata:", self.network.connections[city_name], 0, False)
            if not ok:
                return
            self.network.disconnect(city_name, dest_city)
            for line in self.lines:
                line_x, line_y = line.getData()
                coords = [(line_x[0], line_y[0]), (line_x[1], line_y[1])]
                if self.network.active_cities[city_name]['pos'] in coords and self.network.active_cities[dest_city]['pos'] in coords:
                    self.plot.removeItem(line)
                    self.lines.remove(line)
                    break
            conn = tuple(sorted([city_name, dest_city]))
            planes_to_remove = [p for p in self.active_planes if p.connection == conn]
            for plane in planes_to_remove:
                self.plot.removeItem(plane.item)
                self.active_planes.remove(plane)
    
    def on_airplane_clicked(self, plane):
        plane.clicked = True
        # Chiudi eventuale widget aperto prima
        if hasattr(self, 'current_info_widget') and self.current_info_widget:
            self.plot.removeItem(self.current_info_widget)
            self.current_info_widget = None
    
        # Crea etichetta con informazioni
        label = QtWidgets.QLabel(f"Passeggeri: {plane.passengers}")
        plane.info_label = label  # salva il riferimento
        label.setStyleSheet("""
            background-color: white;
            border: 1px solid black;
            font-size: 20px;
            padding: 1px;
        """)
        # label.setFixedSize(70, 25)

        proxy = QtWidgets.QGraphicsProxyWidget()
        proxy.setWidget(label)
        proxy.setZValue(4)
        self.plot.addItem(proxy)
    
        # Salva riferimento al widget
        self.current_info_widget = proxy
        plane.info_widget = proxy
    
        # Posiziona la finestra vicino all'aereo
        self.update_info_position(plane)
    
    
    # def on_connection_clicked(self, clickable_line):
    #     city1 = clickable_line.city1
    #     city2 = clickable_line.city2
    #     # apri qui il dialogo per aggiungere l'aereo
    #     msg = f"Aggiungere un aereo sulla rotta {city1} ↔ {city2}?"
    #     confirm = QtWidgets.QMessageBox.question(None, "Nuovo Aereo", msg)
        
    #     if confirm == QtWidgets.QMessageBox.Yes:
    #         pos1 = self.network.active_cities[city1]['pos']
    #         pos2 = self.network.active_cities[city2]['pos']
    #         conn = tuple(sorted([city1, city2]))
        
    #         airplane = Airplane("airplane.svg", pos1, pos2, capacity=100, 
    #                             connection=conn, parent = self)
    #         self.plot.addItem(airplane.item)
    #         self.active_planes.append(airplane)
    

                
    def update_info_position(self, plane):
        if hasattr(plane, 'info_widget') and plane.info_widget:
            x, y = plane.position
            transform = QtGui.QTransform()
            transform.scale(1, -1)  # 1 sull'asse X, -1 sull'asse Y → flip verticale

            # Posiziona leggermente sopra l’aereo
            plane.info_widget.setPos(x + 5, y + 5)
            plane.info_widget.setTransform(transform)
    


    

    def animate(self):
        for plane in self.active_planes:
            plane.update(speed = self.animation_speed)
            if hasattr(plane, 'info_widget') and plane.info_widget:
                self.update_info_position(plane)
            
        if not self.active_planes:
            self.animation_timer.stop()


    def on_plot_clicked(self, event):
        pos = self.plot.vb.mapSceneToView(event.scenePos())
        points = self.city_scatter.pointsAt(pos)
        
        # Se non hai cliccato un aereo, rimuovi eventuali info_widget attivi
        for plane in self.active_planes:
            plane.clicked = False
            if hasattr(plane, 'info_widget') and plane.info_widget:
                self.plot.removeItem(plane.info_widget)
                plane.info_widget = None
                
        if len(points) == 0:
            return



    def closeEvent(self, event):
        self.animation_timer.stop()
        self.add_city_timer.stop()
        event.accept()

if __name__ == "__main__":
    game = AirplaneGame()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()

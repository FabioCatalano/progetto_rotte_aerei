import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets, QtGui, QtSvg
import numpy as np
from PyQt5.QtWidgets import QInputDialog
import random
import sys

# Fare in modo che la città di start e quella di end siano definibili. 
# Al momento connection è unico, quindi A->B e B->A sono la stessa cosa

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
                 size = 15, connection = None, capacity = 100):
        self.parent = parent
        self.start = np.array(start_pos)
        self.end = np.array(end_pos)
        self.position = np.array(start_pos)
        self.size = size
        self.distance = 0
        self.direction = 1
        self.connection = connection
        self.capacity = capacity 
        
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

    def set_pos(self, pos):
        self.position = pos
        self.item.setPos(pos[0], pos[1])
        
    def update(self, speed = 0.5):
        self.distance += speed * self.direction
        
        if self.distance >= self.length:
            self.distance = self.length
            self.direction *= -1 #inverte direzione
            
            #aggiorna i passeggeri nelle città
            end_city = self.connection[1]
            start_city = self.connection[0]
            self.parent.network.active_cities[end_city]['pop'] += self.capacity
            self.parent.network.active_cities[start_city]['pop'] -= self.capacity
            
            self.update_transform()
            
            self.parent.plot.removeItem(self.parent.texts[start_city])
            self.parent.add_city_label(start_city, self.parent.network.active_cities[start_city])
            self.parent.plot.removeItem(self.parent.texts[end_city])
            self.parent.add_city_label(end_city, self.parent.network.active_cities[end_city])
            
        elif self.distance <= 0:
            self.distance = 0
            self.direction *= -1  # Inverte la direzione
    
            # Scarica passeggeri alla città di origine
            end_city = self.connection[0]
            start_city = self.connection[1]
            self.parent.network.active_cities[end_city]['pop'] += self.capacity
            self.parent.network.active_cities[start_city]['pop'] -= self.capacity
    
            self.update_transform()
    
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



class AirplaneGame:
    def __init__(self):
        self.app = pg.mkQApp()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        
        self.plane_size = 50
        self.city_size = 30

        self.win = pg.GraphicsLayoutWidget(show=True, title='Gioco aerei volanti')
        self.plot = self.win.addPlot()
        self.plot.setAspectLocked(True)

        self.all_cities = {
            'A': {'pos': (100, 200), 'pop': 5000},
            'B': {'pos': (500, 800), 'pop': 7000},
            'C': {'pos': (700, 400), 'pop': 3000},
            'D': {'pos': (900, 900), 'pop': 10000},
            'E': {'pos': (300, 600), 'pop': 4500},
            'F': {'pos': (800, 200), 'pop': 3500},
            'G': {'pos': (600, 100), 'pop': 2500},
            'H': {'pos': (400, 700), 'pop': 6000}
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
                    {city_name}<br>Pop: {pop}
                    </font>
        """.format(city_name = city_name, pop = pop)
        text = pg.TextItem(label, anchor=(0.4, 0.1), color = 'black', html = html_info)
        text.setPos(*pos)
        text.setZValue(2)
        self.plot.addItem(text)
        self.texts[city_name] = text


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

    def on_city_clicked(self, scatter, points):
        if not points:
            return
        city_name = points[0].data()
        if not city_name:
            return
        start = self.network.active_cities[city_name]['pos']
        options = ["Creare una linea di connessione"] if not self.network.connections.get(city_name) else ["Far partire un aereo", "Creare una linea di connessione", "Eliminare una linea di connessione"]
        choice, ok = QInputDialog.getItem(None, f"Azioni per città {city_name}", "Scegli un'azione:", options, 0, False)
        if not ok:
            return
        if choice == "Far partire un aereo":
            dest_city = random.choice(self.network.connections[city_name])
            end = self.network.active_cities[dest_city]['pos']
            conn = tuple(sorted([city_name, dest_city]))
            
            plane = Airplane('airplane.svg', start, end, size = self.plane_size,
                             connection = conn, capacity = random.randint(20, 150),
                             parent = self)
            
            plane.item.clicked.connect(self.on_airplane_clicked)
            self.plot.addItem(plane.item)
            # Collegamento click sull’aereo alla funzione principale
            plane.item.mousePressEvent = lambda event, p=plane: self.on_airplane_clicked(p)
            self.active_planes.append(plane)
            print(f"Aereo da {city_name} a {dest_city}, capacità: {plane.capacity} passeggeri")
            if not self.animation_timer.isActive():
                self.animation_timer.start()
                
        elif choice == "Creare una linea di connessione":
            possible = [k for k in self.network.active_cities.keys() if k != city_name and k not in self.network.connections[city_name]]
            if not possible:
                return
            dest_city, ok = QInputDialog.getItem(None, "Scegli destinazione", "Città di destinazione:", possible, 0, False)
            if not ok:
                return
            end = self.network.active_cities[dest_city]['pos']
            self.network.connect(city_name, dest_city)
            line = pg.PlotCurveItem(x=[start[0], end[0]], y=[start[1], end[1]],
                                    pen = self.pen_dashed)
            line.setZValue(0.5)
            self.plot.addItem(line)
            self.lines.append(line)
        elif choice == "Eliminare una linea di connessione":
            if not self.network.connections[city_name]:
                return
            dest_city, ok = QInputDialog.getItem(None, "Scegli collegamento da eliminare", "Città collegata:", self.network.connections[city_name], 0, False)
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
        # Chiudi eventuale widget aperto prima
        if hasattr(self, 'current_info_widget') and self.current_info_widget:
            self.plot.removeItem(self.current_info_widget)
            self.current_info_widget = None
    
        # Crea etichetta con informazioni
        label = QtWidgets.QLabel(f"Passeggeri: {plane.capacity}")
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

                
    def update_info_position(self, plane):
        if hasattr(plane, 'info_widget') and plane.info_widget:
            x, y = plane.position
            # Posiziona leggermente sopra l’aereo
            plane.info_widget.setPos(x + 5, y + 5)
    

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

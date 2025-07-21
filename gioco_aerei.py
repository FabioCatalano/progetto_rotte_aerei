import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets, QtGui, QtSvg
import numpy as np
from PyQt5.QtWidgets import QInputDialog
import random
import sys

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
    def __init__(self, svg_path, start_pos, end_pos, size = 5, connection = None):
        self.start = np.array(start_pos)
        self.end = np.array(end_pos)
        self.position = np.array(start_pos)
        self.size = size
        self.distance = 0
        self.direction = 1
        self.connection = connection

        direction_vec = self.end - self.start
        self.length = np.linalg.norm(direction_vec)
        self.angle = np.degrees(np.arctan2(direction_vec[1], direction_vec[0])) + 90

        self.item = QtSvg.QGraphicsSvgItem(svg_path)
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
        if self.distance >= self.length or self.distance <= 0:
            self.direction *= -1 #inverte direzione
            transform = QtGui.QTransform()
            transform.rotate(self.angle + (180 if self.direction == -1 else 0))
            bounds = self.item.boundingRect()
            scale = self.item.scale()
            transform.translate(-bounds.width() * scale / 2, -bounds.height() * scale / 2)
            self.item.setTransform(transform)
            self.distance = max(0, min(self.distance, self.length))

        t = self.distance / self.length if self.length else 1
        new_pos = (1 - t) * self.start + t * self.end
        self.set_pos(new_pos)

class AirplaneGame:
    def __init__(self):
        self.app = pg.mkQApp()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.win = pg.GraphicsLayoutWidget(show=True, title='Gioco aerei volanti')
        self.plot = self.win.addPlot()
        self.plot.setAspectLocked(True)

        self.all_cities = {'A': (10, 20), 'B': (50, 80), 'C': (70, 40), 'D': (90, 90),
                           'E': (30, 60), 'F': (80, 20), 'G': (60, 10), 'H': (40, 70)}

        self.network = CityNetwork(self.all_cities)
        for city in ['A', 'B', 'C']:
            self.network.add_city(city)

        self.city_scatter = pg.ScatterPlotItem(
            pos=list(self.network.active_cities.values()),
            data=list(self.network.active_cities.keys()),
            size=15,
            brush=pg.mkBrush('dodgerblue'),
            pen=pg.mkPen('black')
        )
        self.city_scatter.setZValue(1)
        self.plot.addItem(self.city_scatter)

        self.pen_dashed = pg.mkPen(color=(80, 80, 80), width=2, style=QtCore.Qt.DashLine)
        self.lines = []
        self.texts = []

        for name, (x, y) in self.network.active_cities.items():
            self.add_city_label(name, (x, y))

        self.active_planes = []
        self.animation_speed = 0.5

        self.animation_timer = QtCore.QTimer()
        self.animation_timer.setInterval(30)
        self.animation_timer.timeout.connect(self.animate)

        self.add_city_timer = QtCore.QTimer()
        self.add_city_timer.timeout.connect(self.add_city)
        self.add_city_timer.start(10000)

        self.city_scatter.sigClicked.connect(self.on_city_clicked)
        self.plot.scene().sigMouseClicked.connect(self.on_plot_clicked)
        self.win.closeEvent = self.closeEvent

    def add_city_label(self, city_name, pos):
        text = pg.TextItem(city_name, anchor=(0.5, -0.5), color='black')
        text.setPos(*pos)
        text.setZValue(2)
        self.plot.addItem(text)
        self.texts.append(text)

    def add_city(self):
        remaining = [k for k in self.all_cities if k not in self.network.active_cities]
        if not remaining:
            self.add_city_timer.stop()
            return
        new_city = random.choice(remaining)
        if self.network.add_city(new_city):
            new_pos = self.network.active_cities[new_city]
            self.city_scatter.addPoints(pos=[new_pos], data=[new_city])
            self.add_city_label(new_city, new_pos)

    def on_city_clicked(self, scatter, points):
        if not points:
            return
        city_name = points[0].data()
        if not city_name:
            return
        start = self.network.active_cities[city_name]
        options = ["Creare una linea di connessione"] if not self.network.connections.get(city_name) else ["Far partire un aereo", "Creare una linea di connessione", "Eliminare una linea di connessione"]
        choice, ok = QInputDialog.getItem(None, f"Azioni per città {city_name}", "Scegli un'azione:", options, 0, False)
        if not ok:
            return
        if choice == "Far partire un aereo":
            dest_city = random.choice(self.network.connections[city_name])
            end = self.network.active_cities[dest_city]
            conn = tuple(sorted([city_name, dest_city]))
            plane = Airplane('airplane.svg', start, end, size=5, connection=conn)
            self.plot.addItem(plane.item)
            self.active_planes.append(plane)
            if not self.animation_timer.isActive():
                self.animation_timer.start()
        elif choice == "Creare una linea di connessione":
            possible = [k for k in self.network.active_cities.keys() if k != city_name and k not in self.network.connections[city_name]]
            if not possible:
                return
            dest_city, ok = QInputDialog.getItem(None, "Scegli destinazione", "Città di destinazione:", possible, 0, False)
            if not ok:
                return
            end = self.network.active_cities[dest_city]
            self.network.connect(city_name, dest_city)
            line = pg.PlotCurveItem(x=[start[0], end[0]], y=[start[1], end[1]], pen=self.pen_dashed)
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
                if self.network.active_cities[city_name] in coords and self.network.active_cities[dest_city] in coords:
                    self.plot.removeItem(line)
                    self.lines.remove(line)
                    break
            conn = tuple(sorted([city_name, dest_city]))
            planes_to_remove = [p for p in self.active_planes if p.connection == conn]
            for plane in planes_to_remove:
                self.plot.removeItem(plane.item)
                self.active_planes.remove(plane)

    def animate(self):
        for plane in self.active_planes:
            plane.update(speed=self.animation_speed)
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

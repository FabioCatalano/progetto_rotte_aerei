import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets, QtGui, QtSvg
import numpy as np
from PyQt5.QtWidgets import QInputDialog
import random
import sys


class AirplaneGame:
    def __init__(self):
        self.app = pg.mkQApp()
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.win = pg.GraphicsLayoutWidget(show=True, title='Gioco aerei volanti')
        self.plot = self.win.addPlot()
        self.plot.setAspectLocked(True)

        self.all_cities = {
            'A': (10, 20), 'B': (50, 80), 'C': (70, 40), 'D': (90, 90),
            'E': (30, 60), 'F': (80, 20), 'G': (60, 10), 'H': (40, 70)
        }

        self.cities = {k: v for k, v in self.all_cities.items() if k in ['A', 'B', 'C']}
        self.city_positions = list(self.cities.values())

        self.city_scatter = pg.ScatterPlotItem(
            pos=self.city_positions, size=15, brush=pg.mkBrush('dodgerblue'), pen=pg.mkPen('black')
        )
        self.city_scatter.setZValue(1)
        self.plot.addItem(self.city_scatter)

        self.connections = {city: [] for city in self.all_cities.keys()}

        self.pen_dashed = pg.mkPen(color=(80, 80, 80), width=2, style=QtCore.Qt.DashLine)
        self.lines = []
        self.texts = []

        for name, (x, y) in self.cities.items():
            text = pg.TextItem(name, anchor=(0.5, -0.5), color='black')
            text.setPos(x, y)
            text.setZValue(2)
            self.plot.addItem(text)
            self.texts.append(text)

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

    def add_city(self):
        remaining = [k for k in self.all_cities if k not in self.cities]
        if not remaining:
            self.add_city_timer.stop()
            return

        new_city = remaining[0]
        new_pos = self.all_cities[new_city]
        self.cities[new_city] = new_pos
        self.city_positions = list(self.cities.values())
        self.city_scatter.setData(pos=self.city_positions)

        text = pg.TextItem(new_city, anchor=(0.5, -0.5), color='black')
        text.setPos(*new_pos)
        self.plot.addItem(text)
        self.texts.append(text)

    def create_airplane_svg_item(self, svg_path, starting_point, size=5, angle=0):
        item = QtSvg.QGraphicsSvgItem(svg_path)
        item.setFlags(QtWidgets.QGraphicsItem.ItemClipsToShape)
        item.setCacheMode(QtWidgets.QGraphicsItem.NoCache)
        item.setZValue(3)
        bounds = item.boundingRect()
        scale = size / max(bounds.width(), bounds.height())
        item.setScale(scale)
        translation_value = (-bounds.width() * scale / 2, -bounds.height() * scale / 2)
        transform = QtGui.QTransform()
        transform.rotate(angle)
        transform.translate(*translation_value)
        item.setTransform(transform)
        item.setPos(starting_point[0] - bounds.width() * scale / 2,
                    starting_point[1] - bounds.height() * scale / 2)
        item.setVisible(True)
        return item

    def interpolate_points(self, p1, p2, t):
        return (1 - t) * np.array(p1) + t * np.array(p2)

    def on_city_clicked(self, scatter, points):
        if not points:
            return
        pt = points[0].pos()
        clicked_pos = (pt.x(), pt.y())
        try:
            idx = self.city_positions.index(clicked_pos)
        except ValueError:
            return

        city_name = list(self.cities.keys())[idx]
        start = self.city_positions[idx]

        options = ["Creare una linea di connessione"] if not self.connections[city_name] else ["Far partire un aereo", "Creare una linea di connessione", "Eliminare una linea di connessione"]
        choice, ok = QInputDialog.getItem(None, f"Azioni per città {city_name}", "Scegli un'azione:", options, 0, False)
        if not ok:
            return

        if choice == "Far partire un aereo":
            dest_city = random.choice(self.connections[city_name])
            end = self.cities[dest_city]
            direction = np.array(end) - np.array(start)
            angle = np.degrees(np.arctan2(direction[1], direction[0])) + 90
            length = np.linalg.norm(direction)
            plane = self.create_airplane_svg_item('airplane.svg', start, 5, angle)
            self.plot.addItem(plane)
            self.active_planes.append({'item': plane, 'start': start, 'end': end, 'angle': angle, 'length': length, 'distance': 0, 'direction': 1})
            if not self.animation_timer.isActive():
                self.animation_timer.start()

        elif choice == "Creare una linea di connessione":
            possible = [k for k in self.cities.keys() if k != city_name and k not in self.connections[city_name]]
            if not possible:
                return
            dest_city, ok = QInputDialog.getItem(None, "Scegli destinazione", "Città di destinazione:", possible, 0, False)
            if not ok:
                return
            end = self.cities[dest_city]
            self.connections[city_name].append(dest_city)
            self.connections[dest_city].append(city_name)
            line = pg.PlotDataItem(x=[start[0], end[0]], y=[start[1], end[1]], pen=self.pen_dashed)
            line.setZValue(0.5)
            self.plot.addItem(line)
            self.lines.append(line)

        elif choice == "Eliminare una linea di connessione":
            if not self.connections[city_name]:
                return
            dest_city, ok = QInputDialog.getItem(None, "Scegli collegamento da eliminare", "Città collegata:", self.connections[city_name], 0, False)
            if not ok:
                return
            self.connections[city_name].remove(dest_city)
            self.connections[dest_city].remove(city_name)
            for line in self.lines:
                line_x, line_y = line.getData()
                coords = [(line_x[0], line_y[0]), (line_x[1], line_y[1])]
                if self.cities[city_name] in coords and self.cities[dest_city] in coords:
                    self.plot.removeItem(line)
                    self.lines.remove(line)
                    break

    def animate(self):
        for plane in self.active_planes:
            plane['distance'] += self.animation_speed * plane['direction']
            if plane['distance'] >= plane['length'] or plane['distance'] <= 0:
                plane['direction'] *= -1
                transform = QtGui.QTransform()
                transform.rotate(plane['angle'] + (180 if plane['direction'] == -1 else 0))
                bounds = plane['item'].boundingRect()
                scale = plane['item'].scale()
                transform.translate(-bounds.width()*scale/2, -bounds.height()*scale/2)
                plane['item'].setTransform(transform)
                plane['distance'] = max(0, min(plane['distance'], plane['length']))
            t = plane['distance'] / plane['length'] if plane['length'] else 1
            new_pos = self.interpolate_points(plane['start'], plane['end'], t)
            plane['item'].setPos(*new_pos)

        if not self.active_planes:
            self.animation_timer.stop()

    def on_plot_clicked(self, event):
        pos = self.plot.vb.mapSceneToView(event.scenePos())
        points = self.city_scatter.pointsAt(pos)
        if len(points) == 0:
            return
        if not self.city_scatter.pointsAt(pos):
            pass
    
    def closeEvent(self, event):
        # Ferma i timer in modo sicuro alla chiusura della finestra
        self.animation_timer.stop()
        self.add_city_timer.stop()
        event.accept()  # Accetta l'evento di chiusura senza forzare l'uscita



if __name__ == "__main__":
    game = AirplaneGame()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()



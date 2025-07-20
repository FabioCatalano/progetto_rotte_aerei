import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets, QtGui, QtSvg
import numpy as np
from PyQt5.QtWidgets import QInputDialog
import random


app = pg.mkQApp()

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

win = pg.GraphicsLayoutWidget(show = True, title='Gioco aerei volanti')
plot = win.addPlot()
plot.setAspectLocked(True)

# Lista di città “da aggiungere” (coordinate e nomi non ancora presenti)
all_cities = {
    'A': (10, 20),
    'B': (50, 80),
    'C': (70, 40),
    'D': (90, 90),
    'E': (30, 60),
    'F': (80, 20),
    'G': (60, 10),
    'H': (40, 70)
}

# Iniziamo con alcune città (per esempio solo A, B, C)
cities = {k: v for k, v in all_cities.items() if k in ['A', 'B', 'C']}
city_positions = list(cities.values())

city_scatter = pg.ScatterPlotItem(
    pos = city_positions,
    size = 15,
    brush = pg.mkBrush('dodgerblue'),
    pen = pg.mkPen('black')
)
city_scatter.setZValue(1)
plot.addItem(city_scatter)


# Inizializziamo connections senza collegamenti
connections = {city: [] for city in all_cities.keys()}

pen_dashed = pg.mkPen(color = (80, 80, 80), width = 2, style = QtCore.Qt.DashLine)
lines = []

texts = []

#anchor posiziona rispetto a (x,y)
for name, (x, y) in cities.items():
    text = pg.TextItem(name, anchor = (0.5, -0.5), color='black')
    text.setPos(x, y)
    text.setZValue(2)
    plot.addItem(text)
    texts.append(text)

# Timer per aggiungere città ogni 10 secondi
def add_city():
    global cities, city_positions, texts

    # Trova città non ancora aggiunte
    remaining = [k for k in all_cities.keys() if k not in cities]
    if not remaining:
        # Nessuna città rimasta, ferma timer
        add_city_timer.stop()
        return

    # Prendi una città a caso o in ordine
    new_city = remaining[0]
    new_pos = all_cities[new_city]

    # Aggiungi alla mappa
    cities[new_city] = new_pos
    city_positions = list(cities.values())

    # Aggiorna scatter
    city_scatter.setData(pos=city_positions)

    # Aggiungi testo della nuova città
    text = pg.TextItem(new_city, anchor=(0.5, -0.5), color='black')
    text.setPos(*new_pos)
    plot.addItem(text)
    texts.append(text)

add_city_timer = QtCore.QTimer()
add_city_timer.timeout.connect(add_city)
add_city_timer.start(10000)  # 10 secondi


def create_airplane_svg_item(svg_path, starting_point, size = 5, angle = 0,):
    item = QtSvg.QGraphicsSvgItem(svg_path)
    item.setFlags(QtWidgets.QGraphicsItem.ItemClipsToShape)
    item.setCacheMode(QtWidgets.QGraphicsItem.NoCache)
    item.setZValue(3)
    bounds = item.boundingRect()
    scale = size / max(bounds.width(), bounds.height())
    item.setScale(scale)
    translation_value = (-bounds.width()*scale / 2, -bounds.height()*scale / 2)
    transform = QtGui.QTransform()
    transform.rotate(angle)
    transform.translate(*translation_value)
    item.setTransform(transform)
    x_start = starting_point[0] -bounds.width() * scale / 2
    y_start = starting_point[1] -bounds.height() * scale / 2
    item.setPos(x_start, y_start)
    item.setVisible(True)
    
    return item

active_planes = []

animation_timer = QtCore.QTimer()
animation_timer.setInterval(30)
animation_speed = 0.5


def interpolate_points(p1, p2, t):
    return (1 - t) * np.array(p1) + t * np.array(p2)


def on_city_clicked(scatter, points):
    if points:
        pt = points[0].pos()
        clicked_pos = (pt.x(), pt.y())
        try:
            idx = city_positions.index(clicked_pos)
        except ValueError:
            return


        city_name = list(cities.keys())[idx]
        
        
        if len(connections[city_name]) == 0:
            actions = ["Creare una linea di connessione"]
        else:
            actions = ["Far partire un aereo", "Creare una linea di connessione", "Eliminare una linea di connessione"]
        
        choice, ok = QInputDialog.getItem(
            None,
            f"Azioni per città {city_name}",
            "Scegli un'azione:",
            actions,
            0,
            False
        )
        if not ok:
            return

        start = city_positions[idx]

        if choice == "Far partire un aereo":
            next_city = random.choice(connections[city_name])
            next_idx = list(cities.keys()).index(next_city)
            end = city_positions[next_idx]
            direction = np.array(end) - np.array(start)
            angle = np.degrees(np.arctan2(direction[1], direction[0])) + 90
            length = np.linalg.norm(direction)

            plane = create_airplane_svg_item('airplane.svg', size=5, angle=angle, starting_point=start)
            plot.addItem(plane)
            
            active_planes.append({
                'item': plane,
                'start': start,
                'end': end,
                'angle': angle,
                'length': length,
                'distance': 0,
                'direction': 1,   # inizio volo in avanti
                'base_scale': plane.scale()
            })


            if not animation_timer.isActive():
                animation_timer.start()

        elif choice == "Creare una linea di connessione":
            dest_city, ok = QInputDialog.getItem(
                None,
                f"Scegli destinazione da {city_name}",
                "Città di destinazione:",
                [m for m in list(cities.keys()) if m != city_name and m not in connections[city_name]],
                0,
                False
            )
            if not ok or dest_city == city_name:
                return

            end = cities[dest_city]
            
            connections[city_name].append(dest_city)
            connections[dest_city].append(city_name)
            print(connections)
            
            line = pg.PlotDataItem(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                pen=pen_dashed
            )
            line.setZValue(0.5)
            plot.addItem(line)
            lines.append(line)

        elif choice == "Eliminare una linea di connessione":
            if len(connections[city_name]) == 0:
                return
            dest_city, ok = QInputDialog.getItem(
                None,
                f"Scegli quale connessione eliminare da {city_name}",
                "Città collegata:",
                connections[city_name],
                0,
                False
            )
            if not ok:
                return
            
            connections[city_name].remove(dest_city)
            connections[dest_city].remove(city_name)
            print(connections)

            # Rimuove la linea grafica
            for line in lines:
                line_x = line.getData()[0]
                line_y = line.getData()[1]
                line_coords = [(line_x[0], line_y[0]), (line_x[1], line_y[1])]
                if (cities[city_name] in line_coords) and (cities[dest_city] in line_coords):
                    plot.removeItem(line)
                    lines.remove(line)
                    break


def animate():
    global active_planes
    for anim in active_planes:
        # Aggiorna la distanza in base alla direzione
        anim['distance'] += animation_speed * anim.get('direction', 1)
        
        bounds = anim['item'].boundingRect()
        scale = anim['item'].scale()
        translation_value = (-bounds.width()*scale / 2, -bounds.height()*scale / 2)
        # Se supera la lunghezza, inverti direzione
        if anim['distance'] >= anim['length']:
            transform = QtGui.QTransform()
            transform.rotate(anim['angle'] + 180)
            transform.translate(*translation_value)
            anim['item'].setTransform(transform)
            
            anim['distance'] = anim['length']
            anim['direction'] = -1  # torna indietro

        elif anim['distance'] <= 0:
            transform = QtGui.QTransform()
            transform.rotate(anim['angle'])
            transform.translate(*translation_value)
            anim['item'].setTransform(transform)
            
            anim['distance'] = 0
            anim['direction'] = 1   # torna avanti

        t = anim['distance'] / anim['length'] if anim['length'] != 0 else 1
        new_pos = interpolate_points(anim['start'], anim['end'], t)
        anim['item'].setPos(*new_pos)


    if len(active_planes) == 0:
        animation_timer.stop()

animation_timer.timeout.connect(animate)
city_scatter.sigClicked.connect(on_city_clicked)

def on_plot_clicked(event):
    pos = plot.vb.mapSceneToView(event.scenePos())
    clicked_points = city_scatter.pointsAt(pos)
    if len(clicked_points) == 0:
        pass

plot.scene().sigMouseClicked.connect(on_plot_clicked)

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()

# python3 -m venv Documents/DICIS_8vo_2025/Graficos_por_computadora/Proyecto/
# source /home/pixel/Documents/DICIS_8vo_2025/Graficos_por_computadora/Proyecto/bin/activate
# cd Documents/DICIS_8vo_2025/Graficos_por_computadora/Proyecto
# python3 3D_Renderer_stl.py
# QT_QPA_PLATFORM=xcb python3 3D_Renderer_stl.py
# deactivate
import sys
from PyQt5 import QtWidgets, QtCore, QtGui
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import random
import os

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.setWindowTitle("Renderizador 3D con vtk y PyQt")
        self.setGeometry(100, 100, 800, 600)  # Aumentar el tamaño de la ventana

        # Crear un widget central para la ventana
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # Diseño de la interfaz (usando QVBoxLayout)
        layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(layout)

        # Crear un widget VTK para el renderizado
        self.vtk_widget = QVTKRenderWindowInteractor(central_widget)
        layout.addWidget(self.vtk_widget)

        # Crear un layout horizontal para los botones
        button_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(button_layout)

        # Crear botones para cambiar el color del actor
        self.button_red = QtWidgets.QPushButton("Rojo")
        self.button_green = QtWidgets.QPushButton("Verde")
        self.button_blue = QtWidgets.QPushButton("Azul")
        self.button_random = QtWidgets.QPushButton("Random")
        self.button_texture = QtWidgets.QPushButton("Cargar Textura")

        self.button_red.setFixedWidth(100)
        self.button_green.setFixedWidth(100)
        self.button_blue.setFixedWidth(100)
        self.button_random.setFixedWidth(100)
        self.button_texture.setFixedWidth(150)

        # Conectar los botones a sus funciones correspondientes
        self.button_red.clicked.connect(lambda: self.change_actor_color(1, 0, 0))  # Rojo
        self.button_green.clicked.connect(lambda: self.change_actor_color(0, 1, 0))  # Verde
        self.button_blue.clicked.connect(lambda: self.change_actor_color(0, 0, 1))  # Azul
        self.button_random.clicked.connect(lambda: self.change_actor_color(random.random(), random.random(), random.random()))  # Random
        self.button_texture.clicked.connect(self.load_texture)

        # Añadir los botones al layout horizontal
        button_layout.addWidget(self.button_red)
        button_layout.addWidget(self.button_green)
        button_layout.addWidget(self.button_blue)
        button_layout.addWidget(self.button_random)
        button_layout.addWidget(self.button_texture)

        # Configurar VTK
        self.setup_vtk()

    def setup_vtk(self):
        # Crear el lector de archivos STL
        reader = vtk.vtkSTLReader()
        reader.SetFileName("/home/pixel/Documents/Blender/Models/Keycap_ubunto(2).stl")

        # Generar coordenadas de textura para el modelo
        texture_filter = vtk.vtkTextureMapToPlane()
        texture_filter.SetInputConnection(reader.GetOutputPort())

        # Crear el mapeador
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(texture_filter.GetOutputPort())

        # Crear el actor
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().SetColor(0.3, 0.3, 0.3)  # Color inicial

        # Crear el renderer y la ventana de renderizado
        self.renderer = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)

        # Añadir el actor al renderer
        self.renderer.AddActor(self.actor)
        self.renderer.SetBackground(1, 1, 1)  # Fondo blanco

        # Iniciar el interactor de VTK
        self.vtk_widget.GetRenderWindow().Render()
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

    def change_actor_color(self, r, g, b):
        # Cambiar el color del actor
        self.actor.GetProperty().SetColor(r, g, b)
        # Actualizar la ventana de renderizado
        self.vtk_widget.GetRenderWindow().Render()

    def load_texture(self):
        # Abrir un cuadro de diálogo para seleccionar la imagen
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Cargar Textura", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")

        if file_name:
            # Crear el lector de imagen
            reader = vtk.vtkPNGReader() if file_name.lower().endswith('.png') else \
                     vtk.vtkJPEGReader() if file_name.lower().endswith(('.jpg', '.jpeg')) else \
                     vtk.vtkBMPReader() if file_name.lower().endswith('.bmp') else None

            if reader:
                reader.SetFileName(file_name)

                # Crear el mapeador de textura
                texture = vtk.vtkTexture()
                texture.SetInputConnection(reader.GetOutputPort())

                # Asignar la textura al actor
                self.actor.SetTexture(texture)

                # Actualizar la ventana de renderizado
                self.vtk_widget.GetRenderWindow().Render()
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Formato de imagen no soportado.")

if __name__ == "__main__":
    # Iniciar la aplicación PyQt
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
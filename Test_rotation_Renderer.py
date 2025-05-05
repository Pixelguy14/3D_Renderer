import sys
from PyQt5 import QtWidgets, QtCore
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionWidgets import vtkCameraOrientationWidget
import random
from mainFunc import *
from camControls import *
import os
os.environ["QT_QPA_PLATFORM"] = "xcb" # Comentar esta linea si da problemas en windows

# https://examples.vtk.org/site/Python/Widgets/CameraOrientationWidget/
# https://stackoverflow.com/questions/61304532/how-to-show-alpha-channel-in-pyqt5-qcolordialog
# https://examples.vtk.org/site/Python/ImplicitFunctions/ImplicitSphere1/
# https://examples.vtk.org/site/Python/Rendering/PBR_Materials/
# https://examples.vtk.org/site/Python/Rendering/PBR_Materials_Coat/
# https://examples.vtk.org/site/Python/Rendering/PBR_HDR_Environment/
# https://vtk.org/doc/nightly/html/classvtkOpenGLProperty.html
# https://www.thingiverse.com/

# https://polyhaven.com/
# https://ambientcg.com/
# https://polygon.love/orm/


# https://www.artec3d.com/3d-models/stl

# Physically Based Rendering (PBR)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Renderizador 3D")
        self.setGeometry(100, 100, 1000, 800)
        
        # Variables de estado
        self.current_actor = None
        self.texture = None
        self.current_mapper = None
        self.texture_coords = None
        
        # Configuración de la interfaz
        self.init_ui()
        self.setup_vtk()

    def init_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Barra de herramientas superior para controles de cámara
        toolbar_top = QtWidgets.QHBoxLayout()
        
        self.current_view_index = 0

        # Botones de control de cámara
        camera_controls = [
            ("Alternar Vista", lambda: cycle_views(self)),
            ("45° x", lambda: rotate_view(self.renderer, self.vtk_widget, self.current_actor, 45,0,0)),
            ("45° y", lambda: rotate_view(self.renderer, self.vtk_widget, self.current_actor, 0,45,0)),
            ("45° z", lambda: rotate_view(self.renderer, self.vtk_widget, self.current_actor, 0,0,45)),
            ("Eliminar Modelo", lambda: setattr(self, 'current_actor', remove_model(self.renderer, self.vtk_widget, self.texture, self.current_mapper, self.current_actor, self.texture_coords)))
        ]
        
        for text, callback in camera_controls:
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(callback)
            btn.setFixedWidth(100)
            toolbar_top.addWidget(btn)
        
        layout.addLayout(toolbar_top)
        
        # Widget VTK
        self.vtk_widget = QVTKRenderWindowInteractor(central_widget)
        layout.addWidget(self.vtk_widget)

        self.current_texture_index = 0
        self.current_background_index = 0
        
        # Barra de herramientas inferior para operaciones
        toolbar_bottom = QtWidgets.QHBoxLayout()
        operations = [
            ("Cargar STL", lambda: setattr(self, 'current_actor', load_stl(self, self.renderer, self.vtk_widget, self.texture, self.current_mapper, self.current_actor, self.texture_coords))),
            ("Cargar Imagen", lambda: load_texture(self.renderer, self.vtk_widget, self.current_actor)),
            ("Alternar Textura", lambda: cycle_texture(self, self.renderer, self.vtk_widget, self.current_actor)),
            ("Alternar Fondo", lambda: cycle_background(self, self.current_actor)),
            ("Color Figura", lambda: set_actor_color(self.renderer, self.vtk_widget, self.current_actor, self.texture_coords, self.current_mapper)),
            ("Reiniciar textura", lambda: clear_texture(self.renderer, self.vtk_widget, self.current_actor, self.texture_coords, self.current_mapper)),
            ("Visualizar Mesh", lambda: set_mesh_visible(self.renderer, self.vtk_widget, self.current_actor, self.texture_coords, self.current_mapper))
        ]
        
        for text, callback in operations:
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(callback)
            btn.setFixedWidth(120)
            toolbar_bottom.addWidget(btn)
        
        layout.addLayout(toolbar_bottom)

    def setup_vtk(self):
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.2, 0.2, 0.2)
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        
        # Configurar estilo de interacción
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)
        
        # Configurar el widget de orientación de cámara
        self.camera_orientation_widget = vtkCameraOrientationWidget()
        self.camera_orientation_widget.SetParentRenderer(self.renderer)
        self.camera_orientation_widget.SetInteractor(self.interactor)
        self.camera_orientation_widget.On()

        # Inicialización diferida
        QtCore.QTimer.singleShot(100, self.finalize_vtk_setup)

        # Configurar iluminación ambiental
        #setup_environment_lighting(self)

    def finalize_vtk_setup(self):
        self.vtk_widget.GetRenderWindow().Render()
        self.interactor.Initialize()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # Configuración para sistemas Linux/X11
    if sys.platform == 'linux':
        app.setAttribute(QtCore.Qt.AA_X11InitThreads, True)
    
    window = MainWindow()
    window.show()
    
    # Forzar procesamiento inicial de eventos
    app.processEvents()
    
    sys.exit(app.exec_())
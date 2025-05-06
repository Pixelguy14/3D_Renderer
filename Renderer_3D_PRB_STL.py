import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionWidgets import vtkCameraOrientationWidget
import random
from mainFunc import *
from camControls import *

# Variable que define el ambiente en Linux
# Comentar esta linea si da problemas en windows
os.environ["QT_QPA_PLATFORM"] = "xcb"

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

class IconButton(QtWidgets.QPushButton):
    def __init__(self, icon_name, text="", tooltip="", parent=None):
        super().__init__(parent)
        self.setToolTip(tooltip)
        
        if icon_name:
            self.setIcon(self.get_icon(icon_name))
        
        if text:
            self.setText(text)
            
        self.setFixedSize(36, 36)
        self.setIconSize(QtCore.QSize(20, 20))
        
    def get_icon(self, name):
        # Use Qt's standard icons
        icon_map = {
            "load": QtWidgets.QStyle.SP_FileDialogStart,
            "image": QtWidgets.QStyle.SP_FileDialogDetailedView,
            "texture": QtWidgets.QStyle.SP_FileDialogInfoView,
            "background": QtWidgets.QStyle.SP_DesktopIcon,
            "color": QtWidgets.QStyle.SP_FileDialogListView,
            "reset": QtWidgets.QStyle.SP_BrowserReload,
            "mesh": QtWidgets.QStyle.SP_FileDialogListView,
            "view": QtWidgets.QStyle.SP_ComputerIcon,
            "rotate_x": QtWidgets.QStyle.SP_ArrowRight,
            "rotate_y": QtWidgets.QStyle.SP_ArrowUp,
            "rotate_z": QtWidgets.QStyle.SP_ArrowForward,
            "delete": QtWidgets.QStyle.SP_TrashIcon
        }
        
        if name in icon_map:
            return self.style().standardIcon(icon_map[name])
        return QtGui.QIcon()

class ToolPanel(QtWidgets.QWidget):
    # Definimos la sidebar con el estilo de blender
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(250)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #2a2a2a;
                border-radius: 4px;
            }
        """)
        
    def add_section(self, title):
        """Add a collapsible section to the tool panel"""
        section = QtWidgets.QGroupBox(title)
        section.setStyleSheet("""
            QGroupBox {
                border: 1px solid #444444;
                border-radius: 4px;
                margin-top: 1ex;
                font-weight: bold;
                color: #cccccc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        
        section_layout = QtWidgets.QVBoxLayout(section)
        section_layout.setContentsMargins(8, 16, 8, 8)
        section_layout.setSpacing(4)
        
        self.layout.addWidget(section)
        return section_layout

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Renderizador 3D con Renderizado Basado en la Física")
        self.setGeometry(100, 100, 1200, 800)
        
        # Variables de estado
        self.current_actor = None
        self.texture = None
        self.current_mapper = None
        self.texture_coords = None
        self.current_view_index = 0
        self.current_texture_index = 0
        self.current_background_index = 0
        
        # Aplicacion del estilo y configuracion de la interfaz
        self.apply_stylesheet()
        
        self.init_ui()
        self.setup_vtk()

    def apply_stylesheet(self):
        # Le aplicamos un estilo de color similar a Blender
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #333333;
                color: #cccccc;
            }
            
            QPushButton {
                background-color: #444444;
                color: #cccccc;
                border: none;
                border-radius: 3px;
                padding: 5px;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #555555;
            }
            
            QPushButton:pressed {
                background-color: #5680c2;
            }
            
            QToolBar {
                background-color: #2a2a2a;
                border: none;
                spacing: 3px;
                padding: 3px;
            }
            
            QStatusBar {
                background-color: #232323;
                color: #aaaaaa;
            }
            
            QLabel {
                color: #cccccc;
            }
            
            QSplitter::handle {
                background-color: #444444;
            }
            
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #cccccc;
                padding: 5px;
                border: 1px solid #444444;
            }
            
            QMenu {
                background-color: #2a2a2a;
                color: #cccccc;
                border: 1px solid #444444;
            }
            
            QMenu::item:selected {
                background-color: #5680c2;
            }
        """)

    def init_ui(self):
        # Layout principal
        self.main_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)
        
        # Layout horizontal principal
        main_layout = QtWidgets.QHBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra de herramientas como sidebar
        self.tool_panel = ToolPanel(self)
        
        # Contenido principal 
        self.content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Barra de herramientas superior
        self.top_toolbar = QtWidgets.QToolBar("Controles de la Vista")
        self.top_toolbar.setIconSize(QtCore.QSize(20, 20))
        self.top_toolbar.setMovable(False)
        content_layout.addWidget(self.top_toolbar)
        
        # Herramienta de renderizado VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(self.content_widget)
        content_layout.addWidget(self.vtk_widget, 1)  # 1 = stretch factor
        
        # Barra de herramientas inferior
        self.bottom_toolbar = QtWidgets.QToolBar("Controles del Modelo")
        self.bottom_toolbar.setIconSize(QtCore.QSize(20, 20))
        self.bottom_toolbar.setMovable(False)
        content_layout.addWidget(self.bottom_toolbar)
        
        # Widgets al layout principal
        main_layout.addWidget(self.tool_panel)
        main_layout.addWidget(self.content_widget, 1)  # 1 = stretch factor
        
        # Inicializacion de las toolbars
        self.setup_top_toolbar()
        self.setup_bottom_toolbar()
        self.setup_tool_panel()
        
        # Barra de carga
        self.statusBar().showMessage("Listo")
        
        # Barra del menu
        self.setup_menu()

    def setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #232323;
                color: #cccccc;
            }
            QMenuBar::item:selected {
                background-color: #5680c2;
            }
        """)
        
        # Menu 1 para la topbar: archivos
        file_menu = menubar.addMenu("Archivos")
        
        load_stl_action = QtWidgets.QAction("Cargar STL", self)
        load_stl_action.triggered.connect(lambda: setattr(self, 'current_actor', 
                                         load_stl(self, self.renderer, self.vtk_widget, 
                                                 self.texture, self.current_mapper, 
                                                 self.current_actor, self.texture_coords)))
        file_menu.addAction(load_stl_action)
        
        load_texture_action = QtWidgets.QAction("Cargar Imagen", self)
        load_texture_action.triggered.connect(lambda: load_texture(self.renderer, 
                                             self.vtk_widget, self.current_actor))
        file_menu.addAction(load_texture_action)
        
        file_menu.addSeparator()
        
        exit_action = QtWidgets.QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu 2 para la topbar: vistas
        view_menu = menubar.addMenu("Vistas")
        
        toggle_view_action = QtWidgets.QAction("Alternar Vista", self)
        toggle_view_action.triggered.connect(lambda: cycle_views(self))
        view_menu.addAction(toggle_view_action)
        
        toggle_background_action = QtWidgets.QAction("Alternar Fondo", self)
        toggle_background_action.triggered.connect(lambda: cycle_background(self, self.current_actor))
        view_menu.addAction(toggle_background_action)
        
        # Menu 2 para la topbar: manejo del modelo
        model_menu = menubar.addMenu("Modelo")
        
        color_action = QtWidgets.QAction("Color de la Figura", self)
        color_action.triggered.connect(lambda: set_actor_color(self.renderer, 
                                      self.vtk_widget, self.current_actor, 
                                      self.texture_coords, self.current_mapper))
        model_menu.addAction(color_action)
        
        toggle_mesh_action = QtWidgets.QAction("Visualizar/Ocultar Mesh", self)
        toggle_mesh_action.triggered.connect(lambda: set_mesh_visible(self.renderer, 
                                            self.vtk_widget, self.current_actor, 
                                            self.texture_coords, self.current_mapper))
        model_menu.addAction(toggle_mesh_action)
        
        reset_texture_action = QtWidgets.QAction("Reiniciar Textura", self)
        reset_texture_action.triggered.connect(lambda: clear_texture(self.renderer, 
                                              self.vtk_widget, self.current_actor, 
                                              self.texture_coords, self.current_mapper))
        model_menu.addAction(reset_texture_action)

    def setup_top_toolbar(self):
        # Menu sobre el renderizador: control de la camara
        view_btn = IconButton("view", tooltip="Alternar Vista")
        view_btn.clicked.connect(lambda: cycle_views(self))
        self.top_toolbar.addWidget(view_btn)
        
        self.top_toolbar.addSeparator()
        
        rotate_x_btn = IconButton("rotate_x", tooltip="Rotar 45° X")
        rotate_x_btn.clicked.connect(lambda: rotate_view(self.renderer, self.vtk_widget, 
                                    self.current_actor, 45, 0, 0))
        self.top_toolbar.addWidget(rotate_x_btn)
        
        rotate_y_btn = IconButton("rotate_y", tooltip="Rotar 45° Y")
        rotate_y_btn.clicked.connect(lambda: rotate_view(self.renderer, self.vtk_widget, 
                                    self.current_actor, 0, 45, 0))
        self.top_toolbar.addWidget(rotate_y_btn)
        
        rotate_z_btn = IconButton("rotate_z", tooltip="Rotar 45° Z")
        rotate_z_btn.clicked.connect(lambda: rotate_view(self.renderer, self.vtk_widget, 
                                    self.current_actor, 0, 0, 45))
        self.top_toolbar.addWidget(rotate_z_btn)
        
        self.top_toolbar.addSeparator()
        
        delete_btn = IconButton("delete", tooltip="Eliminar Modelo")
        delete_btn.clicked.connect(lambda: setattr(self, 'current_actor', 
                                  remove_model(self.renderer, self.vtk_widget, 
                                              self.texture, self.current_mapper, 
                                              self.current_actor, self.texture_coords)))
        self.top_toolbar.addWidget(delete_btn)
        
        # Spacer para mover el elemento a la derecha
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.top_toolbar.addWidget(spacer)
        
        # Etiqueta del estado del modelo
        self.status_label = QtWidgets.QLabel("No hay Modelo Cargado")
        self.top_toolbar.addWidget(self.status_label)

    def setup_bottom_toolbar(self):
        # Menu debajo el renderizador: operaciones del modelo
        load_btn = IconButton("load", tooltip="Cargar STL")
        load_btn.clicked.connect(lambda: setattr(self, 'current_actor', 
                                load_stl(self, self.renderer, self.vtk_widget, 
                                        self.texture, self.current_mapper, 
                                        self.current_actor, self.texture_coords)))
        self.bottom_toolbar.addWidget(load_btn)
        
        load_img_btn = IconButton("image", tooltip="Cargar Imagen")
        load_img_btn.clicked.connect(lambda: load_texture(self.renderer, 
                                    self.vtk_widget, self.current_actor))
        self.bottom_toolbar.addWidget(load_img_btn)
        
        self.bottom_toolbar.addSeparator()
        
        texture_btn = IconButton("texture", tooltip="Alternar Textura")
        texture_btn.clicked.connect(lambda: cycle_texture(self, self.renderer, 
                                   self.vtk_widget, self.current_actor))
        self.bottom_toolbar.addWidget(texture_btn)
        
        bg_btn = IconButton("background", tooltip="Alternar Fondo")
        bg_btn.clicked.connect(lambda: cycle_background(self, self.current_actor))
        self.bottom_toolbar.addWidget(bg_btn)
        
        self.bottom_toolbar.addSeparator()
        
        color_btn = IconButton("color", tooltip="Cambiar el Color")
        color_btn.clicked.connect(lambda: set_actor_color(self.renderer, 
                                 self.vtk_widget, self.current_actor, 
                                 self.texture_coords, self.current_mapper))
        self.bottom_toolbar.addWidget(color_btn)
        
        reset_btn = IconButton("reset", tooltip="Reiniciar Textura")
        reset_btn.clicked.connect(lambda: clear_texture(self.renderer, 
                                 self.vtk_widget, self.current_actor, 
                                 self.texture_coords, self.current_mapper))
        self.bottom_toolbar.addWidget(reset_btn)
        
        mesh_btn = IconButton("mesh", tooltip="Visualizar/Ocultar Mesh")
        mesh_btn.clicked.connect(lambda: set_mesh_visible(self.renderer, 
                                self.vtk_widget, self.current_actor, 
                                self.texture_coords, self.current_mapper))
        self.bottom_toolbar.addWidget(mesh_btn)

    def setup_tool_panel(self):
        # Sidebar para controlar operaciones 
        # Seccion del modelo
        model_section = self.tool_panel.add_section("Modelo")
        
        load_model_btn = QtWidgets.QPushButton("Cargar STL")
        load_model_btn.clicked.connect(lambda: setattr(self, 'current_actor', 
                                      load_stl(self, self.renderer, self.vtk_widget, 
                                              self.texture, self.current_mapper, 
                                              self.current_actor, self.texture_coords)))
        model_section.addWidget(load_model_btn)
        
        load_texture_btn = QtWidgets.QPushButton("Cargar Imagen")
        load_texture_btn.clicked.connect(lambda: load_texture(self.renderer, 
                                        self.vtk_widget, self.current_actor))
        model_section.addWidget(load_texture_btn)
        
        delete_model_btn = QtWidgets.QPushButton("Eliminar Modelo")
        delete_model_btn.clicked.connect(lambda: setattr(self, 'current_actor', 
                                        remove_model(self.renderer, self.vtk_widget, 
                                                    self.texture, self.current_mapper, 
                                                    self.current_actor, self.texture_coords)))
        model_section.addWidget(delete_model_btn)
        
        # Seccion de cambio de apariencia
        appearance_section = self.tool_panel.add_section("Apariencia")
        
        color_btn = QtWidgets.QPushButton("Cambiar Color")
        color_btn.clicked.connect(lambda: set_actor_color(self.renderer, 
                                 self.vtk_widget, self.current_actor, 
                                 self.texture_coords, self.current_mapper))
        appearance_section.addWidget(color_btn)
        
        texture_btn = QtWidgets.QPushButton("Alternar Textura")
        texture_btn.clicked.connect(lambda: cycle_texture(self, self.renderer, 
                                   self.vtk_widget, self.current_actor))
        appearance_section.addWidget(texture_btn)
        
        reset_texture_btn = QtWidgets.QPushButton("Reiniciar Textura")
        reset_texture_btn.clicked.connect(lambda: clear_texture(self.renderer, 
                                         self.vtk_widget, self.current_actor, 
                                         self.texture_coords, self.current_mapper))
        appearance_section.addWidget(reset_texture_btn)
        
        mesh_btn = QtWidgets.QPushButton("Visualizar/Ocultar Mesh")
        mesh_btn.clicked.connect(lambda: set_mesh_visible(self.renderer, 
                                self.vtk_widget, self.current_actor, 
                                self.texture_coords, self.current_mapper))
        appearance_section.addWidget(mesh_btn)
        
        bg_btn = QtWidgets.QPushButton("Alternar Fondo")
        bg_btn.clicked.connect(lambda: cycle_background(self, self.current_actor))
        appearance_section.addWidget(bg_btn)
        
        # Seccion de cambio de visualizacion
        view_section = self.tool_panel.add_section("Visualizacion")
        
        view_btn = QtWidgets.QPushButton("Alternar Vista")
        view_btn.clicked.connect(lambda: cycle_views(self))
        view_section.addWidget(view_btn)
        
        # Controles de rotacion
        rotation_layout = QtWidgets.QHBoxLayout()
        
        rotate_x_btn = QtWidgets.QPushButton("X")
        rotate_x_btn.setFixedWidth(30)
        rotate_x_btn.clicked.connect(lambda: rotate_view(self.renderer, self.vtk_widget, 
                                    self.current_actor, 45, 0, 0))
        
        rotate_y_btn = QtWidgets.QPushButton("Y")
        rotate_y_btn.setFixedWidth(30)
        rotate_y_btn.clicked.connect(lambda: rotate_view(self.renderer, self.vtk_widget, 
                                    self.current_actor, 0, 45, 0))
        
        rotate_z_btn = QtWidgets.QPushButton("Z")
        rotate_z_btn.setFixedWidth(30)
        rotate_z_btn.clicked.connect(lambda: rotate_view(self.renderer, self.vtk_widget, 
                                    self.current_actor, 0, 0, 45))
        
        rotation_layout.addWidget(QtWidgets.QLabel("Rotar 45°:"))
        rotation_layout.addWidget(rotate_x_btn)
        rotation_layout.addWidget(rotate_y_btn)
        rotation_layout.addWidget(rotate_z_btn)
        
        view_section.addLayout(rotation_layout)
        
        # Spacer para ajustar el estilo a la izquierda
        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, 
                                      QtWidgets.QSizePolicy.Expanding)
        self.tool_panel.layout.addItem(spacer)

    def setup_vtk(self):
        # Create VTK renderer
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
        
        self.interactor.Start()

        # Inicialización diferida
        QtCore.QTimer.singleShot(100, self.finalize_vtk_setup)
        
        # Actualizamos el estatus
        self.statusBar().showMessage("VTK iniciado")

        # Configurar iluminación ambiental
        #setup_environment_lighting(self)

    def finalize_vtk_setup(self):
        self.vtk_widget.GetRenderWindow().Render()
        self.interactor.Initialize()

    def update_status(self, message):
        self.status_label.setText(message)
        self.statusBar().showMessage(message)

    def closeEvent(self, event):
        self.vtk_widget.GetRenderWindow().Finalize()
        self.vtk_widget.close()
        super().closeEvent(event)

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
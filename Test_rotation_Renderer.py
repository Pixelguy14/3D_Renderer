import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QColorDialog
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import random

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Renderizador 3D Avanzado - Versión Final")
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
        
        # Botones de control de cámara
        camera_controls = [
            ("Vista Superior", self.top_view),
            ("Vista Inferior", self.bottom_view),
            ("Vista Frontal", self.front_view),
            ("Vista Lateral", self.side_view),
            ("0°", lambda: self.rotate_view(0)),
            ("90°", lambda: self.rotate_view(90)),
            ("180°", lambda: self.rotate_view(180)),
            ("270°", lambda: self.rotate_view(270)),
            ("Eliminar Modelo", self.remove_model)
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
        
        # Barra de herramientas inferior para operaciones
        toolbar_bottom = QtWidgets.QHBoxLayout()
        operations = [
            ("Cargar STL", self.load_stl),
            ("Cargar Imagen", self.load_image),
            ("Cargar Textura", self.load_texture),
            ("Color Fondo", self.set_background_color),
            ("Color Figura", self.set_actor_color)
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
        
        # Inicialización diferida
        QtCore.QTimer.singleShot(100, self.finalize_vtk_setup)

    def finalize_vtk_setup(self):
        self.vtk_widget.GetRenderWindow().Render()
        self.interactor.Initialize()

    # ==============================================
    # CONTROLES DE CÁMARA
    # ==============================================
    
    def top_view(self):
        cam = self.renderer.GetActiveCamera()
        cam.SetPosition(0, 0, 1)
        cam.SetViewUp(0, 1, 0)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()

    def bottom_view(self):
        cam = self.renderer.GetActiveCamera()
        cam.SetPosition(0, 0, -1)
        cam.SetViewUp(0, 1, 0)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()

    def front_view(self):
        cam = self.renderer.GetActiveCamera()
        cam.SetPosition(0, -1, 0)
        cam.SetViewUp(0, 0, 1)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()

    def side_view(self):
        cam = self.renderer.GetActiveCamera()
        cam.SetPosition(1, 0, 0)
        cam.SetViewUp(0, 0, 1)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()

    def rotate_view(self, angle):
        if not self.current_actor:
            return
            
        cam = self.renderer.GetActiveCamera()
        cam.Azimuth(angle)
        self.vtk_widget.GetRenderWindow().Render()

    def remove_model(self):
        if self.current_actor:
            self.renderer.RemoveActor(self.current_actor)
            self.current_actor = None
            self.texture = None
            self.current_mapper = None
            self.texture_coords = None
            self.vtk_widget.GetRenderWindow().Render()

    # ==============================================
    # FUNCIONES PRINCIPALES
    # ==============================================
    
    def load_stl(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo STL", "", "STL Files (*.stl)"
        )
        if not filename:
            return

        self.remove_model()
        
        # Leer archivo STL
        reader = vtk.vtkSTLReader()
        reader.SetFileName(filename)

        # Generar coordenadas de textura
        self.texture_coords = vtk.vtkTextureMapToPlane()
        self.texture_coords.SetInputConnection(reader.GetOutputPort())

        # Crear mapper
        self.current_mapper = vtk.vtkPolyDataMapper()
        self.current_mapper.SetInputConnection(self.texture_coords.GetOutputPort())

        # Crear actor
        self.current_actor = vtk.vtkActor()
        self.current_actor.SetMapper(self.current_mapper)
        self.current_actor.GetProperty().SetColor(0.8, 0.8, 0.8)
        
        self.renderer.AddActor(self.current_actor)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()

    def load_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if not filename:
            return

        self.remove_model()
        
        # Cargar imagen según su extensión
        if filename.lower().endswith('.png'):
            reader = vtk.vtkPNGReader()
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            reader = vtk.vtkJPEGReader()
        elif filename.lower().endswith('.bmp'):
            reader = vtk.vtkBMPReader()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Formato de imagen no soportado")
            return

        reader.SetFileName(filename)
        reader.Update()

        # Extraer solo componentes RGB si tiene canal alfa
        if reader.GetOutput().GetNumberOfScalarComponents() == 4:
            extract = vtk.vtkImageExtractComponents()
            extract.SetInputConnection(reader.GetOutputPort())
            extract.SetComponents(0, 1, 2)  # Tomar solo R, G, B
            extract.Update()
            image_data = extract.GetOutput()
        else:
            image_data = reader.GetOutput()

        # Convertir a luminancia para el relieve
        luminance = vtk.vtkImageLuminance()
        luminance.SetInputData(image_data)
        luminance.Update()

        # Convertir a geometría
        geometry = vtk.vtkImageDataGeometryFilter()
        #geometry.SetInputConnection(reader.GetOutputPort())
        geometry.SetInputConnection(luminance.GetOutputPort())
        geometry.Update()

        # Generar coordenadas de textura
        self.texture_coords = vtk.vtkTextureMapToPlane()
        self.texture_coords.SetInputConnection(geometry.GetOutputPort())

        # Aplicar relieve
        self.warp_filter = vtk.vtkWarpScalar()
        self.warp_filter.SetInputConnection(geometry.GetOutputPort())
        self.warp_filter.SetScaleFactor(0.1)
        self.warp_filter.Update()

        # Mapper
        self.current_mapper = vtk.vtkPolyDataMapper()
        #self.current_mapper.SetInputConnection(self.texture_coords.GetOutputPort())
        self.current_mapper.SetInputConnection(self.warp_filter.GetOutputPort())

        # Crear actor con textura original
        self.current_actor = vtk.vtkActor()
        self.current_actor.SetMapper(self.current_mapper)
        
        # Aplicar textura de la imagen original
        self.texture = vtk.vtkTexture()
        self.texture.SetInputConnection(reader.GetOutputPort())
        self.texture.InterpolateOn()
        self.current_actor.SetTexture(self.texture)
        
        self.renderer.AddActor(self.current_actor)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()

    def load_texture(self):
        if not self.current_actor:
            QtWidgets.QMessageBox.warning(self, "Error", "Primero cargue un modelo STL o imagen")
            return

        filename, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar textura", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if not filename:
            return

        # Cargar textura según su extensión
        if filename.lower().endswith('.png'):
            reader = vtk.vtkPNGReader()
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            reader = vtk.vtkJPEGReader()
        elif filename.lower().endswith('.bmp'):
            reader = vtk.vtkBMPReader()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Formato de textura no soportado")
            return

        reader.SetFileName(filename)

        # Crear textura
        self.texture = vtk.vtkTexture()
        self.texture.SetInputConnection(reader.GetOutputPort())
        self.texture.InterpolateOn()

        # Aplicar textura al actor actual
        self.current_actor.SetTexture(self.texture)
        
        # Configurar propiedades para mejor visualización
        self.current_actor.GetProperty().SetColor(1, 1, 1)  # Color base blanco
        self.current_actor.GetProperty().LightingOn()
        
        self.vtk_widget.GetRenderWindow().Render()

    def set_background_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.renderer.SetBackground(color.redF(), color.greenF(), color.blueF())
            self.vtk_widget.GetRenderWindow().Render()

    def set_actor_color(self):
        if not self.current_actor:
            QtWidgets.QMessageBox.warning(self, "Error", "No hay figura para colorear")
            return

        color = QColorDialog.getColor()
        if color.isValid():
            # Remover textura si existe
            self.current_actor.SetTexture(None)
            self.texture = None
            
            # Aplicar color
            if self.warp_filter:
                # Para imágenes con relieve, necesitamos procesar diferente
                # Obtener los datos deformados
                deformed_data = self.warp_filter.GetOutput()
                
                # Crear un nuevo mapper con los datos deformados
                self.current_mapper = vtk.vtkPolyDataMapper()
                self.current_mapper.SetInputData(deformed_data)
                
                # Configurar el actor
                self.current_actor.SetMapper(self.current_mapper)
                self.current_actor.GetProperty().SetColor(color.redF(), color.greenF(), color.blueF())
                self.current_actor.GetProperty().LightingOn()
                
                # Opcional: ajustar propiedades visuales
                self.current_actor.GetProperty().SetAmbient(0.3)
                self.current_actor.GetProperty().SetDiffuse(0.7)
                self.current_actor.GetProperty().SetSpecular(0.4)
                self.current_actor.GetProperty().SetSpecularPower(20)
            else:
                # Para STLs, simplemente aplicar el color
                self.current_actor.GetProperty().SetColor(color.redF(), color.greenF(), color.blueF())
            
            self.vtk_widget.GetRenderWindow().Render()

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
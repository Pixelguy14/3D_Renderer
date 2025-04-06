# python3 -m venv Documents/DICIS_8vo_2025/Graficos_por_computadora/Proyecto/
# source /home/pixel/Documents/DICIS_8vo_2025/Graficos_por_computadora/Proyecto/bin/activate
# python3 Test_Latest_Renderer.py
# QT_QPA_PLATFORM=xcb python3 Test_Latest_Renderer.py 
# deactivate
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QColorDialog
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Renderizador 3D Avanzado - Versión Final")
        self.setGeometry(100, 100, 800, 600)
        
        # Variables de estado
        self.current_actor = None
        self.texture = None
        self.current_mapper = None
        self.warp_filter = None
        
        # Configuración de la interfaz
        self.init_ui()
        self.setup_vtk()

    def init_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Widget VTK
        self.vtk_widget = QVTKRenderWindowInteractor(central_widget)
        layout.addWidget(self.vtk_widget)
        
        # Botones
        button_layout = QtWidgets.QHBoxLayout()
        buttons = [
            ("Cargar STL", self.load_stl),
            ("Cargar Imagen", self.load_image),
            ("Cargar Textura", self.load_texture),
            ("Color Fondo", self.set_background_color),
            ("Color Figura", self.set_actor_color)
        ]
        
        for text, callback in buttons:
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(callback)
            btn.setFixedWidth(120)
            button_layout.addWidget(btn)
        
        layout.addLayout(button_layout)

    def setup_vtk(self):
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.2, 0.2, 0.2)
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        
        # Configurar estilo de interacción
        interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        style = vtk.vtkInteractorStyleTrackballCamera()
        interactor.SetInteractorStyle(style)
        
        # Inicialización diferida
        QtCore.QTimer.singleShot(100, self.finalize_vtk_setup)

    def finalize_vtk_setup(self):
        self.vtk_widget.GetRenderWindow().Render()
        self.vtk_widget.GetRenderWindow().GetInteractor().Initialize()

    def clear_scene(self):
        if self.current_actor:
            self.renderer.RemoveActor(self.current_actor)
        self.current_actor = None
        self.texture = None
        self.current_mapper = None
        self.warp_filter = None

    def load_stl(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo STL", "", "STL Files (*.stl)"
        )
        if not filename:
            return

        self.clear_scene()
        
        reader = vtk.vtkSTLReader()
        reader.SetFileName(filename)

        self.current_mapper = vtk.vtkPolyDataMapper()
        self.current_mapper.SetInputConnection(reader.GetOutputPort())

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

        self.clear_scene()
        
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

        # Crear geometría
        geometry = vtk.vtkImageDataGeometryFilter()
        geometry.SetInputConnection(luminance.GetOutputPort())
        geometry.Update()

        # Aplicar relieve
        self.warp_filter = vtk.vtkWarpScalar()
        self.warp_filter.SetInputConnection(geometry.GetOutputPort())
        self.warp_filter.SetScaleFactor(0.1)
        self.warp_filter.Update()

        # Mapper
        self.current_mapper = vtk.vtkPolyDataMapper()
        self.current_mapper.SetInputConnection(self.warp_filter.GetOutputPort())

        # Crear actor con textura original
        self.current_actor = vtk.vtkActor()
        self.current_actor.SetMapper(self.current_mapper)
        
        # Aplicar textura de la imagen original (conservando canal alfa si existe)
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
                # 1. Obtener los datos deformados
                deformed_data = self.warp_filter.GetOutput()
                
                # 2. Crear un nuevo mapper con los datos deformados
                self.current_mapper = vtk.vtkPolyDataMapper()
                self.current_mapper.SetInputData(deformed_data)
                
                # 3. Configurar el actor
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
# python3 -m venv Documents/DICIS_8vo_2025/Graficos_por_computadora/Proyecto/
# source /home/pixel/Documents/DICIS_8vo_2025/Graficos_por_computadora/Proyecto/bin/activate
# cd Documents/DICIS_8vo_2025/Graficos_por_computadora/Proyecto
# python3 ORM_Renderer_stl.py
# QT_QPA_PLATFORM=xcb python3 ORM_Renderer_stl.py
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
        
        # Configuración inicial de la ventana
        self.setup_ui()
        self.setup_vtk()
        
    def setup_ui(self):
        self.setWindowTitle("Renderizador 3D PBR con VTK")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Widget VTK
        self.vtk_widget = QVTKRenderWindowInteractor(central_widget)
        layout.addWidget(self.vtk_widget)
        
        # Layout horizontal para botones
        button_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Botones nuevos
        self.button_color = QtWidgets.QPushButton("Color (Albedo)")
        self.button_orm = QtWidgets.QPushButton("ORM (PBR)")
        self.button_normal = QtWidgets.QPushButton("Normal Map")
        self.button_red = QtWidgets.QPushButton("Rojo")
        self.button_green = QtWidgets.QPushButton("Verde")
        self.button_random = QtWidgets.QPushButton("Random")
        
        # Configurar tamaños
        for btn in [self.button_color, self.button_orm, self.button_normal,
                   self.button_red, self.button_green, self.button_random]:
            btn.setFixedWidth(120)
        
        # Conectar botones
        self.button_color.clicked.connect(self.load_color_texture)
        self.button_orm.clicked.connect(self.load_orm_texture)
        self.button_normal.clicked.connect(self.load_normal_texture)
        self.button_red.clicked.connect(lambda: self.change_actor_color(1, 0, 0))
        self.button_green.clicked.connect(lambda: self.change_actor_color(0, 1, 0))
        self.button_random.clicked.connect(self.random_color)
        
        # Agregar al layout
        button_layout.addWidget(self.button_color)
        button_layout.addWidget(self.button_orm)
        button_layout.addWidget(self.button_normal)
        button_layout.addWidget(self.button_red)
        button_layout.addWidget(self.button_green)
        button_layout.addWidget(self.button_random)

    def setup_vtk(self):
        # Configuración inicial del renderer y actor
        reader = vtk.vtkSTLReader()
        reader.SetFileName("Resources/Head Sculpture.stl")
        reader.SetFileName("Resources/Metal nut.stl")
        
        texture_filter = vtk.vtkTextureMapToPlane()
        texture_filter.SetInputConnection(reader.GetOutputPort())
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(texture_filter.GetOutputPort())
        
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        
        # Habilitar PBR y configurar propiedades iniciales
        self.actor.GetProperty().SetInterpolationToPBR()
        
        self.actor.GetProperty().SetMetallic(1)
        self.actor.GetProperty().SetRoughness(0)
        self.actor.GetProperty().SetSpecular(0.9)
        self.actor.GetProperty().SetSpecularColor(1,1,1)
        #self.actor.GetProperty().SetOpacity(1)
        self.actor.GetProperty().SetEmissiveFactor(1,0,0) # emitir brillo propio
        #self.actor.GetProperty().SetCoatIOR(0.5)
        #self.actor.GetProperty().SetDiffuse(1)
        
        self.actor.GetProperty().SetColor(0.3, 0.3, 0.3)
        
        # Configurar renderer
        self.renderer = vtk.vtkOpenGLRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.renderer.AddActor(self.actor)
        
        # Configurar iluminación ambiental
        self.setup_environment_lighting()
        
        self.vtk_widget.GetRenderWindow().Render()
        self.vtk_widget.Initialize()

    def setup_environment_lighting(self):
        # Cargar y configurar HDR
        self.renderer.UseImageBasedLightingOn()
        self.renderer.UseSphericalHarmonicsOff()
        
        reader = vtk.vtkHDRReader()
        #reader.SetFileName("Resources/pretoria_gardens_2k.hdr")
        #reader.SetFileName("Resources/tiber_1_1k.hdr")
        reader.SetFileName("Resources/abandoned_games_room_02_4k.hdr")
        reader.Update()

        # Crear textura ambiental
        env_texture = vtk.vtkTexture()
        env_texture.SetColorModeToDirectScalars()
        env_texture.SetInputConnection(reader.GetOutputPort())
        env_texture.MipmapOn()
        env_texture.InterpolateOn()
        
        # Configurar iluminación basada en imagen
        self.renderer.UseImageBasedLightingOn()
        self.renderer.SetEnvironmentTexture(env_texture)
        
        # Crear skybox con el HDR
        skybox = vtk.vtkSkybox()
        skybox.SetTexture(env_texture)
        skybox.SetProjectionToSphere()  # Para HDR equirectangular
        skybox.GammaCorrectOn()  # Corrección gamma para HDR
        
        # Añadir skybox al renderer y quitar color de fondo
        self.renderer.AddActor(skybox)
        self.renderer.SetBackground(0, 0, 0)  # Fondo negro (será cubierto por el skybox)

    def create_texture(self, file_path, sRGB=False):
        # Cargador universal de texturas con soporte sRGB
        if file_path.lower().endswith('.hdr'):
            reader = vtk.vtkHDRReader()
        else:
            reader_factory = vtk.vtkImageReader2Factory()
            reader = reader_factory.CreateImageReader2(file_path)
        
        reader.SetFileName(file_path)
        reader.Update()
        
        texture = vtk.vtkTexture()
        texture.SetInputConnection(reader.GetOutputPort())
        texture.MipmapOn()
        texture.InterpolateOn()
        
        if sRGB:
            texture.UseSRGBColorSpaceOn()
        
        return texture

    def load_color_texture(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleccionar textura Albedo", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if filename:
            texture = self.create_texture(filename, sRGB=True)
            self.actor.GetProperty().SetBaseColorTexture(texture)
            self.vtk_widget.GetRenderWindow().Render()

    def load_orm_texture(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleccionar textura ORM", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if filename:
            texture = self.create_texture(filename)
            self.actor.GetProperty().SetORMTexture(texture)
            self.vtk_widget.GetRenderWindow().Render()

    def load_normal_texture(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleccionar Normal Map", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if filename:
            texture = self.create_texture(filename)
            self.actor.GetProperty().SetNormalTexture(texture)
            self.actor.GetProperty().SetNormalScale(1.0)  # Ajustar según necesidad
            self.vtk_widget.GetRenderWindow().Render()

    def change_actor_color(self, r, g, b):
        self.actor.GetProperty().SetColor(r, g, b)
        self.vtk_widget.GetRenderWindow().Render()

    def random_color(self):
        r = random.random()
        g = random.random()
        b = random.random()
        self.change_actor_color(r, g, b)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
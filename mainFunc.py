from camControls import remove_model
import vtk
from PyQt5.QtWidgets import QFileDialog, QColorDialog
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QColor
import os

# Funciones principales
def load_stl(self, renderer, vtk_widget, texture, current_mapper, current_actor, texture_coords):
    filename, _ = QFileDialog.getOpenFileName(
        None, "Seleccionar archivo STL", "", "STL Files (*.stl)"
    )
    if not filename:
        return

    remove_model(renderer, vtk_widget, texture, current_mapper, current_actor, texture_coords)
    
    # Leer archivo STL
    reader = vtk.vtkSTLReader()
    reader.SetFileName(filename)

    # Generar coordenadas de textura
    texture_coords = vtk.vtkTextureMapToPlane()
    texture_coords.SetInputConnection(reader.GetOutputPort())

    # Crear mapper
    current_mapper = vtk.vtkPolyDataMapper()
    current_mapper.SetInputConnection(texture_coords.GetOutputPort())

    # Crear actor
    current_actor = vtk.vtkActor()
    current_actor.SetMapper(current_mapper)
    current_actor.GetProperty().SetInterpolationToPBR()
    current_actor.GetProperty().SetColor(0.8, 0.8, 0.8)

    # Reiniciar camara
    cam = renderer.GetActiveCamera()
    cam.SetPosition(0, 0, 100)
    cam.SetFocalPoint(0, 0, 0)
    
    renderer.AddActor(current_actor)
    renderer.ResetCamera()
    vtk_widget.GetRenderWindow().Render()
    return current_actor  # Devuelve el actor actualizado

def load_texture(self, vtk_widget, current_actor):
    if not current_actor:
        QtWidgets.QMessageBox.warning(None, "Error", "Primero cargue un modelo STL o imagen")
        return

    filename, _ = QFileDialog.getOpenFileName(
        None, "Seleccionar textura", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
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
        QtWidgets.QMessageBox.warning(None, "Error", "Formato de textura no soportado")
        return

    reader.SetFileName(filename)

    texture = create_texture(self, filename, sRGB=True)
    current_actor.GetProperty().SetBaseColorTexture(texture)
    
    vtk_widget.GetRenderWindow().Render()

def set_actor_color(renderer, vtk_widget, current_actor, warp_filter, current_mapper):
    if not current_actor:
        QtWidgets.QMessageBox.warning(None, "Error", "No hay figura para colorear")
        return

    color = QColorDialog.getColor(options=QColorDialog.ShowAlphaChannel)
    if color.isValid():
        
        # Obtener componentes RGBA desde QColor
        rgba = color.rgba()  # Devuelve el color como un valor entero ARGB
        red = (rgba >> 16) & 0xFF
        green = (rgba >> 8) & 0xFF
        blue = rgba & 0xFF
        alpha = (rgba >> 24) & 0xFF

        # Convertir Alpha a rango 0-1
        alpha_normalized = alpha / 255.0

        # Configurar propiedades visuales del actor
        current_actor.GetProperty().SetColor(red / 255.0, green / 255.0, blue / 255.0)
        current_actor.GetProperty().SetOpacity(alpha_normalized)

        # Para imágenes con relieve, necesitamos procesar diferente
        if warp_filter:
            deformed_data = warp_filter.GetOutput()
            current_mapper = vtk.vtkPolyDataMapper()
            current_mapper.SetInputData(deformed_data)
            current_actor.SetMapper(current_mapper)
            current_actor.GetProperty().SetColor(color.redF(), color.greenF(), color.blueF()) 
            current_actor.GetProperty().LightingOn()

        vtk_widget.GetRenderWindow().Render()

def clear_texture(renderer, vtk_widget, current_actor, warp_filter, current_mapper):
    if not current_actor:
        QtWidgets.QMessageBox.warning(None, "Error", "No hay figura STL o imagen")
        return
    
    prop = current_actor.GetProperty()
    
    # 1. Limpiar texturas PBR
    prop.SetBaseColorTexture(None)
    prop.SetORMTexture(None)
    prop.SetNormalTexture(None)
    
    # 2. Resetear propiedades
    prop.SetColor(0.8, 0.8, 0.8)
    prop.SetMetallic(0.0)
    prop.SetRoughness(0.5)
    prop.SetOpacity(1.0)
    
    # 3. Liberar recursos GPU
    prop.ReleaseGraphicsResources(vtk_widget.GetRenderWindow())
    
    # 4. Reactivar PBR (tu corrección clave)
    prop.SetInterpolationToPBR()
    
    # 5. Actualizar conexiones y render
    if warp_filter:
        warp_filter.RemoveAllInputConnections(0)
        warp_filter.Update()
    
    if current_mapper:
        current_mapper.SetInputConnection(reader.GetOutputPort())  
        current_mapper.Update()
    
    current_actor.Modified()
    renderer.ResetCamera()
    vtk_widget.GetRenderWindow().Render()

def set_mesh_visible(renderer, vtk_widget, current_actor, warp_filter, current_mapper):
    if not current_actor:
        QtWidgets.QMessageBox.warning(None, "Error", "No hay figura STL o imagen")
        return

    
    # Verificar el estado actual de las aristas
    is_mesh_visible = current_actor.GetProperty().GetEdgeVisibility()

    if is_mesh_visible:
        # Desactivar visibilidad del mesh y vértices
        current_actor.GetProperty().EdgeVisibilityOff()
        current_actor.GetProperty().VertexVisibilityOff()
        current_actor.GetProperty().SetOpacity(1.0)  # Opacidad completa
        current_actor.GetProperty().SetColor(0.8, 0.8, 0.8)  # Color base
    else:
        # Activar visibilidad del mesh y vértices
        current_actor.GetProperty().EdgeVisibilityOn()
        current_actor.GetProperty().SetEdgeColor(0.0, 0.0, 0.0)  # Color negro para aristas
        current_actor.GetProperty().VertexVisibilityOn()
        current_actor.GetProperty().SetVertexColor(1.0, 0.0, 0.0)  # Color rojo para vértices
        current_actor.GetProperty().SetPointSize(5)  # Tamaño de vértices
        current_actor.GetProperty().SetOpacity(0.3)  # Semitransparente

    # Renderizar la actualización
    vtk_widget.GetRenderWindow().Render()

def setup_environment_lighting(self, current_actor, filename=""):
    # Limpiar configuración anterior
    self.renderer.RemoveAllViewProps()  # Eliminar skybox si existe
    self.renderer.AddActor(current_actor)  # Volver a añadir el actor principal
    
    # Configuración base
    self.renderer.UseImageBasedLightingOff()
    self.renderer.SetEnvironmentTexture(None)
    
    if filename and os.path.exists(filename):
        try:
            # Cargar HDR
            reader = vtk.vtkHDRReader()
            reader.SetFileName(filename)
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
            
            # Crear skybox
            skybox = vtk.vtkSkybox()
            skybox.SetTexture(env_texture)
            skybox.SetProjectionToSphere()
            skybox.GammaCorrectOn()
            
            # Añadir al renderer
            self.renderer.AddActor(skybox)
            self.renderer.SetBackground(0, 0, 0)  # Fondo negro para skybox
            
        except Exception as e:
            print(f"Error cargando HDR: {str(e)}")
            self.renderer.SetBackground(0.2, 0.2, 0.2)
    else:
        # Configuración por defecto sin HDR
        self.renderer.SetBackground(0.2, 0.2, 0.2)
        self.renderer.UseImageBasedLightingOff()
    
    self.vtk_widget.GetRenderWindow().Render()

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

def load_color_texture(self, texture, current_actor, vtk_widget, filename):
    texture = create_texture(self, filename, sRGB=True)
    current_actor.GetProperty().SetBaseColorTexture(texture)
    vtk_widget.GetRenderWindow().Render()

def load_orm_texture(self, texture, current_actor, vtk_widget, filename):
    texture = create_texture(self,filename)
    current_actor.GetProperty().SetORMTexture(texture)
    vtk_widget.GetRenderWindow().Render()

def load_normal_texture(self, texture, current_actor, vtk_widget, filename):
    texture = create_texture(self, filename)
    current_actor.GetProperty().SetNormalTexture(texture)
    current_actor.GetProperty().SetNormalScale(1.0)  # Ajustar según necesidad
    vtk_widget.GetRenderWindow().Render()

def cycle_texture(self, vtk_widget, texture, current_actor):
    self.texture_cycle_functions = [
            # to load a texture, an orm and a normal functions
            # se usa lambda para cargar multiples funciones, como la carga de texturas avanzadas
            # tambien incluimos propiedades más especificas para darle más profundidad como SetMetallic, SetRoughness, SetSpecular,SetSpecularColor, SetEmissiveFactor 
            lambda: (load_color_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/denim_fabric_diff_1k.jpg"),
                     load_orm_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/denim_fabric_orm.png"),
                     load_normal_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/denim_fabric_nor_gl_1k.png"),
                     current_actor.GetProperty().SetMetallic(0),
                     current_actor.GetProperty().SetRoughness(1),
                     current_actor.GetProperty().SetSpecular(0),
                     current_actor.GetProperty().SetSpecularColor(0,0,0),
                     current_actor.GetProperty().SetEmissiveFactor(0,0,0)
                     ), #denim
            lambda: (load_color_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Grass007_1K-JPG_Color.jpg"),
                     load_orm_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Grass007_orm.png"),
                     load_normal_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Grass007_1K-JPG_NormalGL.jpg"),
                     current_actor.GetProperty().SetMetallic(0),
                     current_actor.GetProperty().SetRoughness(1),
                     current_actor.GetProperty().SetSpecular(0),
                     current_actor.GetProperty().SetSpecularColor(0,0,0),
                     current_actor.GetProperty().SetEmissiveFactor(0,0,0)
                     ), # pasto
            lambda: (load_color_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Metal012_1K-JPG_Color.jpg"),
                     load_orm_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Metal012_orm.png"),
                     load_normal_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Metal012_1K-JPG_NormalGL.jpg"),
                     current_actor.GetProperty().SetMetallic(1),
                     current_actor.GetProperty().SetRoughness(0.2),
                     current_actor.GetProperty().SetSpecular(0),
                     current_actor.GetProperty().SetSpecularColor(0,0,0),
                     current_actor.GetProperty().SetEmissiveFactor(0.3,0.3,0.3)
                     ),# platino espejo
            lambda: (load_color_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Metal048A_1K-JPG_Color.jpg"),
                     load_orm_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Metal048A_orm.png"),
                     load_normal_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Metal048A_1K-JPG_NormalDX.jpg"),
                     current_actor.GetProperty().SetMetallic(0.4),
                     current_actor.GetProperty().SetRoughness(0),
                     current_actor.GetProperty().SetSpecular(0),
                     current_actor.GetProperty().SetSpecularColor(0,0,0),
                     current_actor.GetProperty().SetEmissiveFactor(0,0,0)
                     ), # oro
            lambda: (load_color_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Metal053B_1K-JPG_Color.jpg"),
                     load_orm_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Metal053B_orm.png"),
                     load_normal_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Metal053B_1K-JPG_NormalGL.jpg"),
                     current_actor.GetProperty().SetMetallic(0.7),
                     current_actor.GetProperty().SetRoughness(0.2),
                     current_actor.GetProperty().SetSpecular(0),
                     current_actor.GetProperty().SetSpecularColor(0,0,0),
                     current_actor.GetProperty().SetEmissiveFactor(0,0,0)
                     ), # metal corroido
            lambda: (load_color_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Moss002_1K-JPG_Color.jpg"),
                     load_orm_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Moss002_orm.png"),
                     load_normal_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Moss002_1K-JPG_NormalGL.jpg"),
                     current_actor.GetProperty().SetMetallic(0),
                     current_actor.GetProperty().SetRoughness(1),
                     current_actor.GetProperty().SetSpecular(0.3),
                     current_actor.GetProperty().SetSpecularColor(0,1,0),
                     current_actor.GetProperty().SetEmissiveFactor(0,0,0)
                     ), # moho
            lambda: (load_color_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Onyx011_1K-JPG_Color.jpg"),
                     load_orm_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Onyx011_orm.png"),
                     load_normal_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Onyx011_1K-JPG_NormalGL.jpg"),
                     current_actor.GetProperty().SetMetallic(0.3),
                     current_actor.GetProperty().SetRoughness(0.5),
                     current_actor.GetProperty().SetSpecular(0),
                     current_actor.GetProperty().SetSpecularColor(0,0,0),
                     current_actor.GetProperty().SetEmissiveFactor(1,1,1)
                     ), # onyx
            lambda: (load_color_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Rock058_1K-JPG_Color.jpg"),
                     load_orm_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Rock058_orm.png"),
                     load_normal_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Rock058_1K-JPG_NormalGL.jpg"),
                     current_actor.GetProperty().SetMetallic(0),
                     current_actor.GetProperty().SetRoughness(1),
                     current_actor.GetProperty().SetSpecular(0),
                     current_actor.GetProperty().SetSpecularColor(0,0,0),
                     current_actor.GetProperty().SetEmissiveFactor(0.1,0,0)
                     ), # piedra
            lambda: (load_color_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Tiles132A_1K-JPG_Color.jpg"),
                     load_orm_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Tiles132A_orm.png"),
                     load_normal_texture(self, texture, current_actor, vtk_widget, "Resources/PBR/Tiles132A_1K-JPG_NormalGL.jpg"),
                     current_actor.GetProperty().SetMetallic(0),
                     current_actor.GetProperty().SetRoughness(0.7),
                     current_actor.GetProperty().SetSpecular(0),
                     current_actor.GetProperty().SetSpecularColor(0,0,0),
                     current_actor.GetProperty().SetEmissiveFactor(0.4,0.4,0.7)
                     ), # tejas
        ]
    current_function = self.texture_cycle_functions[self.current_texture_index]
    current_function()

    # Actualizar texturas
    current_actor.Modified()
    self.renderer.ResetCameraClippingRange()
    vtk_widget.GetRenderWindow().Render()
    self.current_texture_index = (self.current_texture_index + 1) % len(self.texture_cycle_functions)

def cycle_background(self, current_actor):
    self.background_cycle_functions = [
            lambda: setup_environment_lighting(self, current_actor, "Resources/PBR/urban_street_01_4k.hdr"),
            lambda: setup_environment_lighting(self, current_actor, "Resources/PBR/abandoned_games_room_02_4k.hdr"),
            lambda: setup_environment_lighting(self, current_actor, "Resources/PBR/kloofendal_48d_partly_cloudy_puresky_4k.hdr"),
            lambda: setup_environment_lighting(self, current_actor, "Resources/PBR/moonless_golf_4k.hdr"),
            lambda: setup_environment_lighting(self, current_actor, "Resources/PBR/rogland_clear_night_4k.hdr"),
            lambda: setup_environment_lighting(self, current_actor, "Resources/PBR/NightSkyHDRI003_4K-HDR.hdr"),
            lambda: setup_environment_lighting(self, current_actor, "Resources/PBR/solitude_night_4k.hdr"),
            lambda: setup_environment_lighting(self, current_actor, "Resources/PBR/NightSkyHDRI007_4K-HDR.hdr"),
            lambda: setup_environment_lighting(self, current_actor, "") # campo vacio para reiniciar al estado base del fondo
        ]
    current_function = self.background_cycle_functions[self.current_background_index]
    current_function()
    self.current_background_index = (self.current_background_index + 1) % len(self.background_cycle_functions)

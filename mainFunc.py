from camControls import remove_model
import vtk
from PyQt5.QtWidgets import QFileDialog, QColorDialog
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QColor


# Funciones principales
def load_stl(renderer, vtk_widget, texture, current_mapper, current_actor, texture_coords):
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
    current_actor.GetProperty().SetColor(0.8, 0.8, 0.8)

    # Reiniciar camara
    cam = renderer.GetActiveCamera()
    cam.SetPosition(0, 0, 100)
    cam.SetFocalPoint(0, 0, 0)
    
    renderer.AddActor(current_actor)
    renderer.ResetCamera()
    vtk_widget.GetRenderWindow().Render()
    return current_actor  # Devuelve el actor actualizado

def load_image(renderer, vtk_widget, texture, current_mapper, current_actor, texture_coords):
    filename, _ = QFileDialog.getOpenFileName(
        None, "Seleccionar imagen", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
    )
    if not filename:
        return

    # Remover cualquier modelo previo
    remove_model(renderer, vtk_widget, texture, current_mapper, current_actor, texture_coords)

    # Identificar formato de imagen
    if filename.lower().endswith('.png'):
        reader = vtk.vtkPNGReader()
    elif filename.lower().endswith(('.jpg', '.jpeg')):
        reader = vtk.vtkJPEGReader()
    elif filename.lower().endswith('.bmp'):
        reader = vtk.vtkBMPReader()
    else:
        QtWidgets.QMessageBox.warning(None, "Error", "Formato de imagen no soportado")
        return

    reader.SetFileName(filename)
    reader.Update()

    # Verificar si la imagen tiene un canal alfa
    if reader.GetOutput().GetNumberOfScalarComponents() == 4:
        extract = vtk.vtkImageExtractComponents()
        extract.SetInputConnection(reader.GetOutputPort())
        extract.SetComponents(0, 1, 2)  # Usar solo R, G, B
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
    texture_coords = vtk.vtkTextureMapToPlane() 
    texture_coords.SetInputConnection(geometry.GetOutputPort())

    # Crear filtro de warp para aplicar el relieve
    warp_filter = vtk.vtkWarpScalar()
    #warp_filter.SetInputData(image_data)
    warp_filter.SetInputConnection(geometry.GetOutputPort())
    warp_filter.SetScaleFactor(0.1)
    warp_filter.Update()

    # Crear mapper
    current_mapper = vtk.vtkPolyDataMapper()
    #current_mapper.SetInputConnection(texture_coords.GetOutputPort())
    current_mapper.SetInputConnection(warp_filter.GetOutputPort())

    # Crear actor y textura
    current_actor = vtk.vtkActor()
    current_actor.SetMapper(current_mapper)

    # Aplicar textura de la imagen
    texture = vtk.vtkTexture()
    texture.SetInputConnection(reader.GetOutputPort())
    texture.InterpolateOn() 
    current_actor.SetTexture(texture)

    # Agregar actor al renderizador
    renderer.AddActor(current_actor)
    renderer.ResetCamera()
    vtk_widget.GetRenderWindow().Render()

    return current_actor  # Devuelve el actor actualizado

def load_texture(renderer, vtk_widget, current_actor):
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

    # Crear textura
    texture = vtk.vtkTexture()
    texture.SetInputConnection(reader.GetOutputPort())
    texture.InterpolateOn()

    # Aplicar textura al actor actual
    current_actor.SetTexture(texture)
    
    # Configurar propiedades para mejor visualización
    #current_actor.GetProperty().SetColor(1, 1, 1)  # Color base blanco
    current_actor.GetProperty().LightingOn()
    
    vtk_widget.GetRenderWindow().Render()

def set_background_color(renderer, vtk_widget):
    color = QColorDialog.getColor()
    if color.isValid():
        renderer.SetBackground(color.redF(), color.greenF(), color.blueF())
        vtk_widget.GetRenderWindow().Render()

def set_actor_color(renderer, vtk_widget, current_actor, warp_filter, current_mapper):
    if not current_actor:
        QtWidgets.QMessageBox.warning(None, "Error", "No hay figura para colorear")
        return

    color = QColorDialog.getColor(options=QColorDialog.ShowAlphaChannel)
    if color.isValid():
        # Remover textura si existe
        #current_actor.SetTexture(None)
        
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
    
    # Limpiar textura y asignar color base
    current_actor.SetTexture(None)
    current_actor.GetProperty().SetColor(0.8, 0.8, 0.8)  # Color base blanco
    current_actor.GetProperty().SetOpacity(1.0)  # Asegurarse de la opacidad completa
    
    # Limpiar posibles configuraciones del filtro warp
    if warp_filter:
        warp_filter.RemoveAllInputs()
        warp_filter.Update()
        warp_filter = None  # Resetear la referencia
    
    # Limpiar mapeo actual
    if current_mapper:
        current_mapper.RemoveAllInputs()
        current_mapper.Update()
        current_mapper = None  # Resetear la referencia

    current_actor.GetProperty().EdgeVisibilityOff()
    current_actor.GetProperty().VertexVisibilityOff()
    
    # Actualizar el renderizador
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
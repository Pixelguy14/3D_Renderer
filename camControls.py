# source /home/pixelguy14/Documentos/DICIS_8vo/Graficos_por_computadora/Tareas/bin/activate

# Controles de camara
def top_view(renderer, vtk_widget):
    cam = renderer.GetActiveCamera()
    cam.SetPosition(0, 0, 100)
    cam.SetFocalPoint(0, 0, 0)
    cam.SetViewUp(0, 1, 0)
    renderer.ResetCamera()
    vtk_widget.GetRenderWindow().Render()

def bottom_view(renderer, vtk_widget):
    cam = renderer.GetActiveCamera()
    cam.SetPosition(0, 0, -100)
    cam.SetFocalPoint(0, 0, 0)
    cam.SetViewUp(0, -1, 0)
    renderer.ResetCamera()
    vtk_widget.GetRenderWindow().Render()

def front_view(renderer, vtk_widget):
    cam = renderer.GetActiveCamera()
    cam.SetPosition(0, 100, 0)
    cam.SetFocalPoint(0, 0, 0)
    cam.SetViewUp(0, 0, 1)
    renderer.ResetCamera()
    vtk_widget.GetRenderWindow().Render()

def side_view(renderer, vtk_widget):
    cam = renderer.GetActiveCamera()
    cam.SetPosition(100, 0, 0)
    cam.SetFocalPoint(0, 0, 0)
    cam.SetViewUp(0, 0, 1)
    renderer.ResetCamera()
    vtk_widget.GetRenderWindow().Render()

def rotate_view(renderer, vtk_widget, current_actor, angleAzimuth, angleElevation, AngleRoll):
    if not current_actor:
        return
    
    # Asegúrate de que el actor no tenga culling activado
    current_actor.GetProperty().BackfaceCullingOff()
    current_actor.GetProperty().FrontfaceCullingOff()
    
    # Rotar la cámara
    cam = renderer.GetActiveCamera()
    cam.Azimuth(angleAzimuth)
    cam.Elevation(angleElevation)
    cam.Roll(AngleRoll)
    renderer.ResetCameraClippingRange()  # Ajusta el rango de clipping de la cámara
    vtk_widget.GetRenderWindow().Render()

def remove_model(renderer, vtk_widget, texture, current_mapper, current_actor, texture_coords):
    if current_actor:
        # Eliminar el actor actual del renderizador
        renderer.RemoveActor(current_actor)
        
        # Reiniciar las propiedades del actor
        current_actor.SetTexture(None)                 # Eliminar cualquier textura
        current_actor.GetProperty().EdgeVisibilityOff()  # Desactivar aristas
        current_actor.GetProperty().VertexVisibilityOff()  # Desactivar vértices
        current_actor.GetProperty().SetColor(1, 1, 1)  # Color blanco como base
        current_actor.GetProperty().SetOpacity(1.0)    # Opacidad completa
        current_actor.GetProperty().LightingOn()       # Restaurar iluminación

        # Limpiar referencias a texturas y mapeos
        texture = None
        current_mapper = None
        texture_coords = None

        # Renderizar los cambios
        vtk_widget.GetRenderWindow().Render()

        # Remover el objeto actual del contexto
        current_actor = None

    return current_actor

def cycle_views(self):
    self.view_cycle_functions = [
            lambda: top_view(self.renderer, self.vtk_widget),
            lambda: bottom_view(self.renderer, self.vtk_widget),
            lambda: front_view(self.renderer, self.vtk_widget),
            lambda: side_view(self.renderer, self.vtk_widget)
        ]
    current_function = self.view_cycle_functions[self.current_view_index]
    current_function()
    self.current_view_index = (self.current_view_index + 1) % len(self.view_cycle_functions)

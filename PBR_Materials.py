import vtk

# Cargar textura HDRI (cubo o equirectangular)
env_texture = vtk.vtkTexture()
env_texture.SetCubeMap(True)
env_texture.SetInputCubeMapImages('xpos.jpg', 'xneg.jpg', 'ypos.jpg', 'yneg.jpg', 'zpos.jpg', 'zneg.jpg')

# Skybox
skybox = vtk.vtkSkybox()
skybox.SetTexture(env_texture)

# Leer modelo STL
reader = vtk.vtkSTLReader()
reader.SetFileName("path_to_model.stl")

# Mapper y actor
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(reader.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)

# Aplicar propiedades PBR
actor.GetProperty().SetInterpolationToPBR()
actor.GetProperty().SetMetallic(0.8)    # Material metálico
actor.GetProperty().SetRoughness(0.2)  # Superficie suave
actor.GetProperty().SetOpacity(0.7)    # Semitransparente
actor.GetProperty().SetColor(1.0, 0.8, 0.8)  # Color rosado

# Renderizador
renderer = vtk.vtkRenderer()
renderer.AddActor(actor)
renderer.AddActor(skybox)
renderer.SetBackground(0.1, 0.1, 0.1)
renderer.UseImageBasedLightingOn()
renderer.SetEnvironmentTexture(env_texture)

# Ventana de renderizado
render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)

# Interacción
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(render_window)

render_window.Render()
interactor.Start()

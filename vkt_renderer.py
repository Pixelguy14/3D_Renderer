# python3 -m venv Documents/DICIS_8vo_2025/Graficos_por_computadora/Proyecto/
# source /home/pixel/Documents/DICIS_8vo_2025/Graficos_por_computadora/Proyecto/bin/activate
# cd Documents/DICIS_8vo_2025/Graficos_por_computadora/Proyecto
# python3 vkt_renderer.py
# QT_QPA_PLATFORM=xcb python3 vkt_renderer.py
# Biblioteca de código abierto para procesamiento y visualización de datos científicos y gráficos 3D.
import vtk

def main():
    # Creamos el lector de archivos STL
    reader = vtk.vtkSTLReader()
    reader.SetFileName("/home/pixel/Documents/Blender/Models/ganchio2.stl")
    #reader.SetFileName("/home/pixel/Documents/Blender/Models/Keycap_ubunto(2).stl")
    #reader.SetFileName("/home/pixel/Documents/Blender/Models/caja laser azul mod v2.stl")

    # Creamos el mapeador de geometria y topologia en el renderizador
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    # Creamos la representacion del modelo 3D, donde podremos ajustar propiedades visuales.
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.5, 0.2, 0.8)  # RGB (valores entre 0 y 1)

    # Se configura la ventana del renderizado
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)

    # Se configuran las interacciones de la ventana
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # Se añade el actor y se define el fondo
    renderer.AddActor(actor)
    renderer.SetBackground(1, 1, 1) # Background color

    #axes = vtk.vtkAxesActor()
    #renderer.AddActor(axes)

    # Se inicializa la renderizacion en la ventana
    renderWindow.Render()
    renderWindowInteractor.Start()

if __name__ == "__main__":
    main()

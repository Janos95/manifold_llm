import math
from manifold3d import Mesh, Manifold
import numpy as np
import trimesh
import polyscope as ps
import polyscope.imgui as psim

def example():
  #integer_parameters
  #float_parameters
  hole_radius = 0.2 # 0.2 0 0.4
  box_size_x = 3. # 1. 0 1
  box_size_y = 1. # 3. 0 5
  box_size_z = 0.2 # 0.2 0 0.5
  #end_parameters

  #centered cube
  box = Manifold.cube(np.array([box_size_x, box_size_y, box_size_z]), True)
  box -= box.scale([0.8, 0.8, 0.8])
  offset = box_size_x / 2 - box_size_z / 2
  bracket = box + box.rotate([0, 90, 0]).translate([offset, 0, offset])
  return bracket

def generated_function():
  #integer_parameters
  num_teeth = 10 # 10
  #float_parameters
  radius = 3. # 1. 0.1 5
  thickness = 0.2 # 0.2 0.01 3
  teeth_width = 0.3 # 0.1 0.01 2
  teeth_height = 0.4 # 0.1 0.01 2
  #end_parameters

  center_piece = Manifold.cylinder(thickness, radius, radius, 20)

  teeth = Manifold.cube(np.array([teeth_height, teeth_width, thickness]), True).translate([radius, 0, thickness/2])
  for i in range(1, num_teeth):
    center_piece += teeth.rotate([0, 0, i * 360 / num_teeth])

  return center_piece


def manifold2trimesh(manifold):
    mesh = manifold.to_mesh()

    if mesh.vert_properties.shape[1] > 3:
        vertices = mesh.vert_properties[:, :3]
        colors = (mesh.vert_properties[:, 3:] * 255).astype(np.uint8)
    else:
        vertices = mesh.vert_properties
        colors = None

    return trimesh.Trimesh(
        vertices=vertices, faces=mesh.tri_verts, vertex_colors=colors
    )

ps.init()
mesh = manifold2trimesh(generated_function())
ps.register_surface_mesh("mesh", mesh.vertices, mesh.faces, smooth_shade=False)
ps.set_give_focus_on_show(True)
ps.show()
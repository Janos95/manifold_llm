
import math
import re
from manifold3d import Mesh, Manifold
import numpy as np
import trimesh
import polyscope as ps
import polyscope.imgui as psim
from openai import OpenAI

input_prompt = "type your prompt here"

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

example_code_working = '''
def generated_function():
  #integer_parameters
  num_holes = {} # 3
  #float_parameters
  hole_radius = {} # 0.2 0 0.4
  bracket_width = {} # 1. 0 1
  bracket_length = {} # 3. 0 5
  bracket_thickness = {} # 0.2 0 0.5
  #end_parameters

  box = Manifold.cube(np.array([bracket_length, bracket_thickness, bracket_width]), True)

  box_with_holes = box
  first_hole_offset = -bracket_length / 2 + bracket_thickness * 2
  dist_between_holes = 0.8 * (bracket_length / num_holes)

  for i in range(3):
    cylinder_height = bracket_thickness + 0.1
    hole = Manifold.cylinder(cylinder_height, hole_radius, hole_radius, 20).translate([0, 0, -cylinder_height/2]).rotate([90, 0, 0])
    box_with_holes = box_with_holes - hole.translate([first_hole_offset + i * dist_between_holes, 0, 0])

  #return box_with_holes
  offset = bracket_length / 2 - bracket_thickness / 2
  return box_with_holes + box_with_holes.rotate([0, 0, -90]).translate([offset, offset, 0])
'''

def get_parameter_maps(code):
  try:
    int_parameter_map = {}
    float_parameter_map = {}

    lines = code.split('\n')
    parameter_type = None

    for line in lines:
      line = line.strip()
      if line == '#integer_parameters':
        parameter_type = 'int'
        continue
      elif line == '#float_parameters':
        parameter_type = 'float'
        continue
      elif line == '#end_parameters':
        break

      if parameter_type and '=' in line:
        parts = line.split('=')
        name = parts[0].strip()
        comment_part = parts[1].split('#')[1].strip()

        if parameter_type == 'int':
          # Extract the default value for integer parameters
          deser = [int(x) for x in comment_part.split()]
          default_value = 0
          if len(deser) > 0:
            default_value = deser[0]
          int_parameter_map[name] = default_value
        elif parameter_type == 'float':
          # Extract the default value and range for float parameters
          default_value, min_range, max_range = map(float, comment_part.split())
          float_parameter_map[name] = {'value': default_value, 'range': (min_range, max_range)}

    return int_parameter_map, float_parameter_map
  except Exception as e:
    print(e)
    return {}, {}

def get_parameter_maps_for_edit(code):
  int_parameter_map = {}
  float_parameter_map = {}

  lines = code.split('\n')
  parameter_type = None

  for line in lines:
    line = line.strip()
    if line == '#integer_parameters':
      parameter_type = 'int'
      continue
    elif line == '#float_parameters':
      parameter_type = 'float'
      continue
    elif line == '#end_parameters':
      break

    if parameter_type and '=' in line:
      parts = line.split('=')
      name = parts[0].strip()
      value_comment = parts[1].split('#')

      if parameter_type == 'int':
        int_parameter_map[name] = int(value_comment[0])
      elif parameter_type == 'float':
        default_value, min_range, max_range = map(float, value_comment[1].split())
        float_parameter_map[name] = {'value': float(value_comment[0]), 'range': (min_range, max_range)}

  return int_parameter_map, float_parameter_map

def generate_geometry():
  #integer_parameters
  num_holes = 3
  #float_parameters
  hole_radius = 0.2
  bracket_width = 1.
  bracket_length = 3.
  bracket_thickness = 0.2
  #end_parameters

  box = Manifold.cube([bracket_length, bracket_thickness, bracket_width], True)

  box_with_holes = box
  first_hole_offset = -bracket_length / 2 + bracket_thickness * 2
  dist_between_holes = 0.8 * (bracket_length / num_holes)

  for i in range(3):
    cylinder_height = bracket_thickness + 0.1
    hole = Manifold.cylinder(cylinder_height, hole_radius, hole_radius, 20).translate([0, 0, -cylinder_height/2]).rotate([90, 0, 0])
    box_with_holes = box_with_holes - hole.translate([first_hole_offset + i * dist_between_holes, 0, 0])

  #return box_with_holes
  offset = bracket_length / 2 - bracket_thickness / 2
  return box_with_holes + box_with_holes.rotate([0, 0, -90]).translate([offset, offset, 0])

def generate_sliders():
  global int_parameter_map, float_parameter_map
  anything_changed = False

  # Iterate through integer parameters
  for name, value in list(int_parameter_map.items()):
    # Assuming 'step' and 'step_fast' values are standard for all integer sliders
    changed, new_value = psim.InputInt(name, value, step=1, step_fast=10)
    if changed:
      anything_changed = True
      int_parameter_map[name] = new_value

  # Iterate through float parameters
  for name, param in list(float_parameter_map.items()):
    value = param['value']
    min_range, max_range = param['range']
    changed, new_value = psim.SliderFloat(name, value, v_min=min_range, v_max=max_range)
    if changed:
      anything_changed = True
      float_parameter_map[name]['value'] = new_value

  return anything_changed

def format_code_with_parameters(code, int_map, float_map):
  # Iterate through integer parameters and replace in code
  for name, value in int_map.items():
    code = code.replace(f'{name} = {{}}', f'{name} = {value}')

  # Iterate through float parameters and replace in code
  for name, param in float_map.items():
    value = param['value']
    code = code.replace(f'{name} = {{}}', f'{name} = {value}')

  return code

def extract_code_snippet(text):
  if "```python" in text:
    # Regular expression pattern for code snippet
    pattern = r"```python(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0]
  else:
    return text
def generate_python_function(code, int_map, float_map):
  try:
    code = format_code_with_parameters(code, int_map, float_map)
    # Define a dictionary to capture the local scope
    local_scope = {}
    exec(code, globals(), local_scope)
    generated_function = local_scope['generated_function']
    return generated_function
  except Exception as e:
    print(e)
    return lambda : Manifold.cube([-1, 1, 1], True)

int_parameter_map = {}
float_parameter_map = {}

client = OpenAI()

context = '''
You are CAD engineer using python to algorithms which generate geometric objects. You are using the following environment:
import math
from manifold3d import Mesh, Manifold
import numpy as np
You answer by providing template string that contains a function generated_function which implements an algorithm to generate the requested geometry. 
You try to extract all important parameters of the object at the beginning of the function using the following format:

#integer_parameters
n = {} # 3
#float_parameters
radius = {} # 0.2 0 0.4
#end_parameters

Here is an example output for the request: Make a simple L bracket
def generated_function():
  #integer_parameters
  #float_parameters
  hole_radius = {} # 0.2 0 0.4
  box_size_x = {} # 1. 0 1
  box_size_y = {} # 3. 0 5
  box_size_z = {} # 0.2 0 0.5
  #end_parameters
  # make cube, second argument indicates that the cube is centered
  box = Manifold.cube([box_size_x, box_size_y, box_size_z], True)
  # hollow out the box by subtracting a scaled box
  offset = box_size_x / 2 - box_size_z / 2
  bracket = box + box.rotate([0, 90, 0]).translate([offset, 0, offset])
  return bracket

Here are some other examples of the manifold api
#cylinder plane is the xy plane, height is along z axis
cylinder = Manifold.cylinder(cylinder_height, lower_radius, upper_radius, 20)
sphere = Manifold.sphere(radius, 20)
center_piece = Manifold.cylinder(thickness, radius, radius, 20)
#makes a cube with provided dimensions that is centered
teeth = Manifold.cube(np.array([teeth_height, teeth_width, thickness]), True).translate([radius, 0, thickness/2])
ONLY use apis that are in one of the examples above. Don't use any other apis.
The provided python code must be fully working without modification. Only provide the function nothing else.
'''

generated_text = ''
def callback():
  global ui_float, input_prompt
  global int_parameter_map, float_parameter_map
  global generated_text

  def run():
    try:
      func = generate_python_function(generated_text, int_parameter_map, float_parameter_map)
      object = func()
      mesh = manifold2trimesh(object)  # trimesh
      ps.register_surface_mesh("mesh", mesh.vertices, mesh.faces, smooth_shade=False)
    except Exception as e:
      print(e)

  _, input_prompt = psim.InputText("Prompt", input_prompt)

  psim.InputTextMultiline("Generated Code", generated_text)

  if psim.Button("Iterate"):
    ps.set_screenshot_extension(".jpg");
    ps.screenshot('temp.jpg', True)


  #if updated_code:
  #  int_parameter_map, float_parameter_map = get_parameter_maps_for_edit(generated_text)

  if psim.Button("Generate"):
    print("prompting with ", input_prompt)
    completion = client.chat.completions.create(
      model="gpt-4",
      messages=[
        {"role": "system", "content": context},
        {"role": "user", "content": input_prompt}
      ]
    )

    generated_text = extract_code_snippet(completion.choices[0].message.content)
    print("generated text: ", generated_text)
    # generate workflow
    int_parameter_map, float_parameter_map = get_parameter_maps(generated_text)
    #print(int_parameter_map)
    #print(float_parameter_map)

    run()

  psim.Separator()

  anything_changed = generate_sliders()
  if anything_changed:
    run()

ps.init()
ps.set_user_callback(callback)
ps.set_build_gui(False)
ps.set_give_focus_on_show(True)
ps.show()




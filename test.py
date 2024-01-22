from openai import OpenAI
import re

result = '''
def generated_function():
  #integer_parameters
  hole_number = {} # 3 1 10
  #float_parameters
  hole_radius = {} # 0.2 0 0.4
  box_size_x = {} # 1. 0 1
  box_size_y = {} # 3. 0 5
  box_size_z = {} # 0.2 0 0.5
  #end_parameters
  
  # make a centered cube
  box = Manifold.cube(np.array([box_size_x, box_size_y, box_size_z]), True)

  # Hole parameters
  hole_offset = box_size_x / (hole_number + 1)

  # Create Holes
  for i in range(hole_number):
    hole_position_x = (i + 1) * hole_offset
    hole_position_y = box_size_y / 2
    hole_cylinder = Manifold.cylinder(hole_radius, hole_radius, box_size_z + 2, 20)
    box -= hole_cylinder.translate([hole_position_x, hole_position_y, 0])

  offset_x = box_size_x / 2 - box_size_z / 2
  half_L = box + box.rotate([0, 90, 0]).translate([offset_x, 0, offset_x])
  
  # Now drill holes on the other side of the 'L'
  hole_offset_y = box_size_y / (hole_number + 1)
  for i in range(hole_number):
    hole_position_x = box_size_x / 2
    hole_position_y = (i + 1) * hole_offset_y
    hole_cylinder = Manifold.cylinder(hole_radius, hole_radius, box_size_z + 2, 20)
    half_L -= hole_cylinder.translate([hole_position_x, hole_position_y, 0])
    
  
  return half_L
'''

def extract_code_snippet(text):
  if "```python" in text:
    # Regular expression pattern for code snippet
    pattern = r"```python(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0]
  else:
    return text

print(extract_code_snippet(result))
# quit script for now
quit()

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

Here is an example output for the request: Make a simple L bracket which is hollow
def generated_function():
  #integer_parameters
  #float_parameters
  hole_radius = {} # 0.2 0 0.4
  box_size_x = {} # 1. 0 1
  box_size_y = {} # 3. 0 5
  box_size_z = {} # 0.2 0 0.5
  #end_parameters
  # make a centered cube
  box = Manifold.cube(np.array([box_size_x, box_size_y, box_size_z]), True)
  # hollow out the box by subtracting a scaled box
  box -= box.scale([0.8, 0.8, 0.8])
  offset = box_size_x / 2 - box_size_z / 2
  bracket = box + box.rotate([0, 90, 0]).translate([offset, 0, offset])
  return bracket

Here are some other examples of the manifold api
cylinder = Manifold.cylinder(cylinder_height, lower_radius, upper_radius, 20)
sphere = Manifold.sphere(radius, 20)
teeth = Manifold.cube(np.array([teeth_height, teeth_width, thickness]), True).translate([radius, 0, thickness/2])
The provided python code must be fully working without modification.
'''

print('starting completion')
completion = client.chat.completions.create(
  model="gpt-4",
  messages=[
    {"role": "system", "content": context},
    {"role": "user", "content": "Make an L shaped bracket with 3 holes on each side of the bracket."}
  ]
)

print(completion.choices[0].message.content)
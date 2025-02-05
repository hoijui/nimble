# SPDX-FileCopyrightText: 2023 Jeremy Wright <wrightjmf@gmail.com>
# SPDX-FileCopyrightText: 2023 Andreas Kahler <mail@andreaskahler.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import cadquery as cq
import os
import json
from exportsvg import export_svg 
import models.nimble_beam
import models.nimble_end_plate
import models.nimble_tray
import config

# generate all models and update documentation



# parameters

selected_devices_ids = config.devices

json_filename = "./src/mech/cadquery_workflow/devices.json"
outputdir_stl = "./src/mech/cadquery_workflow/gitbuilding/models/"
outputdir_step = "./src/mech/step/"
outputdir_svg = "./src/mech/cadquery_workflow/gitbuilding/svg/"
outputdir_gitbuilding = "./src/mech/cadquery_workflow/gitbuilding/"

beam_length = 294
single_width = 155

# set up build env

try:
  os.mkdir(outputdir_stl)
except:
  pass # ignore if already existing

try:
  os.mkdir(outputdir_step)
except:
  pass # ignore if already existing

try:
  os.mkdir(outputdir_svg)
except:
  pass # ignore if already existing

# read json, select entries

selected_devices = []
with open(json_filename) as json_file:
    data = json.load(json_file)
    selected_devices = [x for x in data if x['ID'] in selected_devices_ids]
print([x['ID'] for x in selected_devices])

# create the models and assembly

beam = models.nimble_beam.create(beam_length=beam_length)
plate = models.nimble_end_plate.create(width=single_width, height=single_width)

listOfTrays = []
for device in selected_devices:
    tray = models.nimble_tray.create(device['HeightInUnits'])
    listOfTrays.append((tray, device))


def createAssembly(step):
  assembly = cq.Assembly()
  if step >= 1:
    plate.rotateAboutCenter((1, 0, 0), 0)
    assembly.add(plate, name="baseplate", loc=cq.Location((0, 0, 0)))
  if step >= 2:
    #25, 42, 55
    beam_height = 4
    for tray in listOfTrays:
      if tray[1]['HeightInUnits'] == 2:
        beam_height += 27
      elif  tray[1]['HeightInUnits'] == 3:
        beam_height += 42
      elif  tray[1]['HeightInUnits'] == 4:
        beam_height += 55
    assembly.add(models.nimble_beam.create(beam_length=beam_height), name="beam1", loc=cq.Location((-single_width / 2.0 + 10, -single_width / 2.0 + 10, 3)))
    assembly.add(models.nimble_beam.create(beam_length=beam_height), name="beam2", loc=cq.Location((single_width / 2.0 - 10, -single_width / 2.0 + 10, 3)))
    assembly.add(models.nimble_beam.create(beam_length=beam_height), name="beam3", loc=cq.Location((single_width / 2.0 - 10, single_width / 2.0 - 10, 3)))
    assembly.add(models.nimble_beam.create(beam_length=beam_height), name="beam4", loc=cq.Location((-single_width / 2.0 + 10, single_width / 2.0 - 10, 3)))
  if step >= 3:
    topplate = models.nimble_end_plate.create(width=single_width, height=single_width)
    topplate = topplate.rotateAboutCenter((1, 0, 0), 180)
    topplate = topplate.rotateAboutCenter((0, 0, 1), 180)
    assembly.add(topplate, name="topplate", loc=cq.Location((0, 0, beam_height + 3)))
  if step >= 4:
    index = 0
    for (tray, trayInfo) in listOfTrays:
        assembly.add(tray, loc=cq.Location((-115/2, -155/2-4, 4+index*trayInfo['HeightInUnits'] * 27/2)))
        index = index+1
  return (
    assembly.toCompound() 
    .rotate((0,0,0), (1,0,0), -90) # z should be up
    .rotate((0,0,0), (0,1,0), 10) # rotate a bit around up axis for better view
  )


# export SVGs

export_svg(createAssembly(1), outputdir_svg+"baseplate.svg") 
export_svg(createAssembly(2), outputdir_svg+"baseplate_beams.svg") 
export_svg(createAssembly(3), outputdir_svg+"baseplate_beams_topplate.svg") 
export_svg(createAssembly(4), outputdir_svg+"trays.svg") 

# export STLs and STEPs

partList = []

def exportPart(part, name, long_name):    
  stl_file = outputdir_stl + name + ".stl"
  step_file = outputdir_step + name + ".step"
  cq.exporters.export(part, stl_file)
  #cq.exporters.export(part, step_file) #not needed right now
  partList.append((name, long_name))

exportPart(beam, "beam", "3D printed beam")
exportPart(plate, "baseplate", "3D printed base plate")
exportPart(plate, "topplate", "3D printed top plate")

for (part, device) in listOfTrays:
  exportPart(part, "tray_"+device['ID'], f"tray for {device['Name']}")


# write gitbuilding files

with open(outputdir_gitbuilding+'3dprintingparts.md', 'w') as f:
    f.write("# 3D print all the needed files\n\n")
    for (part,long_name) in partList:
      f.write("* %s.stl ([preview](models/%s.stl){previewpage}, [download](models/%s.stl))\n" % (part, part, part))
    f.write('\n\nYou can [download all of the STLs as a single zipfile](stlfiles.zip){zip, pattern:"*.stl"}')



with open(outputdir_gitbuilding+'3DPParts.yaml', 'w') as f:
  for (part,long_name) in partList:
    f.write("%s:\n" % (part))
    f.write("    Name: %s\n" % (long_name))
    f.write("    Specs:\n")
    f.write("        Filename: %s.stl\n" % (part))
    #f.write("        Filename: %s.stl ([download](models/%s.stl))\n" % (part, part))
    f.write("        Manufacturing: 3D Printing\n")
    f.write("        Material: PLA or PETG\n")
    #f.write("        Preview: [preview](models/beam.stl){previewpage}\n")

with open(outputdir_gitbuilding+'DeviceParts.yaml', 'w') as f:
  for (part, device) in listOfTrays:
    f.write("%s:\n" % (device['ID']))
    f.write("    Name: %s\n" % (device['Name']))
    f.write("    Specs:\n")
    for k in device.keys():
      f.write("        %s: %s\n" % (k, device[k]))

with open(outputdir_gitbuilding+'components.md', 'w') as f:
    f.write("# Installing the components in trays\n\n")
    f.write("{{BOM}}\n")
    f.write("![](svg/baseplate_beams_topplate.svg)\n\n")
    f.write("For all of your components:\n\n")
    f.write("* find the corresponding 3d printed tray\n")
    f.write("* install the tray on the rack\n")
    f.write("* mount the device on the tray\n\n")
    f.write("Here are the devices and the trays\n\n")
    for (part, device) in listOfTrays:
      f.write("* [%s](DeviceParts.yaml#%s){Qty: 1}\n" % (device['Name'], device['ID']))
      stlfile = F"tray_{device['ID']}.stl"
      f.write("* %s ([preview](models/%s){previewpage}, [download](models/%s))\n" % (stlfile, stlfile, stlfile))
    f.write("![](svg/trays.svg)")

#for debugging
#show_object(beam)




# SPDX-FileCopyrightText: 2023 Andreas Kahler <mail@andreaskahler.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import cadquery as cq

def export_svg(part, filename):
  cq.exporters.export(part,
                      filename,
                      opt={
                          "width": 300,
                          "height": 300,
                          "marginLeft": 10,
                          "marginTop": 10,
                          "showAxes": False,
                          "projectionDir": (1, 1, 1),
                          "strokeWidth": 0.8,
                          "strokeColor": (0, 0, 0),
                          "hiddenColor": (0, 0, 255),
                          "showHidden": False,
                      },)

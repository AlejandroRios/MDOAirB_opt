from framework.CPACS_update.cpacsfunctions import *
import numpy as np

MODULE_DIR = 'c:/Users/aarc8/Documents/github\MDOAirB_base/framework/CPACS_update'
cpacs_path = os.path.join(MODULE_DIR, 'ToolInput', 'Aircraft_In.xml')
cpacs_out_path = os.path.join(MODULE_DIR, 'ToolOutput', 'Aircraft_Out.xml')
tixi = open_tixi(cpacs_out_path)
tigl = open_tigl(tixi)

# tixi_out = open_tixi(cpacs_out_path)
# wing = vehicle['wing']
# horizontal_tail = vehicle['horizontal_tail']
# vertical_tail = vehicle['vertical_tail']
# fuselage = vehicle['fuselage']
# engine = vehicle['engine']
# nacelle = vehicle['nacelle']
# aircraft = vehicle['aircraft']


# Reference parameters
Cref = tigl.wingGetMAC(tigl.wingGetUID(1))
Sref = tigl.wingGetReferenceArea(1,1)
b    = tigl.wingGetSpan(tigl.wingGetUID(1))

print(Cref)
print(Sref*2)
print(b)
#Usage Example: 
#conda activate bgrenv
#python3 fluidics-main.py

import schedule, signal, uuid, builtins, json, os, csv, time, math

from contextlib import contextmanager
from time import sleep as sleep
from braingeneers.iot import *
from Apps.autoculture import *
from Apps.feedback import *
from Apps.tecancavro.models import CentrisB, SmartValveB
from Apps.tecancavro.transport import TecanAPISerial


if __name__ == '__main__':
    ###############################
    ### Zambezi Initialization ###
    ###############################
    centris_pump = CentrisB(com_link=TecanAPISerial(0, '/dev/ttyUSB0', 9600), waste_port=6, microliter=True, debug=False, debug_log_path='/home/pi/tecancavro/')
    disp_valve = SmartValveB(com_link=TecanAPISerial(1, '/dev/ttyUSB0', 9600))
    aspir_valve = SmartValveB(com_link=TecanAPISerial(2, '/dev/ttyUSB0', 9600))

    # Instantiate the Autoculture system
    zambezi = Autoculture(centris_pump, 'v1.0', twelve_valve1=disp_valve, twelve_valve2=aspir_valve, device_name='zambezi')
    zambezi.initializeSystem()
    sleep(2)

    # Instantiate a Reservoir (named 'media')
    media = Reservoir(3, 5000, "Ry5")
    zambezi.reservoir_dict[media.variety] = media

    # TODO: Populate/config a well via MQTT (remove this next section)
    default = Well(zambezi, media, 1, 6, 5, in_volume_ul=300, out_volume_ul=3000, disp_valve=disp_valve, disp_port=1, aspir_valve=aspir_valve, aspir_port=1, log=True, estimate="RIGHT", name="default")
    #well_one = Well(zambezi, media, 1, 6, 5, in_volume_ul=300, out_volume_ul=3000, disp_valve=disp_valve, disp_port=1, aspir_valve=aspir_valve, aspir_port=1, log=True, estimate="RIGHT", name="20302")
    #well_two = Well(zambezi, media, 1, 6, 5, in_volume_ul=300, out_volume_ul=3000, disp_valve=disp_valve, disp_port=2, aspir_valve=aspir_valve, aspir_port=2, log=True, estimate="LEFT", name="14237")
    
    zambezi.wells_dict[default.name] = default
    #zambezi.wells_dict[well_one.name] = well_one
    #zambezi.wells_dict[well_two.name] = well_two
    
    # Begin will 2 pulls each (this is priming)
    #well_one.pull(2)
    #sleep(2)
    #well_two.pull(2)
    #sleep(2)

    #################################
    ### Begin MQTT Communications ###
    #################################
    # Check for tasks from the scheduler or MQTT
    zambezi.start_mqtt()

    # Concluding code
    print("Goodbye")

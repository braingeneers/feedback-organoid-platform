import schedule, builtins, json, os, csv, time, math

import sys
sys.path.append('Apps')
sys.path.append('Apps/tecancavro')
sys.path.append(os.path.abspath(os.path.join('..')))

from time import sleep as sleep
#from braingeneers.iot import *
from Apps.autoculture import *
from Apps.feedback import *
from tecancavro.models import CentrisB, SmartValveB
from tecancavro.transport import TecanAPISerial
#from device import MqttDevice
from braingeneers.iot import Device

class Autoculture(Device):
    """
    Class responsible for platform-level methods such as initializing, washing, and experimental configuration
    """
    def __init__(self, centris_pump, version, centris_pump2=None, twelve_valve1=None, twelve_valve2=None, twelve_valve3=None,
                 twelve_valve4=None, reservoir_dict={}, wells_dict={}, device_name='autoculture'):
        """
        Object constructor function, save pump and valve references to self

        Args:
            'centris_pump' (obj) : COM reference to primary Centris syringe pump object
            'version' (str) : reference to Autoculture system version ['v1.0', 'v1.1', 'v2.0']
        Kwargs:
            'centris_pump2' (obj) : COM reference to secondary Centris syringe pump object (v2 aspiration)
            'twelve_valve1' (obj) : reference to Smart Valve object
            'twelve_valve2' (obj) : reference to Smart Valve object
            'twelve_valve3' (obj) : reference to Smart Valve object
            'twelve_valve4' (obj) : reference to Smart Valve object
            'reservoir_dict' (dict) : dictionary of reservoirs (obj)
            'wells_dict' (dict) : dictionary of wells (obj)
            'device_name' (str) : name of the device
        """
        super().__init__(device_name, device_type="autoculture", primed_default=True)
        self.version = version
        self.centris_pump = centris_pump
        self.centris_pump2 = centris_pump2
        self.twelve_valve1 = twelve_valve1
        self.twelve_valve2 = twelve_valve2
        self.twelve_valve3 = twelve_valve3
        self.twelve_valve4 = twelve_valve4
        self.reservoir_dict = reservoir_dict
        self.wells_dict = wells_dict

        if self.version == 'v1.0':
            # 12-plex system with a single syringe pump and 2 distribution valves
            self.pump = centris_pump
            self.disp_valve = twelve_valve1
            self.aspir_valve = twelve_valve2
        elif self.version == 'v1.1':
            # 24-plex system with a single syringe pump and 4 distribution valves
            self.pump = centris_pump
            self.disp_valve = twelve_valve1
            self.disp_valve2 = twelve_valve2
            self.aspir_valve = twelve_valve3
            self.aspir_valve2 = twelve_valve4
        elif self.version == 'v2.0':
            # 24-plex system with a two-syringe pump, servo manifold, and 2 distribution valves
            self.aspir_pump = centris_pump
            self.disp_pump = centris_pump2
            self.disp_valve = twelve_valve1
            self.aspir_valve = twelve_valve2

        # Child must define this when inheriting MqttDevice parent
        self.device_specific_handlers.update({ 
             "WELL": self.handle_well,
             "FEEDBACK": self.handle_feedback,
             "DISPENSE": self.handle_dispense,
             "ASPIRATE": self.handle_aspirate,
             "FEED": self.handle_feed,
             "PULL": self.handle_pull,
             "PLUNGE": self.handle_plunge
        })


    # ShadowsBD
    @property
    def device_state(self):
        return { **super().device_state,
                "WELLS": [well.name for well in self.wells_dict.values()], 
                "AUTOCULTURE": self.version
                }


    def initializeSystem(self):
        """ Physically reset all pumps and valves with electronic initialization """
        # TODO: get state parameters (syringe level, syringe media, port selected)
        self.centris_pump.init()
        sleep(0.5)  # idle for 0.5 sec
        if self.centris_pump2 is not None:
            self.centris_pump2.init()
            time.sleep(0.5)  # idle for 0.5 sec
        if self.twelve_valve1 is not None:
            self.twelve_valve1.init()
            time.sleep(0.5)  # idle for 0.5 sec
        if self.twelve_valve2 is not None:
            self.twelve_valve2.init()
            time.sleep(0.5)  # idle for 0.5 sec
        if self.twelve_valve3 is not None:
            self.twelve_valve3.init()
            time.sleep(0.5)  # idle for 0.5 sec
        if self.twelve_valve4 is not None:
            self.twelve_valve4.init()
            time.sleep(0.5)  # idle for 0.5 sec

    # TODO: remake washCycle program
    def washCycle(self, sterilization_reagent, wash_reagent):
        """
        Wash the system with 10 minutes of the sterilization reagent followed by 10 cycles of washing and drying

        Args:
            'sterilization_reagent'
        """
        sterilization_reagent = sterilization_reagent

    def handle_well(self, topic, message):
        # WELL: Initialize a well object and apend it to the wells list
        
        # Example message: {"WELL" : "REQUEST", "CHIP_ID" : 12345, "INDEX" : "RIGHT",
        #                   "MEDIA" : "Ry5", "IN_PORT" : 1, "OUT_PORT" : 6, "EXHAUST_PORT" : 5, "SPEED" : 15,
        #                   "IN_VOL_UL" : 300, "OUT_VOL_UL" : 3000, "DISP_PORT" : 1, "ASPIR_PORT" : 1}
        
        # Get first key value pair
        #msg_key, msg_value = next(iter(message.items()))
        
        # CHIP_ID is name of the chip (i.e. chip #)
        try:
            msg_index = str(message['CHIP_ID'])
            
        except KeyError:
            self.mb.publish_message(topic=topic,message={"WELL":"MISSING_CHIP_ID","FROM":self.device_name})
            print('Missing CHIP_ID')
            return
        
        # INDEX is which tube for volume estimation (i.e. "RIGHT" of "LEFT")
        try:
            msg_estimate = message['INDEX']
        except KeyError:
            self.mb.publish_message(topic=topic,message={"WELL":"INDEX","FROM":self.device_name})
            return
                
        # Load type-casted Well parameters and use defaults where keys are missing
        msg_well_media = str(message.get("MEDIA", "Ry5"))  # Default: "Ry5"
        msg_well_in_port = int(message.get("IN_PORT", 1))  # Default: 1
        msg_well_out_port = int(message.get("OUT_PORT", 6))  # Default: 6
        msg_well_exhaust_port = int(message.get("EXHAUST_PORT", 5))  # Default: 5
        msg_well_in_vol_ul = int(message.get("IN_VOL_UL", 300))  # Default: 300
        msg_well_out_vol_ul = int(message.get("OUT_VOL_UL", 3000))  # Default: 3000
        msg_well_speed = int(message.get("SPEED", 13))  # Default: 13
        msg_well_disp_port = int(message.get("DISP_PORT", 1))  # Default: 1
        msg_well_aspir_port = int(message.get("ASPIR_PORT", 1))  # Default: 1
        
        #if msg_value == "WELL-REQUEST":
        # Grab the Reservoir object
        res_obj = message.get(msg_well_media, None)
        if res_obj is None:
            res_name, res_obj = next(iter(self.reservoir_dict.items()))
        
        # Make the Well object
        new_well = Well(self, res_obj, in_port=msg_well_in_port, out_port=msg_well_out_port,
                        exhaust_port=msg_well_exhaust_port,
                        in_volume_ul=msg_well_in_vol_ul, out_volume_ul=msg_well_out_vol_ul,
                        speed=msg_well_speed,
                        disp_valve=self.disp_valve, disp_port=msg_well_disp_port,
                        aspir_valve=self.aspir_valve, aspir_port=msg_well_aspir_port,
                        log=True,
                        estimate=msg_estimate,
                        name=msg_index)
        
        print("Made the well " + new_well.name)
    
        # Add the new well to self well_dict
        self.wells_dict[msg_index] = new_well
        return

    def handle_feedback(self, topic, message):
        # FEEDBACK: Volume and/or pH was calculated by computer vision and ready to be used by actionDecider()
        
        # Example message: {"FEEDBACK" : "REQUEST", "CHIP_ID" : 12345, "VOL" : 300.0, "PH" : 7.12}

        # Get first key value pair
        msg_key, msg_value = next(iter(message.items()))
        try:
            msg_index = message['CHIP_ID']
        except KeyError:
            self.mb.publish_message(topic=topic,message={"FEEDBACK":"MISSING_CHIP_ID","FROM":self.device_name})
            print('Missing CHIP_ID')
            return
        
        for key, value in message.items():
            if key == "VOL":
                # Volume estimation received
                volume = float(value)
                action = actionDecider(self.wells_dict[msg_index], 'volume', volume, message["IMAGE"])  # Pass the well and reservoir volume to the actionDecider
                if action is not None:
                    # Publish the Feedback action
                    self.mb.publish_message(topic=topic, message=action)
                    
                    # Post to Slack in some cases
                    for key in ["DISPENSE", "ASPIRATE"]:
                        if key in action:
                            self.post_to_slack(text=self.device_name + " engaged Feedback on " + str(msg_index) + ": {" + key + " : " + str(action["VOL"]) + "}")    
                            break
                    
                    # Schedule a Picture Request for volume estimation to check if the Feedback tactic worked
                    # TODO: is this working?
                    for key in ["ASPIRATE", "PULL", "PLUNGE"]:
                        if key in action:
                            pic_request_msg = { "COMMAND":"SCHEDULE-REQUEST",
                                                "TYPE": "ADD",
                                                "EVERY_X_MINUTES": "1",
                                                "FLAGS": "ONCE",
                                                "DO": { 
                                                    "COMMAND": "PICTURE-REQUEST", 
                                                    "TYPE": ["volume"], 
                                                    "CHIP_ID": msg_index, 
                                                    "INDEX": self.wells_dict[msg_index].estimate,
                                                    "FROM": self.device_name},
                                                "FROM": self.device_name 
                                            }
                            
                            print("Scheduling a photo to check on feedback action results")

                            # TODO: This is hard-coded for now, we want to better direct this message to the camera
                            
                            self.mb.publish_message(topic="telemetry/" + self.experiment_uuid + "/log/zambezi-cam/SCHEDULE/REQUEST", message=pic_request_msg)
                            break
                    
            elif key == "PH_WINDOW":
                # pH estimation received
                pH_window = eval(message["PH_WINDOW"])
                pH_conical = eval(message["PH_CONICAL"])
                action = actionDecider(self.wells_dict[msg_index], 'pH', [pH_window, pH_conical], message["IMAGE"])  # Pass the well and reservoir volume to the actionDecider
                if action is not None:
                    # Publish the actionDecider task
                    self.mb.publish_message(topic=topic, message=action)
                    self.post_to_slack(text="FEEDBACK decided to " + str(action))

    def handle_dispense(self, topic, message):
        # DISPENSE: Dispense requested
        
        # Example message: {"DISPENSE" : "REQUEST", "VOL" : 300, "CHIP_ID" : 12345}

        # Get first key value pair  
        msg_key, msg_value = next(iter(message.items()))
        try:
            msg_index = message['CHIP_ID']
        except KeyError:
            self.mb.publish_message(topic=topic,message={"DISPENSE":"MISSING_CHIP_ID","FROM":self.device_name})
            print('Missing CHIP_ID')
            return

        try:
            vol = float(message['VOL'])
            print("vol =", vol)
            if vol < 0 or vol > 5000:  # <-- Exceptable volumes are 0uL to 5mL
                # Publish task OUTOFBOUNDS
                self.mb.publish_message(topic=topic,message={"DISPENSE":"OUT_OF_BOUNDS","FROM":self.device_name})
            else:
                self.wells_dict[msg_index].dispense(vol)
                # TODO: If key not in wells_dict, render error message
                print("Finished")

        except (ValueError, IndexError) as e:
            print("Error occurred:", e)

            # Publish task ERROR
            self.mb.publish_message(topic=topic,message={"DISPENSE":"ERROR","FROM":self.device_name})

        return
        
    def handle_aspirate(self, topic, message):
        # ASPIRATE: Aspirate requested

        # Get first key value pair
        msg_key, msg_value = next(iter(message.items()))
        try:
            msg_index = message['CHIP_ID']
        except KeyError:
            self.mb.publish_message(topic=topic,message={"ASPIRATE":"MISSING_CHIP_ID","FROM":self.device_name})
            print('Missing CHIP_ID')
            return

        try:
            vol = float(message['VOL'])
            if vol < 0 or vol > 10000:  # <-- Exceptable volumes are 0uL to 10mL
                # Publish task OUTOFBOUNDS
                self.mb.publish_message(topic=topic,message={"ASPIRATE":"OUT_OF_BOUNDS","FROM":self.device_name})
            else:
                self.wells_dict[msg_index].aspirate(vol)

        except (ValueError, IndexError) as e:
            print("Error occurred:", e)

            # Publish task ERROR
            self.mb.publish_message(topic=topic,message={"ASPIRATE":"ERROR","FROM":self.device_name})

        return

    def handle_feed(self, topic, message):
        # FEED: Replenishment cycle requested
        
        # Example message: {"FEED" : "REQUEST", "CHIP_ID" : 12345}

        # Get first key value pair
        msg_key, msg_value = next(iter(message.items()))
        try:
            msg_index = message['CHIP_ID']
        except KeyError:
            self.mb.publish_message(topic=topic,message={"FEED":"MISSING_CHIP_ID","FROM":self.device_name})
            print('Missing CHIP_ID')
            return

        try:
            # Schedule a Picture Request (burst) for pH measuring while aspiration is occuring - 5 seconds after aspiration begins
            pic_request_msg = { "COMMAND":"SCHEDULE-REQUEST",
                                "TYPE": "ADD",
                                "EVERY_X_MINUTES": "1",
                                "FLAGS": "ONCE",
                                "DO": { 
                                    "COMMAND": "PICTURE-REQUEST", 
                                    "TYPE": ["pH"], 
                                    "CHIP_ID": msg_index, 
                                    "INDEX": self.wells_dict[msg_index].estimate,
                                    "FROM": self.device_name},
                                "FROM": self.device_name 
                            }

            # TODO: This is hard-coded for now, we want to better direct this message to the camera
            #sleep(10) # Wait for zambezi-cam to initialize
            self.mb.publish_message(topic="telemetry/" + self.experiment_uuid + "/log/zambezi-cam/SCHEDULE/REQUEST", message=pic_request_msg)

            # Complete the feed (replenishment) cycle
            self.wells_dict[msg_index].replenishmentCycle()

            # Post to to Slack
            #self.post_to_slack(text=self.device_name + "'s " + self.wells_dict[msg_index].name + " FEED COMPLETE")
            
            # Schedule a Picture Request for volume estimation - 1 minute after feed ends
            pic_request_msg = { "COMMAND":"SCHEDULE-REQUEST",
                                "TYPE": "ADD",
                                "EVERY_X_MINUTES": "1",
                                "FLAGS": "ONCE",
                                "DO": { 
                                    "COMMAND": "PICTURE-REQUEST", 
                                    "TYPE": ["volume"], 
                                    "CHIP_ID": msg_index, 
                                    "INDEX": self.wells_dict[msg_index].estimate,
                                    "FROM": self.device_name},
                                "FROM": self.device_name 
                            }

            # TODO: This is hard-coded for now, we want to better direct this message to the camera
            self.mb.publish_message(topic="telemetry/" + self.experiment_uuid + "/log/zambezi-cam/SCHEDULE/REQUEST", message=pic_request_msg)



        except (ValueError, IndexError) as e:
            print("Error occurred:", e)

            # Publish task ERROR
            self.mb.publish_message(topic=topic,message={"FEED":"ERROR", "FROM":self.device_name})

        return
        
    def handle_pull(self, topic, message):
        # PULL: Pull requested

        # Get first key value pair
        msg_key, msg_value = next(iter(message.items()))
        try:
            msg_index = message['CHIP_ID']
        except KeyError:
            self.mb.publish_message(topic=topic,message={"PULL":"MISSING_CHIP_ID", "FROM":self.device_name})
            return

        try:
            num = int(message['NUM'])
            if num < 0 or num > 15:  # <-- Exceptable iterations are 0 to 15
                # Publish task OUTOFBOUNDS
                self.mb.publish_message(topic=topic,message={"PULL":"OUT_OF_BOUNDS", "FROM":self.device_name})
            else:
                self.wells_dict[msg_index].pull(num)

            # Publish task COMPLETE
            #self.post_to_slack(text=self.device_name + str(num) +"PULL COMPLETE")
        except (ValueError, IndexError) as e:
            print("Error occurred:", e)

            # Publish task ERROR
            self.mb.publish_message(topic=topic,message={"PULL":"ERROR", "FROM":self.device_name})

        return
        
    def handle_plunge(self, topic, message):
        # PLUNGE: Plunge requested
        
        # Get first key value pair
        msg_key, msg_value = next(iter(message.items()))
        try:
            msg_index = message['CHIP_ID']
        except KeyError:
            self.mb.publish_message(topic=topic,message={"PLUNGE":"MISSING_CHIP_ID", "FROM":self.device_name})
            return

        try:
            num = int(message['NUM'])
            if num < 0 or num > 15:  # <-- Exceptable iterations are 0 to 15
                # Publish task OUTOFBOUNDS
                self.mb.publish_message(topic=topic,message={"PLUNGE":"OUT_OF_BOUNDS", "FROM":self.device_name})
            else:
                self.wells_dict[msg_index].plunge(num)

            # Publish task COMPLETE
            self.post_to_slack(text=self.device_name + str(num) +"PLUNGE COMPLETE")
        except (ValueError, IndexError) as e:
            print("Error occurred:", e)

            # Publish task ERROR
            self.mb.publish_message(topic=topic,message={"PLUNGE":"OUT_OF_BOUNDS", "FROM":self.device_name})

    # TODO: SETTINGS: Change settings such as speed, wells, media

class Well():
    """
    Class responsible for individual, well methods such as filling
    """
    def __init__(self, autoculture, reservoir, in_port, out_port, exhaust_port,
                 in_volume_ul=0, out_volume_ul=0, speed=15, syringeSpeed=11,
                 disp_valve=None, disp_port=None, aspir_valve=None, aspir_port=None,
                 retry_tally=0, reservoir_offset=0, accumulated_vol=0, reservoir_vol=0,
                 log=False, log_file='Logs/default.log', estimate=None, name=''):
        """
        Object constructor function, save pump and valve references

        Args:
            'autoculture' (obj) : reference to Autoculture class object containing references to the pumps and valves
            'reservoir' (obj) : reference to Reservoir class object containing reagent and port references
            'in_port' (int) : 'pump' port for reagent delivery (to well)
            'out_port' (int) : 'pump' port for reagent extraction (to waste)
            'exhaust_port' (int) : 'pump' port for non-fluidic, air operations
        Kwargs:
            'in_volume_ul' (float) : absolute volume (uL) to deliver
            'out_volume_ul' (float) : absolute volume (uL) to aspirate
            'speed' (int) : syringe speed for dispensing and aspirating
            'syringeSpeed' (int) : syringe speed for pulling media and exhausing air
            'disp_valve' (obj) : reference to dispensing valve object
            'disp_port' (int) : 'disp_valve' port for reagent delivery (to well)
            'aspir_valve' (obj) : reference to aspirating valve object
            'aspir_port' (int) : 'aspir_vavle' port for reagent extraction (to waste)
            'retry_tally' (int) : Current number of retry attemps
            'reservoir_offset' (float) : Offset volume [uL] that will be subtracted from the computer vision computed volume
            'accumulated_vol' (float) : Volume accumulated (from past collection tubes) that should be added to the computed reservoir volume
            'reservoir_vol' (float) : The volume [uL] in the reservoir computed through the computer vision program
            'log' (bool) : True/False on whether to write csv file of logs
            'log_file' (str) : name of csv file to write logs
            'estimate' (str) : Camera index for volume estimation (i.e. "RIGHT", "LEFT")
            'name' (str) : give a label to the well
        """
        self.autoculture = autoculture
        self.reservoir = reservoir
        self.in_port = int(in_port)
        self.out_port = int(out_port)
        self.exhaust_port = int(exhaust_port)
        self.in_volume_ul = in_volume_ul
        self.out_volume_ul = out_volume_ul
        self.speed = int(speed)
        self.syringeSpeed = int(syringeSpeed)
        self.retry_tally = int(retry_tally)
        self.reservoir_offset = float(reservoir_offset)
        self.accumulated_vol = float(accumulated_vol)
        self.reservoir_vol = float(reservoir_vol)
        self.log = log
        self.log_file = log_file
        self.estimate = estimate
        self.name = str(name)

        # State
        self.fluidic_state = {
            'iteration': 0,
            'in_volume': 0,
            'out_volume': 0,
            'disp_valve': False,
            'aspir_valve': False,
            'syringe_volume': 0
        }
        self.disp_valve = disp_valve
        if self.disp_valve is not None:
            self.fluidic_state['disp_valve'] = True
        self.disp_port = disp_port
        self.aspir_valve = aspir_valve
        if self.aspir_valve is not None:
            self.fluidic_state['aspir_valve'] = True
        self.aspir_port = aspir_port

        # Rename the log_file to the name
        if name != '':
            self.log_file = 'Logs/' + name + '_pump.log'

    def dispense(self, vol):
        """ Inject 'vol' [uL] into the well """

        vol = float(vol)

        # Check syringe fill
        # TODO make this more intelligent
        self.checkSyringe()
        if self.fluidic_state['syringe_volume'] < vol:
            self.fillSyringe(self.reservoir, vol)

        # Dispense - Wet pump
        if self.fluidic_state['disp_valve']:
            self.disp_valve.changePort(self.disp_port)
            self.disp_valve.executeChain()
            self.disp_valve.waitReady(delay=0.5)
        self.autoculture.pump.setSpeed(self.speed)
        self.autoculture.pump.dispense(self.in_port, vol)
        self.autoculture.pump.delayExec(2000)
        self.autoculture.pump.executeChain()
        self.autoculture.pump.waitReady(delay=2)

        # Idle on the exhaust port
        self.autoculture.pump.changePort(self.exhaust_port)
        self.autoculture.pump.executeChain()
        self.autoculture.pump.waitReady(delay=1)
        sleep(0.5)

        # Log the input volume
        self.fluidic_state['in_volume'] += vol
        
        if self.log:
            # Check if the file exists
            if os.path.exists(self.log_file):
                # Open the CSV file in append mode
                mode = 'a'
            else:
                # Open the CSV file in write mode
                mode = 'w'
            with open(self.log_file, mode, newline='') as csvfile:
                writer = csv.writer(csvfile)
                time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                writer.writerow([time_stamp, self.name, 'Iter:', self.fluidic_state['iteration'],
                                 'Vol In:', self.fluidic_state['in_volume'], 'Vol Out:', self.fluidic_state['out_volume'],
                                 'DISPENSE'])

        # Print status
        time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        msg = '{0} \tDispensed {1} uL to well {2}'  # TODO: of "reagent name"
        print(msg.format(time_stamp, vol, self.name))

    def aspirate(self, vol):
        """ Extract 'vol' [uL] from well """

        vol = float(vol)

        # Check syringe fill
        # TODO make this more intelligent
        self.checkSyringe()
        if self.fluidic_state['syringe_volume'] > vol:
            self.fillSyringe(self.reservoir, 1000-vol)

        # Aspirate - Dry pump
        if self.fluidic_state['aspir_valve']:
            self.aspir_valve.changePort(self.aspir_port)
            self.aspir_valve.executeChain()
            self.aspir_valve.waitReady(delay=0.5)
        self.autoculture.pump.setSpeed(self.speed)
        self.autoculture.pump.aspirate(self.out_port, vol)
        self.autoculture.pump.executeChain()
        self.autoculture.pump.waitReady(delay=2)

        self.autoculture.pump.setSpeed(self.syringeSpeed)
        self.autoculture.pump.dispense(self.exhaust_port, vol)
        self.autoculture.pump.executeChain()
        self.autoculture.pump.waitReady(delay=2)

        # Log the aspirated volume
        self.fluidic_state['out_volume'] += vol
        
        if self.log:
            # Check if the file exists
            if os.path.exists(self.log_file):
                # Open the CSV file in append mode
                mode = 'a'
            else:
                # Open the CSV file in write mode
                mode = 'w'
            with open(self.log_file, mode, newline='') as csvfile:
                writer = csv.writer(csvfile)
                time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                writer.writerow([time_stamp, self.name, 'Iter:', self.fluidic_state['iteration'],
                                 'Vol In:', self.fluidic_state['in_volume'], 'Vol Out:', self.fluidic_state['out_volume'],
                                 'ASPIRATE'])

        # Print status
        time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        msg = '{0} \tAspirated {1} uL from well {2}'  # TODO: of "reagent name"
        print(msg.format(time_stamp, vol, self.name))

    def replenishmentCycle(self, pause=30, source_port=None, in_volume_ul=None, in_port=None, out_volume_ul=None,
                           out_port=None):
        """
        Conduct a replenishment cycle: extract 'out_volume_ul' from 'out_port' and
        dispense 'in_volume_ul' from 'in_port'

        """

        # TODO expand this to accommodate all types of Autocultures

        pause = float(pause)
        source_port = source_port if source_port is not None else self.reservoir.port
        in_volume_ul = in_volume_ul if in_volume_ul is not None else self.in_volume_ul
        in_port = in_port if in_port is not None else self.in_port
        out_volume_ul = out_volume_ul if out_volume_ul is not None else self.out_volume_ul
        out_port = out_port if out_port is not None else self.out_port

        # Aspirate - Dry pump
        if out_volume_ul > 1000:  # We need to break up the aspirations into sets of 1000uL
            i = 0
            while out_volume_ul - (i * 1000) > 1000:
                self.aspirate(1000)
                i += 1
            if out_volume_ul - (i * 1000) > 0:
                self.aspirate(out_volume_ul - (i * 1000))
        else:
            self.aspirate(out_volume_ul)

        # Delay between aspiration and dispensing
        sleep(pause)

        # Dispense - Wet pump
        self.dispense(in_volume_ul)

        # State update
        self.fluidic_state['iteration'] += 1
        #self.fluidic_state['in_volume'] += in_volume_ul
        #self.fluidic_state['out_volume'] += out_volume_ul
        self.statusReport(tag='REPLENISHMENT CYCLE')
        #self.checkSyringe()

    def plunge(self, iter=3, speed=None):
        """ Plunger the aspiration line 'iter' [int] times """

        iter = int(iter)
        if speed is None:
            speed = self.syringeSpeed-2

        # Empty the syringe
        # TODO make this more intelligent
        self.fillSyringe(self.reservoir, 0)

        # Aspirate - Dry pump
        if self.fluidic_state['aspir_valve']:
            self.aspir_valve.changePort(self.aspir_port)
            self.aspir_valve.executeChain()
            self.aspir_valve.waitReady(delay=0.5)
        self.autoculture.pump.setSpeed(speed)

        # Load the executer with plunger pumps
        for i in range(iter):
            self.autoculture.pump.aspirate(self.out_port, 1000)
            self.autoculture.pump.dispense(self.out_port, 1000)

        self.autoculture.pump.executeChain()
        self.autoculture.pump.waitReady(delay=3)

        # Print status
        time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        msg = '{0} \tPlunged {1} {2} times'
        print(msg.format(time_stamp, iter, self.name))

        if self.log:
            # Check if the file exists
            if os.path.exists(self.log_file):
                # Open the CSV file in append mode
                mode = 'a'
            else:
                # Open the CSV file in write mode
                mode = 'w'
            with open(self.log_file, mode, newline='') as csvfile:
                writer = csv.writer(csvfile)
                time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                writer.writerow([time_stamp, self.name, 'Iter:', self.fluidic_state['iteration'],
                                 'Vol In:', self.fluidic_state['in_volume'], 'Vol Out:', self.fluidic_state['out_volume'],
                                 'PLUNGE TRIGGERED'])

    def pull(self, iter=3, speed=None):
        """ Forceably aspirate the aspiration line 'iter' [int] times """

        iter = int(iter)
        if speed is None:
            speed = self.syringeSpeed-2

        # Empty the syringe
        # TODO make this more intelligent
        self.fillSyringe(self.reservoir, 0)

        # Aspirate - Dry pump
        if self.fluidic_state['aspir_valve']:
            self.aspir_valve.changePort(self.aspir_port)
            self.aspir_valve.executeChain()
            self.aspir_valve.waitReady(delay=0.5)
        self.autoculture.pump.setSpeed(speed)

        # Load the executer with plunger pumps
        for i in range(iter):
            self.autoculture.pump.aspirate(self.out_port, 1000)
            self.autoculture.pump.dispense(self.exhaust_port, 1000)

        self.autoculture.pump.executeChain()
        self.autoculture.pump.waitReady(delay=3)

        # Print status
        time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        msg = '{0} \tPulled {1} from {2}'
        print(msg.format(time_stamp, (iter * 1000), self.name))

        if self.log:
            # Check if the file exists
            if os.path.exists(self.log_file):
                # Open the CSV file in append mode
                mode = 'a'
            else:
                # Open the CSV file in write mode
                mode = 'w'
            with open(self.log_file, mode, newline='') as csvfile:
                writer = csv.writer(csvfile)
                time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                writer.writerow([time_stamp, self.name, 'Iter:', self.fluidic_state['iteration'],
                                 'Vol In:', self.fluidic_state['in_volume'], 'Vol Out:', self.fluidic_state['out_volume'],
                                 'PULL TRIGGERED'])

    def checkSyringe(self):
        """
        Check the plunger position
        """

        # State update
        sleep(0.25)  # idle for 0.25 sec
        plunger_pos = self.autoculture.pump.getPlungerPos()
        if plunger_pos is None:
            plunger_pos = 0
        try:
            self.fluidic_state['syringe_volume'] = plunger_pos  # TODO: keep track of volume, this method is crude
            #self.autoculture.state['syringe_volume'] = plunger_pos  # Redundant
        except (ValueError, IndexError) as e:
            print("plunger_pos error")

    def fillSyringe(self, reservoir, vol, speed=None):
        """
        Load the 'pump' syringe with 'vol' [uL] of reagent from the 'reservoir'

        Args:
            'reservoir' (obj) : reference to Reservoir class object containing reagent and port references
            'vol' (float) : volume in uL to draw into the syringe vial
        """

        vol = float(vol)
        if speed is None:
            speed = self.syringeSpeed

        # TODO: control for multiple reservoirs at play: reference current syringe reagent and change reagent if needed

        self.speed = int(speed)

        # Fill syringe
        self.autoculture.pump.setSpeed(speed)
        self.autoculture.pump.changePort(reservoir.port)
        self.autoculture.pump.delayExec(500)
        if vol > 1000 - self.fluidic_state['syringe_volume']:
           self.autoculture.pump.movePlungerAbs(1000)
           vol = 1000 - self.fluidic_state['syringe_volume']
        else: 
            self.autoculture.pump.movePlungerAbs(vol)
        self.autoculture.pump.delayExec(1000)
        delay = self.autoculture.pump.executeChain()
        self.autoculture.pump.waitReady(delay=delay)
        sleep(0.5)  # idle for 0.5 sec

        # Print status
        time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        msg = '{0} \tSyringe was filled with {1} uL'  # TODO: of "reagent name"
        print(msg.format(time_stamp, vol))

        # State update
        self.checkSyringe()

    def statusReport(self, tag=''):
        """Print the contents of self.fluidic_state in table format."""
        time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        msg = '{0} \t{1} \tIter: {2} \tVol In: {3} \tVol Out: {4} \tSyringe Vol: {5}'
        print(msg.format(time_stamp, self.name, self.fluidic_state['iteration'],
                         self.fluidic_state['in_volume'], self.fluidic_state['out_volume'],
                         self.fluidic_state['syringe_volume']))
        
        if self.log:
            # Check if the file exists
            if os.path.exists(self.log_file):
                # Open the CSV file in append mode
                mode = 'a'
            else:
                # Open the CSV file in write mode
                mode = 'w'
            with open(self.log_file, mode, newline='') as csvfile:
                writer = csv.writer(csvfile)
                time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                writer.writerow([time_stamp, self.name, 'Iter:', self.fluidic_state['iteration'],
                                 'Vol In:', self.fluidic_state['in_volume'], 'Vol Out:', self.fluidic_state['out_volume'], tag])
            
            # Upload/append s3 pump.log
            s3_location = self.autoculture.s3_basepath(self.autoculture.experiment_uuid) + self.autoculture.experiment_uuid + '/fluidics/original/logs/'
            if mode == 'a':
                # Upload s3 pump.log
                s3_path = self.autoculture.upload_file(s3_location, self.log_file)
            else:
                # Upload s3 pump.log
                s3_path = self.autoculture.upload_file(s3_location, self.log_file)
                
                # TODO: Append s3 pump.log
                #s3_path = self.append_to_s3_file(s3_location, self.log_file)
    
# TODO: Remake this class in light of MQTT renovations        
class Reservoir:
    """
    Class of reservoir bottles and their attributes. These are generally media bottles in refrigeration that are
    connected to particular pump ports and required at particular times/volumes depending on the experimental design
    """
    # TODO maybe rethink wrapping this into the Autoculture class and conduct regent mixing events there
    def __init__(self, port, volume=None, variety=""):
        """
        Object constructor function, save port and volume

        Args:
            'port' (str) : 'pump' port that the reservoir o
        Kwargs:
            'volume' (float) : initial volume of reagent in the reservoir
            'variety' (str) : name of the reagent in the reservoir
        """
        # TODO: parameters to handle reservoirs connected to valves

        self.port = int(port)
        self.volume = float(volume)
        self.variety = str(variety)

# TODO: Remake this class in light of MQTT renovations
class DrugChannel:
    """
    Class to operate simultaneous dispensing and aspirating through the "drug channel" of the PDMS connectoid module. 
    """

    # TODO: this is a v2 exclusive program

    def __init__(self, autoculture, reservoir, in_port, out_port, exhaust_port, in_volume_ul=0, out_volume_ul=0, in_speed=40, out_speed=38, disp_valve=None, disp_port=None,
                 aspir_valve=None, aspir_port=None, name=''):
        """
        Object constructor function, save pump and valve references

        Args:
            'autoculture' (obj) : reference to Autoculture class object containing references to the pumps and valves
            'reservoir' (obj) : reference to Reservoir class object containing reagent ("drug") and port references
            `in_port' (int) : 'pump' port for reagent delivery (to well)
            'out_port' (int) : 'pump' port for reagent extraction (to waste)
            'exhaust_port' (int) : 'pump' port for non-fluidic, air operations
        Kwargs:
            'in_volume_ul' (float) : absolute volume (uL) to deliver
            'out_volume_ul' (float) : absolute volume (uL) to aspirate
            'in_speed' (int) : dispensing syringe speed
            'out_speed' (int) : dispensing syringe speed
            'disp_valve' (obj) : reference to dispensing valve object
            `disp_port' (int) : 'disp_valve' port for reagent delivery (to well)
            'aspir_valve' (obj) : reference to aspirating valve object
            'aspir_port' (int) : 'aspir_vavle' port for reagent extraction (to waste)
            `name' (str) : give a label to the well
        """
        self.autoculture = autoculture
        self.reservoir = reservoir
        self.in_port = int(in_port)
        self.out_port = int(out_port)
        self.exhaust_port = int(exhaust_port)
        self.in_volume_ul = in_volume_ul
        self.out_volume_ul = out_volume_ul
        self.in_speed = int(in_speed)
        self.out_speed = int(out_speed)
        self.name = str(name)

        # State
        self.fluidic_state = {
            'iteration': 0,
            'in_volume': 0,
            'out_volume': 0,
            'disp_valve': False,
            'aspir_valve': False,
            'syringe_volume': 0
        }
        self.disp_valve = disp_valve
        if self.disp_valve is not None:
            self.fluidic_state['disp_valve'] = True
        self.disp_port = disp_port
        self.aspir_valve = aspir_valve
        if self.aspir_valve is not None:
            self.fluidic_state['aspir_valve'] = True
        self.aspir_port = aspir_port

        # Speed lookup table { "speed value" : "uL per sec"}
        self.speedTable = {
            0 : 1102,
            23 : 5.51,
            26 : 3.86,
            30 : 1.65,
            36 : 0.331,
            37 : 0.276,
            38 : 0.220,
            39 : 0.165,
            40 : 0.110,
            41 : 0.0551,
            43 : 0.0441,
            45 : 0.0331,
            50 : 0.00551
        }

    def flow(self, in_volume_ul=None, out_volume_ul=None, in_speed=None, out_speed=None, pause=60):
        """
        Flow "drug reagent" through the Drug Channel

        Kwargs:
            'in_volume_ul' (float) : absolute volume (uL) to deliver
            'out_volume_ul' (float) : absolute volume (uL) to aspirate
            'in_speed' (int) : dispensing syringe speed
            'out_speed' (int) : dispensing syringe speed
        """

        in_volume_ul = float(in_volume_ul) if in_volume_ul is not None else self.in_volume_ul
        out_volume_ul = float(out_volume_ul) if out_volume_ul is not None else self.out_volume_ul
        in_speed = int(in_speed) if in_speed is not None else self.in_speed
        out_speed = int(out_speed) if out_speed is not None else self.out_speed

        # Empty the dispensing syringe and fill it with drug reagent
        print("Empty the dispensing syringe")
        self.autoculture.disp_pump.setSpeed(10)  # This is fast enough
        self.autoculture.disp_pump.changePort(self.exhaust_port)
        self.autoculture.disp_pump.delayExec(500)
        self.autoculture.disp_pump.movePlungerAbs(0)
        self.autoculture.disp_pump.delayExec(500)
        self.autoculture.disp_pump.changePort(self.reservoir.port)
        self.autoculture.disp_pump.delayExec(500)
        self.autoculture.disp_pump.movePlungerAbs(in_volume_ul)
        delay = self.autoculture.disp_pump.executeChain()

        # Zero the aspirating syringe to ready for aspiration
        print("Zero the aspirating syringe")
        self.autoculture.aspir_pump.setSpeed(10)  # This is fast enough
        self.autoculture.aspir_pump.changePort(self.exhaust_port)
        self.autoculture.aspir_pump.delayExec(500)
        self.autoculture.aspir_pump.movePlungerAbs(0)
        delay = self.autoculture.aspir_pump.executeChain()
        self.autoculture.aspir_pump.waitReady(delay=delay)
        time.sleep(2)  # idle for 2 seconds

        # Begin aspiration
        print("Begin aspirating")
        self.autoculture.aspir_pump.setSpeed(20)
        self.autoculture.aspir_pump.changePort(self.out_port)
        self.autoculture.aspir_pump.delayExec(100)
        self.autoculture.aspir_pump.movePlungerAbs(3)  # Prime the aspirator
        self.autoculture.aspir_pump.setSpeed(out_speed)
        self.autoculture.aspir_pump.movePlungerAbs(out_volume_ul + 3)
        delay = self.autoculture.aspir_pump.executeChain()
        time.sleep(pause)  # idle for 'pause' seconds

        # Begin dispensing
        print("Begin dispensing")
        self.autoculture.disp_pump.setSpeed(in_speed)
        self.autoculture.disp_pump.changePort(self.in_port)
        self.autoculture.disp_pump.delayExec(500)
        self.autoculture.disp_pump.movePlungerAbs(0)
        self.autoculture.disp_pump.executeChain()
        self.autoculture.aspir_pump.waitReady(delay=delay)

        # Notice completion
        #time.sleep(out_volume_ul / self.speedTable[out_speed])
        print("Complete")

# Old programs
# Autoculture Scheduler Programs
# TODO: Remake these difinitions in light of MQTT renovations
def scheduleWellList(wellList):
    for well in wellList:
        schedule.every((well.period_s/60)).minutes.do(well.replenishmentCycle)

def scheduleOne(well):
    schedule.every(3).hours.at(":08").do(well.replenishmentCycle)
    #schedule.every(1).minutes.do(well.replenishmentCycle)

def scheduleOneFast(well, period=20):
    schedule.every(period).seconds.do(well.replenishmentCycle, pause=2)

# Autoculture Plate Configurations
def feedFrequency(experiment_params, autoculture):
    """ Return a 'wells_list' appended with the Feed Frequency list """

    # TODO: this is unfinished

    # Zero the list
    experiment_params['wells_list'] = []

    # Pull parameters from the autoculture object
    centris_pump = autoculture.centris_pump

    # Line 1: 15-min [A6]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*15,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=1,
                                                aspir_valve=aspir_valve_12,
                                                aspir_port=1,
                                                name="15-min [A6]"))

    # Line 2: 15-min [A5]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*15,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=2,
                                                aspir_valve=aspir_valve_12,
                                                aspir_port=2,
                                                name="15-min [A5]"))

    # Line 3: 15-min [A4]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*15,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=3,
                                                aspir_valve=aspir_valve_12,
                                                aspir_port=3,
                                                name="15-min [A4]"))

    # Line 4: 15-min [A3]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*15,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=4,
                                                aspir_valve=aspir_valve_12,
                                                aspir_port=4,
                                                name="15-min [A3]"))

    # Line 5: 15-min [A2]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*15,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=5,
                                                aspir_valve=aspir_valve_12,
                                                aspir_port=5,
                                                name="15-min [A2]"))

    # Line 6: 15-min [A1]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*15,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=6,
                                                aspir_valve=aspir_valve_12,
                                                aspir_port=6,
                                                name="15-min [A1]"))

    # Line 7: 1-hour [B6]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=7,
                                                aspir_valve=aspir_valve_12,
                                                aspir_port=7,
                                                name="1-hour [B6]"))

    # Line 8: 1-hour [B5]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=8,
                                                aspir_valve=aspir_valve_12,
                                                aspir_port=8,
                                                name="1-hour [B5]"))

    # Line 9: 1-hour [B4]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=9,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=10,
                                                name="1-hour [B4]"))

    # Line 10: 1-hour [B3]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=10,
                                                aspir_valve=aspir_valve_12,
                                                aspir_port=10,
                                                name="1-hour [B3]"))

    # Line 11: 1-hour [B2]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=11,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=11,
                                                name="1-hour [B2]"))

    # Line 12: 1-hour [B1]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=2,
                                                out_port=5,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_12,
                                                disp_port=12,
                                                aspir_valve=aspir_valve_12,
                                                aspir_port=12,
                                                name="1-hour [B1]"))

    # Line 13: 6-hour [C6]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=1,
                                                out_port=6,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60*6,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_24,
                                                disp_port=1,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=1,
                                                name="6-hour [C6]"))

    # Line 14: 6-hour [C5]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=1,
                                                out_port=6,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60*6,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_24,
                                                disp_port=2,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=2,
                                                name="6-hour [C5]"))

    # Line 15: 6-hour [C4]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=1,
                                                out_port=6,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60*6,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_24,
                                                disp_port=3,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=3,
                                                name="6-hour [C4]"))

    # Line 16: 6-hour [C3]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=1,
                                                out_port=6,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60*6,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_24,
                                                disp_port=4,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=4,
                                                name="6-hour [C3]"))

    # Line 17: 6-hour [C2]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=1,
                                                out_port=6,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60*6,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_24,
                                                disp_port=5,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=5,
                                                name="6-hour [C2]"))

    # Line 18: 6-hour [C1]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=1,
                                                out_port=6,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60*6,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_24,
                                                disp_port=6,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=6,
                                                name="6-hour [C1]"))

    # Line 19: 24-hour [D6]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=1,
                                                out_port=6,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60*24,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_24,
                                                disp_port=7,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=7,
                                                name="24-hour [D6]"))

    # Line 20: 24-hour [D5]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=1,
                                                out_port=6,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60*24,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_24,
                                                disp_port=8,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=8,
                                                name="24-hour [D5]"))

    # Line 21: 24-hour [D4]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=1,
                                                out_port=6,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60*24,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_24,
                                                disp_port=9,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=9,
                                                name="24-hour [D4]"))

    # Line 22: 1-hour [B4]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=1,
                                                out_port=6,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_24,
                                                disp_port=10,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=10,
                                                name="1-hour [B2]"))

    # Line 23: 1-hour [B2]
    #experiment_params['wells_list'].append(Well(pump=centris_pump,
    #                                            source_port=3,
    #                                            in_port=1,
    #                                            out_port=6,
    #                                            exhaust_port=4,
    #                                            in_volume_ul=70,
    #                                            out_volume_ul=700,
    #                                            period_s=60*60,
    #                                            tic=experiment_params['tic'],
    #                                            disp_valve=disp_valve_24,
    #                                            disp_port=11,
    #                                            aspir_valve=aspir_valve_24,
    #                                            aspir_port=11,
    #                                            name="1-hour [B2]"))

    # Line 24: 24-hour [D1]
    experiment_params['wells_list'].append(Well(pump=centris_pump,
                                                source_port=3,
                                                in_port=1,
                                                out_port=6,
                                                exhaust_port=4,
                                                in_volume_ul=70,
                                                out_volume_ul=700,
                                                period_s=60*60*24,
                                                tic=experiment_params['tic'],
                                                disp_valve=disp_valve_24,
                                                disp_port=12,
                                                aspir_valve=aspir_valve_24,
                                                aspir_port=12,
                                                name="24-hour [D1]"))

# TODO methods for setting schedules of all wells (gradient functions)

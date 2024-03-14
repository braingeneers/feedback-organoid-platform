import os
import sys
import time
from datetime import datetime,  timedelta, timezone
import re

#Maxwell functions
try:
    import maxlab                                       
    import maxlab.system
    import maxlab.chip
    import maxlab.util
    import maxlab.saving
except:
    print("MaxLab not found, running without MaxLab")

sys.path.append(os.path.abspath(os.path.join('..')))
from braingeneers.iot import Device

# Define paths
MXWBIO_DATA_PATH = "/home/mxwbio/Data/integrated_experiment"
MXWBIO_CONFIGS_PATH = "/home/mxwbio/configs"
MXWBIO_MAXLAB_PATH = "/home/mxwbio/MaxLab/bin"
SMARTPLUG_TOPIC = "smartplug/telemetry"

class MaxOne(Device): 
    """ MaxOne
    MQTT automation of MaxWell workflows
    """
    def __init__(self, device_name, smartplug, data_path=MXWBIO_DATA_PATH, 
                config_path=MXWBIO_CONFIGS_PATH, record_only_spikes=False, gain=512):
        
        #initialize variables accessed by parent functions before calling super init
        self.chip = "None"
        self.config = "None"

        super().__init__(device_name=device_name, device_type = "Other", primed_default=True)

        self.powered_on = False
        self.smartplug = smartplug

        self.recording_length = 0 #minutes
        self.latest_recording_name = None

        # can be hard drive or disk: "/home/mxwbio/Data/integrated_experiment" , "/media/mxwbio/HD"  
        self.data_path = data_path

        self.record_only_spikes = record_only_spikes
        self.gain = gain

        # Child must define this when inheriting MqttDevice parent
        self.device_specific_handlers.update({ 
            "SWAP": self.handle_swap,
            "LIST": self.handle_list,
            "RECORD": self.handle_record,
            #"SETTINGS": self.handle_settings, 
            #"ACTIVITY_SCAN" : self.handle_activity_scan,
            #"SURFACE_SCAN" : self.handle_surface_scan,
        })

        return

        
    @property
    def device_state(self):
        return { **super().device_state,
                "CHIP": self.chip,
                "CONFIG": self.config }


    def is_primed(self):
        return self.primed_default

    #for threading later: while not self.stop_event.is_set() and datetime.now() < twiddle_until:

    def updateParams(self, data_path=MXWBIO_DATA_PATH, config= MXWBIO_CONFIGS_PATH + "test_small.cfg",
                         record_only_spikes=False, gain=512):
        self.data_path = data_path
        self.config = config

        self.gain =  gain
        self.record_only_spikes = record_only_spikes


    # Helper functions ========================================================
    def turn_on(self):
        print("Turning on ephys. Please wait 30 seconds.")    
        self.mb.publish_message(topic=f"{SMARTPLUG_TOPIC}/{self.smartplug}/cmnd/POWER", message="ON")
        time.sleep(14)
        os.system(f"{MXWBIO_MAXLAB_PATH}/mxwserver.sh &") # turn on maxwell server
        os.system(f"{MXWBIO_MAXLAB_PATH}/scope.sh &") # turn on maxwell server
        time.sleep(14)
        print("ephys launched!")
        self.powered_on = True

    def turn_off(self):
        print("Turning off ephys")
        try:
            os.system(f"{MXWBIO_MAXLAB_PATH}/killall.sh") # shut down MaxOne server
        except:
            print("MaxOne programs failed to terminate")
        self.mb.publish_message(topic=f"{SMARTPLUG_TOPIC}/{self.smartplug}/cmnd/POWER", message="OFF")
        self.powered_on = False

    # Helper functions ========================================================
    def handle_swap(self, topic, message):
        if self.is_my_topic(topic) and message["COMMAND"] == "SWAP-REQUEST":

            #look for config:
            config_found = False

            #check if it's s3 link and file exists on s3
            if message["CONFIG"].startswith("s3://"):
                print("config is s3 link")
                if self.check_file_exists_s3(message["CONFIG"]):
                    print("s3 link exists!")
                    config_found = True
                    self.config = self.download_file(message["CONFIG"], MXWBIO_CONFIGS_PATH)
            else: #check if it's a local file and it exists
                if os.path.isfile(f'{MXWBIO_CONFIGS_PATH}/{message["CONFIG"]}'):
                    print("local config exists!")
                    self.config = f'{MXWBIO_CONFIGS_PATH}/{message["CONFIG"]}'
                    config_found = True

            if config_found: #if config found, swap:
                self.chip = message["CHIP_ID"]
                self.update_state(self.state)
            else:
                print("config not found")
                self.mb.publish_message(topic= self.generate_response_topic("SWAP", "ERROR"),
                                        message= { "COMMAND": "SWAP-ERROR",
                                                    "ERROR": f"Config not found: {message['CONFIG']}",
                                                    "FROM": self.device_name
                                                })

        return


    def handle_list(self, topic, message):
        if self.is_my_topic(topic) and message["COMMAND"] == "LIST-REQUEST":
                self.update_state(self.state)
                self.mb.publish_message(topic=self.generate_response_topic("LIST", "RESPONSE"),
                                        message= { "COMMAND": "LIST-RESPONSE",
                                                    "CHIP_ID": self.chip,
                                                    "CONFIG" : self.config,
                                                    "FROM": self.device_name})
        return    

    def handle_record(self, topic, message):

        if self.is_my_topic(topic) and message["COMMAND"] == "RECORD-REQUEST":
        # Do maxone recording here for min = message["RECORD"] #10 if message {"RECORD": 10}

            if message["CHIP_ID"] != self.chip:
                self.mb.publish_message(topic=self.generate_response_topic("RECORD", "ERROR"),
                                        message= { "COMMAND": "RECORD-ERROR",
                                            "ERROR": f"Invalid chip id {message['CHIP_ID']}: current chip on headstage is {self.chip}",
                                            "FROM": self.device_name})
                return

            file_name = self.get_curr_timestamp() + "chip" + message["CHIP_ID"]
            self.recording_length = int(message["MINUTES"])*60

            self.turn_on()
            #broadcast to all devices that MaxOne is recording
            pause_time = str(self.recording_length + 2*60)
            self.mb.publish_message( topic=self.generate_response_topic() + "/PAUSE/REQUEST", 
                                    message={"COMMAND": "PAUSE-REQUEST", 
                                    "FROM": self.device_name, 
                                    "SECONDS" : pause_time}) #add one min extra for autoculture time buffer

            # if not self.prepared:
            #     raise Exception(f"Set Recording Settings! Run prepareRecording to set: data_path, config, record_only_spikes, minutes, and gain")
            #print("recording electrodes for "+str(recording_length)+" seconds")
            maxlab.util.initialize()                                # Initialize Maxwell
            maxlab.send( maxlab.chip.Amplifier().set_gain(self.gain) )   # Set Gain

            array = maxlab.chip.Array('online')     # Load Electrodes
            array.reset()
            array.load_config( self.config )
            #array.select_electrodes( electrodes )
            #array.route()                           #This might be necessary, but not sure
            array.download()
            maxlab.util.offset()   

            s = maxlab.saving.Saving()             # Set up file and wells for recording, 
            s.open_directory(self.data_path)           
            s.set_legacy_format(False) #David/Sury confirmed no legacy format
            s.group_delete_all()

            # if self.record_only_spikes == False:             # start recording and save results
            #     s.group_define(0, "routed")

            s.group_define(0, "routed")
            s.start_file(file_name)

            #offset again just in case
            maxlab.util.offset()   

            #print("Recording Started")
            s.start_recording([0]) #range(1) )

            record_until = datetime.now() + timedelta(seconds=int(self.recording_length))
            while not self.stop_event.is_set() and datetime.now() < record_until:
                time.sleep(1)

            #time.sleep(self.recording_length)
            
            #print("Saving Results")
            s.stop_recording()
            s.stop_file()
            s.group_delete_all()
            print("Finished")
            self.turn_off()
            print("Turned off ephys")

            print(f"Filename: data_path: {self.data_path}, MXW_Path: {MXWBIO_DATA_PATH}, file_name {file_name}")

            self.latest_recording_name = f'{MXWBIO_DATA_PATH}/{file_name}.raw.h5'
            print("MaxWell latest recording name: " + self.latest_recording_name)

            #broadcast to all devices that MaxOne is done recording
            self.mb.publish_message(topic=self.generate_response_topic("RECORD", "COMPLETE"), message={"COMMAND":"RECORD-COMPLETE"})


            filepath_prefix = ""
            #check if self.experiment uuid counatins -e- using regex
            regex_pattern = r"\d{4}-\d{2}-\d{2}-e-"
            if re.search(regex_pattern, self.experiment_uuid):
                filepath_prefix = "original/data"
            else: #-efi- or other subset combos except -e-
                filepath_prefix = "ephys/original/data"

            s3_location = self.s3_basepath(self.experiment_uuid) + self.experiment_uuid + '/' + filepath_prefix + '/' #+ self.chip + '/'
        
            #s3_basepath
            topic = f"{self.root_topic}/{self.experiment_uuid}/{self.logging_token}/experiments/upload"
            #topic = f"experiments/upload",
            #topic = f"#/experiments/upload",



            message = { "COMMAND": "SPIKESORT-REQUEST",
                        "uuid": self.experiment_uuid,
                        "stitch" : "False",
                        "ephys_experiments": 
                                            {file_name: 
                                                {"blocks": [
                                                            {"path": f"{filepath_prefix}/{file_name}.raw.h5"}
                                                            #spike sort output to: {"path": f"ephys/derived/kilosort2/{self.chip}/{file_name}.raw.h5"}
                                                            ]
                                                    }
                                            }
                        }

                #mb.publish_message(topic=topic, message=metadata, confirm_receipt=True)   


            print(f"Going to upload .. s3 location: {s3_location}, self.latest_recording_name: {self.latest_recording_name}")

            #upload to s3, launch upload job in the background and publish message on topic upon completion
            self.upload_file(s3_location, self.latest_recording_name, delete_local=True, announce_completion = (topic, message))
            #TODO: do we need an option for upload to block downstream code execution until upload is finished?
            # Right now we assume it doesn't block



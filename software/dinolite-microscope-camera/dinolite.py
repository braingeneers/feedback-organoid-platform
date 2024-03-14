# pip3 install opencv-python
# sudo apt-get install uvcdynctrl 
import cv2, os, subprocess, time
import sys
from datetime import datetime, timezone
import pytz
from pytz import timezone, utc 
import sys

sys.path.append(os.path.abspath(os.path.join('..')))

from braingeneers.iot import Device

class DinoLite(Device): 
    """ Dinolite
    Class for overheard imaging of organoid in the incubator
    """

    def __init__(self, device_name, chip_id = "00000", cap_num = 0, UUID = None):

        self.camera_mapping = {}

        super().__init__(device_name=device_name, device_type = "Other", primed_default=True)

        print("Make sure no other programs are using the camera")
        self.camera = None #cv2.VideoCapture(cap_num)
        
        self.latest_image_name = ""

        # Child must define this when inheriting MqttDevice parent
        self.device_specific_handlers.update({ 
            #"CALIBRATE": self.handle_calibrate,
            "ADD": self.handle_add,
            "REMOVE":  self.handle_remove,
            "LIST": self.handle_list,
            "PICTURE": self.handle_picture,
        })

        return

    @property
    def device_state(self):
        return {
           **super().device_state,
            "PAIRS": self.camera_mapping 
        }
    
    # Helper functions ========================================================

    def set_exposure(self):
        os.system('DN_DS_Ctrl.exe AE off') #doesn't work, use open CV settings later to test
        cmnd = 'DN_DS_Ctrl.exe EV 20'  
        return os.system(cmnd)
        return

    def lights_on(self, value = 1, cam_index = 0):
        cmnd = f"DN_DS_Ctrl.exe FLCLevel {str(value)} -d video{str(cam_index)}"
        #os.system('DN_DS_Ctrl.exe FLCLevel 1')
        return os.system(cmnd) # may need to remove '-d video4' if dinolite is on video0
        return

    def lights_off(self):
        cmnd = 'DN_DS_Ctrl.exe LED off'
        #print(cmnd)
        return os.system(cmnd) # may need to remove '-d video4' if dinolite is on video0
        return

    def close(self):
        if self.camera:
            print("Released the camera")
            self.camera.release()
        self.camera = None
        time.sleep(1)
        return

    def take_picture(self, chip = "00000", text_note = "", UUID = ""):

        if UUID == "":
                UUID = self.experiment_uuid

        index = self.camera_mapping[chip]
        print(f"In take_picture(): Taking pictue of chip {chip} on index {index}")

        self.camera = cv2.VideoCapture(int(index), cv2.CAP_DSHOW)
        time.sleep(2)

        if not self.camera.isOpened():
            print("Error: Camera not initialized!")
            return

        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

        # Setting the resolution first
        result = self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1600)
        if not result:
            print("Failed to set frame width.")
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1200)
        time.sleep(1)

        #self.set_exposure()
        time.sleep(3) #??

        return_value, image = self.camera.read()
        print("READ, now the return value is:", return_value)

        self.lights_on(1, index)
        time.sleep(3)

        if return_value:
            width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
            print(f"Image resolution: {width}x{height}")

            self.time = (datetime.now(tz=pytz.timezone('US/Pacific')).strftime('%Y_%m_%d_T%H%M%S_')) 

            if text_note != "":
                    text_note = "-" + text_note

            self.latest_image_name = self.time + 'dinolite-chip-' + chip +  text_note + '.png'

            writepath = self.path + '/' + self.latest_image_name
            print(writepath)
            cv2.imwrite(writepath, image)
            time.sleep(1)
            
            # upload picture taken
            print("UUID:", UUID)
            s3_location = f"{self.s3_basepath(UUID)}{UUID}/dinolite/images/{chip}/"
            print(f"s3_location: {s3_location}")
            #s3_path = self.upload_file(s3_location, self.latest_image_name)
            s3_path = self._direct_upload_file(s3_location, self.latest_image_name, False, None)

        else:
            print("Picture failed to be taken! Check camera connection")
            s3_path = None


        self.lights_off()
        self.close()

        return s3_path

    # ========================================================

    def handle_list(self, topic, message):
        if self.is_my_topic(topic) and message["COMMAND"] == "LIST-REQUEST":
            self.update_state(self.state)
            self.mb.publish_message(topic=topic,
                                    message= { "COMMAND": "LIST-RESPONSE",
                                                "PAIRS": self.camera_mapping,
                                                "FROM": self.device_name})


    def handle_add(self, topic, message): 
        if self.is_my_topic(topic) and message["COMMAND"] == "ADD-REQUEST":

            # Check for repeated keys with different values
            pairs_values = list(message["PAIRS"].values())

            #Caution: If you have the same chip mapped to multiple cameras accidentally, it will choose one index (last one in the list)
            #Caution: If you enter the same chip id already stored in the mapping, it will overwrite the previous mapping
           
            # Check if the same value is assigned to multiple keys
            values = list(self.camera_mapping.values())
            for v in message["PAIRS"].values():
                if values.count(v) + list(message["PAIRS"].values()).count(v) > 1:
                    print("Cannot assign camera index to multiple chips.")
                    self.mb.publish_message(topic=self.generate_response_topic("ADD", "ERROR"),
                                            message= {
                                                "COMMAND": "ADD-ERROR",
                                                "ERROR": "Cannot assign the same camera index to multiple chips",
                                                "FROM": self.device_name
                                            })
                    return


            self.camera_mapping.update(message["PAIRS"])
            self.update_state(self.state)
            return


    def handle_remove(self, topic, message): 
        if self.is_my_topic(topic) and message["COMMAND"] == "REMOVE-REQUEST":
            
            # Iterate over the chips to be removed
            for chip in message["PAIRS"].keys():
                # Check if chip exists in the camera_mapping
                if chip in self.camera_mapping:
                    self.camera_mapping.pop(chip)
                else:
                    print(f"No such chip: {chip} in mapping.")
                    # Optionally, send an error message if your system supports it.
                    self.mb.publish_message(topic=self.generate_response_topic("REMOVE", "ERROR"),
                                            message={
                                                "COMMAND": "REMOVE-ERROR",
                                                "ERROR": f"No such chip in mapping: {chip}",
                                                "FROM": self.device_name
                                            })
            return


    def handle_picture(self, topic, message):
        if self.is_my_topic(topic) and message["COMMAND"] == "PICTURE-REQUEST":

            for chip in message["CHIP_ID"]:     
                # Check if chip exists in the camera_mapping
                if chip in self.camera_mapping:
                    try:
                        print(f"Taking picture of chip: {chip} on index {self.camera_mapping[chip]}")
                        #take picture and upload to s3
                        s3_path = self.take_picture(chip)
                        self.mb.publish_message(topic=self.root_topic + '/'+ self.experiment_uuid + '/' + self.logging_token + '/estimator/ESTIMATE/REQUEST',
                                                message={ "COMMAND": "ESTIMATE-REQUEST",
                                                            "PICTURE": s3_path, 
                                                            "TYPE": "well",
                                                            "CHIP_ID": message["CHIP_ID"],
                                                            "INDEX": "None",
                                                            "UUID": self.experiment_uuid,
                                                            "FROM": self.device_name,
                                                            "FOR": message["FROM"]
                                                        })
                    except Exception as e:
                        print(f"ERROR taking picture: {e}")
                        self.mb.publish_message(topic=self.generate_response_topic("PICTURE", "ERROR"),
                                                message={
                                                    "COMMAND": "PICTURE-ERROR",
                                                    "ERROR": f"Chip {chip} picture failed. See device log for details",
                                                    "FROM": self.device_name
                                                })
                else:
                    print(f"No such chip: {chip} in mapping.")
                    # Optionally, send an error message if your system supports it.
                    self.mb.publish_message(topic=self.generate_response_topic("PICTURE", "ERROR"),
                                            message={
                                                "COMMAND": "PICTURE-ERROR",
                                                "ERROR": f"No such chip in mapping: {chip}",
                                                "FROM": self.device_name
                                            })
            return
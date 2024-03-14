import cv2, os, subprocess, time
from datetime import datetime, timezone
import pytz
from pytz import timezone, utc 
import sys
import subprocess

sys.path.append(os.path.abspath(os.path.join('..')))
from braingeneers.iot import Device


class PiCamera_(Device): 
    
    """ Pi Camera
    Class for Raspberry Pi imaging for fluid level detection
    """
    def __init__(self, device_name, cam_focus, exposure, estimation_type):
        super().__init__(device_name=device_name, device_type = "Other", primed_default=True)
    
        self.camera = None
        self.latest_image_name = None
        self.focus = cam_focus
        self.exposure = exposure
        self.estimation_type = estimation_type

        self.device_specific_handlers.update({
            "PICTURE": self.handle_picture
        })

        return

    def take_picture(self, text_note="", UUID="", burst_count=1):

        self.time = datetime.now(pytz.timezone('US/Pacific')).strftime('%Y_%m_%d_T%H%M%S_')

        folder_path = os.path.join(text_note, self.estimation_type)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        image_name_1 = f"{self.time}{self.device_name}-f-340-e-47.jpg"
        origin_path_1 = os.path.join(folder_path, image_name_1)

        for index in range(3):
            device_arg = f"--device=/dev/video{index}"
            try:
                subprocess.run(["v4l2-ctl", device_arg, "--set-ctrl", "focus_automatic_continuous=0"], check=True)
                camera_index = index
                camera_initialized = True
                break
            except subprocess.CalledProcessError:
                continue

        if camera_initialized:
            device_arg = f"--device=/dev/video{camera_index}"
            subprocess.run(["v4l2-ctl", device_arg, "--set-ctrl", "focus_automatic_continuous=0"], check=True)
            subprocess.run(["v4l2-ctl", device_arg, "--set-ctrl", "focus_absolute=330"], check=True)
            subprocess.run(["v4l2-ctl", device_arg, "--set-ctrl", "exposure_time_absolute=60"], check=True)


            for _ in range(5):
                ffmpeg_command = [
                    "ffmpeg", 
                    "-f", "v4l2", 
                    "-input_format", "mjpeg", 
                    "-video_size", "2592x1944", 
                    "-i", f"/dev/video{camera_index}", 
                    "-vframes", "1", 
                    "-f", "null",
                    "-"
                ]
                subprocess.run(ffmpeg_command, check=True)
                time.sleep(0.5) 

            ffmpeg_command = [
                "ffmpeg", 
                "-f", "v4l2", 
                "-input_format", "mjpeg", 
                "-video_size", "2592x1944", 
                "-i", f"/dev/video{camera_index}", 
                "-vframes", "1",
                origin_path_1
            ]
            subprocess.run(ffmpeg_command, check=True)

            s3_location = self.s3_basepath(UUID) + f"{UUID}/output-fluid/images/{text_note}/{self.estimation_type}/"
            s3_path = self._direct_upload_file(s3_location, origin_path_1, False, None)
            
            print(f"In take_picture, uploaded image to {s3_path}")

            return s3_path

        else:
            print("Camera index was not found at indexes 0,1 or 2")
            return None

    def handle_picture(self, topic, message):

        links_dict = {}

        if all(x not in message["TYPE"] for x in ["volume"]):
            self.mb.publish_message(topic= self.generate_response_topic("PICTURE", "ERROR"),
                            message={ "COMMAND": "PICTURE-ERROR",
                                    "ERROR": "INVALID TYPE, value must be a list contaning 'volume'",    
                                    "FOR": message["FROM"]})

        if ("volume" in message["TYPE"]):
            self.estimation_type = "volume"
            s3_path = self.take_picture(text_note=message["CHIP_ID"], UUID = self.experiment_uuid, burst_count=1)
            links_dict["VOL"] = [s3_path]

        self.mb.publish_message(topic= self.generate_response_topic() + '/estimator/ESTIMATE/REQUEST',
                            message={ "COMMAND": "ESTIMATE-REQUEST",
                                    "PICTURE": links_dict, 
                                    "TYPE": message["TYPE"],
                                    "CHIP_ID": message["CHIP_ID"],
                                    "INDEX": message["INDEX"],
                                    "UUID": self.experiment_uuid,
                                    "FROM": self.device_name,
                                    "FOR": message["FROM"]})

        print("ALL GOOD")

    def close(self):
        if self.camera:
            print("Released the camera")
            self.camera.release()
        self.camera = None
        time.sleep(1)
        return
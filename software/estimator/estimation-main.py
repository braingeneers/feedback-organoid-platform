#Usage Example: 
#conda activate bgrenv
#python3 estimation-main.py

import os
import glob
import time
import uuid
from braingeneers.iot import messaging # Assuming you have this module imported elsewhere
from volumeEstimation import VolumeEstimation  # Assuming this class is part of a different module

DEVICE_NAME = "estimator"
MQTT_DEVICE_SUBSCRIBE_TOPIC = f"telemetry/+/log/{DEVICE_NAME}/+/REQUEST" # <-- device listens to any experiments involving DEVICE_NAME

if __name__ == '__main__':

    def response_topic(recieve_topic, response_cmnd_key = None, response_cmnd_value = None):
        topic_elements = recieve_topic.split("/")
        topic_elements[-2] = response_cmnd_key
        topic_elements[-1] = response_cmnd_value
        return '/'.join(topic_elements)

    def download_last_file(s3_path):
        endpoint = '--endpoint https://s3-west.nrp-nautilus.io s3'
        command = f'aws {endpoint} cp {s3_path} .'
        print(f"Running: {command}")
        os.system(command)
        list_of_files = glob.glob("./*.jpg")
        return max(list_of_files, key=os.path.getctime) # latest file


    def handle_estimate(topic, message):
        if message["COMMAND"] == 'ESTIMATE-REQUEST':
            print("Got Estimate Request!")
            mb.publish_message(topic=response_topic(topic, "ESTIMATE", "ACK"),message={"COMMAND":"ESTIMATE-ACK"})

            try:
                if all(x not in message["TYPE"] for x in ["volume"]):
                    mb.publish_message(topic= response_topic(topic, "ESTIMATE", "ERROR"),
                                    message={ "COMMAND": "ESTIMATE-ERROR",
                                            "ERROR": "Invalid message key/values'",    
                                            "FOR": message["FROM"]})
            
                if message["INDEX"] not in ["RIGHT", "LEFT"]:
                    mb.publish_message(topic= response_topic(topic, "ESTIMATE", "ERROR"),
                                    message={ "COMMAND": "ESTIMATE-ERROR",
                                            "ERROR": "Invalid index value, must be 'RIGHT' or 'LEFT'",    
                                            "FOR": message["FROM"]})

                # If we got this far, do the estimation
                response_message= {"COMMAND": "FEEDBACK-REQUEST",
                                    "CHIP_ID": message["CHIP_ID"],
                                    "INDEX": message["INDEX"], 
                                    "FROM": "estimator"}


                if ("volume" in message["TYPE"]):
                    print("Estimating volume...")
                    # Download image from AWS
                    s3_path = message["PICTURE"]["VOL"][0]
                    im_path = download_last_file(s3_path)
                    # Initiate object by defining which side will be evaluated. Enter "right" or "left"
                    obj_vol = VolumeEstimation(message["INDEX"])
                    vol = obj_vol.volume_estimation(im_path) #returns single value of "RIGHT" or "LEFT" volume
                    response_message["VOL"] = str(vol)
                    response_message["IMAGE"] = str(im_path)

                if ("well" in message["TYPE"]):
                    print("Estimating well...")

    

                # Publish task COMPLETE
                mb.publish_message(topic=response_topic(topic, "ESTIMATE", "COMPLETE"),message={"COMMAND":"ESTIMATE-COMPLETE"})
                
                # Publish estimation results
                mb.publish_message(topic=f'telemetry/{message["UUID"]}/log/{message["FOR"]}/FEEDBACK/REQUEST', message=response_message)
            
            except (ValueError, IndexError) as e:
                print("Error occurred: {e}")
                # Publish task OUTOFBOUNDS
                mb.publish_message(topic=response_topic(topic, "ESTIMATE", "OUTOFBOUNDS"), message={"COMMAND": "ESTIMATE-OUTOFBOUNDS"})


    def handle_ping(topic, message):
        if message["COMMAND"] == 'PING-REQUEST':
            mb.publish_message(topic=response_topic(topic, "PING", "RESPONSE"), message={"COMMAND":"PING-RESPONSE", "FROM": DEVICE_NAME})

    def consume_mqtt_message(topic, message):
        print(f"New unsorted message: {topic}\n{message}")

        if "COMMAND" in message.keys() and message["COMMAND"] == "PING-REQUEST":
            handle_ping(topic, message)

        if "COMMAND" in message.keys() and message["COMMAND"] == "ESTIMATE-REQUEST":
            handle_estimate(topic, message)


    # Initialize message broker
    mb = messaging.MessageBroker(str(DEVICE_NAME + str(uuid.uuid4()))) 
    mb.subscribe_message(topic=MQTT_DEVICE_SUBSCRIBE_TOPIC,callback=consume_mqtt_message)

    while True:
        time.sleep(1)

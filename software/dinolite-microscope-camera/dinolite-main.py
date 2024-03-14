# Example: 
# conda activate bgrenv
# sudo -E /home/*/miniconda3/envs/bgrenv/bin/python raspi-fluid-level-main.py 340 2023-07-12-f-mqtttest4 test notsingle

import dinolite
from dinolite import DinoLite
import argparse

if __name__ == "__main__":  

    parser = argparse.ArgumentParser(description="Command line tool for the camera utility")
    # Adding arguments with default values and making them optional
    parser.add_argument('--name', type=str, default="dorothy-cam", help='Name of camera device (default: dorothy-cam)')
    parser.add_argument('--chip', type=str, default="00000", help='Chip id being imaged (default: 00000)')
    parser.add_argument('--cap_num', type=str, default="0", help='Capture number (default: 0)')
    parser.add_argument('--uuid', type=str, default="NONE", help='UUID of the experiment to take one picture')
    parser.add_argument('--note', type=str, required=False, default='', help='Any additional notes')
    parser.add_argument('--single-pic', type=str, default='multiple', choices=['single', 'multiple'], help='Choose single or multiple pictures mode (default: multiple)')

    # Parsing arguments
    args = parser.parse_args()

    # Using arguments
    device_name = args.name #i.e., dorothy-cam
    chip_id = args.chip
    cap_num = args.cap_num
    UUID = args.uuid
    note = args.note
    single_pic = args.single_pic

    # Initialize dinolite camera
    dino_cam = DinoLite(device_name = device_name, chip_id = chip_id, cap_num = cap_num, UUID = UUID)

    if single_pic == 'single':
        print("Take one picture")
        dino_cam.take_picture(chip = chip_id, text_note = note, UUID = UUID)
    else:
        dino_cam.start_mqtt()
    
    dino_cam.close()

#Usage Example: 
#conda activate bgrenv
#sudo -E /home/*/miniconda3/envs/bgrenv/bin/python raspi-fluid-level-main.py --estimation-type volume --note HELLO

from picamera import PiCamera_
from panel_config import PanelConfig
import argparse

if __name__ == "__main__":  

    parser = argparse.ArgumentParser(description="Command line tool for the camera utility")
    # Adding arguments with default values and making them optional
    parser.add_argument('--name', type=str, default="zambezi-cam", help='Name of camera device (default: zambezi-cam)')
    parser.add_argument('--focus', type=int, required=False, default=344, help='Camera focus value (default: 344)')
    parser.add_argument('--exposure', type=int, required=False, default=45, help='Camera exposure value (default: 45)')
    parser.add_argument('--uuid', type=str, required=False, default='0000-00-00-efi-testing', help='UUID of the experiment')
    parser.add_argument('--note', type=str, required=False, default='no_chipid', help='Any additional notes')
    parser.add_argument('--single-pic', type=str, default='single', choices=['single', 'multiple'], help='Choose single or multiple pictures mode (default: single)')
    parser.add_argument('--burst-count', type=int, default=1, help='Count of burst images to be taken (default: 1)')
    parser.add_argument('--estimation-type', type=str, default='volume', choices=['volume'], help='Image type: choose volume or other form of estimation (default: volume)')

    # Parsing arguments
    args = parser.parse_args()

    # Using arguments
    cam_focus = args.focus
    exposure = args.exposure
    UUID = args.uuid
    note = args.note #chip_id
    single_pic = args.single_pic
    burst_count = args.burst_count
    estimation_type = args.estimation_type
    device_name = args.name

    camera = PiCamera_(device_name = device_name, cam_focus = cam_focus, exposure=exposure, estimation_type=estimation_type)
    panel = PanelConfig(estimation_type)

    if single_pic == 'single':
        print("Take one picture")
        camera.take_picture(text_note = note, UUID = UUID, burst_count = burst_count)
    else:
        camera.start_mqtt()

    camera.close()

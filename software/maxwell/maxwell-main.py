#Usage Example: 
#conda activate bgrenv
#python3 maxwell-main.py 14h57m05s.cfg dorothy vaughan 1 2023-03-07-e-mqtttest1

import maxwell 
from maxwell import MaxOne
import argparse

# Default: record 5min on 15 min
if __name__ == "__main__":  
    parser = argparse.ArgumentParser(description="Command line tool for the maxone utility")
    # Adding arguments with default values and making them optional
    parser.add_argument('--name', type=str, default="dorothy", help='Name of MaxWell device (default: dorothy)')
    parser.add_argument('--smartplug', type=str, default="vaughan", help='Name of smartplug conencted to MaxWell device (default: vaughan)')
    parser.add_argument('--gain', type=int, default=512, help='Voltage gain of recording (default: 512)')
    parser.add_argument('--record-only-spikes', type=str, default='False', choices=['True', 'False'], help='Record all raw voltage signals or only spikes, boolean (default: False)')
    parser.add_argument('--data-path', type=str, default="/home/mxwbio/Data/integrated_experiment/", help='Path to data (default: /home/mxwbio/Data/integrated_experiment)')
    parser.add_argument('--config-path', type=str, default="/home/mxwbio/configs/", help='Path to config (default: /home/mxwbio/configs/)')

    # Parsing arguments
    args = parser.parse_args()

    # Using arguments
    device_name = args.name #i.e., dorothy
    smartplug_name = args.smartplug #i.e., vaughan
    record_only_spikes = args.record_only_spikes
    gain = args.gain
    data_path = args.data_path
    config_path = args.config_path

    # initialize maxwell
    maxone = MaxOne(device_name=device_name, smartplug=smartplug_name, 
                    data_path=data_path, config_path=config_path, 
                    record_only_spikes=record_only_spikes, gain=gain)

    maxone.start_mqtt()
import os, csv, time

def actionDecider(well, type, value, im_path):
    """
    This function makes an assessment on the volume programmed through the well and 
    
        Args:
            'well' (obj) : reference to Well class object (from autoculture.py) containing references to the ports and volume values
            'type' (str) : type of feedback ('volume' or 'pH')
            'value' (float) : value predicted by the estimator
            'im_path' (str) : path to the image file used for estimation
            
    """
    action = None
    slackMsg = []  # TODO: Load this up with Slack messages and return this with the function
    
    if type == 'volume':
        reservoir_vol = float(value)  # <-- This is the volume [uL] computed through the computer vision program
        expected_vol = float(well.fluidic_state['in_volume'])  # <-- This is the total volume [uL] sent to the well
        prev_res_vol = float(well.reservoir_vol)  # <-- Get the previous computed reservoir volume
        threshold_vol = 150  # <-- Threshold of deviation [uL] from expectation
        reservoir_offset = well.reservoir_offset  # <-- Volume to subtract from the computed reservoir volume
        accumulated_vol = well.accumulated_vol  # <-- Volume accumulated (from past collection tubes) that should be added to the computed reservoir volume
        wellIter = int(well.fluidic_state['iteration'])  # <-- replenishmentCycle iteration
        retry_tally = well.retry_tally  # <-- number of retries the well has undergone in this iterations, reset at success

        print('Feedback received vol:', reservoir_vol)

        ##########################
        ### DECISION STRUCTURE ###
        ##########################
        # If the previous reservoir volume was at least 2mL more than the current volume, the tube was probably replaced
        if prev_res_vol > reservoir_vol + 2000:
            accumulated_vol += prev_res_vol  # <-- Add the last reservoir volume to the accumulated volume
            well.accumulated_vol = accumulated_vol  # <-- Write the new accumulated volume
            print("Feedback sensed that the " + well.estimate + " reservoir was replaced")  # TODO: Slack this message
            slackMsg.append("Feedback sensed that the " + well.estimate + " reservoir was replaced")

        # Notify user if reservoir volume is high 
        if reservoir_vol > 13000:
            print("Feedback sensed that the " + well.estimate + " reservoir volume is high")  # TODO: Slack this message
            slackMsg.append("Feedback sensed that the " + well.estimate + " reservoir volume is high")

        # Adjust the reservoir volume with offset and accumulation
        reservoir_vol_adj = reservoir_vol - reservoir_offset + accumulated_vol
        error = expected_vol - reservoir_vol_adj
        print("Expectation - Estimation difference: ", error)

        # Skip the first cycle
        if wellIter < 1:
            # Determine the reservoir_offset from volume already in the tube
            reservoir_offset = reservoir_vol - expected_vol if reservoir_vol > expected_vol else 0
            well.reservoir_offset = reservoir_offset
            print("Feedback set the " + well.estimate + " tube offset to " + str(reservoir_offset))
            slackMsg.append("Feedback set the " + well.estimate + " tube offset to " + str(reservoir_offset))
            
            # Adjust the reservoir volume with offset and accumulation
            reservoir_vol_adj = reservoir_vol - reservoir_offset + accumulated_vol
            error = expected_vol - reservoir_vol_adj
        elif reservoir_vol_adj > expected_vol - threshold_vol and reservoir_vol_adj < expected_vol + threshold_vol:  # Reservoir volume is within threshold
            well.retry_tally = 0
        elif reservoir_vol_adj < expected_vol - threshold_vol:  # Reservoir volume is too low
            if retry_tally < 5:
                # Try a aspiration of the difference
                action = {"COMMAND": "ASPIRATE-REQUEST",
                          "VOL" : int(error),
                          "CHIP_ID" : well.name,
                          "INDEX" : well.estimate,
                          "FROM" : "zambezi"}
                well.retry_tally += 1  # Increment the tally
            elif retry_tally < 7:
                # Try a pull
                action = {"COMMAND": "PULL-REQUEST",
                          "NUM" : int(retry_tally),
                          "CHIP_ID" : well.name,
                          "INDEX" : well.estimate,
                          "FROM" : "zambezi"}
                well.retry_tally += 1  # Increment the tally
            else:
                # Call for help
                slackMsg.append("HELP! " + well.name + " is stuck. Expectation " + str(expected_vol) + " Estimation " + str(reservoir_vol_adj))
                # TODO: Pause further feeds
                well.retry_tally += 1  # Increment the tally
        elif reservoir_vol_adj > expected_vol + threshold_vol:  # Reservoir volume is too high
            # Dispense the excess amount
            disp_vol = reservoir_vol_adj - expected_vol
            if disp_vol > 200:
                disp_vol = 200  # Limit to 200
            action = {"COMMAND" : "DISPENSE-REQUEST",
                       "VOL" : disp_vol,
                       "CHIP_ID" : well.name,
                       "INDEX" : well.estimate,
                       "FROM" : "zambezi"}
            well.retry_tally = 0
        
        # Append the volume.log file
        # Check if the file exists
        if os.path.exists('Logs/' + well.name + '_volume.log'):
            # Open the CSV file in append mode
            mode = 'a'
        else:
            # Open the CSV file in write mode
            mode = 'w'
        base_filename = os.path.basename(im_path)  # Strip the path to the basename
        with open('Logs/' + well.name + '_volume.log', mode, newline='') as csvfile:
            writer = csv.writer(csvfile)
            time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            writer.writerow([time_stamp, well.autoculture.device_name, well.name, 
                            'Expctd Vol (pump):', well.fluidic_state['in_volume'], 'Pnuematic Vol (pump):', well.fluidic_state['out_volume'],
                            'Curr Tube Vol (comp vis):', reservoir_vol, 'Tube Offset Vol', reservoir_offset, 'Accum Vol', accumulated_vol,
                            'Estimtd Vol (comp vis):', reservoir_vol_adj, 'Error (Expctd-Estimtd)', error,
                            'Feedback Retry', retry_tally, 'Feedback ACTION', action,
                            'Image', base_filename, 'Tube Index', well.estimate])
        
        # Upload/append s3 volume.log
        s3_location = well.autoculture.s3_basepath(well.autoculture.experiment_uuid) + well.autoculture.experiment_uuid + '/fluidics/original/logs/'
        if mode == 'a':
            # Upload s3 pump.log
            s3_path = well.autoculture.upload_file(s3_location, 'Logs/' + well.name + '_volume.log')
        else:
            # Upload s3 pump.log
            s3_path = well.autoculture.upload_file(s3_location, 'Logs/' + well.name + '_volume.log')
                
            # TODO: Append s3 pump.log
            #s3_path = well.append_to_s3_file(s3_location, 'Logs/' + well.name + '_volume.log')
        
        # Update the computed reservoir volume
        well.reservoir_vol = reservoir_vol
        
    elif type == 'pH':
        [pH_window, pH_conical] = value  # <-- This is the pH computed through the computer vision program
        wellIter = int(well.fluidic_state['iteration'])  # <-- replenishmentCycle iteration

        print('Feedback received pH:', str(pH_window))

        
        # Append the pH.log file
        # Check if the file exists
        if os.path.exists('Logs/' + well.name + '_pH.log'):
            # Open the CSV file in append mode
            mode = 'a'
        else:
            # Open the CSV file in write mode
            mode = 'w'
        base_filename = os.path.basename(im_path)  # Strip the path to the basename
        with open('Logs/' + well.name + '_pH.log', mode, newline='') as csvfile:
            writer = csv.writer(csvfile)
            time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            writer.writerow([time_stamp, well.autoculture.device_name, well.name, 
                            'pH window (comp vis):', pH_window,
                            'pH conical (comp vis):', pH_conical,
                            'Image', base_filename, 'Tube Index', well.estimate])
            
        # Upload/append s3 pump.log
        s3_location = well.autoculture.s3_basepath(well.autoculture.experiment_uuid) + well.autoculture.experiment_uuid + '/fluidics/original/logs/'
        if mode == 'a':
            # Upload s3 pump.log
            s3_path = well.autoculture.upload_file(s3_location, 'Logs/' + well.name + '_pH.log')
        else:
            # Upload s3 pump.log
            s3_path = well.autoculture.upload_file(s3_location, 'Logs/' + well.name + '_pH.log')
                
            # TODO: Append s3 pump.log
            #s3_path = well.append_to_s3_file(s3_location, well.log_file)
        
        # Update the computed reservoir volume
        well.reservoir_pH = pH_window
    
    # Upload/append s3 pump.log
    s3_location = well.autoculture.s3_basepath(well.autoculture.experiment_uuid) + well.autoculture.experiment_uuid + '/fluidics/original/logs/'
    if mode == 'a':
        # Upload s3 pump.log
        s3_path = well.autoculture.upload_file(s3_location, well.log_file)
    else:
        # Upload s3 pump.log
        s3_path = well.autoculture.upload_file(s3_location, well.log_file)
                
        # TODO: Append s3 pump.log
        #s3_path = well.append_to_s3_file(s3_location, well.log_file)
    
    # Return the requested action (MQTT)
    return action

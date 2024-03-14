#  Instrument-Specific Commands

- **Topic Structure:** `telemetry/<experient_uud>/log/<device_name>/<COMMAND_KEY>/<COMMAND_VALUE>`
- **Example:** `telemetry/0000-00-00-efi-testing/log/zambezi/ASPIRATE/REQUEST`
- **Example:** `telemetry/0000-00-00-efi-testing/log/zambezi/WELL/REQUEST`

<details>
<summary><b>Testing Command (Any Device)</b></summary>

- **Topic Structure:** `telemetry/<experiment_uuid>/log/<device_name>/TWIDDLE/<COMMAND_VALUE>`
- **Command Values:** `REQUEST`, `ACK`, `COMPLETE`, `ERROR`
- **Example:** `telemetry/NONE/log/dorothy/TWIDDLE/REQUEST`
- **Payload:**
  - Twiddle Request:
    ```json
    {
        "COMMAND": "TWIDDLE-REQUEST",
        "SECONDS": "<time_seconds>",
        "FROM": "<sender_device_name>"
    }
    ```
  - Twiddle Responses:
    ```json
    {
        "COMMAND": "TWIDDLE-ACK",
        "FROM": "<device_name>"
    }
    ```
    ```json
    {
        "COMMAND": "TWIDDLE-COMPLETE",
        "FROM": "<device_name>"
    }
    ```
- **Description:** The Twiddle command (i.e., busy but not really doing anything) serves as an empty execution command to test device functionality in EXEC mode without running a specific data-generating task. It is used for functionality checking (i.e., new device bring-up) and debugging.
</details>


## Pump
Command Keys: `WELL`, `FEEDBACK`, `DISPENSE`, `ASPIRATE`, `FEED`, `PULL`, `PLUNGE`

<details>
<summary>1. <b>Instantiate a well</b></summary>
  
- **Topic Structure:** `telemetry/<experiment_uuid>/log/<device_name>/WELL/<COMMAND_VALUE>`
- **Command Values:** `REQUEST`, `ACK`, `COMPLETE`, `ERROR`
- **Example:** `telemetry/0000-00-00-efi-testing/log/zambezi/WELL/REQUEST`
- **Payload:**
  - Request:
      ```json
      {
          "COMMAND": "WELL-REQUEST",
          "CHIP_ID": "<maxwell_key>",
          "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
          "MEDIA" : <media_key> (default = "Ry5"),
          "IN_PORT" : <pump_port_number> (choices: 1-6) (default = 1),
          "OUT_PORT" : <pump_port_number> (choices: 1-6) (default = 6),
          "EXHAUST_PORT" : <pump_port_number> (choices: 1-6) (default = 5),
          "SPEED" : <pump_speed_number> (choices: 1-40) (default = 15),
          "IN_VOL_UL" : <feed_in_volume>,
          "OUT_VOL_UL" : <feed_out_volume>,
          "DISP_PORT" : <valve_port_number> (choices: 1-12),
          "ASPIR_PORT" : <valve_port_number> (choices: 1-12)
      }
      ```
      `'<maxwell_key>'` is generally the chip # of the MaxOne chip (i.e. '12345') or a preferred label such as 'condition_A_rep_1'

      `'<estimate_index>'` is the tube 'key' for `volume-estimation`, which is currently restricted to `'RIGHT'` or `'LEFT'`

      `"IN_PORT" : <pump_port_number> (choices: 1-6)` = 'in_port' (int) : 'pump' port for reagent delivery (to well).

      `"OUT_PORT" : <pump_port_number> (choices: 1-6)` = 'out_port' (int) : 'pump' port for reagent extraction (to waste)

      `"EXHAUST_PORT" : <pump_port_number> (choices: 1-6)` = 'exhaust_port' (int) : 'pump' port for non-fluidic, air operations

      `"SPEED" : <pump_speed_number> (choices: 1-40)` = 'speed' (int) : syringe speed for dispensing and aspirating

      `"IN_VOL_UL" : <feed_in_volume>` = 'in_volume_ul' (float) : absolute volume (uL) to deliver

      `"OUT_VOL_UL" : <feed_out_volume>` = 'out_volume_ul' (float) : absolute volume (uL) to aspirate

      `"DISP_PORT" : <valve_port_number> (choices: 1-12)` = 'disp_port' (int) : 'disp_valve' port for reagent delivery (to well)

      `"ASPIR_PORT" : <valve_port_number> (choices: 1-12)` = 'aspir_port' (int) : 'aspir_vavle' port for reagent extraction (to waste)

    - Example message:
      ```json
      {
          "COMMAND" : "WELL-REQUEST",
          "CHIP_ID" : 12345,
          "INDEX" : "RIGHT",
          "MEDIA" : "Ry5",
          "IN_PORT" : 1,
          "OUT_PORT" : 6,
          "EXHAUST_PORT" : 5,
          "SPEED" : 15,
          "IN_VOL_UL" : 300,
          "OUT_VOL_UL" : 3000,
          "DISP_PORT" : 1,
          "ASPIR_PORT" : 1
      }
      ```
  - Responses:
    ```json
    {
        "COMMAND": "WELL-ERROR",
        "ERROR": "MISSING_CHIP_ID", "WELL-MISSING_INDEX", "WELL-MISSING_ESTIMATE",
        "CHIP_ID": "<maxwell_key>",
        "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
        "FROM": "<device_name>"
    }
    ```
- **Description:** This function generates a `Well` object that has specific ports, media reservoirs, and collection tubes. The `'INDEX'` of a `Well` is its handle for log files and scheduling

</details>
    
<details>
<summary>2. <b>Handle estimation feedback response</b></summary>

- **Topic Structure:** `telemetry/<experiment_uuid>/log/<device_name>/FEEDBACK/<COMMAND_VALUE>`
- **Command Values:** `REQUEST`, `ACK`, `COMPLETE`, `ERROR`
- **Example:** `telemetry/0000-00-00-efi-testing/log/zambezi/FEEDBACK/REQUEST`
- **Payload**
  - Requests:
     ```json
     {
         "COMMAND": "FEEDBACK-REQUEST",
         "VOL": <float>,
         "PH": <float>,
         "CHIP_ID": "<maxwell_key>",
         "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT")
     }
     ```
     `'<index>'` is generally the chip # of the MaxOne chip (i.e. '12345') or a preferred label such as 'condition_A_rep_1'

  - Responses:
     ```json
     {
         "COMMAND": "FEEDBACK-MISSING_INDEX",
         "CHIP_ID": "<maxwell_key>",
         "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
         "FROM": "<device_name>"
     }
     ```
- **Description**: This function receives the volume and pH estimation from the `estimator`, logs the value, and decides what action to take based on the result via the `actionDecider()` function

</details>

<details>
<summary>3. <b>Dispense a volume</b></summary>

- **Description**: This function draws media in and dispenses a volume to a well
- **Payload**:
  - Request:
    ```json
    {
        "COMMAND": "DISPENSE-REQUEST",
        "VOL": <float>,
        "CHIP_ID": "<maxwell_key>"
    }
    ```
    `"VOL": <float>` is a value in microliters [uL] that can be 0 to 5000.
    `'<index>'` is generally the chip # of the MaxOne chip (i.e. '12345') or a preferred label such as 'condition_A_rep_1'

  - Responses:
    ```json
    {
        "DISPENSE": "MISSING_INDEX", "OUT_OF_BOUNDS", "ERROR",
        "CHIP_ID": "<maxwell_key>",
        "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
        "FROM": "<device_name>"
    }
    ```

</details>

<details>
<summary>4. <b>Aspirate a volume</b></summary>
  
  - Description: This function draws conditioned media from a well into a particular collection reservoir
  - Accepts these messages:
     ```json
     {
         "ASPIRATE": "REQUEST",
         "VOL": <float>,
         "CHIP_ID": "<maxwell_key>"
     }
     ```
     `"VOL": <float>` is a value in microliters [uL] that can be 0 to 10000.
     `'<index>'` is generally the chip # of the MaxOne chip (i.e. '12345') or a preferred label such as 'condition_A_rep_1'

  - Responses:
     ```json
     {
         "ASPIRATE": "MISSING_INDEX", "OUT_OF_BOUNDS", or "ERROR",
         "CHIP_ID": "<maxwell_key>",
         "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
         "FROM": "<device_name>"
     }
     ```
</details>

<details>
<summary>5. <b>Perform a well feed (replenishment cycle)</b></summary>
     
  - Description: This function draws conditioned media from a well, waits a period for the aspiration to be carried out, draws media from a fresh reservoir, dispenses the media into the well, and logs the event for downstream calculations
  - Accepts these messages:
     ```json
     {
         "FEED": "REQUEST",
         "CHIP_ID": "<maxwell_key>"
     }
     ```
     `'<index>'` is generally the chip # of the MaxOne chip (i.e. '12345') or a preferred label such as 'condition_A_rep_1'

  - Responses:
     ```json
     {
         "FEED": "MISSING_INDEX", "ERROR"
         "CHIP_ID": "<maxwell_key>",
         "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
         "FROM": "<device_name>"
     }
     ```
     The `'COMPLETE'` of `'FEED'` is the trigger to estimate so both `'INDEX'` and `'ESTIMATE'` key values tag along in the message so other devices can respond accordingly

</details>

<details>
<summary>6.<b>Perform a pull</b></summary>
  

  - Description: This function forcefully pulls a full syringe (1mL) on the well aspiration line to initiate aspirate flow in the case of a stuck line
  - Accepts these messages:
     ```json
     {
         "PULL": "REQUEST",
         "VOL": <int>,
         "CHIP_ID": "<maxwell_key>"
     }
     ```
     `"PULL": <int>` is the integer number of successive pulls 0 to 15.
     `'<index>'` is generally the chip # of the MaxOne chip (i.e. '12345') or a preferred label such as 'condition_A_rep_1'

  - Responses:
     ```json
     {
         "PULL": "MISSING_INDEX", "OUT_OF_BOUNDS", "ERROR",
         "CHIP_ID": "<maxwell_key>",
         "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
         "FROM": "<device_name>"
     }
     ```

</details>

<details>
<summary>7. <b>Perform a plunge</b></summary>

  - Description: This function forcefully plunges a full syringe (1mL) on the well aspiration line to initiate aspirate flow in the case of a stuck line
  - Accepts these messages:
     ```json
     {
         "PLUNGE": "REQUEST",
         "NUM": <int>,
         "CHIP_ID": "<maxwell_key>"
     }
     ```
     `"NUM": <int>` is the integer number of successive plunges 0 to 15.
     `'<index>'` is generally the chip # of the MaxOne chip (i.e. '12345') or a preferred label such as 'condition_A_rep_1'

  - Responses:
     ```json
     {
         "PLUNGE": "MISSING_INDEX", "OUT_OF_BOUNDS", or "ERROR",
         "CHIP_ID": "<maxwell_key>",
         "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
         "FROM": "<device_name>"
     }
     ```
</details>


## Fluid Output Camera

Command Keys: `PICTURE`

<details>
<summary>1. <b>Request Picture</b></summary>

- [ ] TODO: Priming requirement: take the first picture and throw it away because it's blurry.
- **Example:** `telemetry/0000-00-00-efi-testing/log/dorothy-cam/PICTURE/REQUEST`
- **Payload:**
    Spencer has Zambezi pump send:

    ```json
    { "COMMAND": "SCHEDULE-REQUEST",
      "TYPE" : "ADD",
      "EVERY_X_SECONDS" : "10",
      "FLAGS" : "ONCE",
      "DO" : {
            "PICTURE": "REQUEST",
            "TYPE": ["pH"],
            "CHIP_ID": "<maxwell_key>",
            "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
            "FROM": "<device_name>"
            },
    "FROM": "<device_name>"
    }
    ```

    as soon as ASPIRATE starts, the camera gets the schedule to take a burst sequence of photos 10 seconds later.
    Then, once the feeding finishes, the pump sends:

    ```json
    { "COMMAND": "SCHEDULE-REQUEST",
      "TYPE" : "ADD",
      "EVERY_X_MINUTES" : "3",
      "FLAGS" : "ONCE",
      "DO" : {
            "PICTURE": "REQUEST",
            "TYPE": ["volume"],
            "CHIP_ID": "<maxwell_key>",
            "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
            "FROM": <device_name>
            },
    "FROM": "<device_name>"
    }
    ```

    So the camera waits 3 min before taking the volume photo. This is enough time to let the liquid fall down the walls of


  - Picture Request:
     ```json
     {
         "COMMAND": "PICTURE-REQUEST",
         "TYPE": ["pH", "volume"],
         "CHIP_ID": "<maxwell_key>",
         "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
         "FROM": "<device_name>"
     }
     ```

  - Responses:
     ```json
     {
         "COMMAND": "ESTIMATE-REQUEST",
         "PICTURE": {"VOL": "<s3-link>", "PH": "<s3-link>"}
         "TYPE": ["pH", "volume"],
         "CHIP_ID": "<maxwell_key>",
         "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
         "FOR": <name_of_pump_that_is_requesting (i.e., zambezi)>
     }
     ```
     ```json
     {
         "COMMAND": "ESTIMATE-REQUEST",
         "PICTURE": {"VOL": "<s3-link>"}
         "TYPE": ["volume"],
         "CHIP_ID": "<maxwell_key>",
         "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
         "UUID": self.experiment_uuid, <-- for estimator send topic
         "FOR": <name_of_pump_that_is_requesting (i.e., zambezi)>
     }
     ```
     ```json
     {
         "COMMAND": "ESTIMATE-REQUEST",
         "PICTURE": {"PH": "<s3-link>"}
         "TYPE": ["pH"],
         "CHIP_ID": "<maxwell_key>",
         "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
         "FOR": <name_of_pump_that_is_requesting (i.e., zambezi)>
     }
     ```
</details>


## Estimator
Command Keys: `ESTIMATE`

<details>
<summary>1. <b> Estimate Volume</b></summary>

- **Topic:** `telemetry/+/log/volume-estimator/+/+`
- **Example:** `telemetry/0000-00-00-efi-testing/log/volume-estimator/ESTIMATE/REQUEST`
- **Payload:**
  - Request:
    ```json
    {
        "COMMAND": "ESTIMATE-REQUEST",
        "PICTURE": "<s3-link>",
        "TYPE": ["pH", "volume"],
        "UUID": "<experiment_uuid>", <-- remove b/c it's in the topic?
        "CHIP_ID": "<maxwell_key>",
        "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT")
    }
    ```
  - Response:
    ```json
    {
        "COMMAND": "ESTIMATE-RESPONSE",
        "VOLUME": "",
        "PH": "",
        "CHIP_ID": "<maxwell_key>",
        "INDEX": "<estimate_index>" (choices: "RIGHT" or "LEFT"),
        "FROM": "<sender_device_name>"
    }
    ```
- **Description:** Request the volume estimator to return volume of the tube. 
- VolumeEstimator will always return a value (i.e. 0 and it will never be None)

</details>


## MaxOne
Command Keys: `SWAP`, `LIST`, `RECORD`

<details>
<summary>1. <b>Swap a chip to be on the headstage</b></summary>

- **Example:** `telemetry/0000-00-00-efi-testing/log/dorothy/SWAP/REQUEST`
- **Payload:**
  - Request:
    ```json
    {
      "COMMAND": "SWAP-REQUEST",
      "CHIP_ID": "<new_chip_id>",
      "CONFIG" : <s3link_or_local_path_to_config_file>,
      "FROM": "<device_name>"
    }
    ```
  - Response:
    - Error:
    ```json
    {
        "COMMAND": "SWAP-ERROR",
        "ERROR": "Config not found at <s3link_or_local_path_to_config_file>",
        "FROM": "<device_name>"
    }
    ```
- **Description:** Sets up a chip with a corresponding configuration file for electrode placements. To keep the same chip and update config, also do this swap.
</details>


<details>
<summary>2. <b>List current chip</b></summary>

- **Example:** `telemetry/0000-00-00-efi-testing/log/dorothy/LIST/REQUEST`
- **Payload:**
  - Request:
    ```json
      {
      "COMMAND": "LIST-REQUEST",
      "FROM": "<device_name>"
      }
    ```
  - Response:
    ```json
      {
      "COMMAND": "LIST-RESPONSE",
      "CHIP_ID": "<new_chip_id>",
      "CONFIG" : <s3link_or_local_path_to_config_file>,
      "FROM": "<device_name>"
      }
    ```
- **Description:** List the current chip that was last swapped onto the headstage and its current associated config file.

</details>


<details>
<summary>2. <b>Record chip</b></summary>

- **Example:** `telemetry/0000-00-00-efi-testing/log/dorothy/LIST/REQUEST`
- **Payload:**
  - Request:
    ```json
      {
      "COMMAND": RECORD-REQUEST",
      "CHIP_ID": "<chip_id>",
      "MINUTES": 1,
      "FROM": "<device_name>"
      }
    ```
  - Error Response:
    ```json
      {
      "COMMAND": "RECORD-ERROR",
      "ERROR": "Invalid chip ID: current chip on headstage is <current_chip>"
      "FROM": "<device_name>"
      }
    ```
- **Description:** Request recording from the current chip on the headstage

</details>

## DinoLite
Command Keys: `CALIBRATE`, `ADD`, `REMOVE`, `LIST`, `PICTURE`

<details>
<summary>1. <b>Calibrate cameras</b></summary>

- **Example:** `telemetry/0000-00-00-efi-testing/log/dorothy-cam/CALIBRATE/REQUEST`
- **Payload:**
  - Request:
    ```json
      {
      "COMMAND": "CALIBRATE-REQUEST",
      "FLAG": "START" or "STOP",
      "FROM": "<device_name>"
      }
    ```
- **Description:** At the beginning of the program, run focusing/calibration. "START" opens the window showing all cameras and indexes. "STOP" closes the window. Turns on DinoLite imaging in a live view on screen and the user can focus them. All camera indexes are shown at the same time. The user can also take this time to write down which chips are on which camera index. TODO: Later add this as a requirement for being PRIMED.

</details>


<details>
<summary>2. <b>Request to register a chip in the experiment</b></summary>
  
- **Example:** `telemetry/0000-00-00-efi-testing/log/dorothy-cam/ADD/REQUEST`
- **Payload:**
  - Request:
    - Add the pairs to a dictionary stored in the program:
    ```json
      {
      "COMMAND": "ADD-REQUEST",
      "PAIRS": { "chip_id": "camera_index", "chip_id": "camera_index" },
      "FROM": "<device_name>"
      }
    ```
    - Remove the indicated pairs from the dictionary stored in the program:
     ```json
       {
        "COMMAND": "REMOVE-REQUEST",
        "PAIRS": { "chip_id": "camera_index", "chip_id": "camera_index", },
        "FROM": "<device_name>"
        }
     ```
  - Response:
    - Add Error:
      ```json
        {
          "COMMAND": "ADD-ERROR",
          "ERROR": "Request contains repeated keys",
          "FROM": "<device_name>"
        })

        {
          "COMMAND": "ADD-ERROR",
          "ERROR": "Cannot assign the same camera index to multiple chips",
          "FROM": "<device_name>"
        })
        ```
    - Remove Error:
      ``` json
        {
        "COMMAND": "REMOVE-ERROR",
        "ERROR": "<error message>",
        "FROM": "<device_name>"
        }
      ```
- **Description:**  Chip must be mapped to a camera index of the corresponsing DinoLite. `"ADD"` binds the chip to a camera index. `"REMOVE"` unbinds a chip from a camera index.

</details>


<details>
<summary>3. <b>List chips in the experiment</b></summary>
  
- **Example:** `telemetry/0000-00-00-efi-testing/log/dorothy-cam/LIST/REQUEST`
- **Payload:**
  - Request:
    ```json
      {
      "COMMAND": "LIST-REQUEST",
      "FROM": "<device_name>"
      }
    ```
  - Response to `"LIST"`, PAIRS carries a dictionary containing registered (chip, camera index) pairs:
     ```json
       {
        "COMMAND": "LIST-RESPONSE",
        "PAIRS":  { ("chip_id", "camera_index") },
        "FROM": "<device_name>"
        }
     ```
- **Description:** `"LIST"` returns the list of all registered (chip, camera index) pairs. The command requests all pairs stored in the dictionary stored in the program.

</details>

<details>
<summary>4. <b>Take a picture of a chip</b></summary>

- **Example:** `telemetry/0000-00-00-efi-testing/log/dorothy-cam/LIST/REQUEST`
- **Payload:**
  - Request:
    ```json
      {
      "COMMAND": "PICTURE-REQUEST",
      "CHIP_ID": ["chip_id"],
      "FROM": "<device_name>"
      }
    ```
  - Error Response:
    ```json
        {
        "COMMAND": "PICTURE-ERROR",
        "ERROR": "Invalid CHIP_ID. Available chips: <chip_ids list>"
        }
    ```
- **Description:** Takes photos of the chips and stores them using the experiment storage structure in s3 documented under Section "Data". User must specify (chip id, camera index).

</details>

# integrated-system-v1-paper
Supplementary Material for paper submission to Science Robotics:

***"A feedback-driven microfluidic, electrophysiology, and imaging platform for brain organoid studies"***

<!-- Journal article: [A feedback-driven microfluidic, electrophysiology, and imaging platform for brain organoid studies](LINK HERE) -->

## Overview

<img src="./img/overview.jpg" height="280">
This work presents a laboratory robotics system that uses IoT collaboration to improve the control of cell culture experiments.
The main parts include software for IoT devices and their control via a webpage, computer vision analysis, an example  bill of materials, and 3D printed components for setting up the system.
This repository includes documentation on how to use and assemble the system.

## Hardware
- Bill of Materials (BOM) for putting together the system is inside [`./hardware`](https://github.com/braingeneers/integrated-system-v1-paper/tree/main/hardware).
- CAD files for 3D printed files and reference assemblies are inside [`./hardware/CAD`](https://github.com/braingeneers/integrated-system-v1-paper/tree/main/hardware/CAD).


## Software
Software to enable voltage sampling and user interaction, with accompanying documentation, is in [`./software`](https://github.com/braingeneers/piphys/tree/main/software).
- *device-class*: [`braingeneerpy`](https://github.com/braingeneers/braingeneerspy)
- *device-class* child implementations: [`./software`](https://github.com/braingeneers/integrated-system-v1-paper/tree/main/software)
   - MaxOne
   - DinoLite
   - Autoculture
   - Camera
- Estimator

© 2024 Braingeneers

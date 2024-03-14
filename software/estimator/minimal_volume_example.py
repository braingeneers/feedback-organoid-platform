import os
from volumeEstimation import VolumeEstimation
from visualization import Visualization
import cv2

img_path = "path/to/image.jpg"
obj = VolumeEstimation("LEFT")
obj_visu = Visualization(obj)
vol = obj.volume_estimation(img_path)
print(vol)

#img = cv2.imread(img_path)
#obj_visu.visualization(img)

#OR
#obj.vol_right
#obj.vol_left
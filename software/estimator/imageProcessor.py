import cv2
import os
import numpy as np
from volumeEstimation import VolumeEstimation
import csv

class ImageProcessor:
    def __init__(self, volume_estimation_obj):
        self.obj = volume_estimation_obj

    def prepare_data(self, dataset_path, output_binary_image_path, output_binary_image_meniscus_path, output_binary_image_edge_path):
            image_files = [file for file in os.listdir(dataset_path) if file.endswith(('.jpg', '.jpeg', '.png'))]

            for image_file in image_files:
                image_path = os.path.join(dataset_path, image_file)

                volume_gt = VolumeEstimation.get_gt_volume(image_file)

                full_image = cv2.imread(image_path)
                for side in ['left', 'right']:
                    binary_image, binary_image_meniscus, binary_edge, area, area_meniscus = self.prepare_data_by_side(full_image, side, volume_gt)
                    binary_image_path = os.path.join(output_binary_image_path, f"{side}_" + image_file)
                    cv2.imwrite(binary_image_path, binary_image)

                    binary_image_meniscus_path = os.path.join(output_binary_image_meniscus_path, f"{side}_" + image_file) 
                    cv2.imwrite(binary_image_meniscus_path, binary_image_meniscus)

                    binary_image_edge_path = os.path.join(output_binary_image_edge_path, f"{side}_" + image_file)
                    cv2.imwrite(binary_image_edge_path, binary_edge)

                    self.save_data_txt(binary_image_path, binary_image_meniscus_path, binary_image_edge_path, area, area_meniscus, volume_gt)
                
    def prepare_data_by_side(self, full_image, side, volume_gt):
        rect_image = VolumeEstimation.image_crop(self.obj, full_image, side)
        binary_image = VolumeEstimation.full_processing_image(self.obj, rect_image)
        rgb_image_meniscus = VolumeEstimation.get_meniscus_area_rgb(self.obj, rect_image)
        binary_image_meniscus = VolumeEstimation.HUE_filter_meniscus(self.obj, rgb_image_meniscus)

        _, binary_edge = VolumeEstimation.liquid_heigth_contour(self.obj, binary_image)
        area = VolumeEstimation.count_white_pixels(self.obj, binary_image)
        area_meniscus = VolumeEstimation.count_white_pixels(self.obj, binary_image_meniscus)
            
        return binary_image, binary_image_meniscus, binary_edge, area, area_meniscus

    def save_data_txt(self, binary_image_path, binary_image_meniscus_path, binary_image_edge_path, area, area_meniscus, volume_gt):
        txt_filename = os.path.splitext("/home/ella/NEW_TUBE/calib_2/data.txt")[0] + ".txt"

        content = [binary_image_path, binary_image_meniscus_path, binary_image_edge_path, area, area_meniscus, volume_gt]
            
        with open(txt_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(content)

    def load_images_and_areas_from_file(self, txt_filepath):
        with open(txt_filepath, 'r') as f:
            lines = f.readlines()

        images_H = []
        images_M = []
        images_E = []
        H_areas = []
        M_areas = []
        volumes = []

        for line in lines:
            img_path_H, img_path_M, img_path_E, H_area, M_area, volume = line.strip().split(',')
            img_H = cv2.imread(img_path_H, cv2.IMREAD_GRAYSCALE)
            img_M = cv2.imread(img_path_M, cv2.IMREAD_GRAYSCALE)
            img_E = cv2.imread(img_path_E, cv2.IMREAD_GRAYSCALE)
            # Get the original image dimensions
            height_H, width_H = img_H.shape[:2]
            height_M, width_M = img_M.shape[:2]
            height_E, width_E = img_E.shape[:2]

            # Resize the images to half of their original size
            img_H = cv2.resize(img_H, (width_H // 2, height_H // 2))
            img_M = cv2.resize(img_M, (width_M // 2, height_M // 2))
            img_E = cv2.resize(img_E, (width_E // 2, height_E // 2))

            if img_H is not None and img_M is not None:
                images_H.append(img_H)
                images_M.append(img_M)
                images_E.append(img_E)
                H_areas.append(float(H_area)/8)
                M_areas.append(float(M_area)/8)
                volumes.append(float(volume))

        image_size = (images_H[0].shape[0], images_H[0].shape[1])
        images_H_array = np.array(images_H)
        images_M_array = np.array(images_M)
        images_E_array = np.array(images_E)
        H_areas_array = np.array(H_areas)
        M_areas_array = np.array(M_areas)
        volumes_array = np.array(volumes)

        return images_H_array, images_M_array, images_E_array, H_areas_array, M_areas_array, volumes_array, image_size
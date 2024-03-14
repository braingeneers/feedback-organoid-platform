import matplotlib.pyplot as plt
import cv2
import os
import numpy as np
import re
import math
import sys
import pandas as pd
import csv
from curveFitting import CurveFitting

class VolumeEstimation:
    def __init__(self, side):
        self.side = side

        self.vol_left = 0
        self.vol_right = 0

        self.cone_vol = 1500

        # self.ref_area = 4141 
        # self.g = 1.7926324420211115e-08 
        # self.h = -5.83145324358848e-05 
        # self.i = 0.29484054799634163 
        # self.j = -1.001049703534974 
        # self.c = 5.849391925211925e-11 
        # self.d = -5.900374269770646e-07 
        # self.e = 0.6290473813935713 
        # self.f = -1109.7396497247462

        self.ref_area = 4380 
        self.g = 5.594097852070963e-09 
        self.h = 1.9955446895130637e-05 
        self.i = 0.15330954704304375 
        self.j = 0.9581548453421256 
        self.c = 2.0508853508601078e-11 
        self.d = 7.701084013461749e-07 
        self.e = 0.6203205589679506 
        self.f = -1217.8468504658977

        self.x1 = 1135  # upper-left (y1, x1)
        self.x2 = 1155  # upper-right (y1, x2)
        self.y1 = 210    # middle-left (y2, x1)
        self.y2 = 970  # middle-right  (y2, x2)
        self.y3 = 1275  # down-left (y3, x1)

        #right image
        self.x3 = 1450  # upper-left (y1, x3)
        self.x4 = 1470  # upper-right (y1, x4)

        self.dist = 290 # down-right (y3, x2)

        self.BLUR_THRESHOLD = 50

        self.volume_gt_left = []
        self.volume_gt_right = []
        self.area_left = []
        self.area_right = []
        self.area_meniscus_left = []
        self.area_meniscus_right = []
        self.K_values = []

        self.image_is_red = False
        self.image_is_blur = False

    def images_temperature(self, dataset_path):
        image_files = [file for file in os.listdir(dataset_path) if file.endswith(('.jpg', '.jpeg', '.png'))]

        # Sort the files by modification time, earliest first
        image_files.sort(key=lambda x: os.path.getmtime(os.path.join(dataset_path, x)))

        Rs = []
        Gs = []
        Bs = []

        for image_file in image_files:
            image_path = os.path.join(dataset_path, image_file)

            avr_colors = self.is_red(image_path)
            Rs.append(avr_colors[0])
            Gs.append(avr_colors[1])
            Bs.append(avr_colors[2])

        indices = list(range(1, len(image_files) + 1))

        plt.plot(image_files, Rs, 'r', label='Red')
        plt.plot(image_files, Gs, 'g', label='Green')
        plt.plot(image_files, Bs, 'b', label='Blue')
        
        plt.xlabel('Image Files')
        plt.ylabel('Temperature Values')
        plt.title('Temperature values of RGB channels against images')
        plt.xticks(rotation=45)  # Rotate x-axis labels for better visibility if needed
        plt.legend()
        plt.tight_layout()
        plt.show()
        return

    def is_red(self, image_path):
        # working with every dataset
        image = cv2.imread(image_path)
        # Define square coordinates (y=1290, x=190, 30 pixels per side)
        x_start, y_start, side_length = 1600, 650, 50
        x_end = x_start + side_length - 20
        y_end = y_start + side_length

        square_region = image[x_start:x_end, y_start:y_end]

        avg_color = np.mean(square_region, axis=(0, 1))

        R = avg_color[2]
        G = avg_color[1]
        B = avg_color[0]

        # R_channel = square_region[:, :, 2]
        # G_channel = square_region[:, :, 1]
        # B_channel = square_region[:, :, 0]
        # color = (10, 100, 1)  # Green color in BGR
        # thickness = 1
        # cv2.rectangle(image, (y_start, x_start), (y_end, x_end), color, thickness)
        # cv2.imshow("oi", image)
        # cv2.waitKey(0)
        # plt.figure()
        # plt.subplot(3, 1, 1)
        # plt.imshow(R_channel, cmap='Reds')
        # plt.title("R channel")
        # plt.colorbar()
        # plt.subplot(3, 1, 2)
        # plt.imshow(G_channel, cmap='Greens')
        # plt.title("G channel")
        # plt.colorbar()
        # plt.subplot(3, 1, 3)
        # plt.imshow(B_channel, cmap='Blues')
        # plt.title("B channel")
        # plt.colorbar()
        # plt.tight_layout()
        # plt.show()

        if (R > 20 and G> 20 and B> 20):
            # the image is red
            self.image_is_red = True
            print(R, G, B)
            print(image_path)
        else:
            self.image_is_red = False
        return (R, G, B)             

    def images_blurness(self, dataset_path):
        image_files = [file for file in os.listdir(dataset_path) if file.endswith(('.jpg', '.jpeg', '.png'))]

        # Sort the files by modification time, earliest first
        image_files.sort(key=lambda x: os.path.getmtime(os.path.join(dataset_path, x)))

        Laplace = []
        for image_file in image_files:
            image_path = os.path.join(dataset_path, image_file)

            fm = self.is_blur(image_path)
            Laplace.append(fm)

        indices = list(range(1, len(image_files) + 1))

        plt.plot(image_files, Laplace, 'r', label='Laplace')        
        plt.xlabel('Index')
        plt.ylabel('Laplacian Values')
        plt.title('Laplacian values per image')
        plt.xticks(rotation=45)  # Rotate x-axis labels for better visibility if needed
        plt.legend()
        plt.tight_layout()
        plt.show()
        return
    
    def is_blur(self, image_path):
        image = cv2.imread(image_path)
        fm = cv2.Laplacian(image, cv2.CV_64F).var()
        if fm < self.BLUR_THRESHOLD:
            # image is too blur
            self.image_is_blur = True
            print(image_path)
            print("is Blur", fm)
        else:
            self.image_is_blur = False
        return fm
    
    def check_image_quality(self, image_path):
        # check blurness
        self.is_blur(image_path)
        # check image color
        self.is_red(image_path)
        if(self.image_is_red):
            print("Image is too red. Please, check panel color.")
        if(self.image_is_blur):
            print("Image is too blur.")
        return
        
    def image_segmentation(self, rect_image):      
        gray_image = cv2.cvtColor(rect_image, cv2.COLOR_RGB2GRAY)
        binary_image = np.zeros_like(gray_image)
        
        # first, check if there is fluid inside the tube
        white_pixels = self.count_white_pixels(self.HUE_filter(rect_image))
        #print(white_pixels)

        #if white_pixels < 60:
        #    return binary_image
        
        #else:
        height = self.get_meniscus_height(rect_image)
        #print("height", height)
        binary_meniscus = self.segmentation_refinement(rect_image, height)
        binary_image[:height, :] = 0
        binary_image[height:, :] = 255

        binary_image = binary_meniscus + binary_image
        binary_image[binary_image > 0] = 255

        return binary_image

    def segmentation_refinement(self, rect_image, height):
        rgb_meniscus = self.get_area_of_interest(rect_image, height)
        binary_meniscus = self.meniscus_segmentation(rgb_meniscus)

        return binary_meniscus

    def volume_estimation(self, image_path):
        #self.check_image_quality(image_path)
        if (not self.image_is_blur) and (not self.image_is_red):
            image = cv2.imread(image_path)
            rect_image = self.image_crop(image, self.side)

            binary_image = self.image_segmentation(rect_image)
    
            area = self.count_white_pixels(binary_image)
            self.area = area
            
            # cylinder lower part
            if area < self.ref_area:
                volume = self.g * area**3 + self.h * area**2 + self.i*area + self.j
            else:
                volume = self.c * area**3 + self.d * area**2 + self.e*area + self.f
            if volume < 0 or volume == self.j:
                volume = 0

            if self.side == 'LEFT':
                self.vol_left = volume
                #print("left", volume)
            elif self.side == 'RIGHT':
                self.vol_right = volume
                #print("right", volume)

            return volume
        else:
            return None

    def HUE_filter(self, image_rgb_crop):
        image_rgb_crop = np.float32(image_rgb_crop) / 255.0

        I = cv2.cvtColor(image_rgb_crop, cv2.COLOR_RGB2HSV)
        I = np.float32(I)

        H_channel = I[:, :, 0]
        U_channel = I[:, :, 1]

        channel1Min = 90.0 * 360 / 179
        channel1Max = 174 * 360 / 179
        channel2Min = 15.0 / 255.0

        mask = ((H_channel >= channel1Min) & (U_channel >= channel2Min) & (H_channel <= channel1Max))
        binary_image = np.zeros_like(I[:, :, 0], dtype=np.float32)
        binary_image[mask] = 1.0
        binary_image = (binary_image * 255).astype(np.uint8)

        return binary_image
    
    def get_meniscus_height(self, rect_image):
        hsv_image = cv2.cvtColor(rect_image, cv2.COLOR_BGR2HSV)
        U_channel = hsv_image[:, :, 1]
        E_channel = hsv_image[:, :, 2]

        line_sum_U = np.sum(U_channel, axis=1)
        line_sum_E = np.sum(E_channel, axis=1)
        max_index_U = np.argmax(line_sum_U)

        lower_bound = max(0, max_index_U - 12)
        upper_bound = min(len(line_sum_E), max_index_U + 13)
        
        restricted_E = line_sum_E[lower_bound:upper_bound]
        
        min_index_E_restricted = np.argmin(restricted_E)

        min_index_E = min_index_E_restricted + lower_bound

        height = round((min_index_E + max_index_U)/2)
        return height
    
    def full_processing_image(self, image_rgb_crop):
        #image_rgb_crop = cv2.GaussianBlur(image_rgb_crop, (5, 5), 0)
        binary_image = self.HUE_filter(image_rgb_crop)
        # Applying dilation
        kernel_size = 4  # You can change this based on your requirements
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        binary_image = cv2.dilate(binary_image, kernel, iterations=1)

        return binary_image

    def save_meniscus_data(self, volume_gt, area, area_meniscus, side):
        if side == "LEFT":
            self.volume_gt_left.append(volume_gt)
            self.area_left.append(area)
            self.area_meniscus_left.append(area_meniscus)
        else:
            self.volume_gt_right.append(volume_gt)
            self.area_right.append(area)
            self.area_meniscus_right.append(area_meniscus)

    def training_data(self, dataset_path):
        volumes_gt_cone = [0]
        volumes_gt_cylinder = []
        areas_cone = [0]
        areas_cylinder = []

        image_files = [file for file in os.listdir(dataset_path) if file.endswith(('.jpg', '.jpeg', '.png'))]

        for image_file in image_files:
            image_path = os.path.join(dataset_path, image_file)
            image = cv2.imread(image_path)
            for side in ['RIGHT', 'LEFT']:
                #self.visualization(image)
                volume_gt = self.get_gt_volume(image_file)
                
                rect_image = self.image_crop(image, side)
                binary_image = self.image_segmentation(rect_image)

                area = self.count_white_pixels(binary_image)

                if volume_gt == self.cone_vol:
                    self.ref_area = area

                    volumes_gt_cone.append(volume_gt)
                    areas_cone.append(area)

                    volumes_gt_cylinder.append(volume_gt)
                    areas_cylinder.append(area)
                    
                if volume_gt < self.cone_vol:
                    volumes_gt_cone.append(volume_gt)
                    areas_cone.append(area)

                # cylinder 
                elif volume_gt > self.cone_vol:
                    volumes_gt_cylinder.append(volume_gt)
                    areas_cylinder.append(area)

        if not np.isin(self.cone_vol, volumes_gt_cone):
            print("To use 'training_data', you must provide the image when the volume is 1500 mL.")
            sys.exit(1)
        _, params_cylinder = CurveFitting.fit_curve('polinomial_3', areas_cylinder, volumes_gt_cylinder)
        _, params_cone = CurveFitting.fit_curve('polinomial_3', areas_cone, volumes_gt_cone)

        x_1 = np.linspace(min(areas_cone), max(areas_cone), 10)
        y_1 = CurveFitting.polinomial_3(x_1, *params_cone)

        x_2 = np.linspace(min(areas_cylinder), max(areas_cylinder), 10)
        y_2 = CurveFitting.polinomial_3(x_2, *params_cylinder)

        g, h, i, j = params_cone
        c, d, e, f = params_cylinder

        self.g = g
        self.h = h
        self.i = i
        self.j = j

        self.c = c
        self.d = d
        self.e = e
        self.f = f

        print("self.ref_area =", self.ref_area, "\nself.g =", g, "\nself.h =", h, "\nself.i =", i, "\nself.j =", j, "\nself.c =", c, "\nself.d =", d, "\nself.e =", e, "\nself.f =", f)
        
        #Plot the data points and the fitted curve
        plt.figure()
        plt.plot(volumes_gt_cylinder, areas_cylinder, 'o', label='Cylinder', color='teal')
        plt.plot(y_2, x_2, label='Fitted Curve (Cylinder)', color='mediumturquoise')
        plt.plot(volumes_gt_cone, areas_cone, 'o', label='Cone', color='darkgoldenrod')
        plt.plot(y_1, x_1, label='Fitted Curve (Cone)', color='gold')
        plt.axvline(x=1500, color='black', linestyle='--', linewidth=1)
        #plt.plot(volume_values, K_values, 'o', label='K')
        plt.ylabel('Area (pixel)')
        plt.xlabel('Volume (uL)')
        plt.title('Area vs Volume')
        plt.grid(True)
        plt.legend()
        plt.savefig('polinomial.svg', dpi=300, format='svg', bbox_inches='tight')
        plt.show()

        params = [g, h, i, j, c, d, e, f]
        return params

    def testing_data(self, dataset_path):
        volumes_gt = []
        volumes = []
        net = []
        image_files = [file for file in os.listdir(dataset_path) if file.endswith(('.jpg', '.jpeg', '.png'))]

        for side in ["RIGHT", "LEFT"]:
            self.side = side 
            for image_file in image_files:
                image_path = os.path.join(dataset_path, image_file)
                volume_gt = self.get_gt_volume(image_file)
                self.volume_estimation(image_path) 
                volume = self.vol_right if side == 'RIGHT' else self.vol_left
                
                net.append(volume_gt - volume)
                #print("GT:", volume_gt, "\nNet:",  volume_gt-volume, "\n")
                volumes_gt.append(volume_gt)
                volumes.append((volume_gt, volume))

        volumes = sorted(volumes, key=lambda x: x[0])
        volume_gt, volume_est = zip(*volumes)

        return volume_gt, volume_est
   
    def calculate_r_squared(self, volume_gt, volume_est):
        # Convert volume_gt and volume_est to numpy arrays if they are tuples or lists
        volume_gt = np.array(volume_gt)
        volume_est = np.array(volume_est)
        
        # Calculate the mean of the ground truth volumes
        mean_gt = np.mean(volume_gt)

        # Total Sum of Squares (SST)
        sst = np.sum((volume_gt - mean_gt) ** 2)

        # Residual Sum of Squares (SSR)
        ssr = np.sum((volume_gt - volume_est) ** 2)

        # Coefficient of Determination (R^2)
        r_squared = 1 - (ssr / sst)

        return r_squared

    def altman_plot(self, volume_gt, volume_est):

        data1 = np.asarray(volume_gt)
        data2 = np.asarray(volume_est)
        mean = np.mean([data1, data2], axis=0)
        diff = data1 - data2                   # Difference between data1 and data2
        md = np.mean(diff)                     # Mean of the difference
        sd = np.std(diff, axis=0)              # Standard deviation of the difference

        plt.scatter(mean, diff)
        plt.axhline(md, color='orange', linestyle='--')
        plt.axhline(0, color='black', linestyle='--')
        plt.axhline(md + 1.96 * sd, color='gray', linestyle='--')
        plt.axhline(md - 1.96 * sd, color='blue', linestyle='--')
        plt.title('Bland-Altman Plot')
        plt.xlabel('GT Value')
        plt.ylabel('Difference (uL)')
        plt.show()

    def error_value(self, volume_gt, volume_est):

        # Initialize variables for RMSE and MAE calculations
        sum_squared_errors = 0
        sum_absolute_errors = 0
        errors = []

        for gt, est in zip(volume_gt, volume_est):
            error = abs(gt - est)
            errors.append(error)
            sum_squared_errors += error ** 2
            sum_absolute_errors += error

            print(f"GT: {gt}, Estimation: {est}, Absolute Error: {error}")

        # Calculate the average absolute error
        average_error = sum_absolute_errors / len(volume_gt)
        std_dev = np.std(errors)

        # Calculate RMSE
        rmse = np.sqrt(sum_squared_errors / len(volume_gt))

        # Calculate MAE
        mae = sum_absolute_errors / len(volume_gt)

        print("Standard Deviation of Absolute Errors:", std_dev)
        print("Average Absolute Error:", average_error)
        print("Root Mean Square Error (RMSE):", rmse)
        print("Mean Absolute Error (MAE):", mae)

        # Plotting
        plt.figure()
        plt.axhline(mae, color='orange', linestyle='--')
        plt.plot(volume_gt, errors, 'o', color='mediumorchid')
        self.plot_regression_curve(volume_gt, errors, color='green', label='Linear Fit')
        plt.xlabel('Volume Ground Truth (mL)')
        plt.ylabel('Absolute Error (mL)')
        plt.title('Error Analysis in Absolute Values')
        #plt.savefig('/mnt/data/absolute_error_analysis.svg', dpi=300, format='svg', bbox_inches='tight')
        plt.show()

    def error_percentage(self, volume_gt, volume):
        # Absolute erros
        errors_abs = [abs((gt - est) / gt) * 100 if gt != 0 else 0 for gt, est in zip(volume_gt, volume)]
        std_dev = np.std(errors_abs)
        mae = np.mean(errors_abs) # Mean Absolute Error (MAE)
        rmse = np.sqrt(np.mean([e**2 for e in errors_abs])) # Root Mean Square Error (RMSE)
        print("Mean Absolute Error (MAE):", mae)
        print("Root Mean Square Error (RMSE):", rmse)
        print("Standard Deviation of Absolute Errors:", std_dev)

        # Errors
        errors = [((gt - est) / gt) * 100 if gt != 0 else 0 for gt, est in zip(volume_gt, volume)]
        std_dev = np.std(errors, ddof=1)
        n = len(errors)
        standard_error = std_dev / np.sqrt(n)
        rmse = np.sqrt(np.mean([e**2 for e in errors_abs])) # Root Mean Square Error (RMSE)
        print("Standard Error:", standard_error)


        # plt.figure()
        # plt.plot(errors, 'o', label='Errors')
        # self.plot_regression_curve(range(len(errors)), errors)
        # plt.xlabel('Index')
        # plt.ylabel('Error (%)')
        # plt.title('Error in Percentage with Regression Curve')
        # plt.legend()
        # plt.show()

        return std_dev, rmse, mae, errors, errors_abs

    def plot_regression_curve(self, x, y, color, label):
        coefficients = np.polyfit(x, y, 1)
        polynomial = np.poly1d(coefficients)

        x_line = np.linspace(min(x), max(x), 100)
        y_line = polynomial(x_line)

        plt.plot(x_line, y_line, color, label=label)
        plt.legend()

        print("Regression:", polynomial)

    def get_area_of_interest(self, rect_image, height):
        start_row = max(height - 20, 0)
        end_row = min(height, rect_image.shape[0])
        region_meniscus = np.zeros_like(rect_image)

        # Copy the specified region to region_meniscus
        region_meniscus[start_row:end_row, :] = rect_image[start_row:end_row, :]
        # cv2.imshow("region_meniscus", region_meniscus)
        # cv2.waitKey(0)

        return region_meniscus
    
    def meniscus_segmentation(self, rgb_meniscus):
        I = cv2.cvtColor(rgb_meniscus, cv2.COLOR_RGB2HSV)

        E_channel = I[:, :, 2]

        channel2Max = 130
        channel2Min = 30

        mask = ((E_channel <= channel2Max) & (E_channel >= channel2Min))
        binary_meniscus = np.zeros_like(I[:, :, 0], dtype=np.float32)
        binary_meniscus[mask] = 1.0
        binary_meniscus = (binary_meniscus * 255).astype(np.uint8)

        return binary_meniscus
 
    def get_meniscus_area_rgb(self, image_rgb_crop):
        image = self.full_processing_image(image_rgb_crop)
    
        height, _ = self.get_meniscus_height(image)
        region_meniscus = np.zeros_like(image_rgb_crop)
        start_row = max(height - 20, 0)
        end_row = min(height + 40, image_rgb_crop.shape[0])

        # Copy the specified region to region_meniscus
        region_meniscus[start_row:end_row, :] = image_rgb_crop[start_row:end_row, :]
        #cv2.imshow("io", region_meniscus)
        #cv2.waitKey(0)

        return region_meniscus
    
    def remove_noise_from_image(self, binary_image):
        #binary_image = cv2.cvtColor(binary_image, cv2.COLOR_RGB2GRAY)
        line_sum = np.sum(binary_image // 255, axis=1)
        line_sum =  line_sum.astype(np.int64)
        original_data = pd.Series(line_sum)
        filtered_data = original_data.copy()

        window_size = 5
        rolling_mean = original_data.rolling(window=window_size).mean()
        global_mean = np.mean(rolling_mean)
        threshold = 0.3

        # For each window, if its mean is significantly lower than the global mean, set all elements in that window to zero
        for i in range(window_size, len(original_data)):
            if rolling_mean[i] < global_mean * threshold:
                filtered_data[i-window_size:i] = 0

        final_data = pd.concat([filtered_data[:self.y2], pd.Series(original_data[self.y2:])], ignore_index=True)
        np_array = final_data.values
        for i, value in enumerate(np_array):
            # If the value at index i is 0, set the corresponding line in binary_image to black
            if value == 0:
                binary_image[i, :] = 0

        # return to 0-255 format
        binary_image = binary_image.astype(np.uint8)

        # Plot new data
        #plt.plot(np_array, label=self.side)
        #plt.legend()
        #plt.show()
        return binary_image
    
    def count_white_pixels(self, binary_image):
        white_pixel_count = np.sum(binary_image == 255)
        return white_pixel_count
    
    def histogram_h(self, binary_image):
        line_sum = np.sum(binary_image // 255, axis=1)

        x = np.arange(len(line_sum))

        plt.figure()
        plt.plot(x, line_sum)
        plt.xlabel('Column Index')
        plt.ylabel('Sum of Pixel Values')
        plt.title('Column Sum Histogram')
        plt.grid(True)
        plt.show()

        return 0

    def image_crop(self, image, side=None):
        if side is None:
            side = self.side

        if side == "LEFT":
            # LEFT tube coordinates
            self.rectangle_tl = (self.y1, self.x1)  # Top-left point of the rectangle
            self.rectangle_tr = (self.y1, self.x2)  # Top-right point of the rectangle
            self.rectangle_bl = (self.y3, self.x1)  # Bottom-left point of the rectangle
            self.rectangle_br = (self.y3, self.x2)  # Bottom-right point of the rectangle

        elif side == "RIGHT":
            # RIGHT tube coordinates
            self.rectangle_tl = (self.y1, self.x3)  # Top-left point of the rectangle
            self.rectangle_tr = (self.y1, self.x4)  # Top-right point of the rectangle
            self.rectangle_bl = (self.y3, self.x3)  # Bottom-left point of the rectangle
            self.rectangle_br = (self.y3, self.x4)  # Bottom-right point of the rectangle

        rect_image = image[self.rectangle_tl[0]:self.rectangle_bl[0], self.rectangle_tl[1]:self.rectangle_tr[1]]
        #rect_image = cv2.resize(rect_image, (rect_image.shape[1], rect_image.shape[0]))

        return rect_image
    
    @staticmethod
    def get_gt_volume(image_file):
        # Pattern 1: Matches a decimal number preceded by '-' followed by '.j' extension
        match = re.search(r"-(\d+\.\d+).j", image_file)
        number = None
        if match:
            number = match.group(1)
            volume_gt = float(number)*1000

        # Pattern 2: Matches a decimal number preceded by '-' followed by 'mL' extension
        if number == None:
            match = re.search(r"-(\d+\.\d+)mL", image_file)
            if match:
                number = match.group(1)
                volume_gt = float(number)*1000

        # Pattern 3: Matches a decimal number preceded by '_' and followed by 'mL' extension
        if number == None:
            match = match = re.search(r"-(\d+)-0.jpg", image_file)
            if match:
                number = match.group(1)
                volume_gt = float(number)
        if number == None:
            match = re.search(r"-(\d+).j", image_file)
            if match:
                number = match.group(1)
                volume_gt = float(number)
        
        # return volume in uL
        #print(volume_gt)
        return volume_gt
    
    def params_to_dict(self, params):
        return {chr(97 + i): coef for i, coef in enumerate(params)}
    
    def compute_poly(self, params, area):
        return sum(params[chr(97 + i)] * area**(len(params) - i - 1) for i in range(len(params)))
    
    def testing_data_no_gt(self, dataset_path):
        volumes = []

        image_files = [file for file in os.listdir(dataset_path) if file.endswith(('.jpg', '.jpeg', '.png'))]

        # Sort the files by modification time, earliest first
        image_files.sort(key=lambda x: os.path.getmtime(os.path.join(dataset_path, x)))


        for side in ["LEFT"]:
            self.side = side
            for image_file in image_files:
                image_path = os.path.join(dataset_path, image_file)
                self.volume_estimation(image_path)
                volume = self.vol_right if side == 'RIGHT' else self.vol_left
                volumes.append(volume)

        # print(volumes)
        # for i in range(1, len(volumes)):
        #     print(volumes[i] - volumes[i - 1])

        # Plotting
        plt.plot(range(len(volumes)), volumes, marker='o')
        plt.xlabel('Index')
        plt.ylabel('Volume')
        plt.title('Volume Estimation in Ascending Order')
        plt.show()

import cv2
import numpy as np
import matplotlib.pyplot as plt

class Visualization:
    def __init__(self, volume_estimation_obj):
        self.obj = volume_estimation_obj
        #self.side = volume_estimation_obj.side
    
    def process_image_side(self, full_image, side):
        image = self.obj.image_crop(full_image, side)
        height = self.obj.get_meniscus_height(image)
        binary_meniscus = self.obj.segmentation_refinement(image, height)
        #image_enhanced = self.obj.pre_processing(image)
        binary_image = self.obj.image_segmentation(image)
        binary_image_2 = binary_meniscus + binary_image
        binary_image_2[binary_image_2 > 0] = 255
        # binary_image_HUE = self.obj.HUE_filter(image)
        # binary_image = self.obj.check_bottom(binary_image)
        # binary_image = self.obj.apply_filter(binary_image)
        image_seg = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2RGB)
        image_seg_2 = cv2.cvtColor(binary_image_2, cv2.COLOR_GRAY2RGB)
        # image_seg_HUE = cv2.cvtColor(binary_image_HUE, cv2.COLOR_GRAY2RGB)
        meniscus_rgb = cv2.cvtColor(binary_meniscus, cv2.COLOR_GRAY2RGB)
        
        H_channel, U_channel, E_channel = self.HUE_space(image)
        self.plot_HUE_channels(image, side)
        
        return {
            'enhanced': self.plot_grid(image_seg),
            'image':    self.plot_grid(meniscus_rgb),
            'segmented': self.plot_grid(image_seg_2),
            'H_channel': self.plot_grid(H_channel),
            'U_channel': self.plot_grid(U_channel),
            'E_channel': self.plot_grid(E_channel),
            'white_pixels': self.obj.count_white_pixels(image_seg)
        }

    def visualization(self, full_image):
        sides = ['RIGHT', 'LEFT']
        for side in sides:
            data = self.process_image_side(full_image, side)
            
            concatenated_image = np.concatenate((data['image'], data['enhanced'], data['segmented']), axis=1)
            concatenated_HUE = np.concatenate((data['H_channel'], data['U_channel'], data['E_channel']), axis=1)
            
            cv2.imshow(f'Concatenated {side.capitalize()} Image', concatenated_image)
            cv2.imshow(f'Concatenated HUE {side.capitalize()} Image', concatenated_HUE)
            
            print(side, data['white_pixels'])
        
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        return 0
    
    def plot_grid(self, image):
        h = image.shape
        #image = cv2.resize(image, (int(1.8* h[1]),  int(1.8* h[0])))
        grid_size = 20
        color = (255, 0, 0)  # White color in BGR format
        # Check if the input image is single-channel or RGB
        if len(image.shape) == 2:
            # Single-channel image, convert it to a 3-channel image
            image_3ch = cv2.merge([image, image, image]).copy()
        elif len(image.shape) == 3 and image.shape[2] == 3:
            # RGB image, create a copy to avoid modifying the original image
            image_3ch = image.copy()
        else:
            raise ValueError("Invalid image format. The image must be single-channel or RGB with 3 channels.")
        height, width = image_3ch.shape[:2]
        for x in range(grid_size, width, grid_size):
            cv2.line(image_3ch, (x, 0), (x, height), color, 1)
        for y in range(grid_size, height, grid_size):
            cv2.line(image_3ch, (0, y), (width, y), color, 1)
        # If the original image was single-channel, convert back to single-channel before returning
        if len(image.shape) == 2:
            image_with_grid = cv2.cvtColor(image_3ch, cv2.COLOR_BGR2GRAY)
        else:
            image_with_grid = image_3ch
        return image
    
    def HUE_space(self, image_rgb_crop):
        # Convert the image to HSV color space
            image_hsv = cv2.cvtColor(image_rgb_crop, cv2.COLOR_RGB2HSV)
            #image_hsv = cv2.GaussianBlur(image_hsv, (15, 15), 0)
            # Extract the H, U, and E channels
            H_channel = image_hsv[:, :, 0]  
            U_channel = image_hsv[:, :, 1]  
            E_channel = image_hsv[:, :, 2]

            # H_channel = cv2.merge([H_channel, H_channel, H_channel])
            # U_channel = cv2.merge([U_channel, U_channel, U_channel])
            # E_channel = cv2.merge([E_channel, E_channel, E_channel])
            # cv2.imshow('H Channel', H_channel)
            # cv2.imshow('U Channel', U_channel)
            # cv2.imshow('E_channel', E_channel)
            # cv2.waitKey(0)

            return H_channel, U_channel, E_channel
    
    def full_processing_image_height(self, rect_image):
        hsv_image = cv2.cvtColor(rect_image, cv2.COLOR_BGR2HSV)
        H_channel = hsv_image[:, :, 0]
        U_channel = hsv_image[:, :, 1]
        E_channel = hsv_image[:, :, 2]

        H_sum = np.sum(H_channel, axis=1)
        U_sum = np.sum(U_channel, axis=1)
        E_sum = np.sum(E_channel, axis=1)

        # Create the x-values, which will be the same for each channel (i.e., row indices)
        x = np.arange(len(H_sum))

        height = self.get_meniscus_height(U_channel, E_channel)
        binary_image = np.zeros_like(E_channel)
        binary_image[:height, :] = 0 
        binary_image[height:, :] = 255
        #print(height)

        # plt.figure()
        
        # plt.plot(x, H_sum, label='H channel', color='r')
        # plt.plot(x, U_sum, label='U channel', color='g')
        # plt.plot(x, E_sum, label='E channel', color='b')
        
        # plt.xlabel('Row Index')
        # plt.ylabel('Sum of Pixel Values')
        # plt.title(height)
        # plt.legend()
        # plt.grid(True)
        # plt.show()

        return binary_image
    

    def plot_HUE_channels(self, image, side):
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Extract the Hue channel
        hue_channel = hsv_image[:, :, 0]
        saturation_channel = hsv_image[:, :, 1]
        value_channel = hsv_image[:, :, 2]

        # Compute the row-wise sum for each channel
        hue_row_sum = np.sum(hue_channel, axis=1)
        saturation_row_sum = np.sum(saturation_channel, axis=1)
        value_row_sum = np.sum(value_channel, axis=1)

        # Plot the row-wise sum for each channel separately
        plt.figure(figsize=(12, 8))

        # Row-wise sum of Saturation channel
        plt.subplot(3, 1, 1)
        plt.plot(hue_row_sum, color='r')
        plt.title(side)
        plt.ylabel("Sum")

        plt.subplot(3, 1, 2)
        plt.plot(saturation_row_sum, color='g')
        plt.title("")
        plt.ylabel("Sum")

        plt.subplot(3, 1, 3)
        plt.plot(value_row_sum, color='b')
        plt.title("")
        plt.ylabel("Sum")
        plt.xlabel("Row Number")

        plt.tight_layout()
        #plt.savefig("rowwise_sum_plot.png", dpi=300)
        plt.show()

# Usage:

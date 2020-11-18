'''
Example script to run segmentation network on MDLA
Models: Resnet34 and Resnet18
'''
import sys
sys.path.append("..")
import microndla

import numpy as np


# Color Palette
CP_R = '\033[31m'
CP_G = '\033[32m'
CP_B = '\033[34m'
CP_Y = '\033[33m'
CP_C = '\033[0m'


class Resnet34_18DLA:
    """
    Load MDLA and run segmentation model on it
    """
    def __init__(self, input_img, bitfile, model_path1,model_path2):
        """
        In this example MDLA will be capable of taking multiple input images
        and running that images through 2 models on 1 fpga 
        """

        print('{:-<80}'.format(''))
        print('{}{}{}...'.format(CP_Y, 'Initializing MDLA', CP_C))
        ################################################################################
        # Initialize 1 Micron DLA
        self.dla = microndla.MDLA()
        # Run the network in batch mode (one image on all clusters)
       #self.dla.SetFlag('nobatch', '0')
        numfpga = 1 
        numclus = 1
        self.batch, self.height, self.width, self.channels = input_img.shape
        sz = "{:d}x{:d}x{:d}".format(self.width, self.height, self.channels)

        # Compile the NN and generate instructions <save.bin> for MDLA
        swnresults1 = self.dla.Compile(sz, model_path1, 'save.bin', numfpga,numclus)
        swnresults2 = self.dla.Compile(sz, model_path2, 'save2.bin',numfpga,numclus)
        self.dla.Loadmulti(('save.bin', 'save2.bin'))

        print('\n1. {}{}{}!!!'.format(CP_B, 'Successfully generated binaries for MDLA', CP_C))
        
        # Send the generated instructions to MDLA
        # Send the bitfile to the FPGA only during the first run
        # Otherwise bitfile is an empty string
        nresults = self.dla.Init('',bitfile)
        
        print('2. {}{}{}!!!'.format(CP_B, 'Finished loading bitfile on FPGA', CP_C))
        print('\n{}{}{}!!!'.format(CP_G, 'MDLA initialization complete', CP_C))
        print('{:-<80}\n'.format(''))

        # Allocate space for output if the model
        output1 = np.ascontiguousarray(np.zeros(swnresults1, dtype=np.float32))
        output2 = np.ascontiguousarray(np.zeros(swnresults2, dtype=np.float32))
        self.dla_output=(output1,output2)


    def __call__(self, input_img1,input_img2):
        return self.forward(input_img1,input_img2)


    def __del__(self):
        self.dla.Free()

    def normalize(self, img, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]):
        img[:,:,0] = (img[:,:,0] - mean[2]) / std[2]
        img[:,:,1] = (img[:,:,1] - mean[1]) / std[1]
        img[:,:,2] = (img[:,:,2] - mean[0]) / std[0]
        return img

    def forward(self, input_img1,input_img2):
        # Normalize and transpose image 1
        img1 = input_img1.astype(np.float32) / 255.0
        img1 = self.normalize(img1)
        img1 = img1.transpose(2, 0, 1) # Change image planes from HWC to CHW

        x1 = np.ascontiguousarray(img1)            

        # Normalize and transpose image 2
        img2 = input_img2.astype(np.float32) / 255.0
        img2 = self.normalize(img2)
        img2 = img2.transpose(2, 0, 1) # Change image planes from HWC to CHW

        x2 = np.ascontiguousarray(img2)            
        
        self.dla.Run((x1,x2), self.dla_output)
        y = self.dla_output # Reshape the output vector into CHW

        return y[0],y[1]


# https://www.pyimagesearch.com/2017/06/19/image-difference-with-opencv-and-python/
# import the necessary packages
from PIL import Image
import imutils
import cv2
 
original = Image.open('dataset/training_set/dogs/dog.175.jpg', 'r')
transparent = Image.open('dog_transparent.png', 'r')

alphaO = original.tobytes("raw","A")
print(len(alphaO))
alphaT = transparent.tobytes("raw","A")
print(len(alphaT))


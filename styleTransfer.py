# Code from https://github.com/walid0925/AI_Artistry/blob/master/main.py

import numpy as np
import pandas as pd
import tensorflow as tf
from PIL import Image
from keras import backend as K
from keras.preprocessing.image import load_img, img_to_array
from keras.applications import VGG16
from keras.applications.vgg16 import preprocess_input
from keras.layers import Input
from scipy.optimize import fmin_l_bfgs_b
import time
import os

# Select GPU and limit memory usage
os.environ["CUDA_VISIBLE_DEVICES"]="0"
gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=.33)
sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
## Specify paths for 1) content image 2) style image
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
cImPath = 'dataset/training_set/dogs/dog.175.jpg'
sImPath = []
sImPath.append('Styles/tsunami.jpg')
sImPath.append('Styles/the_scream.jpg')

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
## Image processing
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
targetHeight = 512
targetWidth = 512
targetSize = (targetHeight, targetWidth)

cImageOrig = Image.open(cImPath)
cImageSizeOrig = cImageOrig.size
cImage = load_img(path=cImPath, target_size=targetSize)
cImArr = img_to_array(cImage)
cImArr = K.variable(preprocess_input(np.expand_dims(cImArr, axis=0)), dtype='float32')

sImage = []
sImArr = []

for i in range(len(sImPath)):
	sImage.append(load_img(path=sImPath[i], target_size=targetSize))
	sImArr.append(img_to_array(sImage[i]))
	sImArr[i] = K.variable(preprocess_input(np.expand_dims(sImArr[i], axis=0)), dtype='float32')

gIm0 = np.random.randint(256, size=(targetWidth, targetHeight, 3)).astype('float64')
gIm0 = preprocess_input(np.expand_dims(gIm0, axis=0))

gImPlaceholder = K.placeholder(dtype="float",shape=(1, targetWidth, targetHeight, 3))

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
## Define loss and helper functions
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##

def get_feature_reps(x, layer_names, model):
    featMatrices = []
    for ln in layer_names:
        selectedLayer = model.get_layer(ln)
        featRaw = selectedLayer.output
        featRawShape = K.shape(featRaw).eval(session=tf_session)
        N_l = featRawShape[-1]
        M_l = featRawShape[1]*featRawShape[2]
        featMatrix = K.reshape(featRaw, (M_l, N_l))
        featMatrix = K.transpose(featMatrix)
        featMatrices.append(featMatrix)
    return featMatrices

def get_content_loss(F, P):
    cLoss = 0.5*K.sum(K.square(F - P))
    return cLoss

def get_Gram_matrix(F):
    G = K.dot(F, K.transpose(F))
    return G

def get_style_loss(ws, Gs, As):
    sLoss = K.variable(0.)
    for w, G, A in zip(ws, Gs, As):
        M_l = K.int_shape(G)[1]
        N_l = K.int_shape(G)[0]
        G_gram = get_Gram_matrix(G)
        A_gram = get_Gram_matrix(A)
        sLoss = sLoss +  w*0.25*K.sum(K.square(G_gram - A_gram))/ (N_l**2 * M_l**2)
    return sLoss

def get_total_loss(gImPlaceholder, alpha=1.0, beta=10000.0):
    F = get_feature_reps(gImPlaceholder, layer_names=[cLayerName], model=gModel)[0]
    Gs = get_feature_reps(gImPlaceholder, layer_names=sLayerNames, model=gModel)
    contentLoss = get_content_loss(F, P)
    styleLossArr = []
    styleLoss = 0
    for i in range(len(sImPath)):
        styleLossArr.append(get_style_loss(ws, Gs, As[i]))
        styleLoss = styleLoss + styleLossArr[i]
    totalLoss = alpha*contentLoss + beta*styleLoss
    return totalLoss

def calculate_loss(gImArr):
    """
    Calculate total loss using K.function
    """
    if gImArr.shape != (1, targetWidth, targetWidth, 3):
        gImArr = gImArr.reshape((1, targetWidth, targetHeight, 3))
    loss_fcn = K.function([gModel.input], [get_total_loss(gModel.input)])
    return loss_fcn([gImArr])[0].astype('float64')

def get_grad(gImArr):
    """
    Calculate the gradient of the loss function with respect to the generated image
    """
    if gImArr.shape != (1, targetWidth, targetHeight, 3):
        gImArr = gImArr.reshape((1, targetWidth, targetHeight, 3))
    grad_fcn = K.function([gModel.input], K.gradients(get_total_loss(gModel.input), [gModel.input]))
    grad = grad_fcn([gImArr])[0].flatten().astype('float64')
    return grad

def postprocess_array(x):
    # Zero-center by mean pixel
    if x.shape != (targetWidth, targetHeight, 3):
        x = x.reshape((targetWidth, targetHeight, 3))
    x[..., 0] = x[..., 0] + 103.939
    x[..., 1] = x[..., 1] + 116.779
    x[..., 2] = x[..., 2] + 123.68
    # 'BGR'->'RGB'
    x = x[..., ::-1]
    x = np.clip(x, 0, 255)
    x = x.astype('uint8')
    return x

def reprocess_array(x):
    x = np.expand_dims(x.astype('float64'), axis=0)
    x = preprocess_input(x)
    return x

def save_original_size(x, iter, target_size=cImageSizeOrig):
    xIm = Image.fromarray(x)
    xIm = xIm.resize(target_size)
    xIm.save('Results/resultTsunamiScreamDog%d.jpg' % (iter))
    return xIm

tf_session = K.get_session()
cModel = VGG16(include_top=False, weights='imagenet', input_tensor=cImArr)
sModel = []
for i in range(len(sImPath)):
	sModel.append(VGG16(include_top=False, weights='imagenet', input_tensor=sImArr[i]))
gModel = VGG16(include_top=False, weights='imagenet', input_tensor=gImPlaceholder)
cLayerName = 'block4_conv2'
sLayerNames = [
                'block1_conv1',
                'block2_conv1',
                'block3_conv1',
                'block4_conv1',
                #'block5_conv1'
                ]

P = get_feature_reps(x=cImArr, layer_names=[cLayerName], model=cModel)[0]
As = []
for i in range(len(sImPath)):
	As.append(get_feature_reps(x=sImArr[i], layer_names=sLayerNames, model=sModel[i]))
ws = np.ones(len(sLayerNames))/float(len(sLayerNames))

# Allows saving images at increasing runtimes
iterations = 1 
base = 200
x_val = gIm0.flatten()
for iteration in range(1, iterations+1):
	start = time.time()
	xopt, f_val, info= fmin_l_bfgs_b(calculate_loss, x_val, fprime=get_grad,
		                    maxiter=iteration * base, disp=True)
	xOut = postprocess_array(xopt)
	xIm = save_original_size(xOut, iteration*base)
	print('Image saved')
	end = time.time()
	print('Time taken: {}'.format(end-start))

# https://stackoverflow.com/questions/10640114/overlay-two-same-sized-images-in-python
background = Image.open('Results/resultTsunamiScreamDog%d.jpg' % (iterations * base))
foreground = Image.open('dogTransparent.png')
background.paste(foreground, (0,0), foreground)
background.save('ArtDog.png', 'PNG')

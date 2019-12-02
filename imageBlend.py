# https://stackoverflow.com/questions/10640114/overlay-two-same-sized-images-in-python
from PIL import Image

background = Image.open('Results/resultTsunamiScreamDog300.jpg')
foreground = Image.open('dogTransparent.png')
background.paste(foreground, (0,0), foreground)
background.save('ArtDog.png', 'PNG')

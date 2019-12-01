# https://stackoverflow.com/questions/10640114/overlay-two-same-sized-images-in-python
from PIL import Image

background = Image.open('resultDog600.jpg')
foreground = Image.open('dog_transparent.png')
background.paste(foreground, (0,0), foreground)
background.save('ArtDog.png', 'PNG')
#overlay = Image.alpha_composite(overlay, overlay)

#overlay.save('new.png', 'PNG')
#background = background.convert("RGBA")
#overlay = overlay.convert("RGBA")

#new_img = Image.alpha_composite(background, overlay)
#new_img = Image.blend(background, overlay, .25)
#new_img.save("new.png","PNG")

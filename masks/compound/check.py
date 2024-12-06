from PIL import Image
import glob

files = glob.glob("masks/compound/*.png")

# check if there are identical images
def are_images_identical(img1, img2):
    return list(img1.getdata()) == list(img2.getdata())

for i in range(len(files)):
    for j in range(i + 1, len(files)):
        img1 = Image.open(files[i])
        img2 = Image.open(files[j])
        if are_images_identical(img1, img2):
            print(f"Identical images found: {files[i]} and {files[j]}")

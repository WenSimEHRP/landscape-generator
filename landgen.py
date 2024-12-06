from PIL import Image, ImageTransform, ImageEnhance
import masks
import sys
import os


class TransformImage:

    def __init__(self, path, resolution=1, strength=1):
        self.path = path
        self._img = None  # original image
        self._imgs = None  # transformed images
        self.resolution = resolution
        self.strength = strength

    @property
    def img(self):
        if self._img is None:
            with Image.open(self.path) as img:
                # resize the image to square shaped, use nearest neighbour to keep the pixel sharp
                self._img = img.resize(
                    (2 * 64 * self.resolution,) * 2
                )
        return self._img

    @property
    def imgs(self):
        if self._imgs is None:
            self._imgs = {
                ind: {
                    i: self.darken_image(self.apply_crop(v, ind), ind)
                    for i, v in val.items()
                }
                for ind, val in self.apply_transform().items()
            }
        return self._imgs

    def apply_transform(self):
        d = {}
        for i in range(4):
            deg = i * 90
            img = self.img.copy().rotate(deg)
            for ind, val in enumerate(masks.TRANSFORM_MATRIX.items()):
                name, matrix = val
                d[name] = {**d.get(name, {}), i: None}
                # mirror from regular coordinates
                combo = (masks.MIRROR @ matrix).tolist()
                combo = list(zip(*combo))

                new_width = round(img.width * 1.5)
                new_height = round(img.height * 1.5)

                img_center_x = img.width / 2
                img_center_y = img.height / 2

                transformed_center_x = (
                    combo[0][0] * img_center_x + combo[0][1] * img_center_y
                )
                transformed_center_y = (
                    combo[1][0] * img_center_x + combo[1][1] * img_center_y
                )

                c = (new_width / 2) - transformed_center_x * 4
                f = (new_height / 2) - transformed_center_y * 4

                a = img.transform(
                    (new_width * 2, new_height * 2),
                    ImageTransform.AffineTransform(combo[0] + (c,) + combo[1] + (f,)),
                )
                d[name][i] = a
        return d

    @staticmethod
    def apply_crop(img, mask_path):
        a = img.copy()
        bbox = a.getbbox()
        if bbox:
            a = a.crop(bbox)
        with Image.open("masks/" + mask_path + ".png") as mask:
            new_size = (mask.width + 2, round((mask.width + 2) / a.width * a.height))
            a = a.resize(new_size)
            a = TransformImage.apply_mask("masks/" + mask_path + ".png", a).convert(
                "RGBA"
            )
        return a

    def darken_image(self, img, factor):
        match factor:
            case "flat_land":
                c = 1.0
            case "cliff_right" | "slope_front_right":
                c = 1 + 0.3 * self.strength**0.5
            case "cliff_front":
                c = 1 + 0.15 * self.strength**0.5
            case "cliff_back" | "slope_front_left" | "cliff_left" | "slope_back_left":
                c = 1 - 0.5 * self.strength**0.5
            case "slope_back_right":
                c = 1 - 0.25 * self.strength**0.5
            case _:
                raise ValueError("Invalid mask")
        enhancer = ImageEnhance.Brightness(img)
        a = enhancer.enhance(c).convert("RGBA")
        return a

    @staticmethod
    def apply_mask(mask_path, img):
        a = img.copy()
        # load mask file
        with Image.open(mask_path) as mask:
            mask = mask.convert("L")
        # create a new image with the same size as the original image and put the mask on its centre
        new_img = Image.new("L", a.size, 0)
        new_img.paste(
            mask,
            (
                (a.width - mask.width) // 2,
                (a.height - mask.height) // 2,
            ),
        )
        # apply the mask to the transformed image
        a.putalpha(new_img)
        bbox = a.getbbox()
        if bbox:
            a = a.crop(bbox)
        return a


def compose_images(img: TransformImage, mask):
    d = {}
    for i in range(4):
        compose = {}
        for mi, mv in mask.items():
            # mi = the mask type
            # mv = the mask path
            m = Image.open("masks/compound/" + mv)
            a = img.imgs[mi][i].copy()
            a = a.convert("RGBA")
            a.putalpha(m.convert("L"))
            # crop
            bbox = a.getbbox()
            if bbox:
                a = a.crop(bbox)
            for n in ("right", "left", "upper", "lower"):
                if n in mv:
                    compose[n] = a
        if "right" in compose and "left" in compose:
            # merge the right and left images side by side
            new_width = compose["right"].width + compose["left"].width
            new_height = max(compose["right"].height, compose["left"].height)
            new_img = Image.new("RGBA", (new_width, new_height))
            new_img.paste(compose["left"], (0, 0))
            new_img.paste(compose["right"], (compose["left"].width, 0))
            d[i] = new_img
        elif "upper" in compose and "lower" in compose:
            # merge the upper and lower images top and bottom
            new_width = max(compose["upper"].width, compose["lower"].width)
            new_height = compose["upper"].height + compose["lower"].height - 1
            new_img = Image.new("RGBA", (new_width, new_height))
            new_img.paste(compose["upper"], (0, 0))
            new_img.paste(compose["lower"], (0, compose["upper"].height - 1))
            d[i] = new_img
        else:
            print(
                compose.keys(),
            )
            raise ValueError("Invalid mask")
    return d


def main(input_path, output_path, strength = 0.25):
    try:
        img = TransformImage(input_path, 1, strength)
    except FileNotFoundError:
        print("Invalid path")
        sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(1)
    for i, v in masks.mask_list.items():
        compose_images(img, v)
    output_imgs = {i: compose_images(img, v) for i, v in masks.mask_list.items()}
    output_imgs = {
        **output_imgs,
        **{masks.order_translation[i]: v for i, v in img.imgs.items()},
    }
    for ind, val in output_imgs.items():
        for i, v in val.items():
            v = v.convert("RGBA")
            v.save(f"{output_path}/{i}/" + f"{ind}" + ".png")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python lib.py <input_path> <output_dir> <strength>","suggested strength: 0.25", sep="\n")
        sys.exit(1)
    try:
        strength = float(sys.argv[3])
    except ValueError:
        print("Invalid strength")
        sys.exit(1)
    for i in range(4):
        os.makedirs(f"{sys.argv[2]}/{i}/", exist_ok=True)
    main(sys.argv[1], sys.argv[2], strength)

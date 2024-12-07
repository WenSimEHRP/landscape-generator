from PIL import Image, ImageTransform, ImageEnhance
import masks
import os
import argparse


class TransformImage:
    def __init__(self, path, resolution=1, strength=1, diagonal=False):
        self.path = path
        self._img = None  # original image
        self._imgs = None  # transformed images
        self.resolution = resolution
        self.strength = strength
        self.diagonal = diagonal

    @property
    def img(self):
        if self._img is None:
            with Image.open(self.path) as img:
                # resize the image to square shaped, use nearest neighbour to keep the pixel sharp
                self._img = img.resize((2 * 64 * self.resolution,) * 2)
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
        for i in range(8 if self.diagonal else 4):
            deg = i * 90
            if i >= 4:
                # create a larger version of the image first, paste the original image 9 times, rotate it, and crop it
                img = self.img.copy().resize((self.img.width * 3, self.img.height * 3))
                for x in range(3):
                    for y in range(3):
                        img.paste(self.img, (self.img.width * x, self.img.height * y))
                # rotate the image
                img = img.rotate(deg + 45)
                # crop the image and zoom
                img = img.crop(
                    (
                        self.img.width,
                        self.img.height,
                        self.img.width * 2,
                        self.img.height * 2,
                    )
                )
            else:
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


def compose_images(img: TransformImage, mask, diagonal_slopes=False):
    d = {}
    t = {}
    for i in range(len(next(iter(img.imgs.values())))):
        compose = {}
        for mi, mv in mask.items():
            m = Image.open("masks/compound/" + mv)
            c = i
            if diagonal_slopes and "cliff" in mi:
                if "lower" in mv or "upper" in mv:
                    print("yes")
                    c += 3
                c = (c + 4) % 8
            a = img.imgs[mi][c].copy().convert("RGBA")
            a.putalpha(m.convert("L"))
            bbox = a.getbbox()
            if bbox:
                a = a.crop(bbox)
            for n in ("right", "left", "upper", "lower"):
                if n in mv:
                    compose[n] = a
        t[i] = compose

    for i, compose in t.items():

        if "right" in compose and "left" in compose:
            new_width = compose["right"].width + compose["left"].width
            new_height = max(compose["right"].height, compose["left"].height)
            new_img = Image.new("RGBA", (new_width, new_height))
            new_img.paste(compose["left"], (0, 0))
            new_img.paste(compose["right"], (compose["left"].width, 0))
            d[i] = new_img
        elif "upper" in compose and "lower" in compose:
            new_width = max(compose["upper"].width, compose["lower"].width)
            new_height = compose["upper"].height + compose["lower"].height - 1
            new_img = Image.new("RGBA", (new_width, new_height))
            new_img.paste(compose["upper"], (0, 0))
            new_img.paste(compose["lower"], (0, compose["upper"].height - 1))
            d[i] = new_img
        else:
            raise ValueError("Invalid mask")
    return d


def main(args):
    try:
        img = TransformImage(
            args.input_path, args.resolution, args.strength, args.diagonal
        )
    except FileNotFoundError:
        print("Invalid path")
        return
    except Exception as e:
        print(e)
        return
    output_imgs = {
        **{
            i: compose_images(img, v, args.diagonal_on_slopes)
            for i, v in masks.mask_list.items()
        },
        **{masks.order_translation[i]: v for i, v in img.imgs.items()},
    }
    if args.diagonal_on_slopes:
        output_imgs[12][0] = output_imgs[12][1]
        output_imgs[3][0] = output_imgs[3][1]
        output_imgs[15][0] = output_imgs[15][5]
        output_imgs[16][0] = output_imgs[16][7]
        output_imgs[17][0] = output_imgs[17][6]
        output_imgs[18][0] = output_imgs[18][4]
    for ind, val in output_imgs.items():
        for i, v in val.items():
            v = v.convert("RGBA")
            v.save(f"{args.output_dir}/{i}/" + f"{ind}" + ".png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some images")
    parser.add_argument(
        "-i", "--input-path", type=str, required=True, help="Path to the input file"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        required=True,
        help="Directory to save the output",
    )
    parser.add_argument(
        "-s",
        "--strength",
        type=float,
        default=0.25,
        help="Strength value (suggested: 0.25)",
    )
    parser.add_argument(
        "-d",
        "--diagonal",
        action="store_true",
        default=False,
        help="Output diagonal textures",
    )
    parser.add_argument(
        "-n",
        "--diagonal-on-slopes",
        action="store_true",
        default=False,
        help="Output diagonal textures on slopes",
    )
    parser.add_argument(
        "-r", "--resolution", type=int, default=1, help="Resolution of the output image"
    )
    args = parser.parse_args()

    for i in range(8 if args.diagonal else 4):
        os.makedirs(f"{args.output_dir}/{i}/", exist_ok=True)
    main(args)

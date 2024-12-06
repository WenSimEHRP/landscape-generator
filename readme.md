# Landscape Generator

A simple command-line landscape generator for use with OpenTTD.

Usage:

```sh
python3 <input_path> <output_path> <shadow_strength>
```

- `input_path`: the path to the image
- `output_path`: where to put the output
- `shadow_strength`: controls shadow strength

This program produces 4 set of landscape sprite (4*19=76 sprites in total), with each set facing a different direction.
The output is in **32bpp 1x**, so make sure to either remap the colours or encode 32bpp flags into your GRF.

Licensed under the MIT license.

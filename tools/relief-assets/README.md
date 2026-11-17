# Portrait relief source

`baby-cutout-grayscale.png` is a background-free grayscale edit of the photograph supplied for this model. The cutout was prepared with the image editing tool; it is a derived image, not the untouched original photograph. It retains the visible baby and clothing in the supplied orientation. Review the cutout when assessing likeness.

`baby-heightmap.npz` is the committed numerical asset used by the model generator. It contains `heights` (millimeters; row zero is the bottom), and the physical `width` and `height`. Keeping this array in the repository makes normal regeneration independent of image services and Pillow. The background maps to zero, dark tones recess, and highlights rise. This is a tonal relief, not a reconstruction of anatomical depth.

The optional `prepare.py` reproduces the height map from the committed cutout. It needs Pillow 13.0.0 in addition to the repository's NumPy. It crops to the visible alpha bounds, fits within 90 × 70 mm without changing aspect ratio, samples a 321 × 251 grid, lightly smooths grayscale/alpha, normalizes the 3rd–97th foreground luminance percentiles, and maps tones from −0.45 to +0.9 mm multiplied by alpha. The model samples this field into watertight brick skins at approximately 0.35 mm spacing. The supplied cutout itself is not modified by the preprocessing script.

Run model regeneration from the repository root with `python models/photo-relief-wall/generate.py`. To make a smaller wall, change its LEGO-grid layout and image fit; do not uniformly scale the STL, which would also scale the studs and clutch geometry.

# Inkscape Export Layers 2

Inkscape extension to export SVG layers as standalone PNG, SVG or JPEG images.
The exported images can be a combination of multiple layers.

## How it works

To export your Inkscape file as an image open an inkscape file with multiple layers
(otherwise you can simply use the in-built export tool `Ctrl + E`).

There are two options for your layers when exporting:
- `[fixed]`: If a layer label starts with the prefix `[fixed]` this layer is always exported and
combined with other layers. It is very useful for backgrounds or fixed elements.
- `[export]`: If a layer label starts with `[export]` this layer is exported along with any `[fixed]` layer and
combined into a single image.

The order of layers remains untouched during export, i.e. a higher layer in the layer list is drawn above lower layers.

**Example**

![Layer export example](http://i.imgur.com/StUpSd1.png)

The layer `[fixed] Background` is a fixed layer and will always be exported combined with the `[export]` layers.

Once export is complete, we get two images: the combination of `version 1` + `Background` and
`version 2` + `Background`.

## How to use

To use the extension once your layers are ready:

1. Go to `Extensions` > `Export` > `Export layers...`
1. Type or paste the path of a directory you want to export your files to (unfortunately,
Inkscape does not support file selection dialogs for extensions).
1. Choose area to export - either document canvas area or contents area. 
1. Choose a format of your export - `PNG`, `SVG` or `JPEG` (`JPEG` required the `ImageMagick` installed in your system).
1. Choose a required DPI.
1. Choose whether to enumerate exported files with prefixes (`001_`, `002_` etc).
1. Click `Apply`.

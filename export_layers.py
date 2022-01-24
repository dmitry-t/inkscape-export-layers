#!/usr/bin/env python3

from pathlib import Path
import collections
import contextlib
import copy
import shutil
import subprocess
import sys
import tempfile

sys.path.append('/usr/share/inkscape/extensions')
import inkex

# inkex.localization.localize()

Layer = collections.namedtuple('Layer', ['id', 'label', 'tag'])
Export = collections.namedtuple('Export', ['visible_layers', 'file_name'])

FIXED = '[fixed]'
F = '[f]'
EXPORT = '[export]'
E = '[e]'

PDF = 'pdf'
SVG = 'svg'
PNG = 'png'
JPEG = 'jpeg'


class LayerExport(inkex.Effect):
    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument('-o', '--output-source',
                            type=Path,
                            default='~/',
                            help='Path to source file in output directory')
        parser.add_argument('--output-subdir',
                            default='',
                            help='Name of sub-directory in output path')
        parser.add_argument('-f', '--file-type',
                            choices=(PDF, PNG, SVG, JPEG),
                            help='Exported file type')
        parser.add_argument('--fit-contents',
                            type=inkex.Boolean,
                            help='Fit output to content bounds')
        parser.add_argument('--dpi',
                            type=int,
                            help="Export DPI value")
        parser.add_argument('--enumerate',
                            type=inkex.Boolean,
                            help="Prefix for exported file names")
        parser.add_argument('--show-layers-below',
                            type=inkex.Boolean,
                            help="Show exported layers below the current layer")

    def effect(self):
        # get output dir from specified source file
        # otherwise set it as $HOME
        source = self.options.output_source.expanduser()
        source = self.options.output_source
        if source.is_file():
            output_dir = source.parent
            prefix = source.stem + '_'
        elif source.is_dir():
            # change the default filled in by inkscape to $HOME
            if source == Path(self.ext_path()):
                output_dir = Path.home()
                prefix = ''
            else:
                output_dir = source
                prefix = ''
        else:
            # a new directory to be created
            output_dir = source
            prefix = ''

        # add subdir if one was passed
        output_dir = output_dir / self.options.output_subdir

        output_dir.mkdir(exist_ok=True)

        layer_list = self.get_layer_list()
        export_list = self.get_export_list(
            layer_list, self.options.show_layers_below)

        with _make_temp_directory() as tmp_dir:
            for export in export_list:
                svg_file = self.export_to_svg(export, tmp_dir)

                if self.options.file_type == PNG:
                    if not self.convert_svg_to_png(svg_file, output_dir, prefix):
                        break
                elif self.options.file_type == SVG:
                    if not self.convert_svg_to_svg(svg_file, output_dir, prefix):
                        break
                elif self.options.file_type == PDF:
                    if not self.convert_svg_to_pdf(svg_file, output_dir, prefix):
                        break
                elif self.options.file_type == JPEG:
                    if not self.convert_png_to_jpeg(
                            self.convert_svg_to_png(svg_file, tmp_dir, prefix),
                            output_dir, prefix=''):
                        break

    def get_layer_list(self):
        """
        Make a list of layers in source svg file
        Elements of the list are of the form (id, label (layer name), tag ('[fixed]' or '[export]')
        """
        svg_layers = self.document.xpath('//svg:g[@inkscape:groupmode="layer"]',
                                         namespaces=inkex.NSS)
        layer_list = []

        for layer in svg_layers:
            label_attrib_name = '{%s}label' % layer.nsmap['inkscape']
            if label_attrib_name not in layer.attrib:
                continue

            layer_id = layer.attrib['id']
            layer_label = layer.attrib[label_attrib_name]

            if layer_label.lower().startswith(FIXED):
                layer_type = FIXED
                layer_label = layer_label[len(FIXED):].lstrip()
            elif layer_label.lower().startswith(F):
                layer_type = FIXED
                layer_label = layer_label[len(F):].lstrip()
            elif layer_label.lower().startswith(EXPORT):
                layer_type = EXPORT
                layer_label = layer_label[len(EXPORT):].lstrip()
            elif layer_label.lower().startswith(E):
                layer_type = EXPORT
                layer_label = layer_label[len(E):].lstrip()
            else:
                continue

            layer_list.append(Layer(layer_id, layer_label, layer_type))

        return layer_list

    def get_export_list(self, layer_list, show_layers_below):
        """selection of layers that should be visible

            Each element of this list will be exported in its own file
        """
        export_list = []

        for counter, layer in enumerate(layer_list):
            # each layer marked as '[export]' is the basis for making a figure that will be exported

            if layer.tag == FIXED:
                # Fixed layers are not the basis of exported figures
                continue

            elif layer.tag == EXPORT:
                # determine which other layers should appear in this figure
                visible_layers = set()
                layer_is_below = True
                for other_layer in layer_list:
                    if other_layer.tag == FIXED:
                        # fixed layers appear in all figures
                        # irrespective of their position relative to other layers
                        visible_layers.add(other_layer.id)
                    else:
                        if other_layer.id == layer.id:
                            # the basis layer for this figure is always visible
                            visible_layers.add(other_layer.id)
                            # all subsequent layers will be above
                            layer_is_below = False

                        elif layer_is_below and show_layers_below:
                            visible_layers.add(other_layer.id)

                layer_name = layer.label
                if self.options.enumerate:
                    layer_name = '{:03d}_{}'.format(counter + 1, layer_name)

                export_list.append(Export(visible_layers, layer_name))
            else:
                # layers not marked as FIXED of EXPORT are ignored
                pass

        return export_list

    def export_to_svg(self, export: Export, output_dir: Path) -> Path:
        """
        Export a current document to an Inkscape SVG file.
        :arg Export export: Export description.
        :arg str output_dir: Path to an output directory.
        :return Output file path.
        """
        document = copy.deepcopy(self.document)

        svg_layers = document.xpath('//svg:g[@inkscape:groupmode="layer"]',
                                    namespaces=inkex.NSS)

        for layer in svg_layers:
            if layer.attrib['id'] in export.visible_layers:
                layer.attrib['style'] = 'display:inline'
            else:
                document.getroot().remove(layer)

        output_file = output_dir / (export.file_name + '.svg')
        document.write(str(output_file))

        return output_file

    def convert_svg_to_png(self, svg_file: Path, output_dir: Path,
                           prefix: str) -> Path:
        """
        Convert an SVG file into a PNG file.
        :param str svg_file: Path an input SVG file.
        :param str output_dir: Path to an output directory.
        :return Output file path.
        """
        return self._convert_svg(svg_file, output_dir, prefix, 'png')

    def convert_svg_to_svg(self, svg_file: Path, output_dir: Path,
                           prefix: str) -> Path:
        """
        Convert an [Inkscape] SVG file into a standard (plain) SVG file.
        :param str svg_file: Path an input SVG file.
        :param str output_dir: Path to an output directory.
        :return Output file path.
        """
        return self._convert_svg(svg_file, output_dir, prefix, 'svg',
                                 ['--export-plain-svg', '--vacuum-defs'])

    def convert_svg_to_pdf(self, svg_file, output_dir, prefix):
        """
        Convert an [Inkscape] SVG file into a PDF.
        :param str svg_file: Path an input SVG file.
        :param str output_dir: Path to an output directory.
        :return Output file path.
        """
        return self._convert_svg(svg_file, output_dir, prefix, 'pdf')

    def _convert_svg(self, svg_file: Path, output_dir: Path,
                     prefix: str, out_type: str, extra_args=()) -> Path:
        output_file = output_dir / (prefix + svg_file.stem + '.' + out_type)

        command = [
            'inkscape', str(svg_file),
            '--export-area-drawing' if self.options.fit_contents else
            '--export-area-page',
            '--export-type', out_type,
            '--export-filename', str(output_file),
        ] + list(extra_args)

        try:
            subprocess.check_call(command)
        except Exception as e:
            raise Exception(
                f'Failed to convert {svg_file} to {output_file}.\n{e}')

        return output_file

    def convert_png_to_jpeg(self, png_file, output_dir, prefix):
        """
        Convert a PNG file into a JPEG file.
        :param str png_file: Path an input PNG file.
        :param str output_dir: Path to an output directory.
        :return Output file path.
        """
        output_file = output_dir / (prefix + png_file.stem + '.jpeg')

        from PIL import Image
        image = Image.open(png_file)
        image = image.convert('RGB')
        image.save(output_file, quality=95)

        return output_file


@contextlib.contextmanager
def _make_temp_directory():
    temp_dir = tempfile.mkdtemp(prefix='tmp-inkscape')
    try:
        yield Path(temp_dir)
    finally:
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    try:
        LayerExport().run(output=False)
    except Exception as e:
        import traceback
        inkex.errormsg(traceback.format_exc(e))
        sys.exit(1)

# Changelog
All notable changes to this project will be documented in this file.

Please use the following tags when editing this file:
*Added* for new features.
*Changed* for changes in existing functionality.
*Deprecated* for soon-to-be removed features.
*Removed* for now removed features.
*Fixed* for any bug fixes.

## Version 3.4.
### Added
- Option for multi-process export (`num-cpus`).

## Version 3.3.4
### Added
- Diagnostic warning for cases where tagged are groups instead of layers
### Fixed
- Create all intermediate parent directories of an output directory.
  Previously a longer output directory path crashed the extension.
- Fix issue where layer did not have a `style` attribute.

## Version 3.3.3
### Added
- Option to export visible layers only

## Version 3.3.2
### Fixed
- Fix relative path processing

## Version 3.3.1
### Changed
- Change supported Python version from 3.9 to 3.8

## Version 3.3
### Changed
- Simplified UI. Now output directory and prefix are specified independently.
  NB: This breaks CLI backward compatibility
- Treat a relative output directory as relative to the original SGV file

## Version 3.2
### Added
- Enable sub-layer support, treat sub-layers in the same way as groups

## Version 3.1.1
### Fixed
- Object clones are now exported correctly to raster images

## Version 3.1
### Changed
- Output SVGs do not contain layers that are not exported (were hidden before)
- JPEG does not require ImageMagick anymore
### Fixed
- Do not open extra Inkscape UI during export

## Version 3.0
### Added
- Selector for output directory
- Option to progressively include content in layers
- Possibility of adding a sub-directory for exported files
### Changed
- Output file format is now: /path/to/output/directory/\[subdirectory/\]\[prefix_\]\[number_\]layer_name.ext 
  with [subdirectory], [prefix] and [number] being optional
### Fixed
- Use Inkscape order for SVG

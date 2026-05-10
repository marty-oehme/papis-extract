# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

<!-- ### Added -->

<!-- ### Changed -->

### Fixed

- Readest: Parse files which do not export title/author
- Readest: Fix crash when last line of export is an annotation

<!-- ### Removed -->

## [0.3.0]

### Added

- Add Readest extractor
- `tags` config option accepts hex-values as colors

### Changed

- Extend minimum Python version support to Python 3.10
- Extract ROADMAP from README
- ! Changed `--output` option to `--format` as it actually changes the formatter used

### Fixed

- Fix uv-enabled CI pipeline
- Do not parse last empty annotation for ReadEra

### Removed

- libmagic dependency

## [0.2.1]

### Added

- Add option to force-add duplicated annotations
- Add cli option to choose extractor
- Add CSV formatter
- Add count formatter (displays the annotation count per item)

### Changed

- Switch to uv packaging and hatch backend

### Fixed

- Only inform if no extractor finds valid files
- Respect minimum color similarity option

## [0.2.0]

### Added

- Add pocketbook extractor (requires BeautifulSoup4)
- Add ReadEra extractor
- Allow different formatting for first format entry
- Add Markdown style formatting
- Add stdout or write to note exporters

### Changed

- Update dependencies
- Update to papis 0.14
- Refactor and simplify test dependencies

## [0.1.0]

### Added

- Add extractor and install info
- Add pdf extractor
- Allow cli option for choosing a template
- Add mustache templating
- Add preliminary README

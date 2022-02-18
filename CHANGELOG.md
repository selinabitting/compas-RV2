# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.7] 2022-02-23

### Added
* Command `RV2file_save_thrust_cmd` for exporting thrustobject's mesh datastructure as json

### Changed

### Removed


## [1.4.6] 2022-02-23

### Added

### Changed
* Fixed `from_triangulation`.
* Disabled version check on init.

### Removed


## [1.4.5] 2022-02-21

### Added

### Changed
* Avoid `None` attribute error detected by conda-forge CI.
* Updated Artists regitery with context for latest `compas`

### Removed


## [1.4.4] 2022-01-21

### Added

### Changed
* updated compas version fixing update boundary issue.

### Removed


## [1.4.3] 2021-11-19

### Added

### Changed
* use `plugable` to indicate installable rhino packages

### Removed

## [1.4.3] 2021-11-19

### Changed
* Update `compas_rv2.datastructures.SubdMesh` to incorporate freeform quadsurfaces and non-quad surfaces.
* Update `RV2pattern_from_surfaces_cmd`, unify mesh cycles before creating pattern.

## [1.4.2] 2021-11-18

### Added
* Auto update changelog in `invoke release`.
* Workflow to check changelog on PRs

### Changed
* Made `from_featrues` more stable

### Removed
* Removed option to publish release candidates.
* Unused scripts

## [1.0.0-beta2] 2020-05-20

### Added

### Changed

* Keep update with new ``compas_cloud`` api.
* Keep update with ``compas_skeleton``
* Remove unused dependencies on ``compas_pattern`` and ``compas_ags``
* Fixed version text and links at electron front-page


### Removed


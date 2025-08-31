# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2025-07-27

### Added
- **New batch conversion tool**: `convert_batch` - Process multiple unit conversions in a single request
  - Supports all 14 conversion types (temperature, length, mass, volume, angle, area, computer_data, density, energy, force, power, pressure, speed, time)
  - Handles mixed success/failure scenarios with detailed error reporting
  - Provides structured results with request tracking via optional `request_id` parameter
  - Returns batch summary with counts of successful vs failed conversions
  - Comprehensive test coverage including performance testing with 100+ conversions
- **Enhanced documentation**: Updated README with improved examples and reorganized tool listing for better readability

### Changed
- **Updated tool exports**: Added batch conversion functionality to the main server and tool initialization
- **Improved code organization**: Better type definitions and imports for batch processing functionality

## [0.1.1] - 2025-01-16

### Added
- **New conversion tools** (10 additional tools):
  - `convert_angle` - Convert between degrees, radians, arcmin, arcsec, turns, gons
  - `convert_area` - Convert between square meter, acre, hectare, square foot, and more
  - `convert_computer_data` - Convert between bits, bytes, KB, MB, GB, TB, PB, EB
  - `convert_density` - Convert between kg/L, g/cm³, lb/gal, and specialized density units
  - `convert_energy` - Convert between joule, kilowatt hour, calorie, BTU, electron volt, and more
  - `convert_force` - Convert between newton, pound force, kilogram force, dyne, kip, and more
  - `convert_power` - Convert between watt, horsepower, BTU/hour, and metric/electrical power units
  - `convert_pressure` - Convert between pascal, bar, PSI, atmosphere, mmHg, and more
  - `convert_speed` - Convert between m/s, mph, km/h, knots, Mach, speed of light, and more
  - `convert_time` - Convert between seconds to millennia, including sub-second precision units
- **Enhanced existing tools**:
  - Expanded `convert_length` with astronomical, microscopic, and specialized units
  - Expanded `convert_volume` with imperial variants, metric prefixes, and specialized units
  - Enhanced `convert_temperature` with improved precision and validation
- **Type safety improvements** with Pydantic Field annotations and Literal types for all units

### Changed
- **Breaking change**: Renamed `convert_weight` to `convert_mass`
- **Enhanced `convert_mass`** with precious metals (carat, troy ounce), imperial (stone), and metric prefixes
- **Improved server architecture** with better type hints and validation
- **Updated tool organization** with cleaner imports and exports
- **Enhanced documentation** with detailed tool descriptions, supported units, and examples

## [0.1.0] - 2025-07-16

### Added
- Initial release of unit-converter-mcp
- FastMCP v2.0 server implementation
- Five unit conversion tools:
  - `convert_temperature` - Convert between Celsius, Fahrenheit, and Kelvin
  - `convert_length` - Convert between metric and imperial length units (meter, kilometer, centimeter, millimeter, inch, foot, yard, mile)
  - `convert_weight` - Convert between various weight/mass units (kilogram, gram, pound, ounce, ton)
  - `convert_volume` - Convert between metric and imperial volume units (liter, milliliter, gallon, quart, pint, cup, fluid_ounce)
  - `list_supported_units` - List all supported units for each conversion type
- Test suite with pytest covering all conversion tools
- Documentation with detailed examples and usage instructions
- PyPI packaging
- MIT License


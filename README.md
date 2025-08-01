# IFC2glTF-Converter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![Issues](https://img.shields.io/github/issues/your-username/IFC2glTF-Converter)](https://github.com/your-username/IFC2glTF-Converter/issues)

A Python-based tool to convert Industry Foundation Classes (IFC) files to glTF format, preserving material colors for accurate 3D visualization of Building Information Modeling (BIM) models.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Local Setup](#local-setup)
  - [Docker Setup](#docker-setup)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies and Dependencies](#technologies-and-dependencies)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Troubleshooting](#troubleshooting)

## Overview
The `IFC2glTF-Converter` transforms IFC files, used in BIM for architectural and engineering designs, into glTF (GL Transmission Format) for web-compatible 3D visualization. It ensures material colors are preserved to prevent grey model outputs, making it ideal for visualizing HVAC systems, structural components, and architectural models in 3D viewers like Blender or web-based platforms.

## Features
- Converts IFC files (IFC2X3, IFC4) to glTF with separate `.bin` files.
- Preserves material colors using `IfcSurfaceStyleRendering`.
- Checks for textures (`IfcImageTexture`, `IfcPixelTexture`) with logging support.
- Robust error handling and detailed logging for debugging.
- Docker and Docker Compose support for consistent deployment.
- Simple user input for specifying input and output file paths.

## How It Works
The conversion process involves several key steps, implemented in the following functions within `converter.py`:

1. **Extract Material Colors** (`extract_material_colors`):
   - Parses the IFC file to extract RGB and transparency values from `IfcSurfaceStyle` and `IfcSurfaceStyleRendering` entities.
   - Creates a dictionary mapping style/material IDs to RGBA colors (0-1 range for glTF compatibility).
   - Handles missing or invalid transparency data to prevent errors.

2. **Extract Textures** (`extract_textures`):
   - Checks for `IfcImageTexture` or `IfcPixelTexture` entities in the IFC file.
   - Logs texture references (e.g., image file paths) for potential future use, though texture application is not currently supported.

3. **Get Product Color** (`get_product_color`):
   - Maps IFC products (e.g., walls, slabs) to their material colors or textures by checking `IfcRelAssociatesMaterial` and `IfcStyledItem` relationships.
   - Returns a default grey color if no material or texture is found to ensure valid output.

4. **Convert IFC to glTF** (`convert_ifc_to_gltf`):
   - Orchestrates the process: loads the IFC file, extracts geometry and materials, builds a 3D mesh with `trimesh`, and exports to glTF.
   - Ensures accurate geometry and color preservation for visualization.

5. **Main Function** (`main`):
   - Prompts the user to enter the input IFC file path and output glTF file path via console input.
   - Validates inputs and calls the conversion function.

These steps produce a glTF file with preserved material colors, ready for viewing in 3D applications.

![Conversion Example](images/conversion-example.png)

## Prerequisites
- **Python**: Version 3.8 or higher.
- **Docker** and **Docker Compose**: For containerized deployment (optional).
- **Operating System**: Windows, macOS, or Linux.
- **Git**: For cloning the repository.

## Installation

### Local Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/IFC2glTF-Converter.git
   cd IFC2glTF-Converter
   ```
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Or manually:
   ```bash
   pip install ifcopenshell trimesh numpy requests
   ```

### Docker Setup
1. Ensure Docker and Docker Compose are installed and running.
2. Create `input/` and `output/` directories in the project root to store IFC and glTF files:
   ```bash
   mkdir input output
   ```
3. Build and run the Docker container using Docker Compose:
   ```bash
   docker-compose up
   ```

## Usage
1. **Prepare Files**:
   - Place your IFC file (e.g., `input.ifc`) in the `input/` directory.
   - Decide on an output path (e.g., `output/output.gltf`) in the `output/` directory.

2. **Local Execution**:
   - Run the script:
     ```bash
     python converter.py
     ```
   - Enter the input IFC file path when prompted (e.g., `input/NVW_DCR-LOD300_Eng-HVAC.ifc`).
   - Enter the output glTF file path when prompted (e.g., `output/NVW_DCR-LOD300_Eng-HVAC.gltf`).
   - The script will convert the IFC file to glTF and save it to the specified output path.

3. **Docker Execution**:
   - Run Docker Compose in interactive mode to allow input:
     ```bash
     docker-compose up
     ```
   - In the terminal, enter the input IFC file path (e.g., `/app/input/NVW_DCR-LOD300_Eng-HVAC.ifc`) and output glTF file path (e.g., `/app/output/NVW_DCR-LOD300_Eng-HVAC.gltf`) when prompted.
   - The container will convert the file and save the output to the mounted `output/` directory.

4. **Verify Output**:
   - Check the `output/` directory for the glTF file and associated `.bin` files.
   - View the glTF file using a 3D viewer like Blender or [glTF Viewer](https://gltf-viewer.donmccurdy.com/).

**Example** (Local):
```bash
$ python converter.py
IFC to glTF Converter
Enter the path to the input IFC file: input/NVW_DCR-LOD300_Eng-HVAC.ifc
Enter the path for the output glTF file: output/NVW_DCR-LOD300_Eng-HVAC.gltf
Conversion completed successfully: output/NVW_DCR-LOD300_Eng-HVAC.gltf
```

**Example** (Docker Compose):
```bash
$ docker-compose up
...
IFC to glTF Converter
Enter the path to the input IFC file: /app/input/NVW_DCR-LOD300_Eng-HVAC.ifc
Enter the path for the output glTF file: /app/output/NVW_DCR-LOD300_Eng-HVAC.gltf
Conversion completed successfully: /app/output/NVW_DCR-LOD300_Eng-HVAC.gltf
```

## Project Structure
```
IFC2glTF-Converter/
├── converter.py          # Main script with conversion functions
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile           # Docker configuration
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── LICENSE              # MIT License
├── .gitignore           # Git ignore file
├── input/               # Directory for input IFC files
├── output/              # Directory for output glTF files
├── images/              # Screenshots or diagrams
└── .github/
    └── workflows/
        └── lint.yml      # GitHub Actions for linting
```

## Technologies and Dependencies
- **Python 3.8+**: Core programming language.
- **Python Packages**:
  - `ifcopenshell>=0.7.0`: Parses IFC files and extracts geometry/materials.
  - `trimesh>=3.9.0`: Creates meshes and exports to glTF.
  - `numpy>=1.24.0`: Manages vertex, face, and color arrays.
  - `requests>=2.28.0`: Handles HTTP requests for API notifications.
  - `logging` (standard library): Logs progress and errors.
  - `os` (standard library): Manages file paths.
  - `time` (standard library): Tracks processing time.
  - `traceback` (standard library): Captures error stacks.
- **Docker** and **Docker Compose**: Containerizes the application for consistent deployment.
- **Git/GitHub**: Version control and repository hosting.
- **Markdown**: Formats documentation.
- **Development Tools** (optional):
  - **Visual Studio Code**: Editor with Python/Markdown extensions.
  - **flake8**: Linting for code quality.
  - **pytest**: Unit testing framework.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a pull request.

Please include tests and update documentation. A `CONTRIBUTING.md` file will be added soon.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments
- [ifcopenshell](http://ifcopenshell.org/) for robust IFC parsing.
- [trimesh](https://trimsh.org/) for glTF export capabilities.
- [Shields.io](https://shields.io/) for badges.
- BIM and 3D visualization communities for inspiration.

## Troubleshooting
- **Grey glTF Output**:
  - Verify material colors in the `.gltf` file’s `"materials"` section.
  - Check logs for `Extracted X material colors`. If `X=0`, the IFC file may lack material definitions.
  - Use a glTF viewer that supports vertex colors (e.g., Blender).
- **Docker Issues**:
  - Ensure `input/` and `output/` directories exist and are mounted correctly.
  - Run `docker-compose up` in a terminal to allow interactive input.
- **Material Extraction Errors**:
  - Check IFC file for valid `IfcSurfaceStyleRendering` entities using an IFC viewer like BIMvision.
  - Run `python -c "import ifcopenshell; f=ifcopenshell.open('input.ifc'); print([s for s in f.by_type('IfcSurfaceStyle')])"` to inspect styles.

For further assistance, open an issue or share logs and the glTF output.
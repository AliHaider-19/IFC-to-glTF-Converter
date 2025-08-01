# IFC2glTF-Converter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![Issues](https://img.shields.io/github/issues/your-username/IFC2glTF-Converter)](https://github.com/your-username/IFC2glTF-Converter/issues)

A Python-based tool to convert Industry Foundation Classes (IFC) files to glTF format, preserving material colors for accurate 3D visualization of Building Information Modeling (BIM) models. Supports tiling for large-scale models and AWS S3 upload for cloud-based rendering.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
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

## Overview
The `IFC2glTF-Converter` transforms IFC files, widely used in BIM for architectural and engineering designs, into glTF (GL Transmission Format) for web-compatible 3D visualization. It addresses common issues like missing material colors (resulting in grey models) by extracting and applying colors from IFC material definitions. The tool also supports tiling for efficient rendering of large models and uploads tiles to AWS S3 for cloud integration.

Key use cases include visualizing HVAC systems, structural components, and architectural models in 3D viewers like Blender or web-based platforms.

![Conversion Example](images/conversion-example.png)

## Features
- Converts IFC files (IFC2X3, IFC4) to glTF with separate `.bin` files.
- Preserves material colors using `IfcSurfaceStyleRendering` to avoid grey outputs.
- Checks for textures (`IfcImageTexture`, `IfcPixelTexture`) with logging support.
- Tiles glTF output for large models using `process_gltf_for_tiles`.
- Uploads tiles to AWS S3 and updates tileset JSON with project metadata.
- Robust error handling and detailed logging for debugging.
- Docker support for consistent deployment.

## Prerequisites
- **Python**: Version 3.8 or higher.
- **Docker**: For containerized deployment (optional).
- **AWS Credentials**: For S3 uploads (configure via AWS CLI or environment variables).
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
4. Configure AWS credentials (for S3 upload):
   ```bash
   aws configure
   ```
   Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_DEFAULT_REGION=your-region
   ```

### Docker Setup
1. Ensure Docker is installed and running.
2. Build the Docker image:
   ```bash
   docker build -t ifc2gltf-converter .
   ```
3. Run the container, mounting input/output directories and passing AWS credentials:
   ```bash
   docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output \
     -e AWS_ACCESS_KEY_ID=your-access-key \
     -e AWS_SECRET_ACCESS_KEY=your-secret-key \
     -e AWS_DEFAULT_REGION=your-region \
     ifc2gltf-converter python converter.py /app/input/input.ifc /app/output/output.gltf ref_id user_id
   ```

## Usage
1. Place your IFC file (e.g., `input.ifc`) in the project directory or a mounted volume (for Docker).
2. Run the converter:
   ```bash
   python converter.py input.ifc output.gltf reference_id user_id
   ```
   - `input.ifc`: Path to the input IFC file.
   - `output.gltf`: Output glTF file path.
   - `reference_id`: Unique identifier for tiling (e.g., project ID).
   - `user_id`: User ID for S3 upload.
3. The script will:
   - Extract geometry and material colors from the IFC file.
   - Export to `output.gltf` with associated `.bin` files.
   - Generate tiles in a folder named after the output file.
   - Upload tiles to AWS S3 and update the tileset JSON.
4. Verify the glTF output using a viewer like Blender or [glTF Viewer](https://gltf-viewer.donmccurdy.com/).

**Example**:
```bash
python converter.py NVW_DCR-LOD300_Eng-HVAC.ifc NVW_DCR-LOD300_Eng-HVAC.gltf ref123 user456
```

**Docker Example**:
```bash
docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output \
  -e AWS_ACCESS_KEY_ID=your-access-key \
  -e AWS_SECRET_ACCESS_KEY=your-secret-key \
  -e AWS_DEFAULT_REGION=your-region \
  ifc2gltf-converter python converter.py /app/input/NVW_DCR-LOD300_Eng-HVAC.ifc /app/output/NVW_DCR-LOD300_Eng-HVAC.gltf ref123 user456
```

## Project Structure
```
IFC2glTF-Converter/
├── converter.py          # Main conversion script
├── Dockerfile           # Docker configuration
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── LICENSE              # MIT License
├── .gitignore           # Git ignore file
├── images/              # Screenshots or diagrams
└── .github/
    └── workflows/
        └── lint.yml      # GitHub Actions for linting
```

## Technologies and Dependencies
- **Python 3.8+**: Core programming language.
- **Python Packages**:
  - `ifcopenshell>=0.7.0`: Parses IFC files and extracts geometry/materials.
  - `trimesh>=4.0.0`: Creates meshes and exports to glTF.
  - `numpy>=1.21.0`: Manages vertex, face, and color arrays.
  - `requests>=2.25.0`: Handles HTTP requests for S3 uploads.
  - `json` (standard library): Modifies tileset JSON.
  - `logging` (standard library): Logs progress and errors.
  - `os` (standard library): Manages file paths.
  - `time` (standard library): Tracks processing time.
  - `traceback` (standard library): Captures error stacks.
- **Docker**: Containerizes the application for consistent deployment.
- **AWS S3**: Stores tiled outputs.
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

Please include tests and update documentation. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines (to be added).

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments
- [ifcopenshell](http://ifcopenshell.org/) for robust IFC parsing.
- [trimesh](https://trimsh.org/) for glTF export capabilities.
- [AWS S3](https://aws.amazon.com/s3/) for cloud storage.
- [Shields.io](https://shields.io/) for badges.
- BIM and 3D visualization communities for inspiration.
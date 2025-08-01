import os
import logging
import numpy as np
import trimesh
import time
import ifcopenshell
import ifcopenshell.geom
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_material_colors(ifc_file):
    """Extract material colors from an IFC file for glTF conversion.

    This function parses `IfcSurfaceStyle` entities to retrieve RGB and transparency values,
    handling `IfcSurfaceStyleRendering` for accurate color representation in glTF.
    Falls back to default opacity if transparency is missing or invalid.

    Args:
        ifc_file (ifcopenshell.file): The loaded IFC file object.

    Returns:
        dict: A dictionary mapping style or material IDs to RGBA color lists [r, g, b, a]
              (values in 0-1 range for glTF compatibility).

    Raises:
        Exception: If material extraction fails, logs a warning and returns an empty dict.
    """
    material_colors = {}
    
    try:
        # Method 1: Get surface styles with colors
        surface_styles = ifc_file.by_type("IfcSurfaceStyle")
        for style in surface_styles:
            if hasattr(style, 'Styles') and style.Styles:
                for style_item in style.Styles:
                    if style_item.is_a('IfcSurfaceStyleRendering') and style_item.SurfaceColour:
                        color = style_item.SurfaceColour
                        r = min(1.0, max(0.0, color.Red))  # glTF uses 0-1 range
                        g = min(1.0, max(0.0, color.Green))
                        b = min(1.0, max(0.0, color.Blue))
                        # Handle transparency safely
                        a = 1.0  # Default to opaque
                        if hasattr(style_item, 'Transparency') and style_item.Transparency is not None:
                            try:
                                a = min(1.0, max(0.0, 1.0 - float(style_item.Transparency)))
                            except (TypeError, ValueError) as e:
                                logger.debug(f"Invalid transparency for style {style.id()}: {e}. Using default opacity (1.0).")
                        else:
                            logger.debug(f"No transparency defined for style {style.id()}. Using default opacity (1.0).")
                        material_colors[style.id()] = [r, g, b, a]
                        logger.debug(f"Found surface style color: {style.id()} = {[r, g, b, a]}")

        # Method 2: Get materials and their surface styles
        materials = ifc_file.by_type("IfcMaterial")
        for material in materials:
            if hasattr(material, 'HasRepresentation') and material.HasRepresentation:
                for rep in material.HasRepresentation:
                    if hasattr(rep, 'Representations'):
                        for representation in rep.Representations:
                            if hasattr(representation, 'Items'):
                                for item in representation.Items:
                                    if item.is_a('IfcSurfaceStyle') and item.id() in material_colors:
                                        material_colors[material.id()] = material_colors[item.id()]
                                        logger.debug(f"Linked material {material.id()} to color {material_colors[item.id()]}")

        # Method 3: Check styled items
        styled_items = ifc_file.by_type("IfcStyledItem")
        for styled_item in styled_items:
            if hasattr(styled_item, 'Styles'):
                for style in styled_item.Styles:
                    if style.id() in material_colors:
                        material_colors[styled_item.id()] = material_colors[style.id()]
                        logger.debug(f"Linked styled item {styled_item.id()} to color {material_colors[style.id()]}")

        logger.info(f"Extracted {len(material_colors)} material colors")
        if not material_colors:
            logger.warning("No material colors found in IFC file. Using default color.")
        return material_colors

    except Exception as e:
        logger.warning(f"Could not extract material colors: {e}")
        return {}

def extract_textures(ifc_file):
    """Extract texture references from an IFC file, if available.

    Checks for `IfcImageTexture` or `IfcPixelTexture` entities and retrieves their
    `URLReference` for potential use in glTF. Currently logs textures without applying them.

    Args:
        ifc_file (ifcopenshell.file): The loaded IFC file object.

    Returns:
        dict: A dictionary mapping texture IDs to their URL references.

    Raises:
        Exception: If texture extraction fails, logs a warning and returns an empty dict.
    """
    textures = {}
    try:
        texture_maps = ifc_file.by_type("IfcImageTexture") + ifc_file.by_type("IfcPixelTexture")
        for texture in texture_maps:
            if hasattr(texture, 'URLReference') and texture.URLReference:
                textures[texture.id()] = texture.URLReference
                logger.debug(f"Found texture: {texture.id()} = {texture.URLReference}")
        logger.info(f"Extracted {len(textures)} textures")
        return textures
    except Exception as e:
        logger.warning(f"Could not extract textures: {e}")
        return {}

def get_product_color(product, material_colors, textures):
    """Retrieve color or texture for an IFC product.

    Maps IFC products to their associated material colors or textures by checking
    `IfcRelAssociatesMaterial` and `IfcStyledItem` relationships. Returns a default
    color if no material or texture is found.

    Args:
        product (ifcopenshell.entity_instance): The IFC product (e.g., IfcWall, IfcSlab).
        material_colors (dict): Dictionary of material/style IDs to RGBA colors.
        textures (dict): Dictionary of texture IDs to URL references.

    Returns:
        dict: A dictionary with 'color' (RGBA list or None) and 'texture' (URL or None).

    Raises:
        Exception: If color/texture retrieval fails, logs a debug message and returns None.
    """
    try:
        # Check material associations
        if hasattr(product, 'HasAssociations') and product.HasAssociations:
            for assoc in product.HasAssociations:
                if assoc.is_a('IfcRelAssociatesMaterial'):
                    material = assoc.RelatingMaterial
                    if material.is_a('IfcMaterial') and material.id() in material_colors:
                        return {'color': material_colors[material.id()], 'texture': None}
                    elif material.is_a('IfcMaterialLayerSet') and hasattr(material, 'MaterialLayers'):
                        for layer in material.MaterialLayers:
                            if hasattr(layer, 'Material') and layer.Material and layer.Material.id() in material_colors:
                                return {'color': material_colors[layer.Material.id()], 'texture': None}

        # Check representation items for styled items
        if hasattr(product, 'Representation') and product.Representation:
            for rep in product.Representation.Representations:
                if hasattr(rep, 'Items'):
                    for item in rep.Items:
                        if hasattr(item, 'StyledByItem') and item.StyledByItem:
                            for styled_item in item.StyledByItem:
                                if styled_item.id() in material_colors:
                                    return {'color': material_colors[styled_item.id()], 'texture': None}
                                # Check for textures
                                if styled_item.id() in textures:
                                    return {'color': None, 'texture': textures[styled_item.id()]}

        return {'color': None, 'texture': None}
    except Exception as e:
        logger.debug(f"Error getting product color/texture: {e}")
        return {'color': None, 'texture': None}

def convert_ifc_to_gltf(ifc_path, output_path):
    """Convert an IFC file to glTF with geometry and colors.

    Main function to process an IFC file, extract geometry and materials, and export to glTF.
    Ensures material colors are preserved to avoid grey outputs.

    Args:
        ifc_path (str): Path to the input IFC file.
        output_path (str): Path for the output glTF file.

    Returns:
        bool: True if conversion succeeds; False otherwise.

    Raises:
        Exception: If conversion fails, logs detailed error and returns False.
    """
    try:
        if not output_path.lower().endswith('.gltf'):
            output_path = output_path + '.gltf'
        start_time = time.time()
        logger.info(f"🚀 Converting IFC: {ifc_path} -> {output_path}")

        ifc_file = ifcopenshell.open(ifc_path)
        logger.info(f"✅ Loaded IFC file - Schema: {ifc_file.schema}")

        material_colors = extract_material_colors(ifc_file)
        textures = extract_textures(ifc_file)

        # Setup geometry extraction
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)

        products = [p for p in ifc_file.by_type("IfcProduct") 
                    if hasattr(p, 'Representation') and p.Representation]
        
        logger.info(f"⚡ Processing {len(products)} products...")

        # Process all products
        all_vertices = []
        all_faces = []
        all_colors = []
        vertex_offset = 0
        successful = 0
        default_color = [0.784, 0.784, 0.784, 1.0]  # Light gray (0-1 range for glTF)

        for i, product in enumerate(products):
            if i % 50 == 0:
                logger.info(f"🔄 Progress: {i}/{len(products)} ({i/len(products)*100:.1f}%)")

            try:
                # Get geometry
                shape = ifcopenshell.geom.create_shape(settings, product)
                if shape and shape.geometry:
                    geometry = shape.geometry
                    if hasattr(geometry, 'verts') and hasattr(geometry, 'faces'):
                        verts = geometry.verts
                        faces = geometry.faces

                        if verts and faces and len(verts) > 0 and len(faces) > 0:
                            vertices = np.array(verts, dtype=np.float32).reshape(-1, 3)
                            face_indices = np.array(faces, dtype=np.uint32).reshape(-1, 3)

                            if len(vertices) > 0 and len(face_indices) > 0:
                                # Get product color or texture
                                product_info = get_product_color(product, material_colors, textures)
                                product_color = product_info['color']
                                product_texture = product_info['texture']

                                if product_texture:
                                    logger.warning(f"Texture {product_texture} found but not applied (unsupported in this version)")
                                if not product_color:
                                    product_color = default_color

                                # Add to collections
                                adjusted_faces = face_indices + vertex_offset
                                all_vertices.append(vertices)
                                all_faces.append(adjusted_faces)

                                # Apply color to all vertices of this product
                                vertex_colors = np.tile(product_color, (len(vertices), 1))
                                all_colors.append(vertex_colors)

                                vertex_offset += len(vertices)
                                successful += 1

            except Exception as e:
                logger.debug(f"Failed product {i}: {e}")
                continue

        elapsed = time.time() - start_time
        logger.info(f"📊 Processed {successful}/{len(products)} products in {elapsed:.1f}s")

        if not all_vertices:
            logger.error("❌ No geometry extracted")
            return False

        # Create final mesh with colors
        logger.info("🔗 Creating mesh...")
        final_vertices = np.vstack(all_vertices)
        final_faces = np.vstack(all_faces)
        final_colors = np.vstack(all_colors)

        mesh = trimesh.Trimesh(
            vertices=final_vertices,
            faces=final_faces,
            vertex_colors=final_colors,
            process=False
        )

        # Export to glTF
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        logger.info("💾 Exporting glTF...")
        mesh.export(output_path, file_type='gltf')

        logger.info(f"✅ Conversion complete: {output_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Conversion failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function to run the IFC to glTF converter from the command line.

    Parses command-line arguments for input IFC file and output glTF file paths,
    then calls the conversion function.

    Usage:
        python converter.py <input_ifc> <output_gltf>

    Args:
        None (parses arguments from sys.argv).

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description="Convert an IFC file to glTF format with material colors.")
    parser.add_argument("input_ifc", type=str, help="Path to the input IFC file")
    parser.add_argument("output_gltf", type=str, help="Path for the output glTF file")
    
    args = parser.parse_args()

    # Validate input file
    if not os.path.isfile(args.input_ifc):
        logger.error(f"Input file does not exist: {args.input_ifc}")
        return

    # Ensure output path has .gltf extension
    output_path = args.output_gltf
    if not output_path.lower().endswith('.gltf'):
        output_path = output_path + '.gltf'

    # Run conversion
    success = convert_ifc_to_gltf(args.input_ifc, output_path)
    if success:
        logger.info("Conversion completed successfully")
    else:
        logger.error("Conversion failed")

if __name__ == "__main__":
    main()
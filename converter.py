import os
import logging
import numpy as np
import trimesh
import time
import ifcopenshell
import ifcopenshell.geom

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_material_colors(ifc_file):
    """Extract material colors from an IFC file for glTF conversion.

    Args:
        ifc_file (ifcopenshell.file): The loaded IFC file object.

    Returns:
        dict: A dictionary mapping style or material IDs to RGBA color lists [r, g, b, a].
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
                        r = min(1.0, max(0.0, color.Red))
                        g = min(1.0, max(0.0, color.Green))
                        b = min(1.0, max(0.0, color.Blue))
                        a = 1.0
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

    Args:
        ifc_file (ifcopenshell.file): The loaded IFC file object.

    Returns:
        dict: A dictionary mapping texture IDs to their URL references.
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

    Args:
        product (ifcopenshell.entity_instance): The IFC product (e.g., IfcWall, IfcSlab).
        material_colors (dict): Dictionary of material/style IDs to RGBA colors.
        textures (dict): Dictionary of texture IDs to URL references.

    Returns:
        dict: A dictionary with 'color' (RGBA list or None) and 'texture' (URL or None).
    """
    try:
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

        if hasattr(product, 'Representation') and product.Representation:
            for rep in product.Representation.Representations:
                if hasattr(rep, 'Items'):
                    for item in rep.Items:
                        if hasattr(item, 'StyledByItem') and item.StyledByItem:
                            for styled_item in item.StyledByItem:
                                if styled_item.id() in material_colors:
                                    return {'color': material_colors[styled_item.id()], 'texture': None}
                                if styled_item.id() in textures:
                                    return {'color': None, 'texture': textures[styled_item.id()]}

        return {'color': None, 'texture': None}
    except Exception as e:
        logger.debug(f"Error getting product color/texture: {e}")
        return {'color': None, 'texture': None}

def convert_ifc_to_gltf(ifc_path, output_path):
    """Convert an IFC file to glTF with geometry and colors.

    Args:
        ifc_path (str): Path to the input IFC file.
        output_path (str): Path for the output glTF file.

    Returns:
        bool: True if conversion succeeds; False otherwise.
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

        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)

        products = [p for p in ifc_file.by_type("IfcProduct") 
                    if hasattr(p, 'Representation') and p.Representation]
        
        logger.info(f"⚡ Processing {len(products)} products...")

        all_vertices = []
        all_faces = []
        all_colors = []
        vertex_offset = 0
        successful = 0
        default_color = [0.784, 0.784, 0.784, 1.0]

        for i, product in enumerate(products):
            if i % 50 == 0:
                logger.info(f"🔄 Progress: {i}/{len(products)} ({i/len(products)*100:.1f}%)")

            try:
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
                                product_info = get_product_color(product, material_colors, textures)
                                product_color = product_info['color']
                                product_texture = product_info['texture']

                                if product_texture:
                                    logger.warning(f"Texture {product_texture} found but not applied (unsupported in this version)")
                                if not product_color:
                                    product_color = default_color

                                adjusted_faces = face_indices + vertex_offset
                                all_vertices.append(vertices)
                                all_faces.append(adjusted_faces)
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
    """Main function to run the IFC to glTF converter with user input prompts.

    Prompts the user for input IFC file path and output glTF file path, then runs the conversion.
    """
    print("IFC to glTF Converter")
    input_path = input("Enter the path to the input IFC file: ").strip()
    
    if not input_path or not os.path.isfile(input_path):
        print(f"Error: Input file '{input_path}' does not exist or is invalid.")
        return
    
    output_path = input("Enter the path for the output glTF file: ").strip()
    
    if not output_path:
        print("Error: Output file path cannot be empty.")
        return

    success = convert_ifc_to_gltf(input_path, output_path)
    if success:
        print(f"Conversion completed successfully: {output_path}")
    else:
        print("Conversion failed. Check logs for details.")

if __name__ == "__main__":
    main()
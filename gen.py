import bpy
import os
import argparse
import sys
from datetime import datetime
from fontTools.ttLib import TTFont
import unicodedata

def create_text_mesh(text, font_path, extrude_depth=0.2, resolution=32, bevel_depth=0.01):
    """
    Create 3D mesh for text

    Args:
    text: Text to be converted
    font_path: Full path to the font file
    extrude_depth: Thickness of the text
    resolution: Mesh resolution
    bevel_depth: Bevel depth for smoother edges

    Returns:
    tuple: (mesh object, original text)
    """

    # Delete all objects in the default scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create text object
    bpy.ops.object.text_add(location=(0, 0, 0))
    text_obj = bpy.context.active_object
    text_obj.data.body = text

    # Set font
    font = bpy.data.fonts.load(font_path)
    text_obj.data.font = font

    # Set text parameters
    text_obj.data.extrude = extrude_depth
    text_obj.data.bevel_depth = bevel_depth
    text_obj.data.bevel_resolution = resolution

    # Save original text
    original_text = text

    # Convert text to mesh
    bpy.context.view_layer.objects.active = text_obj
    bpy.ops.object.convert(target='MESH')

    # Recalculate normals
    bpy.ops.object.shade_smooth()
    bpy.ops.object.modifier_add(type='EDGE_SPLIT')

    return text_obj, original_text

def get_default_output_path(text, file_ext='.obj'):
    """
    Generate default output path

    Args:
    text: Text to be converted
    file_ext: File extension (default: .obj)

    Returns:
    str: Full path to the output file
    """
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Create output directory
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generate filename: text_timestamp.extension
    filename = f"{text}_{timestamp}{file_ext}"

    return os.path.join(output_dir, filename)

def ensure_addons_enabled():
    """
    Ensure necessary export plugins are enabled
    """
    addons = [
        "io_scene_obj",    # OBJ export plugin
        "io_mesh_stl"      # STL export plugin
    ]

    for addon in addons:
        if not addon in bpy.context.preferences.addons:
            try:
                bpy.ops.preferences.addon_enable(module=addon)
                print(f"Enabled plugin: {addon}")
            except Exception as e:
                print(f"Failed to enable plugin {addon}: {str(e)}")

def export_mesh(obj, output_path=None):
    """
    Export mesh based on the extension of the output path

    Args:
    obj: Object to export
    output_path: Full output path (including extension), if None use default path
    """
    # If no output path is specified, use the default path
    if output_path is None:
        output_path = get_default_output_path(original_text)

    # Get file extension
    file_ext = os.path.splitext(output_path)[1].lower()
    if not file_ext:
        file_ext = '.obj'
        output_path = f"{output_path}{file_ext}"

    # Check file type
    if file_ext not in ['.obj', '.blend']:
        print(f"Error: Unsupported file format {file_ext}")
        print("Supported formats: .obj, .blend")
        return False

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Select the object to export
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    try:
        # Export based on file type
        if file_ext == '.obj':
            bpy.ops.wm.obj_export(
                filepath=output_path,
                export_selected_objects=True,
                export_materials=False
            )
        elif file_ext == '.blend':
            bpy.ops.wm.save_as_mainfile(filepath=output_path)

        print(f"Exported to: {output_path}")
        return True

    except Exception as e:
        print(f"Export failed: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description='Generate 3D text model')

    # Required arguments
    parser.add_argument('--text', type=str, default="hello",
                      help='Text to generate')

    # Optional arguments
    parser.add_argument('--font', type=str, default=".\\fonts\\hp.ttf",
                      help='Font file path (default: .\\fonts\\hp.ttf)')
    parser.add_argument('--depth', type=float, default=0.2,
                      help='Text thickness (default: 0.2)')
    parser.add_argument('--resolution', type=int, default=32,
                      help='Mesh resolution (default: 32)')
    parser.add_argument('--bevel', type=float, default=0.01,
                      help='Bevel depth for smoother edges (default: 0.01)')
    parser.add_argument('--output', type=str, default=None,
                      help='Output file path (default: output/text_timestamp.obj)')

    # Get arguments other than those for Blender itself
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(argv)

def check_font_support(font_path, text):
    """
    Check if the font supports the specified text

    Args:
    font_path: Path to the font file
    text: Text to check

    Returns:
    tuple: (whether fully supported, list of unsupported characters)
    """
    try:
        # Load font file
        font = TTFont(font_path)

        # Get the set of characters supported by the font
        cmap = font.getBestCmap()

        # Check each character
        unsupported_chars = []
        for char in text:
            if ord(char) not in cmap and not char.isspace():
                # Get Unicode name and category of the character
                char_name = unicodedata.name(char, 'UNKNOWN')
                char_category = unicodedata.category(char)
                script = unicodedata.script(char)

                unsupported_chars.append({
                    'char': char,
                    'name': char_name,
                    'category': char_category,
                    'script': script
                })

        return len(unsupported_chars) == 0, unsupported_chars

    except Exception as e:
        print(f"Warning: Font check failed - {str(e)}")
        return True, []  # If check fails, assume all characters are supported

def main():
    # Parse command line arguments
    args = parse_args()

    # Get the absolute path of the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the full font path
    font_path = os.path.join(script_dir, args.font)

    # Check if the font file exists
    if not os.path.exists(font_path):
        print(f"Error: Font file not found at {font_path}")
        return

    # Check font support
    is_supported, unsupported_chars = check_font_support(font_path, args.text)
    if not is_supported:
        print("\nWarning: Font may not fully support the required characters:")
        for char_info in unsupported_chars:
            print(f"  - Character '{char_info['char']}' (U+{ord(char_info['char']):04X}):")
            print(f"    Unicode name: {char_info['name']}")
            print(f"    Category: {char_info['category']}")
            print(f"    Script: {char_info['script']}")
        print("Continuing execution, but some characters may not display correctly...\n")

    # Create 3D text mesh
    text_obj, original_text = create_text_mesh(
        text=args.text,
        font_path=font_path,
        extrude_depth=args.depth,
        resolution=args.resolution,
        bevel_depth=args.bevel
    )

    # Center the object
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
    text_obj.location = (0, 0, 0)

    # Export mesh
    if args.output:
        output_path = os.path.join(script_dir, args.output)
    else:
        output_path = get_default_output_path(original_text)

    export_mesh(text_obj, output_path)

if __name__ == "__main__":
    main()

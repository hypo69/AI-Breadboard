## \file /src/utils/convertors/dot.py
# -*- coding: utf-8 -*-

#! .pyenv/bin/python3

"""
.. module:: src.utils.convertors.dot 
	:platform: Windows, Unix
	:synopsis: converts DOT files into PNG images using the Graphviz library

"""


import sys
from graphviz import Source

def dot2png(dot_file: str, png_file: str) -> None:
    """ Converts a DOT file to a PNG image.

    Args:
        dot_file (str): The path to the input DOT file.
        png_file (str): The path where the output PNG file will be saved.

    Raises:
        FileNotFoundError: If the DOT file does not exist.
        Exception: For other errors during conversion.

    Example:
        >>> dot2png('example.dot', 'output.png')
        
        This converts the DOT file 'example.dot' into a PNG image named 'output.png'.
        
        Sample DOT content for 'example.dot':
        
        ```dot
        digraph G {
            A -> B;
            B -> C;
            C -> A;
        }
        ```
        
        To run the script from the command line:
        
        ```bash
        python dot2png.py example.dot output.png
        ```

        This command will create a PNG file named 'output.png' from the graph defined in 'example.dot'.
    """
    try:
        # Read the DOT file
        with open(dot_file, 'r') as f:
            dot_content = f.read()

        # Create a Source object from the DOT content
        source = Source(dot_content)

        # Render the source to a PNG file
        source.format = 'png'
        source.render(png_file, cleanup=True)
    except FileNotFoundError as e:
        print(f"Error: The file '{dot_file}' was not found.")
        raise e
    except Exception as e:
        print(f"An error occurred during the conversion: {e}")
        raise e


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python dot2png.py <input_dot_file> <output_png_file>")
        sys.exit(1)

    input_dot_file = sys.argv[1]
    output_png_file = sys.argv[2]

    dot2png(input_dot_file, output_png_file)

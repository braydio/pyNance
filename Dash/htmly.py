from bs4 import BeautifulSoup
import json

def parse_html_to_json(file_path, output_file):
    """
    Parses an HTML file to extract unique elements, IDs, and classes.
    Saves the structure as a JSON file for ChatGPT to reference.
    
    :param file_path: Path to the input HTML file.
    :param output_file: Path to save the parsed JSON structure.
    """
    try:
        # Read the HTML file
        with open(file_path, 'r', encoding='utf-8') as html_file:
            soup = BeautifulSoup(html_file, 'html.parser')

        # Collect unique elements, IDs, and classes
        elements = set()
        ids = set()
        classes = set()

        # Iterate through all tags
        for tag in soup.find_all(True):  # True matches all tags
            elements.add(tag.name)
            if tag.has_attr('id'):
                ids.add(tag['id'])
            if tag.has_attr('class'):
                classes.update(tag['class'])

        # Structure the data
        parsed_data = {
            "elements": sorted(elements),
            "ids": sorted(ids),
            "classes": sorted(classes),
        }

        # Save the structure to a JSON file
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(parsed_data, json_file, indent=4)
        
        print(f"Parsed data saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

from bs4 import BeautifulSoup

def parse_html_to_css(html_file, css_file):
    """
    Parses an HTML file and generates a draft CSS file for all elements, IDs, and classes.
    
    :param html_file: Path to the input HTML file.
    :param css_file: Path to save the generated CSS file.
    """
    try:
        # Read the HTML file
        with open(html_file, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

        # Collect unique elements, IDs, and classes
        elements = set()
        ids = set()
        classes = set()

        for tag in soup.find_all(True):  # True matches all HTML tags
            elements.add(tag.name)
            if tag.has_attr('id'):
                ids.add(tag['id'])
            if tag.has_attr('class'):
                classes.update(tag['class'])

        # Generate the CSS file
        with open(css_file, 'w', encoding='utf-8') as css:
            # Write global styles
            css.write("/* General Reset */\n")
            css.write("* {\n    margin: 0;\n    padding: 0;\n    box-sizing: border-box;\n}\n\n")

            # Write styles for elements
            css.write("/* Element Styles */\n")
            for element in sorted(elements):
                css.write(f"{element} {{\n    /* Add styles for <{element}> */\n}}\n\n")

            # Write styles for IDs
            css.write("/* ID Styles */\n")
            for id_name in sorted(ids):
                css.write(f"#{id_name} {{\n    /* Add styles for #{id_name} */\n}}\n\n")

            # Write styles for classes
            css.write("/* Class Styles */\n")
            for class_name in sorted(classes):
                css.write(f".{class_name} {{\n    /* Add styles for .{class_name} */\n}}\n\n")

        print(f"Draft CSS file generated: {css_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate CSS or JSON from an HTML file.")
    parser.add_argument("html_file", help="Path to the input HTML file.")
    parser.add_argument("--css", help="Generate a CSS file (provide the output path).", default=None)
    parser.add_argument("--json", help="Generate a JSON structure file (provide the output path).", default=None)
    args = parser.parse_args()

    if args.css:
        parse_html_to_css(args.html_file, args.css)
    if args.json:
        parse_html_to_json(args.html_file, args.json)

if __name__ == "__main__":
    main()

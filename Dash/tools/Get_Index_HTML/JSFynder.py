import os
import re

from bs4 import BeautifulSoup

# Usage:
# -- Move this file to Dash/PYFynder.py and run from there
# -- Replace the path to the HTML (bottom of script) with the specific HTML you are working with


def extract_routes_and_js(html_file, js_directory, output_file):
    """
    Extracts routes and JavaScript functions from HTML and JS files in a directory.

    :param html_file: Path to the HTML file.
    :param js_directory: Directory containing JavaScript files.
    :param output_file: Path to save the output.
    """
    try:
        # Extract routes and identifiers from the HTML
        with open(html_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        routes = []
        identifiers = {}

        for tag in soup.find_all(True):
            if tag.has_attr("onclick"):
                routes.append(tag["onclick"])
            if tag.has_attr("id"):
                identifiers[tag["id"]] = tag.name

        # Extract functions from all JS files in the directory
        js_functions = {}
        for root, _, files in os.walk(js_directory):
            for file in files:
                if file.endswith(".js"):
                    js_file_path = os.path.join(root, file)
                    with open(js_file_path, "r", encoding="utf-8") as js_file:
                        js_content = js_file.read()

                    # Log which file is being processed
                    print(f"Processing: {js_file_path}")

                    # Regex patterns to match functions
                    patterns = [
                        r"function\s+(\w+)\s*\(",  # Regular functions
                        r"(?:const|let|var)\s+(\w+)\s*=\s*\(?\w*\)?\s*=>",  # Arrow functions
                    ]

                    for pattern in patterns:
                        matches = re.finditer(pattern, js_content)
                        for match in matches:
                            function_name = match.group(1)
                            # Ensure the function name is unique
                            if function_name not in js_functions:
                                js_functions[function_name] = {
                                    "file": js_file_path,
                                    "body": extract_function_body(
                                        js_content, match.start()
                                    ),
                                }

        # Write the output to a file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Extracted Routes:\n")
            for route in routes:
                f.write(f"{route}\n")

            f.write("\n# Extracted JS Functions:\n")
            for name, details in js_functions.items():
                f.write(f"## {name} (from {details['file']})\n")
                f.write(f"{details['body']}\n\n")

        print(f"Output saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")


def extract_function_body(js_content, start_index):
    """
    Extracts the body of a function starting at a given index.

    :param js_content: The content of the JavaScript file.
    :param start_index: The starting index of the function definition.
    :return: The function body as a string.
    """
    open_braces = 0
    in_function = False
    function_body = []

    for char in js_content[start_index:]:
        if char == "{":
            open_braces += 1
            in_function = True
        elif char == "}":
            open_braces -= 1
        function_body.append(char)
        if in_function and open_braces == 0:
            break

    return "".join(function_body)


# -- Move this file to Dash/PYFynder.py and run from there
if __name__ == "__main__":
    extract_routes_and_js(
        html_file="templates/dashboard.html",  # Path to your HTML file
        js_directory=".",  # Path to the directory containing JS files
        output_file="JS_Context.txt",  # Output file
    )

import os
import re

from bs4 import BeautifulSoup

# Usage:
# -- Move this file to Dash/PYFynder.py and run from there
# -- Replace the path to the HTML (bottom of script) with the specific HTML you are working with


def extract_routes_and_identifiers(html_file, js_directory, py_directory, output_file):
    """
    Reads an HTML file to extract routes and JS identifiers, matches them with functions
    from JavaScript and Python files in the specified directories, and outputs a summary.

    :param html_file: Path to the HTML file.
    :param js_directory: Path to the directory containing JavaScript files.
    :param py_directory: Path to the directory containing Python files.
    :param output_file: Path to the output file to save the parsed context.
    """
    try:
        # Step 1: Extract routes and JS identifiers from the HTML file
        with open(html_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        routes = []
        identifiers = {}

        # Find onclick, href, and other route-related attributes
        for tag in soup.find_all(True):  # Matches all tags
            # Look for href attributes pointing to routes
            if tag.has_attr("onclick"):
                routes.append(tag["onclick"])
            if tag.has_attr("href") and not tag["href"].startswith("#"):
                routes.append(tag["href"])

            # Collect IDs and classes for interactivity
            if tag.has_attr("id"):
                identifiers[tag["id"]] = tag.name
            if tag.has_attr("class"):
                for cls in tag["class"]:
                    identifiers[cls] = tag.name

        # Search through all Python files in the specified directory
        py_routes = {}
        for root, _, files in os.walk(py_directory):
            for file in files:
                if file.endswith(".py"):  # Process only .py files
                    py_file_path = os.path.join(root, file)
                    with open(py_file_path, "r", encoding="utf-8") as py_file:
                        py_content = py_file.read()

                    # Match route definitions (Flask-style)
                    for route in routes:
                        # Strip JavaScript-related parts (e.g., `window.location.href=`)
                        clean_route = re.sub(
                            r"window\.location\.href\s*=\s*", "", route
                        ).strip("'\"")
                        if clean_route:
                            pattern = rf"@app\.route\(['\"]{clean_route}['\"]"
                            match = re.search(pattern, py_content)
                            if match:
                                # Extract the function definition following the route decorator
                                start = match.end()
                                end = py_content.find("def ", start)
                                end = py_content.find("):", end) + 2
                                function_body = py_content[
                                    end : py_content.find("\n\n", end)
                                ].strip()
                                py_routes[clean_route] = {
                                    "file": py_file_path,
                                    "body": function_body,
                                }

        # Step 4: Save the parsed context to a file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Extracted Routes:\n")
            for route in routes:
                f.write(f"{route}\n")

            f.write("\n# Extracted Python Routes and Functions:\n")
            for route, details in py_routes.items():
                f.write(f"## Route: {route} (from {details['file']})\n")
                f.write(f"{details['body']}\n\n")

        print(f"Parsed context saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")


# Example Usage
# -- Move this file to Dash/PYFynder.py and run from there
if __name__ == "__main__":
    file_path = "templates/settings.html"
    extract_routes_and_identifiers(
        html_file=file_path,  # Replace with your HTML file path
        js_directory=".",  # Replace with the directory containing JavaScript files
        py_directory=".",  # Replace with the directory containing Python files
        output_file=f"{file_path}.txt",  # Output file path
    )

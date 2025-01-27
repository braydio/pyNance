

# Development Tools User Guide

Overview of dev tools (HTMLy.py | JSFynder.py | PYFynder.py) for extracting and analyzing content from HTML, JavaScript, and Python files,

---

## 1. **HTMLy**

**Purpose**: Extracts elements, IDs, and classes from an HTML file and generates either a JSON structure or a draft CSS file.

### Key Features:
- **JSON Extraction**: Creates a JSON file containing:
  - Unique elements
  - IDs
  - Classes
- **CSS Generation**: Drafts a CSS file with boilerplate styles for elements, IDs, and classes.

### Usage:
#### Command-Line Arguments:
- `html_file`: Path to the input HTML file.
- `--css <output_css_path>`: Generate a CSS file.
- `--json <output_json_path>`: Generate a JSON file.

#### Example Command:
```bash
python htmly.py templates/dashboard.html --css output.css --json output.json
```

### Example Output:
#### JSON:
```json
{
  "elements": ["div", "h1", "p"],
  "ids": ["header", "footer"],
  "classes": ["menu", "content"]
}
```
#### CSS:
```css
/* Element Styles */
div {
    /* Add styles for <div> */
}

/* ID Styles */
#header {
    /* Add styles for #header */
}

/* Class Styles */
.menu {
    /* Add styles for .menu */
}
```

---

## 2. **JSFynder**

**Purpose**: Extracts JavaScript routes, identifiers, and functions from HTML and JS files.

### Key Features:
- **Route Extraction**: Captures routes from HTML attributes like `onclick`.
- **JS Function Extraction**: Extracts JavaScript functions from `.js` files.

### Usage:
#### Function Parameters:
- `html_file`: Path to the HTML file.
- `js_directory`: Directory containing JavaScript files.
- `output_file`: Path to save the extracted data.

#### Example Command:
```bash
python JSFynder.py
```

### Example Output:
```
# Extracted Routes:
window.location.href='/accounts'

# Extracted JS Functions:
## initializePlaidLink (from link.js)
function initializePlaidLink() {
    // Function implementation
}
```

---

## 3. **PYFynder**

**Purpose**: Matches routes in an HTML file with corresponding Flask routes in Python files and identifies functions.

### Key Features:
- **Route Matching**: Links routes found in HTML to their Python function definitions.
- **Python Function Extraction**: Captures Flask-style route handlers.

### Usage:
#### Function Parameters:
- `html_file`: Path to the HTML file.
- `js_directory`: Directory containing JavaScript files.
- `py_directory`: Directory containing Python files.
- `output_file`: Path to save the extracted data.

#### Example Command:
```bash
python PYFynder.py
```

### Example Output:
```
# Extracted Routes:
/accounts

# Extracted Python Routes and Functions:
## Route: /accounts (from app.py)
@app.route("/accounts")
def accounts_page():
    # Function implementation
```

---

## Workflow Example:
1. Use **HTMLy** to extract and analyze the structure of an HTML file.
2. Apply **JSFynder** to identify JavaScript routes and functions.
3. Use **PYFynder** to link the routes with Python backend logic.

This process enables you to streamline the development and debugging of web applications by ensuring cohesive integration between front-end and back-end components.

---

For any issues or feature requests, feel free to contact the development team.


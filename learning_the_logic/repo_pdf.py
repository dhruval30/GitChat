from github import Github
import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

g = Github(GITHUB_TOKEN)

def is_binary(file_content):
    """Check if file content is binary."""
    textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
    return bool(file_content.translate(None, textchars))

def build_repo_tree(repo_url):
    try:
        path_parts = repo_url.rstrip('/').split('/')
        owner, repo_name = path_parts[-2], path_parts[-1]
        repo = g.get_repo(f"{owner}/{repo_name}")
        repo_tree = {}

        def add_to_tree(tree, path, content):
            parts = path.split('/')
            current_level = tree
            for part in parts[:-1]:
                current_level = current_level.setdefault(part, {})
            current_level[parts[-1]] = content

        contents = repo.get_contents("")
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            else:
                raw_content = file_content.decoded_content
                if not is_binary(raw_content):
                    try:
                        text_content = raw_content.decode('utf-8')
                        add_to_tree(repo_tree, file_content.path, text_content)
                    except UnicodeDecodeError:
                        print(f"Skipping file due to decoding error: {file_content.path}")
                    except Exception as e:
                        print(f"Skipping file due to an error: {file_content.path}. Error: {e}")
                else:
                    print(f"Skipping binary file: {file_content.path}")

        return repo_tree
    except Exception as e:
        print(f"Error: {e}")
        return None

# Example usage
repo_url = "https://github.com/dhruval30/dhruval-portfolio"
repo_tree = build_repo_tree(repo_url)

# Save the tree as a JSON file
with open("repo_tree.json", "w") as f:
    json.dump(repo_tree, f, indent=4)

print("Repository tree saved to repo_tree.json")


def json_to_pdf(json_file, pdf_file):
    # Load JSON data
    with open(json_file, 'r') as f:
        repo_tree = json.load(f)

    # Create a PDF document
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter

    # Function to add text to PDF
    def add_text(text, x, y, font_size=12, style="normal"):
        c.setFont("Helvetica-Bold" if style == "bold" else "Helvetica-Oblique" if style == "italic" else "Helvetica", font_size)
        c.drawString(x, y, text)

    # Recursive function to traverse the repository tree and print content
    def print_tree(tree, x, y, level=0):
        indent = '  ' * level
        for key, value in tree.items():
            if isinstance(value, dict):
                # If the value is a dictionary, it's a directory
                add_text(f"{indent}{key}/", x, y, style="bold")
                y -= 14
                y = print_tree(value, x + 15, y, level + 1)
            else:
                # If the value is not a dictionary, it's a file
                add_text(f"{indent}{key}", x, y, style="italic")
                y -= 14
                # Add the file content below
                for line in value.splitlines():
                    add_text(f"{indent}    {line}", x + 20, y)
                    y -= 12
                    if y < 40:  # Check if we are close to the bottom of the page
                        c.showPage()
                        y = height - 40
        return y

    # Initial coordinates
    x = 40
    y = height - 40

    # Print the repository tree
    y = print_tree(repo_tree, x, y)

    # Save the PDF file
    c.save()

# Example usage
json_file = "repo_tree.json"
pdf_file = "repo_tree.pdf"
json_to_pdf(json_file, pdf_file)

print(f"JSON content from {json_file} has been saved as PDF in {pdf_file}")

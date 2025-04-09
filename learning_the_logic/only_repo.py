import os
import json
from github import Github

# It's safer to use an environment variable for the GitHub token
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

g = Github(GITHUB_TOKEN)

def build_repo_tree(repo_url):
    try:
        # Parse the owner and repo name from the URL
        path_parts = repo_url.rstrip('/').split('/')
        owner, repo_name = path_parts[-2], path_parts[-1]
        repo = g.get_repo(f"{owner}/{repo_name}")

        print(f"Building tree for repository: {owner}/{repo_name}")

        # Initialize the repo tree
        repo_tree = {}

        def add_to_tree(tree, path, is_file=False):
            parts = path.split('/')
            current_level = tree
            for part in parts[:-1]:
                current_level = current_level.setdefault(part, {})
            if is_file:
                current_level[parts[-1]] = {}  # Represent file as an empty dict
            else:
                current_level = current_level.setdefault(parts[-1], {})

        # Get the repository contents starting from the root
        contents = repo.get_contents("")
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                # Add directory to the tree
                add_to_tree(repo_tree, file_content.path)
                # Extend the contents list with the directory contents
                contents.extend(repo.get_contents(file_content.path))
            else:
                # Add file to the tree
                add_to_tree(repo_tree, file_content.path, is_file=True)

        return repo_tree
    except Exception as e:
        print(f"Error: {e}")
        return None

# Example usage
repo_url = "https://github.com/dhruval30/dhruval-portfolio"
repo_tree = build_repo_tree(repo_url)

if repo_tree:
    # Save the tree as a JSON file
    with open("reporeporeporepo.json", "w") as f:
        json.dump(repo_tree, f, indent=4)
    print("Repository structure saved to backend_github/reporeporeporepo.json")
else:
    print("Failed to build repository structure.")

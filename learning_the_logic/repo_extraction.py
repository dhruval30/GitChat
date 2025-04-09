from github import Github
import os
import json

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

g = Github(GITHUB_TOKEN)

def is_binary(file_content):
    """Check if file content is binary."""
    textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
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

import os

def get_pdf_path(filename, project_root):
    matches = []
    filename_lower = filename.lower()
    for root, dir, files in os.walk(project_root):
        for f in files:
            if f.lower() == filename_lower:
                matches.append(os.path.join(root, f))
    return matches


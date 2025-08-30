import os

def get_pdf_path(filename, project_root):
    matches = []
    filename_lower = filename.lower()
    for root, dirs, files in os.walk(project_root):
        for f in files:
            if f.lower() == filename_lower:
                matches.append(os.path.join(root, f))
    return matches

project_root = r"C:\Users\HP\codingProjects\techjam-jamming"
pdf_name = "Florida State Law.pdf"
matches = get_pdf_path(pdf_name, project_root)

if matches:
    print("PDF found at:")
    for path in matches:
        print(path)
else:
    print("PDF not found")

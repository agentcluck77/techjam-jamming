import fitz
import re
import json

def extract_text_from_utah_bill(file_path):
    text = parse_pdf(file_path)
    output = refactor_cleaned_text(text)    
    print(json.dumps(output, indent=2))

def parse_pdf(file_path):
    """Extract text using PyMuPDF (fitz)"""
    doc = fitz.open(file_path)
    text_parts = []
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text()
        text_parts.append(text)
    
    doc.close()
    return "\n\n".join(text_parts)

def clean_text(text):
    """Clean Utah bill text by removing headers/footers"""
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Skip common Utah bill headers/footers
        if (re.match(r'^Enrolled Copy', line) or
            re.match(r'^SOCIAL MEDIA', line) or
            re.match(r'^2023 GENERAL SESSION', line) or
            re.match(r'^STATE OF UTAH', line) or
            re.match(r'^Chief Sponsor:', line) or
            re.match(r'^Senate Sponsor:', line) or
            re.match(r'^House Sponsor:', line) or
            re.match(r'^Cosponsors:', line) or
            re.match(r'^LONG TITLE', line) or
            re.match(r'^General Description:', line) or
            re.match(r'^Highlighted Provisions:', line) or
            re.match(r'^Money Appropriated in this Bill:', line) or
            re.match(r'^Other Special Clauses:', line) or
            re.match(r'^Utah Code Sections Affected:', line) or
            re.match(r'^AMENDS:', line) or
            re.match(r'^ENACTS:', line) or
            re.match(r'^H\.B\. \d+', line) or
            re.match(r'^S\.B\. \d+', line) or
            re.match(r'^- \d+ -', line) or  # Page numbers like "- 3 -"
            re.match(r'^\d{1,3}$', line) or  # Line numbers
            re.match(r'^\d{1,2} ►', line) or  # Numbered list items
            re.match(r'^Be it enacted by the Legislature of the state of Utah:', line)):
            continue
            
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def refactor_cleaned_text(text):
    """Extract main sections from Utah bill text, focusing on substantive code sections"""
    
    # Clean the text first
    text = clean_text(text)
    
    sections = []
    
    # Extract Utah Code sections (13-63-101, 13-63-201, etc.)
    utah_code_pattern = r'(\d+-\d+-\d+)\.\s+(.*?)(?=\d+-\d+-\d+\.|Section \d+\.|$)'
    code_matches = re.finditer(utah_code_pattern, text, re.DOTALL)
    
    for match in code_matches:
        code_section = match.group(1)
        code_content = match.group(2).strip()
        
        # Clean up the content
        code_content = re.sub(r'\s+', ' ', code_content)
        
        # Determine which bill this belongs to based on content
        regulation = "UT_HB311" if "addiction" in code_content.lower() else "UT_SB152"
        
        sections.append({
            "id": f"{regulation}_{code_section.replace('-', '_')}",
            "regulation": regulation,
            "section": f"Utah Code {code_section}",
            "content": code_content,
            "text": f"Utah Code {code_section}\n{code_content}"
        })
    
    # Extract section amendments (Section 1, Section 2, etc.)
    section_pattern = r'Section (\d+)\.\s+Section (\d+-\d+-\d+).*?is amended to read:(.*?)(?=Section \d+\.|$)'
    section_matches = re.finditer(section_pattern, text, re.DOTALL)
    
    for match in section_matches:
        section_num = match.group(1)
        amended_code = match.group(2)
        section_content = match.group(3).strip()
        
        # Clean up the content
        section_content = re.sub(r'\s+', ' ', section_content)
        
        sections.append({
            "id": f"UT_Amendment_Section_{section_num}",
            "regulation": "UT_Social_Media_Amendments",
            "section": f"Section {section_num} (Amending {amended_code})",
            "content": section_content,
            "text": f"Section {section_num}\nAmending {amended_code}\n{section_content}"
        })
    
    # Extract part headings
    part_pattern = r'Part (\d+)\.\s+(.*?)(?=Part \d+\.|\d+-\d+-\d+\.|$)'
    part_matches = re.finditer(part_pattern, text, re.DOTALL)
    
    for match in part_matches:
        part_num = match.group(1)
        part_title = match.group(2).strip()
        
        sections.append({
            "id": f"UT_Part_{part_num}",
            "regulation": "UT_Social_Media_Regulation",
            "section": f"Part {part_num}: {part_title}",
            "content": part_title,
            "text": f"Part {part_num}: {part_title}"
        })
    
    # Extract effective date
    effective_date_pattern = r'Section \d+\. Effective date\.\s*(.*?)(?=Section \d+\.|$)'
    effective_match = re.search(effective_date_pattern, text, re.DOTALL)
    if effective_match:
        effective_content = effective_match.group(1).strip()
        sections.append({
            "id": "UT_Effective_Date",
            "regulation": "UT_Social_Media_Regulation",
            "section": "Effective Date",
            "content": effective_content,
            "text": f"Effective Date: {effective_content}"
        })
    
    return sections

if __name__ == "__main__":
    extract_text_from_utah_bill(r"C:\Users\HP\Downloads\Utah.pdf")
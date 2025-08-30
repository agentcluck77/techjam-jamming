import google.genai as genai
import json
import re

# --- Step 0: Initialize client ---
client = genai.Client(api_key= "")

# --- Helper: Clean model output of markdown ---
def clean_json_output(text: str) -> str:
    """
    Remove markdown formatting and extra whitespace from model output.
    """
    text = re.sub(r"^```(?:json)?\s*", "", text)  # remove starting ```json or ```
    text = re.sub(r"\s*```$", "", text)           # remove ending ```
    return text.strip()

# --- Step 1: Extract Definitions and Regulations ---
STEP1_SYSTEM_PROMPT = """
You are a legal document parser.
You will be given a raw law or regulation document that may contain headers, metadata, citations, commentary, and formatting.  
Your task is to read a legal document text and extract only:
1. Definitions of legal terms (explicitly defined terms (e.g., 'As used in this section, the term "X" means ...'))
2. Actual legal clauses (enforceable rules, obligations, or prohibitions. Use the statutory provision (Section, Article, Clause) numbers as a guide for each separate regulation)

Rules:
- Always include the official section/article header (e.g., "Section 13-63-201", "Article 5.3") along with its regulation text.
- Do not drop or rewrite section/article numbers. They must appear in the regulations string exactly as they appear in the source text.
- Ignore page headers, footers, coding notes, and enrollments, but keep statutory section/article headers.
- The "regulations" value should be a single string concatenating all sections/articles in order, including their headers.
- Ignore ENROLLED markings or coding notes
- Ignore Legislative commentary, summaries, or prefaces
- Output strictly in JSON format with exactly two keys:
  {
    "definitions": { "TERM1": "Definition text", "TERM2": "Definition text", ... },
    "regulations": "All the regulations text concatenated as a single string"
  }
- Do not include any explanations or extra text outside the JSON.
"""

RAW_LEGAL_TEXT = """
ENROLLED
CS/CS/HB 3, Engrossed 1 2024 Legislature
CODING: Words stricken are deletions; words underlined are additions.
hb0003-04-er
Page 2 of 20
F L O R I D A H O U S E O F R E P R E S E N T A T I V E S
26 compliance actions; authorizing the department to
27 adopt rules; creating s. 501.1737, F.S.; defining
28 terms; requiring a commercial entity that knowingly
29 and intentionally publishes or distributes material
30 harmful to minors on a website or application that
31 contains a substantial portion of such material to use
32 certain verification methods and prevent access to
33 such material by minors; providing applicability and
34 construction; authorizing the department to bring
35 actions under the Florida Deceptive and Unfair Trade
36 Practices Act for violations; providing civil
37 penalties; authorizing punitive damages under certain
38 circumstances; providing for private causes of action;
39 requiring that such actions be brought within a
40 specified timeframe; providing that certain commercial
41 entities are subject to the jurisdiction of state
42 courts; providing construction; authorizing the
43 department to take certain investigative and
44 compliance actions; authorizing the department to
45 adopt rules; creating s. 501.1738, F.S.; defining the
46 term "anonymous age verification"; providing
47 requirements for a third party conducting age
48 verification pursuant to certain provisions; providing
49 for severability; providing an effective date.
50

ENROLLED
CS/CS/HB 3, Engrossed 1 2024 Legislature
CODING: Words stricken are deletions; words underlined are additions.
hb0003-04-er
Page 3 of 20
F L O R I D A H O U S E O F R E P R E S E N T A T I V E S
51 Be It Enacted by the Legislature of the State of Florida:
52
53 Section 1. Section 501.1736, Florida Statutes, is created
54 to read:
55 501.1736 Social media use for minors.—
56 (1) As used in this section, the term:
57 (a) "Account holder" means a resident who opens an account
58 or creates a profile or is identified by the social media
59 platform by a unique identifier while using or accessing a
60 social media platform when the social media platform knows or
61 has reason to believe the resident is located in this state.
62 (b) "Daily active users" means the number of unique users
63 in the United States who used the online forum, website, or
64 application at least 80 percent of the days during the previous
65 12 months, or, if the online forum, website, or application did
66 not exist during the previous 12 months, the number of unique
67 users in the United States who used the online forum, website,
68 or application at least 80 percent of the days during the
69 previous month.
70 (c) "Department" means the Department of Legal Affairs.
71 (d) "Resident" means a person who lives in this state for
72 more than 6 months of the year.
73 (e) "Social media platform" means an online forum,
74 website, or application that satisfies each of the following
75 criteria:
    """

# Combine system prompt and user text into a single string
input_text_step1 = STEP1_SYSTEM_PROMPT + "\n\n" + RAW_LEGAL_TEXT

# Generate Step 1 output
step1_response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents=input_text_step1  # <-- pass a single string, not a list of dicts
)

# Clean and parse JSON
step1_text_clean = clean_json_output(step1_response.text)

try:
    step1_json = json.loads(step1_text_clean)
    definitions = step1_json.get("definitions", {})
    regulations_text = step1_json.get("regulations", "")
    print("Step 1 output:")
    print(json.dumps(step1_json, indent=2))
except json.JSONDecodeError:
    raise ValueError(f"Failed to parse JSON from Step 1:\n{step1_text_clean}")


# --- Step 2: Chunk Regulations by Section/Article ---
STEP2_SYSTEM_PROMPT = """
You are a legal text parser. Your task is to read the legal regulations text and split it into individual sections or articles.

Rules:
- Each output object must have exactly two keys:
  1. "law_id": the section or article identifier (e.g., "Article 1", "Section 2.1").
    - Each law_id must only start with "Section" or "Article" (E.g. "Section 1.236", "Article 2.345")
    - Ignore very general numbers like "Section 1" if a more specific number exists in the same clause.
    - Once "Article" or "Section" has been found, the following text will be "regulation" until the next "Article" or "Section" is found
    
  2. "regulation": the full text of that section/article, preserving punctuation but removing extra line breaks.
- Preserve the order of sections as they appear in the document.
- Combine multi-line clauses under the same law_id.
- Output strictly valid JSON as a list of objects, without any extra explanations.
"""

input_text_step2 = STEP2_SYSTEM_PROMPT + "\n\n" + regulations_text

# Generate Step 2 output
step2_response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents=input_text_step2  # <-- single string
)

# Clean and parse JSON
step2_text_clean = clean_json_output(step2_response.text)

try:
    regulations_list = json.loads(step2_text_clean)
    print("\nStep 2 output:")
    print(json.dumps(regulations_list, indent=2))
except json.JSONDecodeError:
    raise ValueError(f"Failed to parse JSON from Step 2:\n{step2_text_clean}")
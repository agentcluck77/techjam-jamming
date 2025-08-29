#llm to clean law document to leave just definitions and regulations

import asyncio
import sys

# Adjust this path to point to the src/core folder containing llm_service.py
sys.path.append("/techjam-jamming/src")

from llm_service import SimpleLLMClient  

async def clean_law_llm(pdf: str):
    llm = SimpleLLMClient()  

    structure = """{
  "definitions": [
    "string"
  ],
  "regulations": [
    "string"
  ]
}"""

    prompt = f"""
        You are a legal text cleaner.
        You will be given a raw law or regulation document that may contain headers, metadata, citations, commentary, and formatting.  

        Extract only the **actual legal content**, specifically:
        - "definitions": explicitly defined terms (e.g., 'As used in this section, the term "X" means ...')
        - "regulations": enforceable rules, obligations, or prohibitions. Use the statutory provision (Section, Article, Clause) numbers as a guide for each separate regulation

        Exclude everything else:
        - Page numbers, headers, footers
        - ENROLLED markings or coding notes
        - Legislative commentary, summaries, or prefaces

        You are to output a clean, structured JSON object with two top-level keys:
        {structure}

        The following is the legal text:
        {pdf}
        """

    result = await llm._complete_gemini(
        prompt=prompt,
        max_tokens=500,
        temperature=0.2
    )

    print("LLM JSON Response:\n", result["content"])

if __name__ == "__main__":
    sample_pdf_text = """
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
    asyncio.run(clean_law_llm(sample_pdf_text))

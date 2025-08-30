set up techjam schema for law documents
    run schema_setup.py by running
    "python postgres\scripts\schemaSetup.py"

import all law documents
    frontend input region, statute, pdf file name 
    use the function [upsert_law_pdf_by_name] in upsert_law_pdf.py
    fill in with the inputs and it should run 

to retrieve regulations to put into lucas's db, refer to for_lucas.py (it is a json format output)
    use function [regulation] by inputing specific region 
    OR 
    run "python for_lucas.py [region]"

to retrieve definitions (ie law jargon) to give the lawyer agent, refer to for_lucas_2.py  
    use function [definitions] by inputting specific region and statute 
    OR 
    run "python for_lucas.py [region] [statute]"
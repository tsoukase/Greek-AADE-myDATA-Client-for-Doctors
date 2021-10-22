# Greek AADE-myDATA Client for Doctors

** SUITABLE FOR DOCTORs/PHYSICIANs that operate in Greece **

** TODO: In Windows OS's it crashes due to Socket connection and encoding errors. HELP to fix is wellcome.

## Simple Client to manage Invoices in the Greek Electronic Tax System (myDATA).

https://www.aade.gr/mydata

### KEY points:

1) Suitable for DOCTORs-PHYSICIANs that operate in Greece (Invoice type: category1_3-E3_561_003). 

2) Compatible with Python 3. No external dependencies needed (only core packages). Tested in Linux Arch.

3) Connects and uses the myDATA REST API as published [here](https://mydata-dev.portal.azure-api.net/), either in testing or production mode (needs editing the file)

4) Supports: sending, retrieval, canceling, saving in local file and printing of Invoices


### HOW TO:

1) edit/set variables in file myDATA.py: 
- 'isTesting' = 0 (testing) | 1 (production)
- 'USER' and 'KEY'(s) as registered in myDATA server
- 'BRANCHES' dictionary: branch(es) number(s) as registered in TAXIS and their address

2) Run: `python3 myDATA.py`

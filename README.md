# Greek AADE-myDATA Client for Doctors

## Simple Client to manage Invoices in the Greek Electronic Tax System (myDATA) for Doctors/Physicians.

https://www.aade.gr/mydata

### KEY points:

1) Suitable for DOCTORs-PHYSICIANs that operate in Greece (Invoice type: category1_3-E3_561_003). 

3) uses the myDATA REST API as published [here](https://mydata-dev.portal.azure-api.net/), either in testing or production mode (needs editing the file)

4) Supports: sending, retrieval based on conditions, canceling and printing of Invoices

5) TODO: In Windows OS's it crashes due to Socket connection and encoding errors. HELP to fix is wellcome.

### BEFORE running, edit/set variables in file myDATA.py: 
- 'isTesting' = 0 (testing) | 1 (production)
- your 'USERNAME' and 'KEY' as registered in myDATA server
- 'BRANCHES' dictionary: branch(es) information and number as registered in TAXIS

### Implementations:

1) PYTHON
- compatible with Python version 3.x 
- no external dependencies needed (only core packages) 
- tested in Linux Arch

2) HTML/Javascript
- The Production server of myDATA does not support the CORS protocol, so a CORS-proxy must be used (https://cors-anywhere.herokuapp.com) and can intercept our traffic (if you are ok with that!)
- All modern browsers should be supported

## Fixes are welcome!

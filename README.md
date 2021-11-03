# Greek AADE-myDATA Client for Doctors

** SUITABLE FOR DOCTORs/PHYSICIANs that operate in Greece (Invoice type: category1_3-E3_561_003) **

** TODO: In Windows OS's it crashes due to Socket connection and encoding errors. HELP to fix is wellcome.

## Simple Client to manage Invoices in the Greek Electronic Tax System (myDATA).

https://www.aade.gr/mydata

### KEY points:

1) Suitable for DOCTORs-PHYSICIANs that operate in Greece (Invoice type: category1_3-E3_561_003). 

3) uses the myDATA REST API as published [here](https://mydata-dev.portal.azure-api.net/), either in testing or production mode (needs editing the file)

4) Supports: sending (one-by-one), retrieval, canceling and printing (sent or not sent) of Invoices


### BEFORE run: edit/set variables in file myDATA.py: 
- 'isTesting' = 0 (testing) | 1 (production)
- your 'USERNAME' and 'KEY(s)' as registered in myDATA server
- 'BRANCHES' dictionary: branch(es) information and number as registered in TAXIS and their address

### Implementations:

1) Python
- compatible with v3.x 
- no external dependencies needed (only core packages) 
- tested in Linux Arch 

2) HTML/Javascript
- The Production Server of myDATA (mydatapi.aade.gr/myDATA) does not support the CORS protocol, so the script hits an Access-Control-Allow-Origin block. When programmers are public servants...

### TODO:

1) Windows bug(s), as described

2) CORS block, as described

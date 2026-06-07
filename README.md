# Greek AADE-myDATA Client for Doctors

## Simple Client to manage Invoices in the Greek Electronic Tax System (myDATA) for Doctors/Physicians.

### KEY points:

1) suitable only for Doctors/Physicians that operate in Greece (Invoice type: category1_3-E3_561_003)

2) use of myDATA REST API as published [here](https://www.aade.gr/en/mydata/technical-specifications-versions-mydata)
  
3) works in production or testing mode (needs editing the file)

4) supports: sending, retrieval, canceling, printing and filtering of Invoices

5) QR-image is shown on Invoice   

6) Only Linux is supported

### BEFORE running, edit/set variables in file myDATA.py: 
- 'isTesting' = 0 (testing) | 1 (production)
- your 'USERNAME' and 'KEY' as registered in myDATA account
- 'BRANCHES' dictionary: office branch(es) information and number as registered in TAXIS

### Implementations:

1) PYTHON
- compatible with Python version 3.x 
- no external dependencies (only core packages) 
- tested in Linux Arch

2) HTML/Javascript
- The Production server of myDATA does not support the CORS protocol, so a CORS-proxy must be used (eg. https://cors-anywhere.herokuapp.com) and can intercept our traffic (if you are ok with that!)
- All modern browsers should be supported

## Fixes are welcome!

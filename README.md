# Greek-AADE-myDATA-Client-for-Doctors

SUITABLE ONLY FOR DOCTORs/PHYSICIANs that operate in Greece

Simple Client to manage Invoices in the Greek Electronic Tax System (myDATA).

https://www.aade.gr/mydata

Key points:

1) It is suitable ONLY for DOCTORs-PHYSICIANs that operate in Greece.
(Invoice type: category1_3-E3_561_003) 

2) Compatible with Python 3. No external dependencies needed (only core packages)

3) Connects and uses the myDATA REST API as published in:
  https://mydata-dev.portal.azure-api.net/
either in devel or production mode (needs editing the file)

4) Supports: sending, retreival, canceling and printing, saving in file of Invoices,


HOW TO:

1) EDIT the file:
   variable DEVEL = {0|1}
   variables, user and key as registered in myDATA server

2) python3 myDATA.py

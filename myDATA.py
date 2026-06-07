#!/usr/bin/env python

"""
==================================================
* Εφαρμογή για αποστολή απλών ιατρικών ΑΠΥ στο MYDATA
* Application for sending simple medical invoices to MYDATA
==================================================

* Licence:      MIT
* Copywrite: 	  2026
* Written by:   Dr. Evangelos D. Tsoukas

Υποστηρίζει:
1) αποστολή ΑΠΥ στο MyDATA
2) εισαγωγή ΑΠΥ είτε από αρχείο (αν είναι πρόσφατο) ή κατέβασμα από MyDATA (από περασμένο μήνα μέχρι σήμερα)
3) φιλτράρισμα ΑΠΥ με βάση ΑΑ, ημερoμηνία, όνομα/υπηρεσία
4) ακύρωση ΑΠΥ βάσει ΜΑΡΚ
5) εκτύπωση ΑΠΥ βάσει ΜΑΡΚ (online-με QR-code) ή βάσει των fields (offline-χωρίς QR-code)
6) οι ακυρωμένες ΑΠΥ μπορούν να ληφθούν με αλλαγή της μεθόδου DownloadInvoices (if hasattr(invoice.find('%scancelledByMark' ...)
7) τo WindowsOS ΔΕΝ υποστηρίζεται! (F-U Bill)
Πεδία ΑΠΥ: ΥΠΟΚ; ΑΑ; ΗΜ/ΝΙΑ (yy-mm-dd); ΠΟΣΟ (Ε); ΠΛΗΡ (τρόπος); ΣΧΟΛΙΟ (Όνομα-Διεύθυνση-Υπηρεσία); ΜΑΡΚ; qrCodeUrl

SOS: SET Testing/Production operation

TODOs
1) αντικατάσταση της .findall με .find όταν υπάρχει μόνο μία τιμή στο xml
2) το αρχείο των Invoices γίνεται corrupt και επιστρέφει fatal error όταν μια γραμμή χωρίζεται σε δύο ή ανάμεσα υπάρχουν κενές γραμμές

"""

import os.path
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import tkinter as tk
import http.client, urllib.request, urllib.parse, urllib.error, base64
import webbrowser
import qrcode

########################
# Hardcoded Globals
########################

# External variables
TITLE	= "ΕΦΑΡΜΟΓΗ MYDATA-AADE ΓΙΑ ΙΑΤΡΟΥΣ"
USER	= 'tsoukase'
AFM		= '062725970'
DEFAULT_AMOUNT 		= '10.00'
DEFAULT_SERVICE 	= 'ΣΥΝΤΑΓΟΓΡΑΦΗΣΗ'

# Internal variables
NS 			= '{http://www.aade.gr/myDATA/invoice/v1.0}' # MyDATA XML namespace
INVOICE_HEADER = 'ΥΠΟΚ; ΑΑ; ΗΜ/ΝΙΑ; ΠΟΣΟ; ΠΛΗΡ; ΟΝ/ΜΟ-ΑΙΤΙΑ; ΜΑΡΚ; QRURL'
D 			= ';' # field delimiter
APY_FILE	= os.path.abspath('.Zapy2print.html')
QR_FILE		= os.path.abspath('.Zqrcode.png')

isProduction = 1	# 0 = TESTING

if isProduction:

  KEY      		= '' # FIRST KEY
  BASE_URL 		= 'mydatapi.aade.gr'
  BASE_EXT 		= '/myDATA'
  INVOICE_FILE 	= 'Zinvoices.csv'
  DISCARD_FILE_AFTER = 21600 # secs after which the invoice file is discarded and a fresh download follows (CURR: 6 hours)
  # Date Range: current day < 15th -> includes whole previous month, > 15th -> only current month
  firstOfCurrMonth = datetime.today().replace(day=1)
  if datetime.today().day > 15:
    daysBefore = 2
  else:
    daysBefore = 32
  DATEFROM 		= (firstOfCurrMonth - timedelta(days = daysBefore)).strftime('%d/%m/%Y')

else: # TESTING

  TITLE 		= TITLE + "- TESTING"
  KEY      		= ''
  BASE_URL 		= 'mydataapidev.aade.gr'
  BASE_EXT 		= ''
  INVOICE_FILE 	= 'Zinvoices_test.csv'
  DISCARD_FILE_AFTER = 0
  DATEFROM 		= "07/07/2019" # Πρώτη κυβέρνηση του Γκαντέμη

headers = {
           'aade-user-id': USER,
           'Ocp-Apim-Subscription-Key': KEY,
          }

# Υποκαταστήματα (κωδικός από TAXIS)
BRANCHES = {
    'ΦΛΩΡΙΝΑ':
        ['1', 'Σαρανταπόρου 28, 53100, Φλώρινα<br />τηλ 2385023513, 6972422931'],
    'ΑΜΥΝΤΑΙΟ':
        ['2', 'Ανδρέα Παπανδρέου 171, 53200, Αμύνταιο<br />τηλ 2386024440, 6972422931'],
    'ΠΤΟΛΕΜΑΙΔΑ':
        ['3', 'Βασιλέως Κωνσταντίνου 15, 50200, Πτολεμαϊδα<br />τηλ 2463082307, 6972422931']
    }

# Τρόποι πληρωμής
PAYMETHODS = {
    'Μετρητά': '3',
    'POS': '7',
    'eBanking': '6',
    'IRIS': '8'
    }

##################
# MAIN METHODS
##################

def DownloadInvoices():
  ''' DownloadInvoices downloads invoices from MyDATA and exports them to file'''

  params = urllib.parse.urlencode({ 'mark': 0,
                                    'issuervat': AFM, 
                                    'dateFrom': DATEFROM,
                                    'dateTo': datetime.today().strftime('%d/%m/%Y')})
  # 'issuervat' can be substituted by 'entityVatNumber' (not in Testing env)
  # an invoice type filter can be used, eg: 'invType': '11.2'
  conn = http.client.HTTPSConnection(BASE_URL)
  conn.request("GET", BASE_EXT + "/RequestTransmittedDocs?%s" % params, "", headers)
  response = conn.getresponse().read().decode('utf-8')

  if (response.startswith('<?xml')):
    response_root = ET.fromstring(response)

    # Save retrieved invoices in global variable and in file
    global INVOICES; INVOICES = []

    for invoice in response_root.findall('%sinvoicesDoc/%sinvoice' % (NS, NS)):
      # Selection criteria of APYs
      if (
           invoice.find('%sissuer' % (NS)) is not None and
           invoice.find('%sissuer/%svatNumber' % (NS, NS)).text == AFM and
           invoice.find('%sinvoiceHeader' % (NS)) is not None and
           invoice.find('%sinvoiceHeader/%sinvoiceType' % (NS, NS)).text == '11.2'
          ):
      
       # Exclude cancelled invoices (to include them, remove the 'not' from next line)
       if not hasattr(invoice.find('%scancelledByMark' % (NS)), 'text'):
        branch = invoice.find(
            '%sissuer/%sbranch' % (NS, NS)).text
        aa = invoice.find(
            '%sinvoiceHeader/%saa' % (NS, NS)).text
        date = invoice.find(
            '%sinvoiceHeader/%sissueDate' % (NS, NS)).text
        amount = invoice.find(
            '%spaymentMethods/%spaymentMethodDetails/%samount' % (NS, NS, NS)).text
        paymethod = invoice.find(
            '%spaymentMethods/%spaymentMethodDetails/%stype' % (NS, NS, NS)).text
        comment = invoice.find(
            '%spaymentMethods/%spaymentMethodDetails/%spaymentMethodInfo' % (NS, NS, NS))
        if not (hasattr(comment, 'text') and (comment.text is not None)): # no comment (pun)
          comment.text = ''
        mark = invoice.find('%smark' % (NS)).text
        qrCodeUrl = invoice.find('%sqrCodeUrl' % (NS)).text

        # Build invoice line
        l = D.join((branch
                  , aa
                  , date
                  , amount
                  , paymethod
                  , comment.text
                  , mark
                  , qrCodeUrl))
        INVOICES.append(l)

    with open(INVOICE_FILE, 'w') as f:
      for l in INVOICES:
        f.write("%s\n" % l.replace('\n', ''))

    result = 'Οι ΑΠΥ φορτώθηκαν από MyDATA, από ' + DATEFROM + ' μέχρι σήμερα'

    for r in response_root.iter("message"):
      result = r.text

  else:
     result = response

  ShowNotification(result, [520, H_BUTT+20])
  conn.close()


def LoadInvoicesFromFile():
  ''' LoadInvoicesFromFile loads invoices from existing file'''

  global INVOICES; INVOICES = []
  with open(INVOICE_FILE, 'r') as f:
    for l in f:
      INVOICES.append(l)

  ShowNotification('Οι ΑΠΥ φορτώθηκαν από το ΑΡΧΕΙΟ!', [520, H_BUTT+20])


def FilterInvoices():
  ''' FilterInvoices filters invoices based on the range and populate the drop down list '''

  setRange()
  
  range_until = entry_until.get()
  range_from = entry_from.get()
  sel = [INVOICE_HEADER]

  # ... based on AA
  if filtertermOmVar.get()[0] == '1':
    for l in INVOICES:
      if int(range_from) <= int(l.split(D)[1]) <= int(range_until):
        sel.append(l)

  # ... based on Date
  elif filtertermOmVar.get()[0] == '2':
    for l in INVOICES:
      if range_from <= l.split(D)[2] <= range_until:
        sel.append(l)

  # ... based on Name-Visit
  else: 
    for l in INVOICES:
      if ( (range_from in l.split(D)[5].split('-')[0])
      and (range_until in l.split(D)[5].split('-')[1]) ):
        sel.append(l)

  # remove QR-html
  sel = [l.split('https', 1)[0] for l in sel]

  # TODO: replace Optionmenu with Combobox (to fit an arbitrary number of rows in a dropdown menu)
  om_invoices = tk.OptionMenu(root, invoiceOmVar, *sel,
    command=lambda _: setMark())
  canvas.create_window(520, H_LOW, window=om_invoices, width = 380)
 


def SendInvoice():
  ''' SendInvoice SENDS an invoice to MYDATA '''

  # Get variables froms entry boxes
  branch =    BRANCHES[branchOmVar.get()][0]
  aa =        entry_aa.get()
  amount =    entry_amount.get()
  date =      entry_date.get()
  paymethod = PAYMETHODS[paymethodOmVar.get()]
  comment =   (
               entry_patname.get() + '-'
             + entry_pataddr.get() + '-'
             + entry_patvisit.get()
               ).replace(';', '')

  # Based on documentation
  payload_xml = """
<InvoicesDoc xmlns="http://www.aade.gr/myDATA/invoice/v1.0" xmlns:icls="https://www.aade.gr/myDATA/incomeClassificaton/v1.0" xmlns:ecls="https://www.aade.gr/myDATA/expensesClassificaton/v1.0">

<invoice>
  <issuer>
    <vatNumber>062725970</vatNumber>
    <country>GR</country>
    <branch>%d</branch>
  </issuer>
  <invoiceHeader>
    <series>A</series>
    <aa>%d</aa>
    <issueDate>%s</issueDate>
    <invoiceType>11.2</invoiceType>
    <currency>EUR</currency>
  </invoiceHeader>
  <paymentMethods>
    <paymentMethodDetails>
      <type>%d</type>
      <amount>%s</amount>
      <paymentMethodInfo>%s</paymentMethodInfo>
    </paymentMethodDetails>
  </paymentMethods>
  <invoiceDetails>
    <lineNumber>1</lineNumber>
    <netValue>%s</netValue>
    <vatCategory>7</vatCategory>
    <vatAmount>0</vatAmount>
    <vatExemptionCategory>7</vatExemptionCategory>
    <incomeClassification>
      <icls:classificationType>E3_561_003</icls:classificationType>
      <icls:classificationCategory>category1_3</icls:classificationCategory>
      <icls:amount>%s</icls:amount>
        <icls:id>1</icls:id>
    </incomeClassification>
  </invoiceDetails>
  <invoiceSummary>
    <totalNetValue>%s</totalNetValue>
    <totalVatAmount>0</totalVatAmount>
    <totalWithheldAmount>0.00</totalWithheldAmount>
    <totalFeesAmount>0.00</totalFeesAmount>
    <totalStampDutyAmount>0.00</totalStampDutyAmount>
    <totalOtherTaxesAmount>0.00</totalOtherTaxesAmount>
    <totalDeductionsAmount>0.00</totalDeductionsAmount>
    <totalGrossValue>%s</totalGrossValue>
    <incomeClassification>
      <icls:classificationType>E3_561_003</icls:classificationType>
      <icls:classificationCategory>category1_3</icls:classificationCategory>
      <icls:amount>%s</icls:amount>
    </incomeClassification>
  </invoiceSummary>
</invoice>
</InvoicesDoc>
  """ % (
         int(branch),
         int(aa),
         date,
         int(paymethod),
         amount,
         comment,
         amount, amount, amount, amount, amount # ...a mountain in the valley :)
         )

  # urllib accepts only bytes
  payload_xml = payload_xml.encode('utf-8')
  
  conn = http.client.HTTPSConnection(BASE_URL)
  conn.request("POST", BASE_EXT + "/SendInvoices", payload_xml, headers)
  response = conn.getresponse().read().decode('utf-8')

  if (response.startswith('<?xml')):
    response_root = ET.fromstring(response)

    # Get QR-code URL
    qrCodeUrl = ''
    for r in response_root.iter("qrCodeUrl"):    
      qrCodeUrl = r.text

    # Get Invoice Data
    for r in response_root.iter("invoiceMark"):
      l = D.join((branch
                , aa
                , date
                , amount
                , paymethod
                , comment
                , r.text
                , qrCodeUrl))
      INVOICES.append(l)

      with open(INVOICE_FILE, 'a') as f:
        f.write("%s\n" % l)

      result = 'Επιτυχής αποστολή!'

      # Reinitialize GUI entries
      entry_aa.delete(0, 'end')
      entry_aa.insert(0, str(int(aa)+1))
      entry_amount.delete(0, 'end')
      entry_amount.insert(0, DEFAULT_AMOUNT)
      paymethodOmVar.set(list(PAYMETHODS.keys())[0])
      entry_patname.delete(0,'end')
      entry_pataddr.delete(0, 'end')
      entry_pataddr.insert(0, branchOmVar.get())
      entry_patvisit.delete(0,'end')
      entry_patvisit.insert(0, DEFAULT_SERVICE)
      entry_mark.delete(0,'end')
      entry_mark.insert(0, r.text)
      FilterInvoices()

    # Iterate over all (error) Messages
    for r in response_root.iter("message"):
      result = r.text

  else:
     result = response # eg. 'Access Denied'

  ShowNotification(result, [240, H_BUTT+30])
  conn.close()



def CancelInvoice():
  ''' CancelInvoice CANCELS an invoice based on MARK '''

  mark = entry_mark.get()
  if (len(mark) != 15):
    ShowNotification("Μη έγκυρο μήκος ΜΑΡΚ (15 ψηφία)", [800, H_UPP+20])
    return
    
  params = urllib.parse.urlencode({ 'mark': mark })
  conn = http.client.HTTPSConnection(BASE_URL)
  conn.request("POST", BASE_EXT + "/CancelInvoice?%s" % params, "", headers)
  response = conn.getresponse().read().decode('utf-8')

  if (response.startswith('<?xml')):
    response_root = ET.fromstring(response)
    for r in response_root.iter("cancellationMark"):

      # Remove cancelled invoice from global variable and from file
      global INVOICES
      INVOICES = [ x for x in INVOICES if mark not in x ]
      with open(INVOICE_FILE, 'w') as f:
        for l in INVOICES:
          f.write("%s\n" % l)

      result = 'Επιτυχής διαγραφή!'
      entry_mark.delete(0,'end')
      FilterInvoices()

    for r in response_root.iter("message"):
      result = r.text

  else:
    result = response

  ShowNotification(result, [800, H_MID+35])
  conn.close()



def PrintInvoice(mode):
  ''' Print online prints an already valid APY, retrieved from file based on MARK
      Print offline prints an nonexistend APY, retrieved from GUI entries
  '''

  if mode == 'online':
    mark = entry_mark.get()
    if (len(mark) != 15):
      ShowNotification("Μη έγκυρος ΜΑΡΚ", [800, H_UPP+20])
      return

    for l in INVOICES:
      if mark in l:
        row = l.split(D)
        # Note: Branch Code->City conversion works provided the BRANCHES are numbered 1,2... 
        row[0] = list(BRANCHES.keys())[int(row[0])-1]
        # Note: Payment method string is hardcoded
        match row[4]:
          case '3': row[4] = 'Μετρητά'
          case '7': row[4] = 'POS'
          case '6': row[4] = 'eBanking'
          case '8': row[4] = 'IRIS'
        patient_info = row[5].split('-')
        # if QRcode-URL exists, add the image to html, else add empty space
        if len(row[7]) > 1:
          qrCodeHTML = """<td> <img src="%s" width="80" height="80"> </td>"""
          img = qrcode.make(row[7])
          img.save(QR_FILE)
        else:
          qrCodeHTML = """<!--%s--!>"""

    if not ('row' in locals()):
      ShowNotification("Ο ΜΑΡΚ δεν βρέθηκε", [800, H_UPP+20])
      return
      
    entry_mark.delete(0, 'end')

  else: # 'offline':
    mark = ''
    row = [branchOmVar.get()
                  , entry_aa.get()
                  , entry_date.get()
                  , entry_amount.get()
                  , paymethodOmVar.get()]
    patient_info = [entry_patname.get()
                  , entry_pataddr.get()
                  , entry_patvisit.get()]
    qrCodeHTML = """<!--%s--!>"""

  # Empty Name and Address entries
  if len(patient_info) == 2:
    patient_info[2] = DEFAULT_SERVICE
  # Empty Visit entry
  if patient_info[2] == '':
    patient_info[2] = DEFAULT_SERVICE

  # HTML-CSS template to show
  apy_html1 = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>ΑΠΥ Ιατρικών Υπηρεσιών</title>
    <style>
      .invoice-box {
        max-width: 800px;
        margin: auto;
        padding: 30px;
        border: 1px solid #eee;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.15);
        font-size: 16px;
        line-height: 24px;
        font-family: 'Helvetica Neue', 'Helvetica', Helvetica, Arial, sans-serif;
        color: #555;
      }
      .invoice-box table {
        width: 100%;
        line-height: inherit;
        text-align: left;
      }
      .invoice-box table td {
        padding: 5px;
        vertical-align: top;
      }
      .invoice-box table tr td:nth-child(2) {
        text-align: right;
      }
      .invoice-box table tr.top table td {
        padding-bottom: 20px;
      }
      .invoice-box table tr.top table td.title {
        font-size: 45px;
        line-height: 45px;
        color: #333;
      }
      .invoice-box table tr.information table td {
        padding-bottom: 40px;
      }
      .invoice-box table tr.heading td {
        background: #eee;
        border-bottom: 1px solid #ddd;
        font-weight: bold;
      }
      .invoice-box table tr.details td {
        padding-bottom: 20px;
      }
      .invoice-box table tr.item td {
        border-bottom: 1px solid #eee;
      }
      .invoice-box table tr.item.last td {
        border-bottom: none;
      }
      .invoice-box table tr.total td:nth-child(2) {
        border-top: 2px solid #eee;
        font-weight: bold;
      }
      @media only screen and (max-width: 600px) {
        .invoice-box table tr.top table td {
          width: 100%;
          display: block;
          text-align: center;
        }
        .invoice-box table tr.information table td {
          width: 100%;
          display: block;
          text-align: center;
        }
      }
      /** RTL **/
      .invoice-box.rtl {
        direction: rtl;
        font-family: Tahoma, 'Helvetica Neue', 'Helvetica', Helvetica, Arial, sans-serif;
      }
      .invoice-box.rtl table {
        text-align: right;
      }
      .invoice-box.rtl table tr td:nth-child(2) {
        text-align: left;
      }
    </style>
  </head>
  """
  apy_html2 = """
  <body>
    <div class="invoice-box">
      <table cellpadding="0" cellspacing="0">
        <tr class="top">
          <td colspan="2">
            <table>
              <tr class="heading">
                <td>
                  Απόδειξη Παροχής Υπηρεσιών<br />
                  Αριθμός: %s<br />
                  Ημερομηνία: %s
                </td>
                <td>
                  ΕΥΑΓΓΕΛΟΣ Δ. ΤΣΟΥΚΑΣ<br />
                  Ιατρικές Υπηρεσίες Νευρολογίας<br />
                  ΑΦΜ: 062725970, ΔΟΥ: ΦΛΩΡΙΝΑΣ
                </td>
                {qrCodeHTML}
              </tr>
            </table>
          </td>
        </tr>
        <tr class="information">
          <td colspan="2">
            <table>
              <tr>
                <td>
                  Διεύθυνση Έδρας:<br />
                  %s
                </td>
                <td>
                  ΠΑΡΑΛΗΠΤΗΣ:<br />
                  %s<br />
                  %s
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <tr class="heading">
          <td>ΥΠΗΡΕΣΙΑ</td>
          <td>Αξία σε Ευρώ [Εξόφληση]</td>
        </tr>
        <tr class="item">
          <td>%s<br />
              (χωρίς ΦΠΑ, άρθρο 27 Κώδικα)
          </td>
          <td>%s [%s]
          </td>
        </tr>
        <tr class="heading">
          <td><p style="font-size: 10px">%s</p></td>
          <td>ΠΑΡΑΛΑΒΗ &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; ΕΚΔΟΣΗ &emsp;&emsp;&emsp;&emsp;&emsp;</td>
        </tr>
      </table>
    </div>
  </body>
</html>
  """.format(qrCodeHTML=qrCodeHTML) % (
         row[1]
       , row[2]
       , QR_FILE    
       , BRANCHES[row[0]][1]
       , patient_info[0]
       , patient_info[1]
       , patient_info[2]
       , row[3]
       , row[4]
       , mark)

  with open(APY_FILE, 'w', encoding='utf-8') as f: 
    f.write(apy_html1 + apy_html2)
    webbrowser.open('file://' + APY_FILE)



##################
# HELPER METHODS
##################

def ShowNotification(content, place):
  ''' ShowNotification shows a temporary notification '''

  label_result = tk.Label(root, text=content, font=(SMALL_FONT))
  label_result.after(NOTIF_DUR, lambda: label_result.destroy())
  canvas.create_window(place[0], place[1], window=label_result)


def setRange():
  ''' setRange sets default or validates given range '''
  
  range_until = entry_until.get()
  range_from = entry_from.get()

  # AA range
  if filtertermOmVar.get()[0] == '1':
    if not range_until.isnumeric():
      entry_until.delete(0, 'end')
      entry_until.insert(0, "10")
    if not range_from.isnumeric():
      entry_from.delete(0, 'end')
      entry_from.insert(0, "0")

  # Date range
  elif filtertermOmVar.get()[0] == '2':
    if '-' not in range_until:
      range_until = datetime.today().strftime('%Y-%m-%d')
      entry_until.delete(0, 'end')
      entry_until.insert(0, range_until)
    if range_from == '':
      range_from = range_until
      entry_from.delete(0, 'end')
      entry_from.insert(0, range_from)

  # Name/Visit range (no change)
  else:
    pass


def SetAAandCityBasedOnBranch():
  ''' SetAAandCityBasedOnBranch inserts the next AA and the city in Address entry when a Branch is selected '''

  max_aa = 0
  for l in INVOICES:
    if ( l.split(D)[0] == BRANCHES[branchOmVar.get()][0] and
         int(l.split(D)[1]) > max_aa ):
      max_aa = int(l.split(D)[1])

  entry_aa.delete(0, 'end')
  entry_aa.insert(0, str(max_aa+1))
  entry_pataddr.delete(0, 'end')
  entry_pataddr.insert(0, branchOmVar.get())


def setMark():
  ''' setMark is a lambda and adds MARK to entry when an invoice is selected from drop-down menu'''

  entry_mark.delete(0,'end')
  entry_mark.insert(0, invoiceOmVar.get().split(D)[6].strip())





########################
# GUI: Main Window
########################

NOTIF_DUR = 3000 # msec
DEF_COLOUR = 'lavender'
BIG_FONT = 'helvetica', 14
MID_FONT = 'helvetica', 10
SMALL_FONT = 'helvetica', 9, 'bold'
H_TIT = 40
H_UPP = 80
H_MID = 120
H_LOW = 160
H_BUTT = 230 # no pun intented with 'tit' and 'butt'

root = tk.Tk()
root.title(TITLE)
canvas = tk.Canvas(root, bg=DEF_COLOUR, width = 900, height = 300)
canvas.pack()
root.resizable(False, False)
root.option_add("*font", MID_FONT)


########################
# GUI: Αποστολή ΑΠΥ
########################

canvas.create_window(100, H_TIT, window=tk.Label(root,
    text="Αποστολή ΑΠΥ", bg=DEF_COLOUR, font=BIG_FONT))

# branches
branchOmVar = tk.StringVar()
branchOmVar.set(list(BRANCHES.keys())[0])
om_branch = tk.OptionMenu(root
  , branchOmVar, *list(BRANCHES.keys())
  , command=lambda _: SetAAandCityBasedOnBranch())
canvas.create_window(240, H_TIT, window=om_branch, width = 120)

# AA
canvas.create_window(90, H_UPP, window=tk.Label(root
  , text="AA", bg=DEF_COLOUR, font=MID_FONT))
entry_aa = tk.Entry(root)
canvas.create_window(130, H_UPP, window=entry_aa, width=50)

# date
canvas.create_window(190, H_UPP, window=tk.Label(root
  , text="ΗΜ", bg=DEF_COLOUR, font=MID_FONT))
entry_date = tk.Entry(root)
canvas.create_window(250, H_UPP, window=entry_date, width=90)

# amount
canvas.create_window(90, H_MID, window=tk.Label(root
  , text="EΥ", bg=DEF_COLOUR, font=MID_FONT))
entry_amount = tk.Entry(root)
canvas.create_window(130, H_MID, window=entry_amount, width=50)

# paymethods
canvas.create_window(190, H_MID, window=tk.Label(root
  , text="ΠΛ", bg=DEF_COLOUR, font=MID_FONT))
paymethodOmVar = tk.StringVar()
paymethodOmVar.set(list(PAYMETHODS.keys())[0])
om_paymethod = tk.OptionMenu(root
  , paymethodOmVar, *list(PAYMETHODS.keys()))
canvas.create_window(250, H_MID, window=om_paymethod, width = 90)

# patient data (comments)
canvas.create_window(50, H_LOW, window=tk.Label(root
  , text="Ον/μο", bg=DEF_COLOUR, font=MID_FONT))
entry_patname = tk.Entry(root)
canvas.create_window(190, H_LOW, window=entry_patname, width=220)

canvas.create_window(50, H_LOW+30, window=tk.Label(root
  , text="Διευθ", bg=DEF_COLOUR, font=MID_FONT))
entry_pataddr = tk.Entry(root)
canvas.create_window(190, H_LOW+30, window=entry_pataddr, width=220)

canvas.create_window(50, H_LOW+60, window=tk.Label(root
  , text="Αιτία", bg=DEF_COLOUR, font=MID_FONT))
entry_patvisit = tk.Entry(root)
canvas.create_window(190, H_LOW+60, window=entry_patvisit, width=220)

# Send button
button_Send = tk.Button(text="Αποστολή", command=SendInvoice
  , bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(140, H_BUTT+30, window=button_Send)


########################
# GUI: Αναζήτηση ΑΠΥ
########################

canvas.create_window(520, H_TIT, window=tk.Label(root,
  text="Αναζήτηση ΑΠΥ", bg=DEF_COLOUR, font=BIG_FONT))

# filter terms (X = index in columns) 
filterTerms = [
               "1. Αριθμοί ΑΠΥ [Από] [Έως]"
             , "2. Ημερομηνία [Από] [Έως]"
             , "5. Στοιχεία [Όνομα ή Αιτία]"
               ] 
filtertermOmVar = tk.StringVar()
filtertermOmVar.set(filterTerms[1])
om_filterterm = tk.OptionMenu(root
  , filtertermOmVar, *filterTerms
  , command=lambda _: setRange())
canvas.create_window(520, H_UPP, window=om_filterterm, width = 210)

# range
entry_from = tk.Entry(root)
canvas.create_window(460, H_MID, window=entry_from, width = 90)
entry_until = tk.Entry(root)
canvas.create_window(580, H_MID, window=entry_until, width = 90)

# invoices (the rest is implemented in FilterInvoices)
invoiceOmVar = tk.StringVar()
invoiceOmVar.set(INVOICE_HEADER)
om_invoices = tk.OptionMenu(root, invoiceOmVar, [])
  
# Filter button
button_Request = tk.Button(text='Αναζήτηση'
  , command=FilterInvoices
  , bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(520, H_BUTT-20, window=button_Request)


########################
# GUI: Διαχείριση ΑΠΥ
########################

canvas.create_window(800, H_TIT, window=tk.Label(root
  , text="Διαχείριση ΑΠΥ", bg=DEF_COLOUR, font=BIG_FONT))

# mark
entry_mark = tk.Entry(root)
canvas.create_window(800, H_UPP, window=entry_mark, width = 120)

# Cancel button
button_Cancel = tk.Button(text='Ακύρωση'
  , command=CancelInvoice
  , bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(800, H_MID+10, window=button_Cancel)

# Print button
button_Print = tk.Button(text='Εκτύπωση'
  , command=lambda: PrintInvoice('online')
  , bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(800, H_LOW+20, window=button_Print)

# Print offline button
button_Print_offline = tk.Button(text='Εκτύπωση Offline'
  , command=lambda: PrintInvoice('offline'))
canvas.create_window(800, H_BUTT,
  window=button_Print_offline)


#########################
# Initialise DATA and GUI
#########################

entry_date.insert(0, datetime.today().strftime('%Y-%m-%d'))
entry_amount.insert(0, DEFAULT_AMOUNT)
entry_pataddr.insert(0, branchOmVar.get())
entry_patvisit.insert(0, DEFAULT_SERVICE)

if (not os.path.isfile(INVOICE_FILE) or
    datetime.now().timestamp() - os.path.getmtime(INVOICE_FILE) > DISCARD_FILE_AFTER):
  DownloadInvoices()
 
else:
  LoadInvoicesFromFile()

SetAAandCityBasedOnBranch()
FilterInvoices()

# BAM!!!
root.mainloop()

#!/usr/bin/env python

"""

==================================================
* Εφαρμογή για αποστολή ιατρικών ΑΠΥ στο MYDATA
* Application for sending medical invoices to MYDATA
==================================================

* Licence:      GPLv3
* Written by:   Dr. Evangelos D. Tsoukas
* Last updated: 2022.06

Supports:
1) αποστολή ΑΠΥ στο MyDATA
2) εισαγωγή ΑΠΥ από αρχείο ή, αν δεν υπάρχει αρχείο,
   κατέβασμα όλων των ΑΠΥ από MyDATA και αποθήκευση σε αρχείο
3) φιλτράρισμα ΑΠΥ με βάση ΑΑ, ημερoμηνία, όνομα/αιτία
4) ακύρωση ΑΠΥ βάση ΜΑΡΚ
5) εκτύπωση ΑΠΥ βάση ΜΑΡΚ ή βάση των entries ('offline') 

Pitfalls:
1) Οι ακυρωμένες ΑΠΥ αγνοούνται, οπότε κατά την συμπλήρωση ΑΑ
προσοχή στην ύπαρξη ίδιου ΑΑ ακυρωμένης ΑΠΥ
Για να κατέβουν οι ακυρωμένες, τροποποίησε την SyncAndExportInvoices
2) Σε περιβάλλον Windows:
 - compatible Python version = 3.4.3
 - only Print offline works!
3) Sometimes the invoice file gets corrupted and program craches, eg.
 - a line is split in two
 - empty lines are added after cancelling an invoice
Then you must either correct or remove it and rerun the program

Invoice columns (7): ΥΠΟΚ; ΑΑ; ΗΜ/ΝΙΑ; ΠΟΣΟ; ΠΛΗΡ; ΣΧΟΛΙΟ; ΜΑΡΚ
Comment format: Όνομα-Διεύθυνση-Αιτία επίσκεψης

Hardcoded User Info (CHECK BEFORE USE!!):
1) Testing/Production operation 
2) Minimum MARK number to download
3) Username and Keys
3) Branches (as shown in Taxis)
4) Paymethods

"""

import os
from datetime import datetime
import xml.etree.ElementTree as ET
import tkinter as tk
import http.client, urllib.request, urllib.parse, urllib.error, base64
import webbrowser


########################
# Globals
########################


# ATTENTION!!
isTesting = 0

# MYDATA credentials
USER = 'MYUSERNAME'

if isTesting:
  MARK_MIN = 0
  KEY      = 'MYKEY-testing'
  BASE_URL = 'mydata-dev.azure-api.net'
  BASE_EXT = ''
  INVOICE_FILE = 'Zinvoices_test.csv'

else:

  # Minimum Mark for invoices to Sync
  MARK_MIN = 0 # change as needed
  KEY      = 'MYKEY-production'
  BASE_URL = 'mydatapi.aade.gr'
  BASE_EXT = '/myDATA'
  INVOICE_FILE = 'Zinvoices_prod.csv'

headers = {
           'aade-user-id': USER,
           'Ocp-Apim-Subscription-Key': KEY,
          }

# Υποκαταστήματα (κωδικός από TAXIS)
BRANCHES = {
    'CITY1':
        ['1', 'ADDRESS1, TK1, CITY1<br />τηλ LAND, MOBILE'],
    'CITY2':
        ['2', 'ADDRESS2, TK2, CITY2<br />τηλ LAND, MOBILE']
    }

# Τρόποι πληρωμής
PAYMETHODS = {
    'Μετρητά': '3',
    'POS': '1'
    }

# Default service values
DEFAULT_AMOUNT = '10.00'
DEFAULT_SERVICE = 'ΣΥΝΤΑΓΟΓΡΑΦΗΣΗ'

# Internal globals
D =             ';' # line delimiter
INVOICE_HEAD = 'ΥΠΟΚ; ΑΑ; ΗΜ/ΝΙΑ; ΠΟΣΟ; ΠΛΗΡ; ΟΝ/ΜΟ-ΑΙΤΙΑ; ΜΑΡΚ'
INVOICES =      []
DISCARD_FILE_AFTER = 21600 # secs after which the file is deleted and a new Sync follows (CURR = 6 hours)

# MyDATA XML namespace
NS = '{http://www.aade.gr/myDATA/invoice/v1.0}'


##################
# MAIN METHODS
##################

def SyncAndExportInvoices():
  ''' SyncAndExportInvoices syncs invoices with MyDATA and exports them to file '''

  # Get invoices with mark > MARK_MIN
  params = urllib.parse.urlencode({'mark': MARK_MIN})
  conn = http.client.HTTPSConnection(BASE_URL)
  conn.request("GET", BASE_EXT + "/RequestTransmittedDocs?%s" % params, "", headers)
  response = conn.getresponse().read().decode('utf-8')

  if (response.startswith('<?xml')):
    response_root = ET.fromstring(response)

    # Save retrieved invoices in global variable and in file
    global INVOICES
    INVOICES = []

    for invoice in response_root.findall('%sinvoicesDoc/%sinvoice' % (NS, NS)):

      # Exclude cancelled invoices
      # (in order to include only them, remove the 'not' from the next line)
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

        # Build invoice line
        l = D.join((branch
                  , aa
                  , date
                  , amount
                  , paymethod
                  , comment.text
                  , mark))
        INVOICES.append(l)

    with open(INVOICE_FILE, 'w') as f:
      for l in INVOICES:
        f.write("%s\n" % l.replace('\n', ''))

    result = 'Οι ΑΠΥ φορτώθηκαν από το MyDATA!'

    for r in response_root.iter("message"):
      result = r.text

  else:
     result = response

  ShowNotification(result, [520, H_BUTT+20])
  conn.close()


def LoadInvoicesFromFile():
  ''' LoadInvoicesFromFile loads invoices from existing file '''

  global INVOICES
  with open(INVOICE_FILE, 'r') as f:
    for l in f:
      INVOICES.append(l)

  ShowNotification('Οι ΑΠΥ φορτώθηκαν από αρχείο. ΜΠΟΡΕΙ ΝΑ ΜΗΝ ΕΙΝΑΙ ΕΝΗΜΕΡΕΣ!', [520, H_BUTT+20])


def FilterInvoices():
  ''' FilterInvoices filters invoices based on the range and populate the drop down list '''

  setRange()
  
  range_until = entry_until.get()
  range_from = entry_from.get()
  sel = [INVOICE_HEAD]

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

  # TODO 1: replace Optionmenu with Combobox (to fit conveniently an arbitrary number of entries)
  # 2: canvas should be first destroyed, eg with canvas.delete(...), in order not to stack them
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

    # Iterate over all Invoices
    for r in response_root.iter("invoiceMark"):
      l = D.join((branch
                , aa
                , date
                , amount
                , paymethod
                , comment
                , r.text))
      INVOICES.append(l)

      with open(INVOICE_FILE, 'a') as f:
        f.write("%s\n" % l)

      result = 'Επιτυχής!'

      # Reinitialize GUI entries
      entry_aa.delete(0, 'end')
      entry_aa.insert(0, str(int(aa)+1))
      entry_amount.delete(0, 'end')
      entry_amount.insert(0, DEFAULT_AMOUNT)
      entry_patname.delete(0,'end')
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
  ''' CancelInvoice CANCELS an invoice based on MARK (no way to correct an already sent invoice) '''

  mark = entry_mark.get()
  if (len(mark) != 15):
    ShowNotification("Μη έγκυρο ΜΑΡΚ", [800, H_UPP+20])
    return
    
  params = urllib.parse.urlencode({'mark': mark})
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

      result = 'Επιτυχής!'
      entry_mark.delete(0,'end')
      FilterInvoices()

    for r in response_root.iter("message"):
      result = r.text

  else:
    result = response

  ShowNotification(result, [800, H_MID+35])
  conn.close()



def PrintInvoice(mode):
  ''' Print online prints an already valid APY, retrieved from MyData based on MARK
      Print offline prints an imaginary APY, retrieved from GUI entries
  '''

  if mode == 'online':
    mark = entry_mark.get()
    if (len(mark) != 15):
      ShowNotification("Μη έγκυρο ΜΑΡΚ", [800, H_UPP+20])
      return

    for l in INVOICES:
      if mark in l:
        invoice_info = l.split(D)
        # Note: Branch Code->City conversion works provided the BRANCHES are numbered 1,2... 
        invoice_info[0] = list(BRANCHES.keys())[int(invoice_info[0])-1]
        # Note: Code->Method conversion is specific
        if (invoice_info[4] == '3'): invoice_info[4] = 'Μετρητά'
        else: invoice_info[4] = 'POS'
        patient_info = invoice_info[5].split('-')

    if not ('invoice_info' in locals()):
      ShowNotification("Ο ΜΑΡΚ δεν βρέθηκε", [800, H_UPP+20])
      return
      
    entry_mark.delete(0, 'end')

  else: # 'offline':
    invoice_info = [branchOmVar.get()
                  , entry_aa.get()
                  , entry_date.get()
                  , entry_amount.get()
                  , paymethodOmVar.get()]
    patient_info = [entry_patname.get()
                  , entry_pataddr.get()
                  , entry_patvisit.get()]

  # Empty Name and Address entries
  if len(patient_info) == 2:
    patient_info[2] = DEFAULT_SERVICE
  # Empty Visit entry
  if patient_info[2] == '':
    patient_info[2] = DEFAULT_SERVICE

  # Default template to show
  apy_html = """
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
        width: 100%%;
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
          width: 100%%;
          display: block;
          text-align: center;
        }
        .invoice-box table tr.information table td {
          width: 100%%;
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

  <body>
    <div class="invoice-box">
      <table cellpadding="0" cellspacing="0">
        <tr class="top">
          <td colspan="2">
            <table>
              <tr class="heading">
                <td>
                  ΕΥΑΓΓΕΛΟΣ Δ. ΤΣΟΥΚΑΣ<br />
                  Ιατρικές Υπηρεσίες Νευρολογίας<br />
                  ΑΦΜ: 062725970, ΔΟΥ: ΦΛΩΡΙΝΑΣ
                </td>
                <td>
                  Απόδειξη Λιανικών Συναλλαγών<br />
                  Αριθμός: %s<br />
                  Ημερομηνία: %s
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr class="information">
          <td colspan="2">
            <table>
              <tr>
                <td>
                  Διεύθυνση:<br />
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
              (χωρίς ΦΠΑ, άρθρο 22 Κώδικα)
          </td>
          <td>%s [%s]
          </td>
        </tr>
        <tr class="heading">
          <td></td>
          <td>ΠΑΡΑΛΑΒΗ &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; ΕΚΔΟΣΗ &emsp;&emsp;&emsp;&emsp;&emsp;</td>
        </tr>
      </table>
    </div>
  </body>
</html>
  """ % (invoice_info[1]
       , invoice_info[2]    
       , BRANCHES[invoice_info[0]][1]
       , patient_info[0]
       , patient_info[1]
       , patient_info[2]
       , invoice_info[3]
       , invoice_info[4])

  file_html = os.path.abspath('Zapy2print.html')
  with open(file_html, 'w', encoding='utf-8') as f:  # enc... fixes Windows charmap bug 
    f.write(apy_html)
    webbrowser.open('file://' + file_html)



##################
# HELPER METHODS
##################


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


def AdjustMenuForSelectedBranch():
  ''' AdjustMenuForSelectedBranch increments AA and updates the city based on the selected Branch '''

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
  ''' setMark adds mark to mark entry for the selected invoice '''

  entry_mark.delete(0,'end')
  entry_mark.insert(0, invoiceOmVar.get().split(D)[6].strip())


def ShowNotification(content, place):
  ''' ShowNotification shows a temporary notification '''

  label_result = tk.Label(root, text=content, font=(SMALL_FONT))
  label_result.after(NOTIF_DUR, lambda: label_result.destroy())
  canvas.create_window(place[0], place[1], window=label_result)




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
root.title("ΕΦΑΡΜΟΓΗ MYDATA ΓΙΑ ΙΑΤΡΟΥΣ - TESTING" if isTesting == 1
            else "ΕΦΑΡΜΟΓΗ MYDATA ΓΙΑ ΙΑΤΡΟΥΣ - PRODUCTION") 
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
  , command=lambda _: AdjustMenuForSelectedBranch())
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
invoiceOmVar.set(INVOICE_HEAD)
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

if os.name != 'nt': # well, not Windows ...

  if os.path.isfile(INVOICE_FILE):
    last_modif = datetime.now().timestamp() - os.path.getmtime(INVOICE_FILE) 

    if last_modif < DISCARD_FILE_AFTER:
      LoadInvoicesFromFile()

    else:
      os.rename(INVOICE_FILE, INVOICE_FILE+'_prev')
      SyncAndExportInvoices()
 
  else:
    SyncAndExportInvoices()

  AdjustMenuForSelectedBranch()
  FilterInvoices()

# BAM!!!
root.mainloop()

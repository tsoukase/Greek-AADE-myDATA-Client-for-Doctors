#!/usr/bin/env python

"""

ATTENTION: CHECK testing operation BEFORE USE!!

=============================================
Εφαρμογή για αποστολή ιατρικών ΑΠΥ στο MYDATA
=============================================

Υποστηρίζει:
1) αποστολή ΑΠΥ
2) κατέβασμα όλων των ΑΠΥ από MyDATA
2) αναζήτηση με βάση ΑΑ, ημερoμηνία, όνομα/αιτία
4) ακύρωση ΑΠΥ βάση ΜΑΡΚ
5) εκτύπωση ΑΠΥ βάση ΜΑΡΚ ή βάση των entries (offline) 

Invoice columns: Υποκ, ΑΑ, Ημ/νία, Ποσό, Πληρωμή, Σχόλιο, ΜΑΡΚ
Comment = Patient Name - Address - Visit reason

Hardcoded User info:
1) testing operation, CHECK IT BEFORE USE!!
2) Username and Keys
3) Branches (όπως φαίνονται στο Taxis)
4) Paymethods

In Windows:
1) compatible Python version = 3.4.3
2) only Print offline works
  
"""

import os
from datetime import datetime
import xml.etree.ElementTree as ET
import webbrowser
import tkinter as tk
import http.client, urllib.request, urllib.parse, urllib.error, base64

# =====================================================
# Globals
# =====================================================

# ===== ATTENTION
isTesting = 1
# ===== ATTENTION

# MYDATA credentials
USER = 'user'
if isTesting:
  KEY      = 'key'
  BASE_URL = 'mydata-dev.azure-api.net'
  BASE_EXT = ''
else:
  KEY      = 'key'
  BASE_URL = 'mydatapi.aade.gr'
  BASE_EXT = '/myDATA'
headers = {
  'aade-user-id': USER,
  'Ocp-Apim-Subscription-Key': KEY,
  }
# MYDATA XML namespace
NS = '{http://www.aade.gr/myDATA/invoice/v1.0}'

# Υποκαταστήματα με κωδικό από TAXIS (preffered key is City name)
BRANCHES = {
  'ΑΘΗΝΑ':
    ['1', 'ΔΙΕΥΘΥΝΣΗ 1, ΤΗΛΕΦΩΝΟ 1'],
  'ΘΕΣΣΑΛΟΝΙΚΗ':
    ['2', 'ΔΙΕΥΘΥΝΣΗ 2, ΤΗΛΕΦΩΝΟ 2']
  }

# Paymethods (Missing: Διεθνές POS)
PAYMETHODS = {
  'Μετρητά': '3',
  'POS': '1'
  }

# Globals
INVOICES     = []
INVOICE_HEAD = 'ΥΠΟΚ; ΑΑ; ΗΜ/ΝΙΑ; ΠΟΣΟ; ΠΛΗΡ; ΟΝ/ΜΟ-ΑΙΤΙΑ; ΜΑΡΚ'
MAIN_SERVICE = 'ΣΥΝΤΑΓΟΓΡΑΦΗΣΗ'
D            = ';' # line delimiter


def SendInvoice():
  ''' SENDS an invoice to MYDATA '''

  # Get needed entries
  branch = BRANCHES[branchOmVar.get()][0]
  aa = entry_aa.get()
  amount = entry_amount.get()
  date = entry_date.get()
  paymethod = PAYMETHODS[paymethodOmVar.get()]
  comment = (
             entry_patname.get() + '-' +
             entry_pataddr.get() + '-' +
             entry_patvisit.get()
             ).replace(';', '')

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
         amount, amount, amount, amount, amount # ...a mountain in in the valley...
         )

  # urllib accepts only bytes
  payload_xml = payload_xml.encode('utf-8')
  
  conn = http.client.HTTPSConnection(BASE_URL)
  conn.request("POST", BASE_EXT + "/SendInvoices", payload_xml, headers)
  response = conn.getresponse().read().decode('utf-8')
  if (response.startswith('<?xml')):
    response_root = ET.fromstring(response)
    for r in response_root.iter("invoiceMark"): # TODO replace with .find

      # Add sent invoice in global variable
      INVOICES.append(D.join((
                              branch,
                              aa,
                              date,
                              amount,
                              paymethod,
                              comment,
                              r.text
                              )))
      result = 'Επιτυχής!'

      # Reinit GUI entries
      entry_aa.delete(0, 'end')
      entry_aa.insert(0, str(int(aa)+1))
      entry_patname.delete(0,'end')
      entry_patvisit.delete(0,'end')
      entry_patvisit.insert(0, MAIN_SERVICE)
      entry_mark.delete(0,'end')
      entry_mark.insert(0, r.text)
      SearchInvoices()

    for r in response_root.iter("message"):
      result = r.text

  else:
     result = response # eg. 'Access Denied'

  ShowNotification(result, [240, H_BUTT+30])
  conn.close()



def RequestTransmittedDocs():
  ''' REQUEST invoices from MyDATA (with mark > 0, ie. all)
      and calls: SearchInvoices() + AdjustForBranch() 
   '''

  params = urllib.parse.urlencode({'mark': '0'})
  conn = http.client.HTTPSConnection(BASE_URL)
  conn.request("GET", BASE_EXT + "/RequestTransmittedDocs?%s" % params, "", headers)
  response = conn.getresponse().read().decode('utf-8')

  if (response.startswith('<?xml')):
    response_root = ET.fromstring(response)

    # Add retrieved invoices in variable
    global INVOICES
    INVOICES = []
    for invoice in response_root.findall('%sinvoicesDoc/%sinvoice' % (NS, NS)):
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
        if not (hasattr(comment, 'text') and comment.text is not None): # no comment (pun)
            comment.text = ''
        mark = invoice.find(
          '%smark' % (NS)).text
        INVOICES.append(D.join((
                                branch,
                                aa,
                                date,
                                amount,
                                paymethod,
                                comment.text,
                                mark
                                )))

    result = 'OK'
    SearchInvoices()
    AdjustForBranch()

    # Write to a file, just in case
#    with open("INVOICES.csv", 'w') as f:
#      for l in INVOICES: f.write("%s\n" % l)
    
    for r in response_root.iter("message"):
      result = r.text

  else:
     result = response
   
  ShowNotification(result, [650, H_BUTT])
  conn.close()


def SearchInvoices():
  ''' Search based on range and populates invoice drop down '''

  setRange()
  
  range_until = entry_until.get()
  range_from = entry_from.get()
  sel = [INVOICE_HEAD]

  # AA search
  if searchtermOmVar.get()[0] == '1':
    for l in INVOICES:
      if int(range_from) <= int(l.split(D)[1]) <= int(range_until):
        sel.append(l)

  # Date search
  elif searchtermOmVar.get()[0] == '2':
    for l in INVOICES:
      if range_from <= l.split(D)[2] <= range_until:
        sel.append(l)

  # Name-Visit search
  else: 
    for l in INVOICES:
      if ( (range_from in l.split(D)[5].split('-')[0])
      and (range_until in l.split(D)[5].split('-')[1]) ):
        sel.append(l)

  # TODO 1: replace Optionmenu with Combobox
  # 2: canvas should be first destroyed (canvas.delete(...))
  om_invoices = tk.OptionMenu(root, invoiceOmVar, *sel,
    command=lambda _: setMark())
  canvas.create_window(520, H_LOW, window=om_invoices, width = 380)
 

def CancelInvoice():
  ''' CANCEL an invoice based on mark (there is no way to corrent an already sent invoice '''

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
    for r in response_root.iter("cancellationMark"): # TODO: replace with .find

      # Remove cancelled incvoice from global variable
      global INVOICES
      INVOICES = [ x for x in INVOICES if mark not in x ]
      result = 'Επιτυχής!'
      entry_mark.delete(0,'end')
      SearchInvoices()

    for r in response_root.iter("message"):  # eg. MARK not found
      result = r.text

  else:
    result = response

  ShowNotification(result, [800, H_MID+35])
  conn.close()



def PrintInvoice(mode):
  ''' Print online = an already valid APY, retreived from INVOICES
      Print offline = a virtual APY, retreived from GUI entries
  '''

  if mode == 'online':
    mark = entry_mark.get()
    if (len(mark) != 15):
      ShowNotification("Μη έγκυρο ΜΑΡΚ", [800, H_UPP+20])
      return

    for l in INVOICES:
      if mark in l:
        invoice_info = l.split(D)
        # Branch Code -> City works provided the BRANCHES are numbered 1,2... 
        invoice_info[0] = list(BRANCHES.keys())[int(invoice_info[0])-1]
        patient_info = invoice_info[5].split('-')

    if not ('invoice_info' in locals()):
      ShowNotification("Ο ΜΑΡΚ δεν βρέθηκε", [800, H_UPP+20])
      return
      
    entry_mark.delete(0, 'end')

  else: # 'offline':
    invoice_info = [
                    branchOmVar.get(),
                    entry_aa.get(),
                    entry_date.get(),
                    entry_amount.get()
                    ]
    patient_info = [entry_patname.get(), entry_pataddr.get(), entry_patvisit.get()]

  # empty Name and Address entries
  if len(patient_info) == 2:
    patient_info[2] = MAIN_SERVICE
  # empty Visit entry
  if patient_info[2] == '':
    patient_info[2] = MAIN_SERVICE

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
                  ΙΑΤΡΟΣ ΙΑΤΡΟΠΟΥΛΟΣ<br />
                  Ιατρικές Υπηρεσίες<br />
                  ΑΦΜ: ΧΧΧ, ΔΟΥ: ΥΥΥ
                </td>
                <td>
                  Απόδειξη Λιανικών Συναλλαγών (ΑΠΥ)<br />
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
          <td>Υπηρεσία</td>
          <td>Αξία (Ευρώ)</td>
        </tr>
        <tr class="item">
          <td>%s<br />
              (χωρίς ΦΠΑ, άρθρο 22 Κώδικα)
          </td>
          <td>%s
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
  """ % (
         invoice_info[1],
         invoice_info[2],    
         BRANCHES[invoice_info[0]][1],
         patient_info[0],
         patient_info[1],
         patient_info[2],
         invoice_info[3]
         )

  file_html = os.path.abspath('Zapy2print.html')
  with open(file_html, 'w', encoding='utf-8') as f:  # enc... fixes Windows charmap bug 
    f.write(apy_html)
    webbrowser.open('file://' + file_html)



# SMALL METHODS

def setMark():
  ''' Adds mark to mark entry for the selected invoice '''

  entry_mark.delete(0,'end')
  entry_mark.insert(0, invoiceOmVar.get().split(D)[6].strip())


def setRange():
  ''' Sets default or validates given range '''
  
  range_until = entry_until.get()
  range_from = entry_from.get()

  # AA range
  if searchtermOmVar.get()[0] == '1':
    if not range_until.isnumeric():
      entry_until.delete(0, 'end')
      entry_until.insert(0, "10")
    if not range_from.isnumeric():
      entry_from.delete(0, 'end')
      entry_from.insert(0, "0")

  # Date range
  elif searchtermOmVar.get()[0] == '2':
    if '-' not in range_until:
      range_until = datetime.today().strftime('%Y-%m-%d')
      entry_until.delete(0, 'end')
      entry_until.insert(0, range_until)
    if range_from == '':
      range_from = range_until
      entry_from.delete(0, 'end')
      entry_from.insert(0, range_from)

  # Name/Visit range not changed
  else:
    pass


def AdjustForBranch():
  ''' Increments AA and updates city in Address entry based on selected Branch '''

  max_aa = 0
  for l in INVOICES:
    if ( l.split(D)[0] == BRANCHES[branchOmVar.get()][0] and
        int(l.split(D)[1]) > max_aa ):
       max_aa = int(l.split(D)[1])

  entry_aa.delete(0, 'end')
  entry_aa.insert(0, str(max_aa+1))
  entry_pataddr.delete(0, 'end')
  entry_pataddr.insert(0, branchOmVar.get())


def ShowNotification(content, place):
  ''' Present a temporary notification '''

  label_result = tk.Label(root, text=content, font=(SMALL_FONT))
  label_result.after(NOTIF_DUR, lambda: label_result.destroy())
  canvas.create_window(place[0], place[1], window=label_result)



#===========================
# GUI: Main Window
#===========================

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


#================
# GUI: Αποστολή ΑΠΥ
#================

canvas.create_window(100, H_TIT, window=tk.Label(root,
    text="Αποστολή ΑΠΥ", bg=DEF_COLOUR, font=BIG_FONT))
    
# branches
branchOmVar = tk.StringVar()
branchOmVar.set(list(BRANCHES.keys())[0])
om_branch = tk.OptionMenu(root, branchOmVar, *list(BRANCHES.keys()),
  command=lambda _: AdjustForBranch())
canvas.create_window(240, H_TIT, window=om_branch, width = 120)

# AA
canvas.create_window(90, H_UPP, window=tk.Label(root,
  text="AA", bg=DEF_COLOUR, font=MID_FONT))
entry_aa = tk.Entry(root)
canvas.create_window(130, H_UPP, window=entry_aa, width=50)

# date
canvas.create_window(190, H_UPP, window=tk.Label(root,
  text="ΗΜ", bg=DEF_COLOUR, font=MID_FONT))
entry_date = tk.Entry(root)
canvas.create_window(250, H_UPP, window=entry_date, width=90)

# amount
canvas.create_window(90, H_MID, window=tk.Label(root,
  text="EΥ", bg=DEF_COLOUR, font=MID_FONT))
entry_amount = tk.Entry(root)
canvas.create_window(130, H_MID, window=entry_amount, width=50)

# paymethods
canvas.create_window(190, H_MID, window=tk.Label(root,
  text="ΠΛ", bg=DEF_COLOUR, font=MID_FONT))
paymethodOmVar = tk.StringVar()
paymethodOmVar.set(list(PAYMETHODS.keys())[0])
om_paymethod = tk.OptionMenu(root, paymethodOmVar, *list(PAYMETHODS.keys()))
canvas.create_window(250, H_MID, window=om_paymethod, width = 90)

# patient data (comments)
canvas.create_window(50, H_LOW, window=tk.Label(root,
  text="Ον/μο", bg=DEF_COLOUR, font=MID_FONT))
entry_patname = tk.Entry(root)
canvas.create_window(190, H_LOW, window=entry_patname, width=220)

canvas.create_window(50, H_LOW+30, window=tk.Label(root,
  text="Διευθ", bg=DEF_COLOUR, font=MID_FONT))
entry_pataddr = tk.Entry(root)
canvas.create_window(190, H_LOW+30, window=entry_pataddr, width=220)

canvas.create_window(50, H_LOW+60, window=tk.Label(root,
  text="Αιτία", bg=DEF_COLOUR, font=MID_FONT))
entry_patvisit = tk.Entry(root)
canvas.create_window(190, H_LOW+60, window=entry_patvisit, width=220)

# Send button
button_Send = tk.Button(text="Αποστολή", command=SendInvoice,
  bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(150, H_BUTT+30, window=button_Send)


#====================
# GUI: Αναζήτηση ΑΠΥ
#====================

canvas.create_window(520, H_TIT, window=tk.Label(root,
  text="Αναζήτηση ΑΠΥ", bg=DEF_COLOUR, font=BIG_FONT))

# search terms (X = index in columns) 
searchTerms = [
               "1. Αριθμοί ΑΠΥ [Από] [Έως]"
             , "2. Ημερομηνία [Από] [Έως]"
             , "5. Στοιχεία [Όνομα ή Αιτία]"
               ] 
searchtermOmVar = tk.StringVar()
searchtermOmVar.set(searchTerms[1])
om_searchterm = tk.OptionMenu(root, searchtermOmVar, *searchTerms,
    command=lambda _: setRange())
canvas.create_window(520, H_UPP, window=om_searchterm, width = 210)

# range
entry_from = tk.Entry(root)
canvas.create_window(460, H_MID, window=entry_from, width = 90)
entry_until = tk.Entry(root)
canvas.create_window(580, H_MID, window=entry_until, width = 90)

# invoices (the rest is implemented in SearchInvoices)
invoiceOmVar = tk.StringVar()
invoiceOmVar.set(INVOICE_HEAD)

# Search button
button_Request = tk.Button(text='Αναζήτηση',
  command=SearchInvoices,
  bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(450, H_BUTT, window=button_Request)

# Sync button
button_RequestTransmittedDocs = tk.Button(text='Sync MyDATA',
  command=RequestTransmittedDocs)
canvas.create_window(580, H_BUTT, window=button_RequestTransmittedDocs)

#=====================
# GUI: Διαχείριση ΑΠΥ
#=====================

canvas.create_window(800, H_TIT, window=tk.Label(root,
    text="Διαχείριση ΑΠΥ", bg=DEF_COLOUR, font=BIG_FONT))

# mark
entry_mark = tk.Entry(root)
canvas.create_window(800, H_UPP, window=entry_mark, width = 120)

# Cancel button
button_Cancel = tk.Button(text='Ακύρωση',
  command=CancelInvoice,
  bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(800, H_MID+10, window=button_Cancel)

# Print button
button_Print = tk.Button(text='Εκτύπωση',
  command=lambda: PrintInvoice('online'),
  bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(800, H_LOW+20, window=button_Print)

# Print offline button
button_Print_offline = tk.Button(text='Εκτύπωση Offline',
  command=lambda: PrintInvoice('offline'),
  bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(800, H_BUTT , window=button_Print_offline)

#=====================
# GUI: Initialise
#=====================

entry_amount.insert(0, '5.00')
entry_date.insert(0, datetime.today().strftime('%Y-%m-%d'))
entry_pataddr.insert(0, branchOmVar.get())
entry_patvisit.insert(0, MAIN_SERVICE)
if os.name != 'nt': # well, Windows ...
  RequestTransmittedDocs()

# BAM!!!
root.mainloop()

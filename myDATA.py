#!/usr/bin/env python

"""

ATTENTION: CHECK testing operation BEFORE USE!!

=============================================
Εφαρμογή για αποστολή ιατρικών ΑΠΥ στο MYDATA
=============================================

Υποστηρίζει:
1) αποστολή ΑΠΥ και προσθήκη στο local αρχείο
2) αναζήτηση από local αρχείο με βάση την ΑΑ/ημερ/σχολιο
3) κατέβασμα όλων των ΑΠΥ από MyDATA και αποθήκευση στο local αρχείο
4) ακύρωση ΑΠΥ βάση ΜΑΡΚ
5) εκτύπωση ΑΠΥ βάση ΜΑΡΚ και βάση των entries (offline) 

Local file to save:
  File: ./InvoiceList.csv
  Columns: Υποκ, ΑΑ, Ημ/νία, Ποσό, Πληρωμή, Σχόλιο, ΜΑΡΚ
  Σχόλιο: Ονομα, Διεύθυνση - Αιτία επίσκεψης

Hardcoded constants:
1) testing operation, CHECK IT BEFORE USE!!
2) Username and Keys
3) Branches (όπως φαίνονται στο Taxis)
4) Paymethods
5) Local save file of invoices, delimiter

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
testing = 1
# ===== ATTENTION

# local file to save invoice
INVOICE_FNAME = 'InvoiceList.csv'
# local file delimiter
D = ';'

# the MYDATA XML namespace
NS = '{http://www.aade.gr/myDATA/invoice/v1.0}'

# MYDATA credentials
USER = 'XXX'
KEY = 'YYY'

isDevel = 1
if isDevel:
  BASE_URL = 'mydata-dev.azure-api.net'
  BASE_EXT = ''
else:
  BASE_URL = 'mydatapi.aade.gr'
  BASE_EXT = '/myDATA'

# Υποκαταστήματα με κωδικό από TAXIS
BRANCHES = {
  'Θεσσαλονίκη': ['1',
    'Βασ. Ολγας 1, Θεσσαλονίκη<br />τηλ 2310222222, 6977777777'],
  'Αθήνα': ['3',
    'Βασ. Σοφίας 1, Αθήνα<br />τηλ 2102222222, 6977777777'],
  }

# Missing: Διεθνές POS
PAYMETHODS = {
  'Μετρητά': '3',
  'POS': '1'
  }

headers = {
  'aade-user-id': USER,
  'Ocp-Apim-Subscription-Key': KEY,
  }


# =====================================================
# SEND methods
# =====================================================

# ... farewell to... MYDATA
def SendInvoices():

  branch = BRANCHES[branchOmVar.get()][0]
  aa = entry_aa.get()
  amount = entry_amount.get()
  date = entry_date.get()
  comment = (
             entry_comment1.get() + ', ' +
             entry_comment2.get() + '-' +
             entry_comment3.get()
             ).replace(';', '')
  paymethod = PAYMETHODS[paymethodOmVar.get()]

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
    for r in response_root.iter("invoiceMark"): # executed only once
      result = 'Επιτυχής!'
      entry_mark.delete(0,'end')
      entry_mark.insert(0, r.text)
      
      with open(INVOICE_FNAME, 'a') as f:
        f.write(D.join((
                        branch,
                        aa,
                        date,
                        amount,
                        paymethod,
                        comment,
                        r.text)) + '\n'
                        )

      entry_aa.delete(0, 'end')
      entry_aa.insert(0, str(int(aa)+1))

      populateFromLocalFile()

    for r in response_root.iter("message"):
      result = r.text

  else:
     result = response # eg. 'Access Denied'

  label_result = tk.Label(root, text = result, font=(SMALL_FONT))
  label_result.after(TEMP_LABEL_DUR, lambda: label_result.destroy())
  canvas.create_window(250, H_BUTT+30, window=label_result)
  conn.close()

# increments selected Branch's AA and updates city in Name entry
def setAA():

  max_aa = 0
  with open(INVOICE_FNAME, 'r') as f:
    for l in f:
      if (
        l.split(D)[0] == BRANCHES[branchOmVar.get()][0] and
        int(l.split(D)[1]) > max_aa
        ):
         max_aa = int(l.split(D)[1])

  entry_aa.delete(0, 'end')
  entry_aa.insert(0, str(max_aa+1))
  entry_comment2.delete(0, 'end')
  entry_comment2.insert(0, branchOmVar.get())



# =====================================================
# SEARCH methods
# =====================================================

# Search based on range and ...
def populateFromLocalFile():

  setRange()
  
  range_until = entry_until.get()
  range_from = entry_from.get()
  sel = ["ΥΠΟΚ; ΑΑ; ΗΜ/ΝΙΑ; ΠΟΣΟ; ΠΛΗΡ; ΟΝ/ΜΟ-ΑΙΤΙΑ; ΜΑΡΚ"]

  with open(INVOICE_FNAME, 'r') as f:

    if searchtermOmVar.get()[0] == '1': # AA search
      for l in f:
        if int(range_from) <= int(l.split(D)[1]) <= int(range_until):
             sel.append(l)

    elif searchtermOmVar.get()[0] == '2': # Date search
      for l in f:
        if range_from <= l.split(D)[2] <= range_until:
          sel.append(l)

    else:
      for l in f:
        if (range_from in l.split(D)[5]) or (range_until in l.split(D)[5]):
           sel.append(l)

  # Canvas should be first destroyed (canvas.delete(...)
  om_invoices = tk.OptionMenu(root, invoiceOmVar, *sel,
    command=lambda _: setMark())
  canvas.create_window(510, H_LOW, window=om_invoices, width = 360)
 

def setRange():

  range_until = entry_until.get()
  range_from = entry_from.get()

  if searchtermOmVar.get()[0] == '1': # AA range

     if not range_until.isnumeric():
       entry_until.delete(0, 'end')
       entry_until.insert(0, 1)
     if not range_from.isnumeric():
       entry_from.delete(0, 'end')
       entry_from.insert(0, 2)

  elif searchtermOmVar.get()[0] == '2': # Date range

    range_until = datetime.today().strftime('%Y-%m-%d')
    entry_until.delete(0, 'end')
    entry_until.insert(0, range_until)
    range_from = range_until
    entry_from.delete(0, 'end')
    entry_from.insert(0, range_from)


# Saves in local file the Invoices with MARK > mark (now: 0)
def RequestTransmittedDocs(mark):

  mark = 0
  params = urllib.parse.urlencode({'mark': mark})
  conn = http.client.HTTPSConnection(BASE_URL)
  conn.request("GET", BASE_EXT + "/RequestTransmittedDocs?%s" % params, "", headers)
  response = conn.getresponse().read().decode('utf-8')

  if (response.startswith('<?xml')):
    response_root = ET.fromstring(response)

    with open(INVOICE_FNAME, 'w') as f:
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
          mark = invoice.find(
    '%smark' % (NS)).text
          if not (hasattr(comment, 'text') and comment.text is not None):
            comment.text = ''
          f.write(D.join((
                          branch,
                          aa,
                          date,
                          amount,
                          paymethod,
                          comment.text,
                          mark)) + '\n'
                          )
    populateFromLocalFile()
    result = 'OK'
    
    for r in response_root.iter("message"):
      result = r.text

  else:
     result = response
   
  label_result = tk.Label(root, text = result, font=(SMALL_FONT))
  label_result.after(TEMP_LABEL_DUR, lambda: label_result.destroy())
  canvas.create_window(650, H_BUTT, window=label_result)
  conn.close()



# =====================================================
# CANCEL methods
# =====================================================

# There is no way of correcting an invoice...
def CancelInvoice(mark):

  mark = entry_mark.get()
  if (len(mark) != 15):
    label_result = tk.Label(root, text = "Μη έγκυρο ΜΑΡΚ", font=(SMALL_FONT))
    label_result.after(TEMP_LABEL_DUR, lambda: label_result.destroy())
    canvas.create_window(800, H_UPP+20, window=label_result)
    return
    
  params = urllib.parse.urlencode({'mark': mark})
  conn = http.client.HTTPSConnection(BASE_URL)
  conn.request("POST", BASE_EXT + "/CancelInvoice?%s" % params, "", headers)
  response = conn.getresponse().read().decode('utf-8')

  if (response.startswith('<?xml')):
    response_root = ET.fromstring(response)

    for r in response_root.iter("cancellationMark"): # executed only once
      with open(INVOICE_FNAME, 'r') as f:
        l = f.readlines()
        
      with open(INVOICE_FNAME, 'w') as f:
        for line in l:
          if line.split(D)[6].rstrip() != mark:
            f.write(line)
      result = 'Επιτυχής!'
      entry_mark.delete(0,'end')
      populateFromLocalFile()

    for r in response_root.iter("message"):  # eg. MARK not found
      result = r.text

  else:
    result = response
   
  label_result = tk.Label(root, text=result, font=(SMALL_FONT))
  label_result.after(TEMP_LABEL_DUR, lambda: label_result.destroy())
  canvas.create_window(800, H_MID+30, window=label_result)

  conn.close()


# ... in Management MARK entry
def setMark():

  entry_mark.delete(0,'end')
  entry_mark.insert(0, invoiceOmVar.get().split(D)[6].strip())


# ====================
# PRINT methods 
# ====================

# ... online = an already valid APY, retreived from local file
# ... offline = a virtual APY, retreived from GUI entries
def PrintInvoice(mode):

  if mode == 'online':
    mark = entry_mark.get()
    if (len(mark) != 15):
      label_result = tk.Label(root, text = "Μη έγκυρο ΜΑΡΚ", font=(SMALL_FONT))
      label_result.after(TEMP_LABEL_DUR, lambda: label_result.destroy())
      canvas.create_window(800, H_UPP+20, window=label_result)
      return

    with open(INVOICE_FNAME, 'r') as f:
      for l in f:
        if mark in l:
          invoice_details = l.split(D)
          # TODO: get values from BRANCHES dict
          if   invoice_details[0] == '3': invoice_details[0] = list(BRANCHES.keys())[1]
          elif invoice_details[0] == '4': invoice_details[0] = list(BRANCHES.keys())[2]
          else: invoice_details[0] = list(BRANCHES.keys())[0] # 'Φλώρινα'

    if not ('invoice_details' in locals()):
      label_result = tk.Label(root, text = "Ο ΜΑΡΚ δεν βρέθηκε", font=(SMALL_FONT))
      label_result.after(TEMP_LABEL_DUR, lambda: label_result.destroy())
      canvas.create_window(760, H_UPP+20, window=label_result)
      return
      
    entry_mark.delete(0, 'end')

  else: # 'offline':
    invoice_details = (
                       branchOmVar.get(),
                       entry_aa.get(),
                       entry_date.get(),
                       entry_amount.get(),
                       '',
                       entry_comment1.get() + ', ' + entry_comment2.get() + '-' + entry_comment3.get()
                       )

  address = BRANCHES[invoice_details[0]][1]

  # comment[0]=name, [1]=visit reason
  comment = invoice_details[5].replace(',', '<br />').split('-')
  if len(comment) == 1: # no comment <no pun intented< (-:
    comment = ['-'.join(comment), 'Συνταγογράφηση']
  if comment[1] == '':
    comment[1] = 'Συνταγογράφηση'

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
                  Απόδειξη Λιανικών Συναλλαγών (ΑΠΥ)<br />
                  Αριθμός: %s<br />
                  Ημερομηνία: %s<br />
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
                  Υποκατάστημα:<br />
                  %s
                </td>
                <td>
                  ΠΑΡΑΛΗΠΤΗΣ:<br />
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
         invoice_details[1], 
         invoice_details[2],
         address,
         comment[0],
         comment[1],
         invoice_details[3]
         )

  file_html = os.path.abspath('apy2print.html')
  with open(file_html, 'w') as f:
    f.write(apy_html)
    webbrowser.open('file://' + file_html)




#===========================
# GUI
#===========================

TEMP_LABEL_DUR = 2000 # msec
H_TIT = 40
H_UPP = 80
H_MID = 120
H_LOW = 160
H_BUTT = 230 # no pun intented with 'tit' and 'butt'

root = tk.Tk()
root.title("ΕΦΑΡΜΟΓΗ MYDATA ΓΙΑ ΙΑΤΡΟΥΣ") 
canvas = tk.Canvas(root, bg='lavender', width = 900, height = 300)
canvas.pack()
root.resizable(False, False)

BIG_FONT = 'helvetica', 14
MID_FONT = 'helvetica', 10
SMALL_FONT = 'helvetica', 9, 'bold'
root.option_add("*font", MID_FONT)

DEF_COLOUR = 'lavender'

#================
# Αποστολή ΑΠΥ
#================

canvas.create_window(100, H_TIT, window=tk.Label(root,
    text="Αποστολή ΑΠΥ", bg=DEF_COLOUR, font=BIG_FONT))
    
# branch
branchOmVar = tk.StringVar()
branchOmVar.set(list(BRANCHES.keys())[0])
om_branch = tk.OptionMenu(root, branchOmVar, *list(BRANCHES.keys()),
  command=lambda _: setAA())
canvas.create_window(230, H_TIT, window=om_branch, width = 100)

# AA
canvas.create_window(50, H_UPP, window=tk.Label(root,
  text="#", bg=DEF_COLOUR, font=MID_FONT))
entry_aa = tk.Entry(root)
canvas.create_window(100, H_UPP, window=entry_aa, width=70)
entry_date = tk.Entry(root)
canvas.create_window(230, H_UPP, window=entry_date, width=100)

# amount
canvas.create_window(50, H_MID, window=tk.Label(root,
  text="E", bg=DEF_COLOUR, font=MID_FONT))
entry_amount = tk.Entry(root)
canvas.create_window(100, H_MID, window=entry_amount, width=70)

# paymethod
paymethodOmVar = tk.StringVar()
paymethodOmVar.set(list(PAYMETHODS.keys())[0])
om_paymethod = tk.OptionMenu(root, paymethodOmVar, *list(PAYMETHODS.keys()))
canvas.create_window(230, H_MID, window=om_paymethod, width = 100)

# comments
canvas.create_window(50, H_LOW, window=tk.Label(root,
  text="Ον/μο", bg=DEF_COLOUR, font=MID_FONT))
entry_comment1 = tk.Entry(root)
canvas.create_window(190, H_LOW, window=entry_comment1, width=220)

canvas.create_window(50, H_LOW+30, window=tk.Label(root,
  text="Διευθ", bg=DEF_COLOUR, font=MID_FONT))
entry_comment2 = tk.Entry(root)
canvas.create_window(190, H_LOW+30, window=entry_comment2, width=220)

canvas.create_window(50, H_LOW+60, window=tk.Label(root,
  text="Αιτία", bg=DEF_COLOUR, font=MID_FONT))
entry_comment3 = tk.Entry(root)
canvas.create_window(190, H_LOW+60, window=entry_comment3, width=220)

# Send
button_Send = tk.Button(text="Αποστολή", command=SendInvoices,
  bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(160, H_BUTT+30, window=button_Send)

#================
# Αναζήτηση ΑΠΥ
#================

canvas.create_window(510, H_TIT, window=tk.Label(root,
  text="Αναζήτηση ΑΠΥ", bg=DEF_COLOUR, font=BIG_FONT))

# search list
searchtermList = [
                   "1. Αριθμοί ΑΠΥ [Από] [Έως]",
                   "2. Ημερομηνία [Από] [Έως]",
                   "5. Στοιχεία [Όνομα ή Αιτία]"
                   ] 
searchtermOmVar = tk.StringVar()
searchtermOmVar.set(searchtermList[1])
om_searchterm = tk.OptionMenu(root, searchtermOmVar, *searchtermList,
    command=lambda _: setRange())
canvas.create_window(510, H_UPP, window=om_searchterm, width = 200)

# range
entry_from = tk.Entry(root)
canvas.create_window(450, H_MID, window=entry_from, width = 100)
entry_until = tk.Entry(root)
canvas.create_window(570, H_MID, window=entry_until, width = 100)

# invoice list (TODO: replace Invoice Optionmenu with Combobox)
invoiceOmVar = tk.StringVar()
invoiceOmVar.set("ΥΠΟΚ; ΑΑ; ΗΜ/ΝΙΑ; ΠΟΣΟ; ΠΛΗΡ; ΟΝ/ΜΟ-ΑΙΤΙΑ; ΜΑΡΚ")
om_invoices = tk.OptionMenu(root, invoiceOmVar, [])
canvas.create_window(510, H_LOW, window=om_invoices, width = 360)

# Search
button_Request = tk.Button(text='Αναζήτηση',
  command=populateFromLocalFile,
  bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(430, H_BUTT, window=button_Request)

# Sync
button_RequestTransmittedDocs = tk.Button(text='Sync MyDATA',
  command=lambda: RequestTransmittedDocs(0))
canvas.create_window(570, H_BUTT, window=button_RequestTransmittedDocs)

#================
# Διαχείριση ΑΠΥ
#================

canvas.create_window(800, H_TIT, window=tk.Label(root,
    text="Διαχείριση ΑΠΥ", bg=DEF_COLOUR, font=BIG_FONT))

# mark
entry_mark = tk.Entry(root)
canvas.create_window(800, H_UPP, window=entry_mark, width = 120)

# Cancel
button_Cancel = tk.Button(text='Ακύρωση',
  command=lambda: CancelInvoice(0),
  bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(800, H_MID+10, window=button_Cancel)

# Print
button_Print = tk.Button(text='Εκτύπωση',
  command=lambda: PrintInvoice('online'),
  bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(800, H_LOW+20, window=button_Print)

# Print offline
button_Print_offline = tk.Button(text='Εκτύπωση Offline',
  command=lambda: PrintInvoice('offline'),
  bg='brown', fg='white', font=(MID_FONT))
canvas.create_window(800, H_BUTT, window=button_Print_offline)

# Initialise entries
#entry_mark.insert(0, 'ΜΑΡΚ')
entry_amount.insert(0, '5.00')
entry_comment1.insert(0, 'Αρρωστος')
entry_comment2.insert(0, branchOmVar.get())
entry_comment3.insert(0, 'Συνταγογράφηση')
entry_date.insert(0, datetime.today().strftime('%Y-%m-%d'))
if not os.path.isfile(INVOICE_FNAME):
  RequestTransmittedDocs(0)
populateFromLocalFile()
setAA()

# BAM!!!
root.mainloop()

#!/usr/bin/env python3

# vanguard.py
#
# Script that reads a Vanguard investment OFX file and converts it to a
# banking OFX file. Assumes that the Vanguard account that produced the
# OFX file is only using the settlement fund (no other investments).
#
# Stephen Sorley, 9/14/2024

import argparse
import re
from datetime import datetime,timedelta,timezone


def fromOfxDate(ofxDate):
  tz = timezone.utc
  
  ## NOTE: currently the timestamps provided by Vanguard in their QFX files
  ##       are buggy - they include an offset into local time (EST), but the
  ##       actual recorded date and time are in UTC. So, just ignore the offset.
  #
  #m = re.search(r'\[([-+]?[0-9]+)',ofxDate)
  #if m:
  #  tz = timezone(timedelta(hours = int(m[1])))

  return datetime(
    year=int(ofxDate[0:4]),
    month=int(ofxDate[4:6]),
    day=int(ofxDate[6:8]),
    hour=int(ofxDate[8:10]),
    minute=int(ofxDate[10:12]),
    second=int(ofxDate[12:14]),
    tzinfo = tz
  )

def toOfxDate(dt):
  return dt.astimezone(timezone.utc).strftime('%Y%m%d%H%M%S') + '[-0:GMT]'


argparser = argparse.ArgumentParser("vanguard.py")
argparser.add_argument("input")
argparser.add_argument("-o","--output",default="vanguard-bank.ofx")
args = argparser.parse_args()

with open(args.output, 'w', newline='') as outFile:

  with open(args.input, 'r', newline='') as inFile:
    inData = inFile.read()
    
    # Read header data from the file.
    fileDate = datetime.now(timezone.utc)
    m = re.search(r'<DTSERVER>(.+?)\s*<', inData)
    if m:
      fileDate = fromOfxDate(m[1])

    m = re.search(r'<DTSTART>(.+?)\s*<', inData)
    startDate = fromOfxDate(m[1])
    
    m = re.search(r'<DTEND>(.+?)\s*<', inData)
    endDate = fromOfxDate(m[1])

    # Write header data.
    outFile.write(
f'''OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SIGNONMSGSRSV1><SONRS>
<STATUS><CODE>0<SEVERITY>INFO</STATUS>
<DTSERVER>{toOfxDate(fileDate)}
<LANGUAGE>ENG
</SONRS></SIGNONMSGSRSV1>
<BANKMSGSRSV1><STMTTRNRS><TRNUID>0<STATUS><CODE>0<SEVERITY>INFO</STATUS>
<STMTRS>
  <CURDEF>USD
  <BANKACCTFROM>
    <BANKID>Vanguard
    <ACCTID>Vanguard
    <ACCTTYPE>CHECKING
  </BANKACCTFROM>
  <BANKTRANLIST>
    <DTSTART>{toOfxDate(startDate)}
    <DTEND>{toOfxDate(endDate)}''')

    # Common patterns.
    pId = re.compile(r'<FITID>\s*(.+?)\s*<')
    pDate = re.compile(r'<DTSETTLE>\s*(.+?)\s*<')
    pAmount = re.compile(r'<TOTAL>\s*(.+?)\s*<')

    # Read and write each dividend reinvestment.
    p = re.compile(r'<REINVEST>\s*(.+?)\s*</REINVEST>',re.DOTALL)
    for m in p.finditer(inData):
      outFile.write(f'''
    <STMTTRN>
      <TRNTYPE>INT
      <DTPOSTED>{toOfxDate(fromOfxDate(pDate.search(m[1])[1]))}
      <TRNAMT>{pAmount.search(m[1])[1].replace('-','')}
      <FITID>{pId.search(m[1])[1]}
      <NAME>Dividend
    </STMTTRN>''')

    # Read and write each stock sale.
    p = re.compile(r'<SELLSTOCK>\s*(.+?)\s*</SELLSTOCK>',re.DOTALL)
    pUnits = re.compile(r'<UNITS>\s*(.+?)\s*<')
    pSecId = re.compile(r'<UNIQUEID>\s*(.+?)\s*<')
    pSecIdType = re.compile(r'<UNIQUEIDTYPE>\s*(.+?)\s*<')
    for m in p.finditer(inData):
      outFile.write(f'''
    <STMTTRN>
      <TRNTYPE>CREDIT
      <DTPOSTED>{toOfxDate(fromOfxDate(pDate.search(m[1])[1]))}
      <TRNAMT>{pAmount.search(m[1])[1].replace('-','')}
      <FITID>{pId.search(m[1])[1]}
      <NAME>Stock sale: {pUnits.search(m[1])[1].replace('-','')} shares of [{pSecIdType.search(m[1])[1]}]{pSecId.search(m[1])[1]}
    </STMTTRN>''')

    # Read and write each bank transfer in and out.
    p = re.compile(r'<INVBANKTRAN>\s*(.+?)\s*</INVBANKTRAN>',re.DOTALL)
    pPosted = re.compile(r'<DTPOSTED>\s*(.+?)\s*<')
    pTrnAmt = re.compile(r'<TRNAMT>\s*(.+?)\s*<')

    bankTransfers = set() # (date, amount) of each INVBANKTRAN, used to skip duplicate sweeps
    for m in p.finditer(inData):
      date = fromOfxDate(pPosted.search(m[1])[1])
      amount = pTrnAmt.search(m[1])[1]
      bankTransfers.add((date.date(), float(amount)))
      outFile.write(f'''
    <STMTTRN>
      <TRNTYPE>XFER
      <DTPOSTED>{toOfxDate(date)}
      <TRNAMT>{amount}
      <FITID>{pId.search(m[1])[1]}
      <NAME>Transfer
    </STMTTRN>''')

    # Read and write each sweep into or out of the settlement fund.
    #
    # Starting in late 2026, Vanguard reports bank transfers as a sale (sweep out) or
    # purchase (sweep in) of the settlement fund instead of as an INVBANKTRAN. If a file
    # contains both for the same transfer (same date and amount), only the INVBANKTRAN is kept.
    pMemo = re.compile(r'<MEMO>\s*(.+?)\s*<')
    sweeps = [
      ('SELLMF', 'Sweep Out', -1),
      ('BUYMF',  'Sweep In',  +1),
    ]
    unhandledSweepless = {'SELLMF': 0, 'BUYMF': 0}
    for tag, memoText, sign in sweeps:
      p = re.compile(rf'<{tag}>\s*(.+?)\s*</{tag}>', re.DOTALL)
      for m in p.finditer(inData):
        memo = pMemo.search(m[1])
        if not memo or memoText.lower() not in memo[1].lower():
          unhandledSweepless[tag] += 1
          continue
        date = fromOfxDate(pDate.search(m[1])[1])
        amount = sign * abs(float(pAmount.search(m[1])[1]))
        if (date.date(), amount) in bankTransfers:
          continue
        outFile.write(f'''
    <STMTTRN>
      <TRNTYPE>XFER
      <DTPOSTED>{toOfxDate(date)}
      <TRNAMT>{amount:.2f}
      <FITID>{pId.search(m[1])[1]}
      <NAME>Transfer
    </STMTTRN>''')

    # Warn about any transactions in the input that weren't converted.
    unhandled = {}
    for tag in re.findall(r'<(BUYDEBT|BUYMF|BUYOPT|BUYOTHER|BUYSTOCK|CLOSUREOPT|INCOME|INVEXPENSE|'
                          r'JRNLFUND|JRNLSEC|MARGININTEREST|RETOFCAP|SELLDEBT|SELLMF|SELLOPT|'
                          r'SELLOTHER|SPLIT|TRANSFER)>', inData):
      if tag not in unhandledSweepless:
        unhandled[tag] = unhandled.get(tag, 0) + 1
    for tag, count in unhandledSweepless.items():
      if count:
        unhandled[tag] = count
    for tag, count in unhandled.items():
      print(f'WARNING: skipped {count} <{tag}> transaction(s) - not converted, enter manually if needed')

    # Write footer.
    balance = re.search(r'<AVAILCASH>\s*(.+?)\s*<', inData)[1]
    outFile.write(f'''
  </BANKTRANLIST>
  <LEDGERBAL>
    <BALAMT>{balance}
    <DTASOF>{toOfxDate(endDate)}
  </LEDGERBAL>
</STMTRS>
</STMTTRNRS></BANKMSGSRSV1>
</OFX>''')

    # Tell user that we wrote the file, and the balance to check against QBO after import.
    print('Wrote file: ' + args.output)
    print(f'Ending balance: {balance} as of {endDate.strftime("%m/%d/%Y")} - '
          'Vanguard register in QBO should match this after import')


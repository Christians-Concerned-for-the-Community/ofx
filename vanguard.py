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

    # Read and write each dividend reinvestment.
    p = re.compile(r'<REINVEST>\s*(.+?)\s*</REINVEST>',re.DOTALL)
    pDate = re.compile(r'<DTSETTLE>\s*(.+?)\s*<')
    pAmount = re.compile(r'<TOTAL>\s*(.+?)\s*<')

    for m in p.finditer(inData):
      outFile.write(f'''
    <STMTTRN>
      <TRNTYPE>INT
      <DTPOSTED>{toOfxDate(fromOfxDate(pDate.search(m[1])[1]))}
      <TRNAMT>{pAmount.search(m[1])[1].replace('-','')}
      <FITID>{pId.search(m[1])[1]}
      <NAME>Dividend
    </STMTTRN>''')


    # Read and write each bank transfer in and out.
    p = re.compile(r'<INVBANKTRAN>\s*(.+?)\s*</INVBANKTRAN>',re.DOTALL)
    pDate = re.compile(r'<DTPOSTED>\s*(.+?)\s*<')
    pAmount = re.compile(r'<TRNAMT>\s*(.+?)\s*<')

    for m in p.finditer(inData):
      outFile.write(f'''
    <STMTTRN>
      <TRNTYPE>{'XFER'}
      <DTPOSTED>{toOfxDate(fromOfxDate(pDate.search(m[1])[1]))}
      <TRNAMT>{pAmount.search(m[1])[1]}
      <FITID>{pId.search(m[1])[1]}
      <NAME>Transfer
    </STMTTRN>''')
      
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

    # Tell user that we wrote the file.
    print('Wrote file: ' + args.output)


#!/usr/bin/env node


function safe(str) {
    return str
        .replaceAll("&", "&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&rt;");
}

function makeOfxDate(date) {
    const jsDate = new Date(date);
    ret = "";

    ret += jsDate.getUTCFullYear();
    ret += (""+(jsDate.getUTCMonth()+1)).padStart(2,"0");
    ret += (""+jsDate.getUTCDate()).padStart(2,"0");
    ret += (""+jsDate.getUTCHours()).padStart(2,"0");
    ret += (""+jsDate.getUTCMinutes()).padStart(2,"0");
    ret += (""+jsDate.getUTCSeconds()).padStart(2,"0");
    ret += "." + (""+jsDate.getUTCMilliseconds()).padStart(3,"0");
    ret += "[+00]";

    return ret;
}


function makeHeader(creationDate) {
    ret =
`OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SONRS>
<STATUS><CODE>0<SEVERITY>INFO</STATUS>
<DTSERVER>${makeOfxDate(creationDate)}
<LANGUAGE>ENG
</SONRS>
<BANKMSGSRSV1><STMTTRNRS><TRNUID>0<STATUS><CODE>0<SEVERITY>INFO</STATUS>
<STMTRS>`;
    return ret;
}

function makeBalance(amount,balanceDate) {
    return `
    <LEDGERBAL>
        <BALAMT>${amount.toFixed(2)}
        <DTASOF>${makeOfxDate(balanceDate)}
    </LEDGERBAL>`;
}

function makeTransaction(type, date, amount, id, name, memo) {
    ret = `
    <STMTTRN>
        <TRNTYPE>${type}
        <DTPOSTED>${makeOfxDate(date)}
        <TRNAMT>${amount.toFixed(2)}
        <FITID>${safe(id)}`;
    if (name) {
        ret += `
        <NAME>${safe(name)}`;
    }
    if (memo) {
        ret += `
        <MEMO>${safe(memo)}`;
    }
    ret += `
    </STMTTRN>`;
    return ret;
}

function makeFooter() {
    return `
</STMTRS>
</STMTTRNRS></BANKMSGSRSV1></OFX>`;
}

const fs = require('node:fs');

const outFile = 'test.ofx';

const now = new Date(Date.now());

let content = '';

content += makeHeader(now);

content += makeTransaction(
    "CREDIT",
    "2023-11-09T03:24:00Z",
    12.35,
    "871a934d-b47c-45d3-a92f-e124ee0ca3e5",
    "Test transaction #1",
    "testing - dev - <can you believe &>?"
);

content += makeBalance(100, now);

content += makeFooter();

fs.writeFileSync(outFile, content);
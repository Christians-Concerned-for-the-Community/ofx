#!/usr/bin/env node


function makeOfxDate(jsDate) {
    ret = "";

    ret += jsDate.getUTCFullYear();
    ret += (""+(jsDate.getUTCMonth()+1)).padStart(2,"0");
    ret += (""+jsDate.getUTCDate()).padStart(2,"0");
    ret += (""+jsDate.getUTCHours()).padStart(2,"0");
    ret += (""+jsDate.getUTCMinutes()).padStart(2,"0");
    ret += (""+jsDate.getUTCSeconds()).padStart(2,"0");
    ret += ("."+jsDate.getUTCMilliseconds()).padStart(3,"0");
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
<STMTRS>
`;
    return ret;
}

function makeFooter() {
    ret =
`</STMTRS>
</STMTTRNRS></BANKMSGSRSV1></OFX>`;
    return ret;
}

const fs = require('node:fs');

const outFile = 'test.ofx';


let content = '';

content += makeHeader(new Date(Date.now()));


content += makeFooter();

fs.writeFileSync(outFile, content);
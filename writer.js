#!/usr/bin/env node


function makeHeader() {
    return
`OFXHEADER:100
DATA:OFXSGML
VERSION: 102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
`;
}

function makeSignon()


const fs = require('node:fs');

const outFile = 'test.ofx';


let content = '';




// OFX standard header, version 1.02
content +=
`OFXHEADER:100
DATA:OFXSGML
VERSION: 102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
`;

fs.writeFileSync(outFile, content);
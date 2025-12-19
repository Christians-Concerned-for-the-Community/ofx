# OFX file utilities

This project contains a few utilities for working with Open Financial Exchange
formatted files (.ofx, .qfx, .qbo).

The only one that's actively in use is vanguard.py.

This utility converts the "investment" type file returned by Vanguard's download
center into a "bank" type file that can be imported into Quickbooks.

It will ignore all but the following three kinds of transactions:
 * Bank transfers in/out of the settlement fund
 * Dividend reinvestments for the settlement fund
 * Stock sales (proceeds go into settlement fund)

Effectively, this looks at the settlement fund as if it was a bank account. If you
maintain other assets in your vanguard brokerage account, like long-term stock or
mutual fund holdings, you'll need to manually update those in Quickbooks as 
separate assets.

# OFX file utilities

This project contains a few utilities for working with Open Financial Exchange
formatted files (.ofx, .qfx, .qbo).

The only one that's actively in use is vanguard.py.

This utility converts the "investment" type file returned by Vanguard's download
center into a "bank" type file that can be imported into Quickbooks.

It will ignore all but the following kinds of transactions:
 * Bank transfers in/out of the settlement fund. Vanguard reports these either as
   bank transactions (older exports) or as sweeps into/out of the settlement fund
   (exports since late 2026). If a file has both for the same transfer (same date
   and amount), it's only counted once.
 * Dividend reinvestments for the settlement fund
 * Stock sales (proceeds go into settlement fund)

Any other transaction types in the file are skipped, and a warning is printed for
each kind so you can enter them manually if needed.

After writing the output file, the script prints the account's ending balance.
Once you've imported the file, the Vanguard register in Quickbooks should match it.

Effectively, this looks at the settlement fund as if it was a bank account. If you
maintain other assets in your vanguard brokerage account, like long-term stock or
mutual fund holdings, you'll need to manually update those in Quickbooks as 
separate assets.

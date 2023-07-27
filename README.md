# AmDesp
## MiddleWare connecting Commence Rm Database entries to DespatchBay Shipping API

* Takes .Dbase files representing Sale or Hire records, and connects to DespatchBay.com's shipping Api to book and track inbound and outbound courier collections.

* Prints Shipping Labels for outbound, Sends generated Email to customer for outbound 

* Configured via toml

* Matches Postcode + naive address string to PostOffice data, or else uses fuzzy logic to match a best-guess and a GUI for user confirmation / input. 

* PysimpleGui for User interface

* Logs tracking data back to Commence Rm via powershell and [CmcLibNet](https://cmclibnet.vovin.nl/)

## Environment Variables

access to despatchbay api requires the following keys to be set in systyem environment or .env
`DESPATCH_API_USER`
`DESPATCH_API_KEY`

for sandbox operation the following keys are required:
`DESPATCH_API_USER_SANDBOX`
`DESPATCH_API_KEY_SANDBOX`

user_config.toml must be complete. or nearly complete. or mostly complete? basically it probably wont work if you dont fill in all the user_config fields, but you don't exist this is mostly for show this code is only useful to one company.


## Installation
do that

## Setup
also that

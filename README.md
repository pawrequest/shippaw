# AmDesp

## MiddleWare connecting Commence Rm Database entries to DespatchBay Shipping API

* Takes .Dbase files representing Sale or Hire records, and connects to DespatchBay.com's shipping Api to book and track
  inbound and outbound courier collections and ad-hoc drop-offs.

* Prints Shipping Labels for outbound, Sends generated Email to customer for inbound

* Configured via user_config.toml

* Matches Postcode + naive address string to PostOffice data, or else uses fuzzy logic to match a best-guess and a GUI
  for user confirmation / input.

* PysimpleGui for User interface

* Logs tracking data back to Commence Rm via powershell and [CmcLibNet](https://cmclibnet.vovin.nl/)

## Environment Variables

access to despatchbay api requires the following keys to be set in systyem environment or .env
`DESPATCH_API_USER`
`DESPATCH_API_KEY`

for sandbox operation the following keys are required:
`DESPATCH_API_USER_SANDBOX`
`DESPATCH_API_KEY_SANDBOX`

user_config.toml must be complete. or nearly complete. or mostly complete? basically it probably wont work if you dont
fill in all the user_config.toml fields, but you don't exist this is mostly for show this code is only legitmately
useful to one company.

## Installation

do that

## Setup

also that

## Usage

### CLI

Run `Amdesp.exe` or `main.py` from CLI, providing the following arguments:

1) ShipMode ('SHIP' | 'TRACK')
2) ShipDirection ('IN' | 'OUT')
3) Category ('HIRE' | 'SALE')
4) InputFile (stringified path to a .dbase file)

## Overview

### main.py

Entry point for CLI

* parses args and prompts for input file if none given
* instantiates `Config` object from `config.py` as per `user_config.toml`
* instantiates `Shipper` object from `Shipper.py`
* calls `Shipper.get_shipments()` to create `Shipment` objects from dbase file
* calls `shipper.dispatch()` if ShipMode is SHIP, .track() if TRACK

### shipper.py

Main Module with user-facing methods\
`__init__()`:

* instantiates `DespatchBaySDK` Client from `DespatchBaySDK.py`
* Wraps Client to track and log API calls (implements exponential backoff when required)

`get_shipments()`:

* parses dbase file and creates `Shipment` objects
* stores Shipment objects in `Shipper.shipments`

`dispatch()`:

* calls `addresser.address_shipments()` to set contact and address data for each `Shipment`
* calls `gather_dbay_objs()` to get `Service`, `CollectionDate`, `Parcels`, and `ShipmentRequest` objects
* calls `dispatch_loop()` to launch Gui for user to confirm / edit details before booking carriage
* calls `post_book()` to display results, allow reprinting of labels, etc

### addresser.py

various functions relating to addressing shipments, includes:
`address_shipments()`:

* calls get_home_base() to get either a `Sender` or `Recipient` object (per config.outbound) to represent the user's
  address as provided in user_config.toml
* creates a `Contact` object from Shipment.email, Shipment.phone, and Shipment.contact_name
* calls remote_address_script() to get `Address` object from Shipment details
* calls `sender_from_contact_address()` or `recip_from_contact_address()` to create either a `Sender` or `Recipient`
  object representing the remote address

`remote_address_script()`:
Uses incresingly fuzzy logic to return an address
* calls `address_from_direct_search()` to return an `Address` from explicit search matches against `Shipment.customer, .delivery_name, and .str_to_match`
* if no address returned calls `fuzzy_address` to search valid addresses at postcode and return a `BestMatch.address` from `FuzzyScores`
* displays `BestMatch.address` in Gui for user to confirm / edit




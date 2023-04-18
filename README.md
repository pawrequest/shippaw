# AmDesp

* Takes .Dbase files and connects to DespatchBay.com's shipping Api to book and track courier collections.


* Configured via config toml


* Features 3 modes: 'ship_out', 'ship_in', and 'track' modes. base address as defined in toml is used as sender address in 'ship_out' and recipient in 'ship_in' modes.


* Parses exported .Dbase files for customer, address, and consignment details


* Tries to match address details with Dbay address database - first with direct searches, then with increasingly fuzzy logic, then by user/gui as a fallback. 


* PysimpleGui displays each shiment with various command buttons.


* PySimpleGui to view and edit addresses.


* Gui invoked functions allow user to change:
    * Sender address
    * Recipient address
    * Collection data
    * Shipping Service
    * number of parcels


* Logs shipment_ids back to commence via powershell script including Vovin CmcLibNet. 


* fetches and displays tracking data for shipment_ids if they existing


* define base address to use as sender for 'ship_out' or 'recipient' for ship_in in config toml


* checks / sets api keys into system environment, prompts user for input if necessary

## Environment Variables

access to despatchbay api requires the following keys to be set in systyem environment or .env
`DESPATCH_API_USER`
`DESPATCH_API_KEY`

for sandbox operation the following keys are required:
`DESPATCH_API_USER_SANDBOX`
`DESPATCH_API_KEY_SANDBOX`


## Installation

## Setup


## Environment Variables

access to despatchbay api requires the following keys to be set in systyem environment or .env

`DESPATCH_API_USER`

`DESPATCH_API_KEY`


## Installation

Install my-project with npm

```bash
  npm install my-project
  cd my-project
```
    
## Acknowledgements

 - [Awesome Readme Templates](https://awesomeopensource.com/project/elangosundar/awesome-README-templates)
 - [Awesome README](https://github.com/matiassingers/awesome-readme)
 - [How to write a Good readme](https://bulldogjob.com/news/449-how-to-write-a-good-readme-for-your-github-project)



## Usage/Examples

```javascript
import Component from 'my-project'

function App() {
  return <Component />
}
```


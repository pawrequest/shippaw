# todo updates commence when shipment delivered
# todo tests
# todo better logging
# todo async / multiproces
# todo api rate limit avoidance?
# todo move from r drive to platform agnostic

import sys

from amdesp.config import Config, ROOT_DIR, LOG_FILE, ShipMode, get_amdesp_logger
from amdesp.shipper import Shipper
import PySimpleGUI as sg
import logging

FAKE_MODE = 'ship_in'
# FAKE_MODE = 'track'

"""
Amdesp - middleware to connect Commence RM to DespatchBay's shipping service.
modes = [ship_in, ship_out, track_in, track_out]
takes xml and (soon) dbase files as inputs - location provided as argument
validates and corrects data to conform to shipping service requirements,
allows user to update addresses / select shipping services etc, queue and book collection,
prints labels, gets tracking info on existing shipments
includes
+ Commence vbs scripts for exporting xml,
+ python app with pysimplegui gui
+ powershell to check vbs into commence
+ powershell to log shipment ids to commence
+ Vovin CmcLibNet installer for interacting with commence
"""


logger = get_amdesp_logger()

def main(main_mode: str):
	""" sandbox = fake shipping client, no money for labels!"""
	sg.popup_quick_message('Config', keep_on_top=True)
	try:
		config = Config.from_toml2(mode=main_mode)

		config.log_config()
		client = config.get_dbay_client_ag(sandbox=config.sandbox)
		# config.setup_amdesp(sandbox=sandbox, client=client)

		shipper = Shipper(config=config)
		shipper.dispatch(client=client, in_file=config.paths.dbase_export, config=config)

	except Exception as e:
		logger.exception(f'MAINLOOP ERROR: {e}')


if __name__ == '__main__':
	# AmDesp called from commandline, i.e launched from Commence vbs script - parse args for mode
	logger.info(f'launched with {len(sys.argv)} arguments:{sys.argv}')
	if len(sys.argv) > 1:
		# exe location = 0
		mode = sys.argv[1].lower()
		# in_file = sys.argv[2].lower()

	# AmDesp called from IDE - inject mode
	else:
		# in_file = INPUT_FILE
		mode = FAKE_MODE
	logger.info(f'{mode=}')
	main(main_mode=mode)

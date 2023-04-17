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

# todo updates commence when shipment delivered
# todo tests
# todo better logging
# todo async / multiproces

import sys

from amdesp.config import Config, ROOT_DIR, LOG_FILE, ShipMode
from amdesp.shipper import Shipper
import PySimpleGUI as sg
import logging

logger = logging.getLogger(name='AmDesp_logger')
logging.basicConfig(
	level=logging.INFO,
	format='{asctime} {levelname:<8} {message}',
	style='{',
	handlers=[
		logging.FileHandler(LOG_FILE, mode='a'),
		logging.StreamHandler(sys.stdout)
	])
logger.info('logger')

# get stored data files for non CLI

# STORED_XML = str(ROOT_DIR / 'data' / 'amship.xml')
# STORED_XML = r'c:\amdesp\data\amship.xml'
# INPUT_FILE = STORED_XML

STORED_DBASE = str(ROOT_DIR / 'data' / 'amherst_export.dbf')
INPUT_FILE = STORED_DBASE
FAKE_MODE = 'ship_in'
FAKE_SANDBOX = False


def main(main_mode: str, main_sandbox: bool, infile: str):
	""" sandbox = fake shipping client, no money for labels!"""
	sg.popup_quick_message('Config', keep_on_top=True)
	outbound = None
	try:
		config = Config.from_toml2(sandbox=main_sandbox, mode=main_mode)

		config.log_config()
		client = config.get_dbay_client_ag(sandbox=sandbox)
		if mode == 'ship_out':
			outbound = True
		elif mode == 'ship_in':
			outbound = False
		else:
			logger.exception('MODE FAULT')

		shipper = Shipper(config=config)
		shipper.dispatch(client=client, in_file=infile, config=config)

	except Exception as e:
		logger.exception(f'MAINLOOP ERROR: {e}')


if __name__ == '__main__':
	# AmDesp called from commandline, i.e launched from Commence vbs script - parse args for mode
	logger.info(f'launched with {len(sys.argv)} arguments:{sys.argv}')
	if len(sys.argv) > 1:
		# exe location = 0
		mode = sys.argv[1].lower()
		in_file = sys.argv[2].lower()
		sandbox = False

	# AmDesp called from IDE - inject mode
	else:
		in_file = INPUT_FILE
		sandbox = FAKE_SANDBOX
		mode = FAKE_MODE
	# mode = 'track_out'
	logger.info(f'{mode=}')
	logger.info(f'{in_file=}')
	logger.info(f'{sandbox=}')
	main(main_mode=mode, infile=in_file, main_sandbox=sandbox)

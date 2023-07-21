


@dataclass
class ShipmentABC(ABC):
    def __init__(self, ship_dict: dict, category:ShipmentCategory):
        """
        :param ship_dict: a dictionary of shipment details
        """

        # input paramaters
        self.category= category.title()
        self._shipment_name: str = ship_dict.get('shipment_name')
        self.address_as_str: str = ship_dict.get('address_as_str')
        self.boxes: int = int(ship_dict.get('boxes', 1))
        self.customer: str = ship_dict.get('customer')
        self.contact_name: str = ship_dict.get('contact')
        # self.contact_name: str = next((ship_dict.get(key) for key in ['contact', 'contact_name'] if key in ship_dict), None)
        self.email: str = ship_dict.get('email')
        self.postcode: str = ship_dict.get('postcode')
        self.send_out_date: datetime.date = ship_dict.get('send_out_date', datetime.today())
        self.status: str = ship_dict.get('status')
        self.telephone: str = ship_dict.get('telephone')
        self.delivery_name = ship_dict.get('delivery_name')
        self.inbound_id: Optional[str] = ship_dict.get('inbound_id')
        self.outbound_id: Optional[str] = ship_dict.get('outbound_id')

        self.shipment_name_printable = re.sub(r'[:/\\|?*<">]', "_", self._shipment_name)

        self.collection_booked:bool = False
        self.printed:bool = False
        self.date_matched:bool = False
        self.default_service_matched: bool = False
        self.logged_to_commence: bool = False

        self.label_location: Path = Path()

        self.date_menu_map = dict()
        self.service_menu_map: dict = dict()
        self.candidate_keys = {}

        self.bestmatch: Optional[BestMatch] = None
        self.remote_contact: Optional[Contact] = None

        # [logging.info(f'SHIPMENT - {self.shipment_name_printable} - {var} : {getattr(self, var)}') for var in vars(self)]
        logging.info(f'SHIPMENT - {self.shipment_name_printable} - {self.__dict__.items()}')
        logging.info('\n')

    @property
    def str_to_match(self):
        return parse_amherst_address_string(self.address_as_str)

    #
    #
    # @classmethod
    # def get_shipments(cls, config: Config, category:ShipmentCategory, dbase_file:str) -> list:
    #     """ parses input filetype and calls appropriate function to construct and return a list of shipment objects"""
    #     logger.info(f'DBase file = {dbase_file}')
    #     shipments: [Shipment] = []
    #     try:
    #         for record in DBF(dbase_file):
    #             [logger.debug(f'DBASE RECORD - {k} : {v}') for k, v in record.items()]
    #             try:
    #                 ship_dict = shipdict_from_dbase(record=record, import_mapping=config.import_mapping)
    #                 shipment = Shipment(ship_dict=ship_dict, category=category)
    #                 shipments.append(shipment)
    #             except Exception as e:
    #                 logger.exception(f'{record.__repr__()} - {e}')
    #                 continue
    #
    #     except UnicodeDecodeError as e:
    #         logging.exception(f'DBASE import error with {dbase_file} \n {e}')
    #     except DBFNotFound as e:
    #         logger.exception(f'.Dbf or Dbt are missing \n{e}')
    #     except Exception as e:
    #         logger.exception(e)
    #         raise e
    #     return shipments

    # def to_dict(self):
    #     allowed_types = [dict, str, tuple, list, int, float, set, bool, datetime, None]
    #     result = {}
    #     for attr_name in dir(self):
    #         attr_value = getattr(self, attr_name)
    #         if type(attr_value) in allowed_types:
    #             result[attr_name] = attr_value
    #     return result

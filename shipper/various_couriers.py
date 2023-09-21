
#
# class DbayShipment(Shipment):
#     def __init__(self, ship_dict, category):
#         super().__init__(category=category, ship_dict=ship_dict)
#
#         self.parcels: [Parcel] = []
#         self.remote_address: Address | None = None
#         self.sender_contact = None
#         self.remote_contact: Optional[Contact] = None
#         self.remote_sender_recip: Optional[Sender | Recipient] = None
#         self.sender = Sender
#         # self.recipient_contact = None
#
#         self.despatch_objects = DespatchObjects()
#         self.recipient: Recipient
#         self.collection_date: CollectionDate
#         self.shipment_request: ShipmentRequest
#         self.shipment_return: ShipmentReturn
#         self.service: Service
#         self.available_services: [List[Service]]
#         self.collection: Collection
#
#     @classmethod
#     def get_dbay_shipments(cls, import_mapping: dict, category: ShipmentCategory, dbase_file: str):
#         amdesp_logger.debug(f'DBase file = {dbase_file}')
#         shipments_dict = {}
#         shipments_list: [DbayShipment] = []
#         try:
#             for record in DBF(dbase_file):
#                 [amdesp_logger.debug(f'DBASE RECORD - {k} : {v}') for k, v in record.items()]
#                 try:
#                     ship_dict = shipdict_from_dbase(record=record, import_mapping=import_mapping)
#                     shipment = DbayShipment.from_dbase_record(record=record, ship_dict=ship_dict, category=category)
#                     shipments_dict.update({shipment.shipment_name_printable: shipment})
#                     shipments_list.append(shipment)
#                 except Exception as e:
#                     amdesp_logger.exception(f'{record.__repr__()} - {e}')
#                     continue
#
#         except UnicodeDecodeError as e:
#             logging.exception(f'DBASE import error with {dbase_file} \n {e}')
#             raise e
#         except DBFNotFound as e:
#             amdesp_logger.exception(f'.Dbf or Dbt are missing \n{e}')
#             raise e
#         except Exception as e:
#             amdesp_logger.exception(e)
#             raise e
#         # return shipments_dict
#         return shipments_list
#
#
# def get_dbay_shipments(import_mapping: dict, category: ShipmentCategory, dbase_file: str):
#     amdesp_logger.debug(f'DBase file NEW = {dbase_file}')
#     shipments_dict = {}
#     try:
#         for record in DBF(dbase_file):
#             [amdesp_logger.debug(f'DBASE RECORD - {k} : {v}') for k, v in record.items()]
#             try:
#                 ship_dict = shipdict_from_dbase(record=record, import_mapping=import_mapping)
#                 shipment = DbayShipment.from_dbase_record(record=record, ship_dict=ship_dict, category=category)
#                 shipments_dict.update({shipment.shipment_name_printable: shipment})
#             except Exception as e:
#                 amdesp_logger.exception(f'{record.__repr__()} - {e}')
#                 continue
#
#     except UnicodeDecodeError as e:
#         logging.exception(f'DBASE import error with {dbase_file} \n {e}')
#     except DBFNotFound as e:
#         amdesp_logger.exception(f'.Dbf or Dbt are missing \n{e}')
#     except Exception as e:
#         amdesp_logger.exception(e)
#         raise e
#     return shipments_dict

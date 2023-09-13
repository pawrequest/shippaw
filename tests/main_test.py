from core.enums import ShipmentCategory
from tests.fixtures import records_ryzen

"""
records have correct fields (including arbitrary names like FIELD10, i.e. export correctly configured in cmc)


"""


def test_one(record_sale_ryzen):
    assert record_sale_ryzen is not None
    assert len(record_sale_ryzen) >= 9


# def test_main():
#     for outbound in [True, False]:
#         for category in ShipmentCategory:
#             record_name = f'record_{category.value.lower()}'
#             record = getattr(records_ryzen, record_name)
#             assert record is not None
#             assert len(record) == 15
    #         config = get_config(outbound=outbound, category=category)
    #         establish_client(dbay_creds=config.dbay_creds)
    #         records = records_from_dbase(dbase_file=args.file)
    #         shipments = shipments_from_records(category=category, import_map=config.import_map, outbound=outbound,
    #                                            records=records)
    #         if not shipments:
    #             logger.info('No shipments to process.')
    #             sys.exit()
    #
    #         if args.shipping_mode == ShipMode.SHIP:
    #             dispatch(config=config, shipments=shipments)
    #
    #         # elif args.shipping_mode == ShipMode.TRACK:
    #         #     shipper.track()
    #
    #         sys.exit(0)
    # initial_checks()
    # outbound = 'out' == args.direction.value.lower()
    # category = args.category
    #
    # config = get_config(outbound=outbound, category=category)
    # establish_client(dbay_creds=config.dbay_creds)
    # records = records_from_dbase(dbase_file=args.file)
    # shipments = shipments_from_records(category=category, import_map=config.import_map, outbound=outbound,
    #                                    records=records)
    # if not shipments:
    #     logger.info('No shipments to process.')
    #     sys.exit()
    #
    # if args.shipping_mode == ShipMode.SHIP:
    #     dispatch(config=config, shipments=shipments)
    #
    # # elif args.shipping_mode == ShipMode.TRACK:
    # #     shipper.track()
    #
    # sys.exit(0)

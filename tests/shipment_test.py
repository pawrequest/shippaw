import pytest

from core.config import ROOT_DIR
from core.enums import ShipmentCategory
from gui.keys_and_strings import BOOK_KEY, PRINT_EMAIL_KEY
from shipper.shipment import ShipmentBooked, records_from_dbase, shipment_from_record, ShipmentDict, \
    shipments_from_records_dict
from shipper.shipper import address_shipment, book_shipment, pre_request_shipment, prepare_shipment, queue_shipment, \
    read_window_cboxs, \
    request_shipment, prepare_batch_dict
from tests.config_test import dbay_client_sandbox, config_sandbox, config_dict_from_toml, category

fixtures_dir = ROOT_DIR / 'tests' / 'fixtures'

record_dict = {
    ShipmentCategory.HIRE: records_from_dbase(dbase_file=fixtures_dir / 'hire.dbf')[0],
    ShipmentCategory.SALE: records_from_dbase(dbase_file=fixtures_dir / 'sale.dbf')[0],
    ShipmentCategory.CUSTOMER: records_from_dbase(dbase_file=fixtures_dir / 'customer.dbf')[0],
    'bulk': records_from_dbase(dbase_file=fixtures_dir / 'bulk.dbf')
}


@pytest.fixture()
def shipment_input_fixture(category, config_sandbox):
    record = record_dict[category]
    import_map = config_sandbox.import_mappings[category.name.lower()]
    return shipment_from_record(category=category, record=record, outbound=True, import_map=import_map)


@pytest.fixture()
def shipment_addressed_fixture(shipment_input_fixture, config_sandbox, dbay_client_sandbox):
    return address_shipment(shipment=shipment_input_fixture, home_address=config_sandbox.home_address,
                            home_contact=config_sandbox.home_contact, client=dbay_client_sandbox)


@pytest.fixture()
def shipment_prepared_fixture(shipment_addressed_fixture, config_sandbox, dbay_client_sandbox):
    return prepare_shipment(shipment=shipment_addressed_fixture,
                            default_courier=config_sandbox.default_carrier.courier, client=dbay_client_sandbox)


@pytest.fixture()
def shipment_pre_request_fixture(shipment_prepared_fixture, config_sandbox, dbay_client_sandbox):
    return pre_request_shipment(shipment=shipment_prepared_fixture,
                                default_shipping_service_id=config_sandbox.default_carrier.service,
                                client=dbay_client_sandbox)


@pytest.fixture()
def shipment_requested_fixture(shipment_pre_request_fixture, dbay_client_sandbox):
    return request_shipment(shipment=shipment_pre_request_fixture, client=dbay_client_sandbox)


# def test_record_to_requested(category, shipment_requested_fixture):
#     shipment = shipment_requested_fixture
#     assert isinstance(shipment, ShipmentRequested)
#     assert shipment.category == category
#     assert isinstance(shipment.sender.sender_address, Address)

def test_sandbox_dispatch(dbay_client_sandbox, shipment_requested_fixture, config_sandbox):
    assert config_sandbox.sandbox is True
    values = {
        PRINT_EMAIL_KEY(shipment=shipment_requested_fixture): True,
        BOOK_KEY(shipment=shipment_requested_fixture): True
    }

    shipment_read = read_window_cboxs(shipment=shipment_requested_fixture, values=values)
    shipment_queued = queue_shipment(shipment=shipment_read, client=dbay_client_sandbox)
    shipment_booked = book_shipment(shipment=shipment_queued, client=dbay_client_sandbox)
    assert isinstance(shipment_booked, ShipmentBooked)

    # shipment.label_location = download_shipment_label(shipment=shipment, config=config_from_toml_sandbox, client=dbay_client_sandbox)
    # print_email_label(print_email=shipment.is_to_print_email, email_body=config_from_toml_sandbox.return_label_email_body,
    #                   shipment=shipment)
    # booked = ShipmentCompleted(**shipment.__dict__, **shipment.model_extra)
    ...


def test_prepare_dict(dbay_client_sandbox, config_sandbox, category):
    records = record_dict['bulk']
    import_map = config_sandbox.import_mappings.get(category.name.lower())
    shipment_dict = shipments_from_records_dict(category=category, import_map=import_map, outbound=True, records=records)
    prepared = prepare_batch_dict(client=dbay_client_sandbox, config=config_sandbox, shipments_dict=shipment_dict)
    assert isinstance(prepared, ShipmentDict)


# def fake_popup():
#     return "Da16 3hu"
#
#
# def test_bad_postcode(config_sandbox, monkeypatch):
#     # Use monkeypatch to override the popup function
#     monkeypatch.setattr(addresser, 'get_candidate_keys',
#                         lambda postcode: get_candidate_keys(postcode, popup_func=fake_popup))
#
#     record = record_hire_bad_postcode
#     shipment = shipment_from_record(
#         category=ShipmentCategory.HIRE,
#         record=record,
#         outbound=True,
#         import_map=get_import_map(
#             category=ShipmentCategory.HIRE,
#             mappings=config_sandbox.import_mappings
#         )
#     )
#     addressed = address_shipment(
#         shipment=shipment,
#         home_address=config_sandbox.home_address,
#         home_contact=config_sandbox.home_contact
#     )
#     assert isinstance(addressed, ShipmentAddressed)

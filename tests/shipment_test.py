from typing import Dict, List

import pytest

from src.desp_am.core.config import ROOT_DIR
from src.desp_am.gui.keys_and_strings import BOOK_KEY, PRINT_EMAIL_KEY
from src.desp_am.shipper.shipment import ShipmentBooked, records_from_dbase, shipment_from_record, ShipmentDict, \
    shipments_from_records
from src.desp_am.shipper.ship import address_shipment, book_shipment, pre_request_shipment, prepare_batch, prepare_shipment, \
    queue_shipment, read_window_cboxs, request_shipment
from tests.fixtures.records import RECORDS_DICT

fixtures_dir = ROOT_DIR / 'tests' / 'fixtures'

@pytest.fixture()
def records_fixture(category) -> List[Dict]:
    return RECORDS_DICT.get(category.name.lower())



def test_dbf_import(category, records_fixture):
    dbf_file = fixtures_dir / f'{category.name.lower()}.dbf'
    records = records_from_dbase(dbase_file=dbf_file)
    records_on_file = records_fixture
    assert records == records_on_file

@pytest.fixture()
def shipment_input_fixture(category, config_sandbox):
    record = RECORDS_DICT.get(category.name.lower())[0]
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

#
# def test_prepare_dict(dbay_client_sandbox, config_sandbox, category):
#     records = record_dict['bulk']
#     import_map = config_sandbox.import_mappings.get(category.name.lower())
#     shipment_dict = shipments_from_records_dict(category=category, import_map=import_map, outbound=True, records=records)
#     prepared = prepare_batch_dict(client=dbay_client_sandbox, config=config_sandbox, shipments_dict=shipment_dict)
#     assert isinstance(prepared, ShipmentDict)

def test_prepare_dict_prod(dbay_client_production, config_production, category, records_fixture):
    import_map = config_production.import_mappings.get(category.name.lower())
    shipments = shipments_from_records(category=category, import_map=import_map, outbound=True, records=records_fixture)
    # prepared = prepare_batch_dict(client=dbay_client_production, config=config_production, shipments=shipments)
    prepared = prepare_batch(client=dbay_client_production, config=config_production, shipments=shipments)
    dicty = ShipmentDict({shipment.shipment_name: shipment for shipment in prepared})
    assert isinstance(dicty, ShipmentDict)


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

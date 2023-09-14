from collections import OrderedDict
from pathlib import Path

import pytest
from despatchbay.despatchbay_entities import Address

from core.config import Config, get_import_map
from core.enums import ShipmentCategory
from shipper import addresser
from shipper.addresser import get_candidate_keys
from shipper.shipment import ShipmentAddressed, ShipmentInput, ShipmentPreRequest, ShipmentPrepared, \
    ShipmentRequested, records_from_dbase, shipment_from_record
from shipper.shipper import address_shipment, establish_client, pre_request_shipment, prepare_shipment, request_shipment
from tests.fixtures.fixtures import record_hire_bad_postcode, record_sale

hire_dbf = Path(r'E:\Dev\AmDesp\tests\fixtures\hire.dbf')
sale_dbf = Path(r'E:\Dev\AmDesp\tests\fixtures\sale.dbf')
customer_dbf = Path(r'E:\Dev\AmDesp\tests\fixtures\customer.dbf')


@pytest.fixture()
def hire_record():
    return records_from_dbase(dbase_file=hire_dbf)[0]


@pytest.fixture()
def sale_record():
    return records_from_dbase(dbase_file=sale_dbf)[0]


@pytest.fixture()
def customer_record():
    return records_from_dbase(dbase_file=customer_dbf)[0]



@pytest.fixture()
def shipment_input_fixture(category, config_from_toml, request):
    record = request.getfixturevalue(f'{category.name.lower()}_record')
    import_map = get_import_map(category=category, mappings=config_from_toml.import_mappings)
    return shipment_from_record(category=category, record=record, outbound=True, import_map=import_map)

@pytest.fixture()
def shipment_addressed_fixture(shipment_input_fixture, config_from_toml):

    return address_shipment(shipment=shipment_input_fixture, home_address=config_from_toml.home_address, home_contact=config_from_toml.home_contact)

@pytest.fixture()
def shipment_prepared_fixture(shipment_addressed_fixture, config_from_toml):
    return prepare_shipment(shipment=shipment_addressed_fixture, default_courier=config_from_toml.default_carrier.courier)

@pytest.fixture()
def shipment_pre_request_fixture(shipment_prepared_fixture, config_from_toml):
    return pre_request_shipment(shipment=shipment_prepared_fixture, default_shipping_service_id=config_from_toml.default_carrier.service)

@pytest.fixture()
def shipment_requested_fixture(shipment_pre_request_fixture):
    return request_shipment(shipment=shipment_pre_request_fixture)

test_cases = [(category, fixture_name, expected_type)
              for category in ShipmentCategory
              for fixture_name, expected_type in [
                  # ('shipment_input_fixture', ShipmentInput),
                  # ('shipment_addressed_fixture', ShipmentAddressed),
                  # ('shipment_prepared_fixture', ShipmentPrepared),
                  # ('shipment_pre_request_fixture', ShipmentPreRequest),
                  ('shipment_requested_fixture', ShipmentRequested),
              ]]

@pytest.mark.parametrize("category,fixture_name,expected_type", test_cases)
def test_record_to_requested(category, fixture_name, expected_type, request):
    fixture_instance = request.getfixturevalue(fixture_name)
    assert isinstance(fixture_instance, expected_type)



#
# def test_imported(config_from_toml):
#     record = record_hire_bad_postcode
#     shipment = shipment_from_record(category=ShipmentCategory.HIRE, record=record, outbound=True, import_map=get_import_map(category=ShipmentCategory.HIRE, mappings=config_from_toml.import_mappings))
#     addressed = address_shipment(shipment=shipment, home_address=config_from_toml.home_address, home_contact=config_from_toml.home_contact)
#     assert isinstance(addressed, ShipmentAddressed)
#

# def fake_popup(message):
#     return "Da16 3hu"
#

# def test_bad_postcode(config_from_toml, monkeypatch):
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
#             mappings=config_from_toml.import_mappings
#         )
#     )
#     addressed = address_shipment(
#         shipment=shipment,
#         home_address=config_from_toml.home_address,
#         home_contact=config_from_toml.home_contact
#     )
#     assert isinstance(addressed, ShipmentAddressed)

#
#
import pytest
from despatchbay.despatchbay_entities import Address

from core.config import ROOT_DIR, get_import_map
from core.enums import ShipmentCategory
from shipper.shipment import ShipmentRequested, records_from_dbase, shipment_from_record
from shipper.shipper import address_shipment, pre_request_shipment, prepare_shipment, request_shipment

fixtures_dir = ROOT_DIR / 'tests' / 'fixtures'


record_dict = {
    ShipmentCategory.HIRE: records_from_dbase(dbase_file=fixtures_dir / 'hire.dbf')[0],
    ShipmentCategory.SALE: records_from_dbase(dbase_file=fixtures_dir / 'sale.dbf')[0],
    ShipmentCategory.CUSTOMER: records_from_dbase(dbase_file=fixtures_dir / 'customer.dbf')[0],
}


@pytest.fixture()
def shipment_input_fixture(category, config_from_toml, request):
    record = record_dict[category]
    import_map = get_import_map(category=category, mappings=config_from_toml.import_mappings)
    return shipment_from_record(category=category, record=record, outbound=True, import_map=import_map)


@pytest.fixture()
def shipment_addressed_fixture(shipment_input_fixture, config_from_toml):
    return address_shipment(shipment=shipment_input_fixture, home_address=config_from_toml.home_address,
                            home_contact=config_from_toml.home_contact)


@pytest.fixture()
def shipment_prepared_fixture(shipment_addressed_fixture, config_from_toml):
    return prepare_shipment(shipment=shipment_addressed_fixture,
                            default_courier=config_from_toml.default_carrier.courier)


@pytest.fixture()
def shipment_pre_request_fixture(shipment_prepared_fixture, config_from_toml):
    return pre_request_shipment(shipment=shipment_prepared_fixture,
                                default_shipping_service_id=config_from_toml.default_carrier.service)


@pytest.fixture()
def shipment_requested_fixture(shipment_pre_request_fixture):
    return request_shipment(shipment=shipment_pre_request_fixture)


@pytest.mark.parametrize("category", ShipmentCategory)
def test_record_to_requested(category, shipment_requested_fixture):
    shipment = shipment_requested_fixture
    assert isinstance(shipment, ShipmentRequested)
    assert shipment.category == category
    assert isinstance(shipment.sender.sender_address, Address)

# def fake_popup():
#     return "Da16 3hu"
#
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

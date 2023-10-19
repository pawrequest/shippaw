from pathlib import Path

from dotenv import load_dotenv


# @pytest.fixture(params=list(ShipmentCategory))
# def category(request):
#     return request.param
#


# def test_client_sandbox(dbay_client_sandbox):
#     assert isinstance(dbay_client_sandbox, DespatchBaySDK)
#     balance = dbay_client_sandbox.get_account_balance().balance
#     assert balance == 1000.0
#

#
# def test_client_production(dbay_client_production):
#     assert isinstance(dbay_client_production, DespatchBaySDK)
#     balance = dbay_client_production.get_account_balance().balance
#     assert isinstance(balance, float)

# import ctypes
# import subprocess
#
# DESPATCH_API_KEY = '2DE45B0B5EDEB688841F'
# DESPATCH_API_KEY_SANDBOX = 'AAD2F91ED25CAE38B4D1'
# DESPATCH_API_USER = '25RM-EB372013'
# DESPATCH_API_USER_SANDBOX = 'D25RM-E1305A31'
# DESPATCH_SENDER_ID = 5536
#
# # set_despatch_api_env(api_user=DESPATCH_API_USER_SANDBOX, api_key=DESPATCH_API_KEY_SANDBOX, sandbox=True)
#
# # def is_admin():
# #     try:
# #         return ctypes.windll.shell32.IsUserAnAdmin()
# #     except:
# #         return False
# # for i in range(1,3):
# #     if not is_admin():
# #
# #         # Re-run the program with elevated privileges
# #         print("not admin")
# #
# #         # Exit the current process
# #         # sys.exit()
# #
# #     else:
# #         ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
# #
# #         # Set the environment variable permanently
# #         print("IS ADMIN")
# #
# #
#
# variable {key_name} set to {key_value}")
from enum import Enum


class ShipMode(Enum):
    SHIP_OUT = 'ship_out'
    SHIP_IN = 'ship_in'
    TRACK_OUT = 'track_out'
    TRACK_IN = 'track_in'


mode = ShipMode('ship_in')
...
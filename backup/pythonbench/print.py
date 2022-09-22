# # import os
# #
# # os.startfile("C:\AmDesp\shipmentJson\Parcelforce Labels\label_string.pdf", "print")
#
# import tempfile
# import win32api
# import win32print
#
# filename = "C:\AmDesp\shipmentJson\Parcelforce Labels\label_string.pdf"
# open(filename, "w").write("This is a test")
# win32api.ShellExecute(
#     0,
#     "printto",
#     filename,
#     '"%s"' % win32print.GetDefaultPrinter(),
#     ".",
#     0
# )

# import syst
# System.Diagnostics.Process.Start("cd","Z:")
import os
if os.path.exists("I:\\"):
    print ("CONNECTED")
from pathlib import Path

from office_tools.email_handler import Email, EmailHandler, GmailSender


parcel_contents = 'Radios'
return_label_email_body = """Thanks for Hiring from Amherst.\n\n\
                            Your prepaid label is attached for returning the radios.\n\
                            Please print the label off and stick securely to the box.\n\
                            Also make sure any old Parcelforce labels are removed - or the box could get delivered back to you!\n\n\
                            Collection has been booked from:\n\
                            __--__ADDRESSREPLACE__--__\n\
                            on: __--__DATEREPLACE__--__\n\n\
                            We are unable to provide accurate collection times - please contact us urgently if there will not be somebody at the collection address on the specified date.\n\
                            If the collection is missed for any reason, you can also just take the box, with the label securely attached, and drop it at any Post Office, the carriage fee is already paid.\n\
                            Thanks\n\
                            Regards,\nGiles Toman\
                          """

def returns_email(to_address:str, label_path:Path, body = return_label_email_body):
    return Email(
        to_address=to_address,
        subject='Amherst Radios Returns Label',
        body=body,
        attachment_path=label_path,
    )


returns_collection_dropoff ="""Thanks for Hiring from Amherst.\n\
                            Your prepaid label is attached for returning the radios.\n\
                            Please print the label off, stick securely to the box, and drop it at any Post Office, the carriage fee is already paid.\n\
                            Please make very sure that any old Parcelforce labels are removed or overstuck - otherwise the box could be delivered back to you!\n\
                            Thanks\n\
                            Regards,\nGiles Toman\
                          """

def returns_dropoff_email(to_address:str, label_path:Path, body = returns_collection_dropoff):
    return Email(
        to_address=to_address,
        subject='Amherst Radios Returns Label',
        body=body,
        attachment_path=label_path,
    )
from pathlib import Path

from office_tools.email_handler import Email

parcel_contents = 'Radios'

return_greeting_txt = """Thanks for Hiring from Amherst.\n\n\
                        Your prepaid label is attached for returning the radios.\n\
                        Please print the label off and stick securely to the box.\n\
                        Also make sure any old Parcelforce labels are removed - or the box could get delivered back to you!\n"""


def collection_booked_txt(col_address, col_date):
    return (f""" \nCollection has been booked from: \t{col_address} \ton: {col_date}\n
            \nWe are unable to provide accurate collection times - please contact us urgently if there will not be somebody at the collection address on the specified date.\n
            If the collection is missed for any reason, you can also just take the box, with the label securely attached, and drop it at any Post Office, the carriage fee is already paid.\n
            """)


def sms_alert_number_txt(phone_number):
    return f"\nThe contact number {phone_number} was given to the courier - you should receive sms delivery updates on the day of delivery\n"


def email_contact_txt(email_address):
    return f"\nThe email address {email_address} was given to the courier - you should receive email updates.\n"


closing_txt = "Thanks\nRegards,\nGiles Toman"


def returns_email_collection(email_address: str, col_address, col_date, label_path: Path, phone_number: str):
    body = (return_greeting_txt
            + collection_booked_txt(col_address, col_date)
            + sms_alert_number_txt(phone_number)
            + email_contact_txt(email_address)
            + closing_txt)
    return Email(
        to_address=email_address,
        subject='Amherst Radios Returns Label',
        body=body,
        attachment_path=label_path,
    )


def returns_dropoff_email(to_address: str, label_path: Path):
    body = return_greeting_txt + closing_txt
    return Email(
        to_address=to_address,
        subject='Amherst Radios Returns Label',
        body=body,
        attachment_path=label_path,
    )

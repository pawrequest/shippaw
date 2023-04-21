from datetime import datetime

from amdesp.shipment import parse_amherst_address_string


def ship_dict_from_xml(config: Config, xml_file: str) -> dict:
    """parse amherst shipment xml"""
    shipment_fields = config.fields.shipment
    ship_dict = dict()
    tree = ET.parse(xml_file)
    root = tree.getroot()
    fields = root[0][2]

    category = root[0][0].text
    for field in fields:
        k = field[0].text
        k = to_snake_case(k)
        v = field[1].text
        if v:
            k = unsanitise(k)
            v = unsanitise(v)

            if "number" in k.lower():
                # if not v.isnumeric():
                #     v = re.sub(r"\D", "", v)
                if 'serial' in k.lower():
                    v = [int(x) for x in v.split() if x.isdigit()]
                else:
                    if isinstance(v, str):
                        v = re.sub(r"\D", "", v)

                        # v = int(v.replace(',', ''))
            if k == 'name':
                k = 'shipment_name'
                v = "".join(ch if ch.isalnum() else '_' for ch in v)
            if k[:6] == "deliv ":
                k = k.replace('deliv', 'delivery')
            k = k.replace('delivery_', '')
            if k == 'tel':
                k = 'telephone'
            if k == 'address':
                k = 'address_as_str'
            ship_dict.update({k: v})

    # get customer name
    if category in ["Hire", "Sale"]:
        ship_dict['customer'] = root[0][3].text
    elif category == "Customer":
        ship_dict['customer'] = fields[0][1].text
        ship_dict[
            'shipment_name'] = f'{ship_dict["shipment_name"]} - {datetime.now().isoformat(" ", timespec="seconds")}'
    try:
        ship_dict['date'] = datetime.strptime(ship_dict['send_out_date'], config.datetime_masks['DT_HIRE'])
    except:
        ship_dict['date'] = datetime.today()
    ship_dict['category'] = category
    ship_dict['search_term'] = parse_amherst_address_string(ship_dict['address_as_str'])
    ship_dict['boxes'] = ship_dict.get('boxes', 1)

    missing = []
    for attr_name in shipment_fields:
        if attr_name not in ship_dict.keys():
            if attr_name not in ['cost', 'inbound_id', 'outbound_id']:
                missing.append(attr_name)
    if missing:
        sg.popup(f"*** Warning - {missing} not found in ship_dict - Warning ***")
    return ship_dict



    @classmethod
    def get_shipments(cls, config: Config, in_file: str) -> list:
        """ parses input filetype and calls appropriate function to construct and return a list of shipment objects"""
        shipments: [Shipment] = []
        file_ext = in_file.split('.')[-1].lower()
        if file_ext == 'xml':
            ship_dict = ship_dict_from_xml(config=config, xml_file=in_file)
            try:
                shipments.append(Shipment(ship_dict=ship_dict))
            except KeyError as e:
                print(f"Shipdict Key missing: {e}")
        elif file_ext == 'dbf':
            shipments = cls.shipments_from_dbase(dbase_file=in_file, config=config)
            # shipments.append(cls.shipments_from_dbase(dbase_file=in_file))
        else:
            sg.popup(f"Invalid input file: {in_file}"
                     f"file extension: {file_ext}"
                     f"Config: {config.__repr__()}"
                     f"Shipments: f'{(shipment.shipment_name for shipment in shipments)}'")
        return shipments



def blank_window(config: Config):
    sg.set_options(**default_params)

    if config.sandbox:
        sg.theme('Tan')
    else:
        sg.theme('Dark Blue')

    layout = []
    headers = [
        sg.Push(),
        sg.T('Customer', **bulk_params),
        sg.Text('Collection Date', **bulk_params),
        sg.T('Sender', **bulk_params),
        sg.T('Recipient', **bulk_params),
        sg.T('Service', **bulk_params)
    ]
    layout.append(headers)

    window = sg.Window('Bulk Shipper', layout=layout, finalize=True)
    return window




def shipment_layout(shipment: Shipment):
    layout = []
    key_string = shipment.shipment_name.upper()

    layout.append(
        [sg.T(shipment.customer, **bulk_params),

         sg.Text(enable_events=True, k=f'-{key_string}_DATE-', **bulk_params),

         sg.T(enable_events=True, k=f'-{key_string}_SENDER-', **bulk_params),

         sg.T(enable_events=True, k=f'-{key_string}_RECIPIENT-', **bulk_params),

         sg.T(enable_events=True, k=f'-{key_string}_SERVICE-', **bulk_params)]
    )
    return layout


def non_address_prep(shipment: Shipment, client: DespatchBaySDK, config: Config):
    """ despatchbay requires us to supply a service to get a shipment_request and a shipment_request to get an available_service. funtimes.
    so we get a service regardless of avilability, make a request, then get available services and check against pre-selected one"""
    try:
        shipment.service = get_arbitrary_service(client=client, config=config)
    except Exception as e:
        ...
    try:
        shipment.collection_date = get_collection_date(client=client, config=config, shipment=shipment)
    except Exception as e:
        ...
    try:
        shipment.parcels = get_parcels(num_parcels=shipment.boxes, client=client, config=config)
    except Exception as e:
        ...
    try:
        shipment.shipment_request = get_shipment_request(client=client, shipment=shipment)
    except Exception as e:
        ...
    try:
        shipment.service = get_actual_service(client=client, config=config, shipment=shipment)
    except Exception as e:
        ...



#
# def date_chooser() -> sg.Combo:
#     return sg.Combo(values=[], pad=(10, 5), size=30, readonly=True, k='-DATE-')
#

# def go_button():
#     return sg.Button(f'Go!', k="-GO-", size=(12, 5), expand_y=True, pad=20, )

# # backup
# def get_dates_menu(client: DespatchBaySDK, config: Config, shipment: Shipment) -> dict:
#     """ get available collection dates as dbay collection date objects for shipment.sender.address
#         construct a menu_def for a combo-box
#         if desired send-date matches an available date then select it as default, otherwise select soonest colelction
#         return a dict with values and default_value"""
#
#     # potential dates as dbay objs not proper datetime objs
#     available_dates = client.get_available_collection_dates(shipment.sender.sender_address, config.courier_id)
#     datetime_mask = config.datetime_masks['DT_DISPLAY']
#
#     chosen_collection_date_dbay = next((date for date in available_dates if parse(date.date) == shipment.date),
#                                        available_dates[0])
#
#     chosen_date_hr = f'{parse(chosen_collection_date_dbay.date):{datetime_mask}}'
#     shipment.date_menu_map.update({f'{parse(date.date):{datetime_mask}}': date for date in available_dates})
#     men_def = [f'{parse(date.date):{datetime_mask}}' for date in available_dates]
#
#     shipment.date = chosen_collection_date_dbay
#     return {'default_value': chosen_date_hr, 'values': men_def}


#
# def get_service_menu(client: DespatchBaySDK, config: Config, shipment: Shipment) -> dict:
#     """ gets available shipping services for shipment sender and recipient
#     builds menu_def of potential services and if any matches service_id specified in config.toml then select it by default
#      return a dict of menu_def and default_value"""
#     services = client.get_services()
#     # todo get AVAILABLE services needs a request
#     # services = client.get_available_services()
#     shipment.service_menu_map.update({service.name: service for service in services})
#     chosen_service = next((service for service in services if service.service_id == config.service_id), services[0])
#     shipment.service = chosen_service
#     return {'values': [service.name for service in services], 'default_value': chosen_service.name}


# def get_queue_or_book_menu(shipment: Shipment) -> dict:
#     """ construct menu options for queue / book / print etc
#         return values and default value"""
#     q_o_b_dict = {}
#     print_or_email = "email" if shipment.is_return else "print"
#     values = [
#         f'Book and {print_or_email}',
#         'Book only',
#         'Queue only'
#     ]
#     default_value = f'Book and {print_or_email}'
#     q_o_b_dict.update(values=values, default_value=default_value)
#     return q_o_b_dict
#


# def queue_shipment(client: DespatchBaySDK, shipment: Shipment, shipment_request: ShipmentRequest) -> str:
#     """ queues a shipment specified by the provided dbay shipment_request object
#         returns the shipment id for tracking purposes"""
#     if shipment.is_return:
#         shipment.inbound_id = client.add_shipment(shipment_request)
#         shipment_id = shipment.inbound_id
#     else:
#         shipment.outbound_id = client.add_shipment(shipment_request)
#         shipment_id = shipment.outbound_id
#     return shipment_id


# def populate_non_address_fields(client: DespatchBaySDK, config: Config, shipment: Shipment, window: Window):
#     """ fills gui from shipment details. if customer address is invalid launch a popup to fix"""
#
#     services_dict = get_service_menu(client=client, config=config, shipment=shipment)
#     dates_dict = get_dates_menu(client=client, config=config, shipment=shipment)
#     q_o_b_dict = get_queue_or_book_menu(shipment=shipment)
#
#     window['-SHIPMENT_NAME-'].update(shipment.shipment_name)
#     # todo color date based on match.... how to update without bg-color in update method? = learn TKinter
#     window['-DATE-'].update(values=dates_dict['values'], value=dates_dict['default_value'])
#     window['-SERVICE-'].update(values=services_dict['values'], value=services_dict['default_value'])
#     if shipment.inbound_id:
#         window['-INBOUND_ID-'].update(shipment.inbound_id)
#     if shipment.outbound_id:
#         window['-OUTBOUND_ID-'].update(shipment.outbound_id)
#     window['-QUEUE_OR_BOOK-'].update(values=q_o_b_dict['values'], value=q_o_b_dict['default_value'])
#     window['-BOXES-'].update(value=shipment.boxes or 1)
#


# def book_collection(client: DespatchBaySDK, config: Config, shipment: Shipment,
#                     shipment_id: str) -> ShipmentReturn | None:
#     """ books collection of shipment specified by provided shipment id"""
#     try:
#         shipment_return = client.book_shipments(shipment_id)[0]
#     except:
#         sg.popup_error("Unable to Book")
#         # return None
#     else:
#         shipment.collection_booked = True
#         sg.popup_scrolled(f'Shipment booked: \n{shipment_return}', size=(20, 20))
#         shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
#         return shipment_return


# backup
# def shipping_loop(self, client: DespatchBaySDK, config: Config, sandbox: bool, shipment: Shipment):
#     if sandbox:
#         sg.theme('Tan')
#     else:
#         sg.theme('Dark Blue')
#
#     window = main_window()
#     populate_home_address(client=client, config=config, shipment=shipment, window=window)
#     populate_remote_address(client=client, config=config, shipment=shipment, window=window)
#     populate_non_address_fields(client=client, config=config, shipment=shipment, window=window)
#
#     while True:
#         window['-SENDER_POSTAL_CODE-'].bind("<Return>", '')
#         window['-RECIPIENT_POSTAL_CODE-'].bind("<Return>", '')
#         if not window:
#             # prevent crash on exit
#             break
#         event, values = window.read()
#
#         if event in (sg.WINDOW_CLOSED, 'Exit'):
#             break
#
#         # click company name to copy customer in
#         if 'company_name' in event:
#             window[event.upper()].update(shipment.customer)
#
#         # click 'postcode' or enter 'Return' in postcode box to list and choose from addresses at postcode
#         if 'postal_code' in event.lower():
#             self.postcode_click(client=client, event=event, values=values, window=window, shipment=shipment)
#
#         # click existing shipment id to track shipping
#         if event == '-INBOUND_ID-':
#             tracking_viewer_window(shipment_id=shipment.inbound_id, client=client)
#         if event == '-OUTBOUND_ID-':
#             tracking_viewer_window(shipment_id=shipment.outbound_id, client=client)
#
#         if event == '-GO-':
#             decision = values['-QUEUE_OR_BOOK-'].lower()
#             if 'queue' or 'book' in decision:
#                 shipment_request = make_request(client=client, shipment=shipment, values=values, config=config)
#                 answer = sg.popup_scrolled(f"{decision}?\n{shipment_request}", size=(30, 30))
#
#                 # todo remove safety checks when ship
#                 if answer == 'OK':
#                     if not sandbox:
#                         if not sg.popup("NOT SANDBOX DO YOU WANT TO PAY?!!!") == 'OK':
#                             continue
#
#                     # queue shipment
#                     shipment_id = queue_shipment(shipment_request=shipment_request, shipment=shipment,
#                                                  client=client)
#                     if 'book' in decision:
#                         shipment_return = book_collection(client=client, config=config, shipment=shipment,
#                                                           shipment_id=shipment_id)
#                         download_label(client=client, config=config, shipment_return=shipment_return,
#                                        shipment=shipment)
#
#                     if 'print' in decision:
#                         print_label(shipment=shipment)
#
#                     if 'email' in decision:
#                         ...  # todo implement this, which email client?
#
#                     # log shipment id to commence database
#                     update_commence(config=config, shipment=shipment)
#
#                     # log to json
#                     log_shipment(config=config, shipment=shipment)
#                     break
#
#     window.close()

# def postcode_click(self, client: DespatchBaySDK, event: str, values: dict, shipment: Shipment, window: Window):
#     new_address = get_new_address(client=client, postcode=values[event.upper()], shipment=shipment)
#     if new_address:
#         sender_or_recip = shipment.sender if 'sender' in event.lower() else 'recipient'
#         update_gui_from_address(address=new_address, window=window, sender_or_recip=sender_or_recip)
#


#
# def process_outbound(self, shipments: [Shipment], mode: str, client, config):
#     if mode.startswith('ship'):
#         self.shipping_loop(client=client, config=config, shipments=shipments, mode=mode)
#     # elif mode.startswith('track'):
#     #     self.tracking_loop(mode=mode, client=client, shipment=shipment)


#
# def shipping_loop(self, mode: str, client: DespatchBaySDK, config: Config, shipments: [Shipment]):
#     if config.sandbox:
#         sg.theme('Tan')
#     else:
#         sg.theme('Dark Blue')
#
#     home_sender = get_home_sender(client=client, config=config)
#     home_recip = get_home_recipient(client=client, config=config)
#     services = client.get_services()
#     default_service = next((service for service in services if service.service_id == config.service_id),
#                                             services[0])
#
#     shipment_ids=[]
#     for shipment in shipments:
#
#
#         shipment.is_return = 'in' in mode
#         remote_add = get_remote_address(client=client, shipment=shipment, config=config)
#         if shipment.is_return:
#             shipment.sender = remote_sender(client=client, shipment=shipment, remote_address=remote_add)
#             shipment.recipient = home_recip
#             id_to_log = 'inbound_id'
#         else:
#             shipment.sender = home_sender
#             shipment.recipient = remote_recip(client=client, shipment=shipment, remote_address=remote_add)
#             id_to_log = 'outbound_id'
#         shipment.service = default_service
#         shipment.collection_date = get_collection_date(client=client, config=config, shipment=shipment)
#         shipment.parcels = get_parcels(int(shipment.boxes), client=client, config=config)
#         shipment.shipment_request = get_shipment_request(client=client, shipment=shipment)
#
#         if change_service:
#             # cahnge service
#             ...
#         if change_date:
#             ...
#         if queue:
#             added_id = client.add_shipment(shipment.shipment_request)
#             setattr(shipment, id_to_log, added_id)
#             if book:
#                 shipment_ids.append(added_id)
#
#
#
#
#     window = bulk_shipper_window(shipments=shipments)
#     e, v = window.read()
#     window.close()


#
# def main_window() -> Window:
#     sg.set_options(**default_params)
#     # elements
#     shipment_name = shipment_name_element()
#     sender = sender_recipient_frame('sender')
#     recipient = sender_recipient_frame('recipient')
#     # todo get addresses before dates
#     date_match = date_chooser()
#     parcels = parcels_spin()
#     service = service_combo()
#     queue = queue_or_book_combo()
#     ids = shipment_ids_frame()
#     book_button = go_button()
#
#     # frames
#     button_layout = [
#         [date_match],
#         [parcels],
#         [service],
#         [queue],
#     ]
#     button_col = sg.Column(layout=button_layout, element_justification='center', pad=20, expand_x=True)
#     button_frame = sg.Frame('', layout=[[button_col, book_button]], pad=20, element_justification='center',
#                             border_width=8,
#                             relief=sg.RELIEF_GROOVE)
#     layout = [[shipment_name],
#               [sender, recipient],
#               [ids, sg.P(), button_frame]
#               ]
#     window = sg.Window("Paul Sees Solutions - AmDesp Shipping Client", layout, finalize=True)
#     return window
#

#
# def bulk_date_gui(shipment: Shipment):
#     collection_date = parse(shipment.collection_date.date).date()
#     bg_col = 'green' if shipment.send_out_date == collection_date else 'red'


#     fuzzy_match = get_bestmatch(client=client, shipment=shipment, postcode=shipment.postcode)
#     chosen_bestmatch = popup_confirm_fuzzy(fuzzy_match)
#     if chosen_bestmatch:
#         return chosen_bestmatch.address
#     else:
#         return address_from_user_loop(bestmatch=fuzzy_match, client=client, config=config,
#                                          shipment=shipment)
# #
#     while not address:
#         if sg.popup_yes_no("No address - choose from postcode?") == "Yes":
#             address = get_new_address(client=client, postcode=shipment.postcode, shipment=shipment)
#         else:
#             sg.popup_error("Well then I guess I'll crash now.\nGoodbye")
#             break
#     return address
# #
# def get_remote_address(client: DespatchBaySDK, config: Config, shipment: Shipment):
#     """
#     Return a dbay recipient/sender object representing the customer address defined in imported xml or dbase file.
#     search by customer name, then shipment search_term
#     call explicit_matches to compare strings,
#     call get_bestmatch for fuzzy results,
#     if best score exceed threshold ask user to confirm
#     If still no valid address, call get_new_address.
#     """
#     address = None
#     fuzzy_match_threshold = 60
#
#     try:
#         address = client.find_address(shipment.postcode, shipment.customer)
#     except ApiException:
#         try:
#             address = client.find_address(shipment.postcode, shipment.search_term)
#         except ApiException as e:
#             try:
#                 fuzzy_match = get_bestmatch(client=client, shipment=shipment, postcode=shipment.postcode)
#             except Exception as e:
#                 ...
#             else:
#                 chosen_bestmatch = popup_confirm_fuzzy(fuzzy_match)
#                 if chosen_bestmatch:
#                     return chosen_bestmatch.address
#                 else:
#                     address = address_from_user_loop(bestmatch=fuzzy_match, client=client, config=config,
#                                                      shipment=shipment)
#
#     # # todo unswitch
#     # temp_fuzzy_match = get_bestmatch(client=client, shipment=shipment, postcode=shipment.postcode)
#     # if temp_fuzzy_match := popup_confirm_fuzzy(temp_fuzzy_match):
#     #     ...
#     # else:
#     #     ...
#
#     while not address:
#         if sg.popup_yes_no("No address - choose from postcode?") == "Yes":
#             address = get_new_address(client=client, postcode=shipment.postcode, shipment=shipment)
#         else:
#             sg.popup_error("Well then I guess I'll crash now.\nGoodbye")
#             break
#     return address


# def get_bestmatch(client: DespatchBaySDK, shipment: Shipment, postcode=None) -> BestMatch:
#     """
#     takes a shipment and optional postcode, searches dbay api
#     returns a BestMatch namedtuple with address, best-matched category, and best-match score
#     stores candidate list in shipment object
#     calls
#     """
#     shipment.address_as_str = shipment.address_as_str.split('\n')[0].replace('Units', 'Unit')
#     candidate_keys = get_candidate_keys(client=client, shipment=shipment)
#     fuzzyscores = []
#
#     for candidate_key in candidate_keys:
#         candidate_address = client.get_address_by_key(candidate_key.key)
#         if best_match := get_explicit_match(candidate_address=candidate_address, shipment=shipment):
#             break
#         else:
#             fuzzyscores.append(get_fuzzy_scores(candidate_address=candidate_address, shipment=shipment))
#             time.sleep(.2)
#     else:
#         # finished loop, no explicit matches so get highest scoring one from the list of fuzzyscores
#         best_match = bestmatch_from_fuzzyscores(fuzzyscores=fuzzyscores)
#     return best_match


#

# def bulk_services(client: DespatchBaySDK, config: Config, shipments: [Shipment]):
#     for shipment in shipments:
#         services = client.get_services()
#         # todo get AVAILABLE services needs a request
#         # services = client.get_available_services()
#         shipment.service_menu_map.update({service.name: service for service in services})
#         shipment.service = next((service for service in services if service.service_id == config.service_id),
#                                 services[0])


# def get_menus(client:DespatchBaySDK, config:Config, shipment:Shipment):
#
#     return {
#     'services_dict': get_service_menu(client=client, config=config, shipment=shipment),
#     'dates_dict': get_dates_menu(client=client, config=config, shipment=shipment),
#     'q_o_b_dict': get_queue_or_book_menu(shipment=shipment)
#     'q_o_b_dict': get_queue_or_book_menu(shipment=shipment)
#     }


#
# window['-SHIPMENT_NAME-'].update(shipment.shipment_name)
# # todo color date based on match.... how to update without bg-color in update method? = learn TKinter
# window['-DATE-'].update(values=dates_dict['values'], value=dates_dict['default_value'])
# window['-SERVICE-'].update(values=services_dict['values'], value=services_dict['default_value'])
# if shipment.inbound_id:
#     window['-INBOUND_ID-'].update(shipment.inbound_id)
# if shipment.outbound_id:
#     window['-OUTBOUND_ID-'].update(shipment.outbound_id)
# window['-QUEUE_OR_BOOK-'].update(values=q_o_b_dict['values'], value=q_o_b_dict['default_value'])
# window['-BOXES-'].update(value=shipment.boxes or 1)


#
# def populate_home_address(client: DespatchBaySDK, config: Config, shipment: Shipment,
#                           window: Window):
#     """ updates shipment and gui window with homebase contact and address details in sender or recipient position as appropriate"""
#     if shipment.is_return:
#         shipment.recipient = get_home_recipient(client=client, config=config)
#         update_gui_from_contact(config=config, sender_or_recip=shipment.recipient, window=window)
#         update_gui_from_address(address=shipment.recipient.recipient_address, sender_or_recip=shipment.recipient,
#                                 window=window)
#     else:
#         shipment.sender = get_home_sender(client=client, config=config)
#         update_gui_from_contact(config=config, sender_or_recip=shipment.sender, window=window)
#         update_gui_from_address(address=shipment.sender.sender_address, sender_or_recip=shipment.sender, window=window)

#
# def populate_remote_address(client: DespatchBaySDK, config: Config, shipment: Shipment, window: Window):
#     """ updates shipment and gui window with customer contact and address details in sender or recipient position as appropriate"""
#     remote_address = get_remote_address(client=client, config=config, shipment=shipment)
#
#     if shipment.is_return:
#         shipment.sender = client.sender(
#             name=shipment.contact,
#             email=shipment.email,
#             telephone=shipment.telephone,
#             sender_address=remote_address)
#
#         update_gui_from_contact(config=config, sender_or_recip=shipment.sender, window=window)
#         update_gui_from_address(address=shipment.sender.sender_address, sender_or_recip=shipment.sender, window=window)
#
#     else:
#         shipment.recipient = client.recipient(
#             name=shipment.contact,
#             email=shipment.email,
#             telephone=shipment.telephone,
#             recipient_address=remote_address)
#
#         update_gui_from_contact(config=config, sender_or_recip=shipment.recipient, window=window)
#         update_gui_from_address(address=shipment.recipient.recipient_address, sender_or_recip=shipment.recipient,
#                                 window=window)
#


# def fix_address(shipment: Shipment, client: DespatchBaySDK, config: Config):
#     while True:
#         sg.popup(f"There's a problem with the address for {shipment.customer}... "
#                  f"let's fix it")
#         shipment.recipient.recipient_address = address_from_user_loop(client=client, config=config,
#                                                                       shipment=shipment)
#         non_address_prep(shipment=shipment, client=client, config=config)


# def attempt_populate_shipment(window: Window, shipment: Shipment, config: Config):
#     dt_mask = config.datetime_masks['DT_DISPLAY']
#     try:
#         window[f'-{shipment.shipment_name}_recipient-'.upper()].update(shipment.recipient.recipient_address.street)
#     finally:
#         try:
#             window[f'-{shipment.shipment_name}_sender-'.upper()].update(shipment.sender.sender_address.street)
#         finally:
#             try:
#                 window[f'-{shipment.shipment_name}_date-'.upper()].update(
#                     f'{parse(shipment.collection_date.date):{dt_mask}}')
#             finally:
#                 try:
#                     window[f'-{shipment.shipment_name}_service-'.upper()].update(
#                         f'{parse(shipment.collection_date.date):{dt_mask}}')
#                 except Exception as e:
#                     ...
#                 else:
#                     return True
#

#
# def silent_address(shipment: Shipment, client: DespatchBaySDK, config: Config):
#     address = search_adddress(client=client, shipment=shipment)
#     if not address:
#         address = get_silent_match(client=client, config=config, shipment=shipment)
#
#     if address:
#         shipment.recipient = get_remote_recip(client=client, shipment=shipment, remote_address=address)
#         shipment.remote_address = address
#         return address
#     else:
#         ...
#

#
# def outbound_address_prepper(shipment: Shipment, client: DespatchBaySDK, config: Config):
#     # todo unswitch search
#     while True:
#         if address := search_adddress(client=client, shipment=shipment):
#             break
#         if address := get_really_goodmatch(client=client, shipment=shipment, config=config):
#             break
#         else:
#             address = address_from_user_loop(client=client, config=config, shipment=shipment)
#             break
#
#     shipment.sender = get_home_sender(client=client, config=config)
#     shipment.recipient = get_remote_recip(client=client, shipment=shipment, remote_address=address)
#     shipment.remote_address = address
#


#
# def get_silent_match(client: DespatchBaySDK, config: Config, shipment: Shipment):
#     """
#     Return a dbay recipient/sender object representing the customer address defined in imported xml or dbase file.
#     search by customer name, then shipment search_term
#     call explicit_matches to compare strings,
#     call get_bestmatch for fuzzy results,
#     if best score exceed threshold ask user to confirm
#     If still no valid address, call get_new_address.
#     """
#     candidate_keys: [AddressKey] = get_candidate_keys_dict(client=client, shipment=shipment)
#     if address := quick_match(candidate_keys=candidate_keys, shipment=shipment, client=client):
#         return address
#     fuzzyscores = []
#
#     for candidate_key in candidate_keys:
#         candidate_address = client.get_address_by_key(candidate_key.key)
#         if explicit_match := get_explicit_bestmatch(candidate_address=candidate_address, shipment=shipment):
#             return explicit_match.address
#         else:
#             fuzzyscores.append(get_fuzzy_scores(candidate_address=candidate_address, shipment=shipment))
#     else:
#         # finished loop, no explicit matches so get highest scoring one from the list of fuzzyscores
#         best_match = bestmatch_from_fuzzyscores(fuzzyscores=fuzzyscores)
#         # best_match = popup_confirm_fuzzy(best_match)
#
#     return best_match.address if best_match else None
#


# def remote_frame_from_bestmatch(shipment: Shipment, client: DespatchBaySDK, bestmatch: BestMatch):
#     if shipment.is_return:
#         sender_or_recip = client.sender(
#             name=shipment.contact,
#             email=shipment.email,
#             telephone=shipment.telephone,
#             sender_address=bestmatch.address)
#         shipment.sender = sender_or_recip
#         remote_frame = bulk_sender_recipient_frame(mode='sender')
#
#     else:
#         sender_or_recip = client.recipient(
#             name=shipment.contact,
#             email=shipment.email,
#             telephone=shipment.telephone,
#             recipient_address=bestmatch.address)
#         shipment.recipient = sender_or_recip
#         remote_frame = bulk_sender_recipient_frame(mode='recipient')
#
#     return remote_frame


#
# def get_new_address(client: DespatchBaySDK, shipment: Shipment, postcode: str = None) -> Address:
#     """ calls address chooser for user to select an address from those existing at either provided or shipment postcode """
#     while True:
#         postcode = postcode or sg.popup_get_text(f'Bad Postcode for {shipment.customer} - please enter one')
#         if shipment.candidate_keys:
#             candidates = shipment.candidate_keys
#         else:
#             try:
#                 candidates = client.get_address_keys_by_postcode(postcode)
#             except:
#                 postcode = None
#                 continue
#
#             # address_key_dict = {candidate.address: candidate.key for candidate in candidates}
#             address_key = address_chooser_popup(candidates=candidates)
#
#             return address_key
#

#
# def address_chooser(candidates: list, client: DespatchBaySDK) -> Address:
#     """ returns an address as chosen by user from a given list of candidates"""
#     address_key_dict = {candidate.address: candidate.key for candidate in candidates}
#     address_key = address_chooser_popup(address_key_dict)

#
# if address_key:
#     address = client.get_address_by_key(address_key)
#     return address


#
# def bestmatch_checker(best_match: BestMatch, shipment: Shipment, config: Config):
#     """ takes a bestmatch tuple
#     return the bestmatch object or none if user declines"""
#     display_vars = ['company_name', 'street', 'locality']
#
#     category_map = {'str_to_company': 'Input address string to Address Company',
#                     'str_to_street': 'Input address String to Address String',
#                     'customer_to_company': 'Customer name to Address Company Name',
#                     }
#
#     address = best_match.address
#     category = category_map[best_match.category]
#     frame = remote_address_frame(shipment=shipment, address=address, config=config)
#     layout = [
#         [sg.Text('No exact address match - accept fuzzy match?\n\n',)],
#         [sg.Text(f'Best match category was {category} '
#                  f'\nwith a score of {best_match.score} '
#                  f'\nBest Address match is:')],
#         [frame]
#     ]
#
#     window = sg.Window("Bestmatch Checker", layout=layout)
#     e, v = window.read()
#     if 'submit' in e.lower():
#         update_address_from_gui(config=config, address=shipment.recipient.recipient_address, values=v)
#
#         return
#


#
# def update_address_from_gui(config: Config, shipment: Shipment, sender_or_recip: Sender | Recipient, values: dict):
#     address_to_edit = sender_or_recip.sender_address if shipment.is_return else sender_or_recip.recipient_address
#     address_fields = config.fields.address
#     for field in address_fields:
#         value = values.get(f'-{type(sender_or_recip).__name__.upper()}_{field.upper()}-', None)
#         setattr(address_to_edit, field, value)
#     return address_to_edit
#


#
# def ship_dict_from_xml(config: Config, xml_file: str) -> dict:
#     """parse amherst shipment xml"""
#     shipment_fields = config.fields.shipment
#     ship_dict = dict()
#     tree = ET.parse(xml_file)
#     root = tree.getroot()
#     fields = root[0][2]
#
#     category = root[0][0].text
#     for field in fields:
#         k = field[0].text
#         k = to_snake_case(k)
#         v = field[1].text
#         if v:
#             k = unsanitise(k)
#             v = unsanitise(v)
#
#             if "number" in k.lower():
#                 # if not v.isnumeric():
#                 #     v = re.sub(r"\D", "", v)
#                 if 'serial' in k.lower():
#                     v = [int(x) for x in v.split() if x.isdigit()]
#                 else:
#                     if isinstance(v, str):
#                         v = re.sub(r"\D", "", v)
#
#                         # v = int(v.replace(',', ''))
#             if k == 'name':
#                 k = 'shipment_name'
#                 v = "".join(ch if ch.isalnum() else '_' for ch in v)
#             if k[:6] == "deliv ":
#                 k = k.replace('deliv', 'delivery')
#             k = k.replace('delivery_', '')
#             if k == 'tel':
#                 k = 'telephone'
#             if k == 'address':
#                 k = 'address_as_str'
#             ship_dict.update({k: v})
#
#     # get customer name
#     if category == "Hire":
#         ship_dict['customer'] = root[0][3].text
#     elif category == "Customer":
#         ship_dict['customer'] = fields[0][1].text
#         ship_dict[
#             'shipment_name'] = f'{ship_dict["shipment_name"]} - {datetime.now().isoformat(" ", timespec="seconds")}'
#     elif category == "Sale":
#         ship_dict['customer'] = root[0][3].text
#
#     # convert send-out-date to dt object, or insert today
#     ship_dict['date'] = ship_dict.get('send_out_date', None)
#     if ship_dict['date']:
#         # ship_dict['date'] = parse(ship_dict['date'])
#         ship_dict['date'] = datetime.strptime(ship_dict['date'], config.datetime_masks['DT_HIRE'])
#     else:
#         ship_dict['date'] = datetime.today()
#
#     ship_dict['category'] = category
#     ship_dict['search_term'] = parse_amherst_address_string(ship_dict['address_as_str'])
#
#     ship_dict['boxes'] = ship_dict.get('boxes', 1)
#
#     missing = []
#     for attr_name in shipment_fields:
#         if attr_name not in ship_dict.keys():
#             if attr_name not in ['cost', 'inbound_id', 'outbound_id']:
#                 missing.append(attr_name)
#     if missing:
#         print_and_pop(f"*** Warning - {missing} not found in ship_dict - Warning ***")
#     return ship_dict
#

# def to_snake_case(input_string: str) -> str:
#     """Convert a string to lowercase snake case."""
#     input_string = input_string.replace(" ", "_")
#     input_string = ''.join(c if c.isalnum() else '_' for c in input_string)
#     input_string = input_string.lower()
#     return input_string


# def remote_address_window(shipment: Shipment, client: DespatchBaySDK, bestmatch: BestMatch):
#     if shipment.is_return:
#         remote_sender = remote_sender_from_bestmatch(shipment=shipment, client=client, bestmatch=bestmatch)
#
#         window = sg.Window('Sender', layout=[[remote_frame]], finalize=True)
#     else:
#         remote_recip = remote_recip_from_bestmatch(shipment=shipment, client=client, bestmatch=bestmatch)
#
#         window = sg.Window('Recipient', layout=[[remote_frame]], finalize=True)
#     return window

# def remote_sender_window():
#     remote_sender = remote_sender_from_bestmatch(shipment=shipment, client=client, bestmatch=bestmatch)
#     window = sg.Window('Sender', layout=[[remote_frame]], finalize=True)
#
#
# def remote_sender_from_bestmatch(shipment: Shipment, client: DespatchBaySDK, bestmatch: BestMatch):
#     return client.sender(
#         name=shipment.contact,
#         email=shipment.email,
#         telephone=shipment.telephone,
#         sender_address=bestmatch.address)
#
#
# def remote_recip_from_bestmatch(shipment: Shipment, client: DespatchBaySDK, bestmatch: BestMatch):
#     return client.recipient(
#         name=shipment.contact,
#         email=shipment.email,
#         telephone=shipment.telephone,
#         recipient_address=bestmatch.address)



# def populate_non_address_fields(client: DespatchBaySDK, config: Config, shipment: Shipment, window: Window):
#     """ fills gui from shipment details. if customer address is invalid launch a popup to fix"""
#
#     services_dict = get_service_menu(client=client, config=config, shipment=shipment)
#     dates_dict = get_dates_menu(client=client, config=config, shipment=shipment)
#     q_o_b_dict = get_queue_or_book_menu(shipment=shipment)
#
#     window['-SHIPMENT_NAME-'].update(shipment.shipment_name)
#     # todo color date based on match.... how to update without bg-color in update method? = learn TKinter
#     window['-DATE-'].update(values=dates_dict['values'], value=dates_dict['default_value'])
#     window['-SERVICE-'].update(values=services_dict['values'], value=services_dict['default_value'])
#     if shipment.inbound_id:
#         window['-INBOUND_ID-'].update(shipment.inbound_id)
#     if shipment.outbound_id:
#         window['-OUTBOUND_ID-'].update(shipment.outbound_id)
#     window['-QUEUE_OR_BOOK-'].update(values=q_o_b_dict['values'], value=q_o_b_dict['default_value'])
#     window['-BOXES-'].update(value=shipment.boxes or 1)
#



#
# def get_matched_address_new(client: DespatchBaySDK, config: Config, shipment: Shipment) -> Address:
#     """
#     Return a dbay recipient/sender object representing the customer address defined in imported xml or dbase file.
#     search by customer name, then shipment search_term
#     call explicit_matches to compare strings,
#     call get_bestmatch for fuzzy results,
#     if best score exceed threshold ask user to confirm
#     If still no valid address, call get_new_address.
#     """
#     address: Address | None = None
#     while not address:
#         address = search_adddress(client=client, shipment=shipment)
#         if address.company_name:
#             if address.company_name != shipment.customer:
#                 pop_msg = f'Address matched from direct search\n' \
#                           f'But <Shipment Customer> and <Address Company Name> do not match:\n' \
#                           f'\n{shipment.customer} =/= {address.company_name}\n'
#                 if address.company_name in shipment.address_as_str:
#                     pop_msg += f'\nHowever <Company Name> is in <Shipment address string>:' \
#                                f'{address.company_name} -> {shipment.address_as_str} \n'
#                 pop_msg += '\n[Yes] to accept matched address or [No] to fetch a new one'
#                 if sg.popup_yes_no(pop_msg) == 'Yes':
#                     return address
#                 else:
#                     return address_from_user_loop(client=client, config=config, shipment=shipment,
#                                                   address=shipment.bestmatch.address)
#



def get_service(client: DespatchBaySDK, config: Config, shipment: Shipment):
    """ return the dbay service specified in toml or the first available"""
    services = client.get_services()
    # todo get AVAILABLE services needs a request
    # services = client.get_available_services()
    # shipment.service_menu_map.update({service.name: service for service in services})

    return next((service for service in services if service.service_id == config.dbay['service']),
                services[0])


#
#
# def get_remote_sender(client: DespatchBaySDK, shipment: Shipment, remote_address: Address) -> Sender:
#     return client.sender(
#         name=shipment.contact,
#         email=shipment.email,
#         telephone=shipment.telephone,
#         sender_address=remote_address)
#
#
# def get_remote_recip(shipment: Shipment, client: DespatchBaySDK, remote_address: Address) -> Sender:
#     recip = client.recipient(
#         name=shipment.contact,
#         email=shipment.email,
#         telephone=shipment.telephone,
#         recipient_address=remote_address)
#     logger.info(f'PREP SHIPMENT - REMOTE RECIPIENT {recip}')
#     return recip




#
# def get_home_sender(client: DespatchBaySDK, config: Config) -> Sender:
#     """ return a dbay sender object representing home address defined in toml / Shipper.config"""
#     sender = client.sender(
#         address_id=config.home_contact['address_id'],
#         name=config.home_address['contact'],
#         email=config.home_address['email'],
#         telephone=config.home_address['telephone'],
#         sender_address=client.get_sender_addresses()[0].sender_address
#     )
#     logger.info(f'PREP - GET HOME SENDER {sender}')
#     return sender


# def get_home_recipient(client: DespatchBaySDK, config: Config) -> Recipient:
#     """ return a dbay recipient object representing home address defined in toml / Shipper.config"""
#     return client.recipient(
#         name=config.home_address['contact'],
#         email=config.home_address['email'],
#         telephone=config.home_address['telephone'],
#         recipient_address=client.find_address(config.home_address['postal_code'],
#                                               config.home_address['search_term'])
#     )



def update_remote_address_from_gui(config: Config, values: dict):
    contact_fields = config.fields.contact
    for field in contact_fields:
        ...


# value = values.get(address_frame_key)
# if all([value, field]):
#     setattr(address, field, value)


def update_contact_from_gui(config: Config, contact: Sender | Recipient, values: dict):
    contact_fields = config.fields.contact
    contact_type = type(contact).__name__
    for field in contact_fields:
        value = values.get(f'-{contact_type}_{field}-'.upper())
        if all([value, field]):
            setattr(contact, field, value)

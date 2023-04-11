
def ship_dict_from_xml(config: Config, xml_file: str) -> dict:
    """parse amherst shipment xml"""
    shipment_fields = config.shipment_fields
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

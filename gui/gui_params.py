import PySimpleGUI as sg

default_params = {
    'font': 'Rockwell 12',
    'element_padding': (5, 5),
    'border_width': 4,
}

shipment_params = {
    'size': (22, 2),
    'justification': 'center',
    'pad': (5, 5),
    # 'border_width': 4,
    'relief': sg.RELIEF_GROOVE,
}

head_params = {
    'size': (22, 2),
    'justification': 'center',
    'pad': (5, 5),
}

date_params = {
    'size': (12, 2),
    # 'expand_y': True,
    # 'justification': 'center',
    'pad': (5, 5),
    'border_width': 4,
    'relief': sg.RELIEF_GROOVE,

}

date_head_params = {
    'size': (12, 2),
    'justification': 'center',
    'pad': (5, 5),
}

address_params = {
    'size': (30, 4),
    'justification': 'center',
    'pad': (5, 5),
    'border_width': 4,
    'relief': sg.RELIEF_GROOVE,
    'auto_size_text': True,
}

address_head_params = {
    'size': (30, 2),
    'justification': 'center',
    'pad': (5, 5),
}

boxes_head_params = {
    'size': (5, 2),
    'justification': 'center',
    'pad': (5, 5),
    # 'auto_size_text': True,
}

boxes_params = {
    'size': (5, 1),
    # 'justification': 'center',
    'pad': (5, 5),
    'border_width': 4,
    'relief': sg.RELIEF_GROOVE,
    # 'auto_size_text': True,
}

address_input_params = {
    'size': (18, 1),
    'justification': 'left',
    'expand_x': True,
    'pad': (20, 8),
}

address_fieldname_params = {
    'size': (15, 1),
    'justification': 'center',
    'pad': (20, 8),
}

option_menu_params = {
    'pad': (10, 5),
    'size': (30, 1),
    'readonly': True,
}

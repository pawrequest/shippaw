import PySimpleGUI as sg


def item_row(item_num):
    row = [sg.pin(sg.Col([[sg.B("X", border_width=0, button_color=(sg.theme_text_color(), sg.theme_background_color()),
                                k=('-DEL-', item_num), tooltip='Delete this item'),
                           sg.In(size=(20, 1), k=('-DESC-', item_num)),
                           sg.T(f'Key number {item_num}', k=('-STATUS-', item_num))]], k=('-ROW-', item_num)))]
    return row


def make_window():
    layout = [[sg.Text('Add and "Delete" Rows From a Window', font='_ 15')],
              [sg.Col([item_row(0)], k='-TRACKING SECTION-')],
              [sg.pin(sg.Text(size=(35, 1), font='_ 8', k='-REFRESHED-', ))],
              [sg.T("X", enable_events=True, k='Exit', tooltip='Exit Application'),
               sg.T('Refresh', enable_events=True, k='Refresh', tooltip='Save Changes & Refresh'),
               sg.T('+', enable_events=True, k='Add Item', tooltip='Add Another Item')]]

    right_click_menu = [[''], ['Add Item', 'Edit Me', 'Version']]

    window = sg.Window('Window Title', layout, right_click_menu=right_click_menu, use_default_focus=False, font='_ 15',
                       metadata=0)

    return window


def main():
    window = make_window()
    while True:
        event, values = window.read()  # wake every hour
        print(event, values)
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        if event == 'Add Item':
            window.metadata += 1
            window.extend_layout(window['-TRACKING SECTION-'], [item_row(window.metadata)])
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), location=window.current_location(), keep_on_top=True,
                              non_blocking=True)
        elif event[0] == '-DEL-':
            window[('-ROW-', event[1])].update(visible=False)
    window.close()


if __name__ == '__main__':
    main()

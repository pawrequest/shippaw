import PySimpleGUI as sg
"""
    Demo - 2 simultaneous windows using read_all_window

    Window 1 launches window 2
    BOTH remain active in parallel

    Both windows have buttons to launch popups.  The popups are "modal" and thus no other windows will be active

    Copyright 2020 PySimpleGUI.org
"""

def make_win1():
    layout = [[sg.Text('This is the FIRST WINDOW'), sg.Text('      ', k='-OUTPUT-')],
              [sg.Text('Click Popup anytime to see a modal popup')],
              [sg.Button('Launch 2nd Window'), sg.Button('Popup'), sg.Button('Exit')]]
    return sg.Window('Window Title', layout, location=(800,600), finalize=True)


def make_win2():
    layout = [[sg.Text('The second window')],
              [sg.Input(key='-IN-', enable_events=True)],
              [sg.Text(size=(25,1), k='-OUTPUT-')],
              [sg.Button('Erase'), sg.Button('Popup'), sg.Button('Exit')]]
    return sg.Window('Second Window', layout, finalize=True)

window1, window2 = make_win1(), None        # start off with 1 window open

while True:             # Event Loop
    window, event, values = sg.read_all_windows()
    if event == sg.WIN_CLOSED or event == 'Exit':
        window.close()
        if window == window2:       # if closing win 2, mark as closed
            window2 = None
        elif window == window1:     # if closing win 1, exit program
            break
    elif event == 'Popup':
        sg.popup('This is a BLOCKING popup','all windows remain inactive while popup active')
    elif event == 'Launch 2nd Window' and not window2:
        window2 = make_win2()
    elif event == '-IN-':
        window['-OUTPUT-'].update(f'You enetered {values["-IN-"]}')
    elif event == 'Erase':
        window['-OUTPUT-'].update('')
        window['-IN-'].update('')
window.close()
#
# [name('Multiline'), sg.Multiline(s=(15,2))],
#                 [name('Output'), sg.Output(s=(15,2))],
#                 [name('Combo'), sg.Combo(sg.theme_list(), default_value=sg.theme(), s=(15,22), enable_events=True, readonly=True, k='-COMBO-')],
#                 [name('OptionMenu'), sg.OptionMenu(['OptionMenu',],s=(15,2))],
#                 [name('Checkbox'), sg.Checkbox('Checkbox')],
#                 [name('Radio'), sg.Radio('Radio', 1)],
#                 [name('Spin'), sg.Spin(['Spin',], s=(15,2))],
#                 [name('Button'), sg.Button('Button')],
#                 [name('ButtonMenu'), sg.ButtonMenu('ButtonMenu', sg.MENU_RIGHT_CLICK_EDITME_EXIT)],
#                 [name('Slider'), sg.Slider((0,10), orientation='h', s=(10,15))],
#                 [name('Listbox'), sg.Listbox(['Listbox', 'Listbox 2'], no_scrollbar=True,  s=(15,2))],
#                 [name('Image'), sg.Image(sg.EMOJI_BASE64_HAPPY_THUMBS_UP)],
#                 [name('Graph'), sg.Graph((125, 50), (0,0), (125,50), k='-GRAPH-')]
#
# layout_r = [[name('Canvas'), sg.Canvas(background_color=sg.theme_button_color()[1], size=(125, 50))],
#             [name('ProgressBar'), sg.ProgressBar(100, orientation='h', s=(10, 20), k='-PBAR-')],
#             [name('Table'), sg.Table([[1, 2, 3], [4, 5, 6]], ['Col 1', 'Col 2', 'Col 3'], num_rows=2)],
#             [name('Tree'), sg.Tree(treedata, ['Heading', ], num_rows=3)],
#             [name('Horizontal Separator'), sg.HSep()],
#             [name('Vertical Separator'), sg.VSep()],
#             [name('Frame'), sg.Frame('Frame', [[sg.T(s=15)]])],
#             [name('Column'), sg.Column([[sg.T(s=15)]])],
#             [name('Tab, TabGroup'), sg.TabGroup([[sg.Tab('Tab1', [[sg.T(s=(15, 2))]]), sg.Tab('Tab2', [[]])]])],
#             [name('Pane'), sg.Pane([sg.Col([[sg.T('Pane 1')]]), sg.Col([[sg.T('Pane 2')]])])],
#             [name('Push'), sg.Push(), sg.T('Pushed over')],
#             [name('VPush'), sg.VPush()],
#             [name('Sizer'), sg.Sizer(1, 1)],
#             [name('StatusBar'), sg.StatusBar('StatusBar')],
#             [name('Sizegrip'), sg.Sizegrip()]]
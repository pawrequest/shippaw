import PySimpleGUI as sg

menu_def = ['mon','tue','wed']
element = sg.OptionMenu(default_value= menu_def[0], values=(menu_def),  k='-OPTION MENU-')
layout = [
    [element]
]
window = sg.Window('Test', layout)

while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Exit'):
        break

    print(values)

window.close()

#
# while True:
#     ...
#
# # Define the layout of the window
# layout = [[sg.Button('Click me!', key='-BUTTON-')],
#           [sg.Combo(['Option 1', 'Option 2', 'Option 3'], key='-COMBO-', visible=False)]]
#
# # Create the window
# window = sg.Window('Dropdown Example', layout)
#
# # Event loop to process events and get input
# while True:
#     event, values = window.read()
#
#     # If the window is closed or the user clicks the exit button, close the window and exit the program
#     if event == sg.WINDOW_CLOSED or event == 'Exit':
#         break
#
#     # If the user clicks the button, show the dropdown menu
#     if event == '-BUTTON-':
#         window['-COMBO-'].update(visible=True)
#
#     # If the user selects an option from the dropdown, capture the input
#     if event == '-COMBO-':
#         selected_option = values['-COMBO-']
#         print(f'The user selected {selected_option}')
#
# # Close the window and exit the program
# window.close()

# import PySimpleGUI as sg
#
# sg.theme('DarkBlue')
#
# button_layout = [[sg.Button('Button 1'), sg.Button('Button 2'), sg.Button('Button 3')]]
#
# inner_layout = [[sg.Text('This is the inner frame')],
#                 [sg.InputText()],
#                 [sg.Checkbox('Checkbox 1'), sg.Checkbox('Checkbox 2')]]
#
# inner_frame = sg.Frame('Inner Frame', inner_layout)
#
# outer_layout = [[sg.Text('This is the outer frame')],
#                 [sg.Column(button_layout)],
#                 [inner_frame]]
#
# outer_frame = sg.Frame('Outer Frame', outer_layout)
#
# layout = [[outer_frame]]
#
# window = sg.Window('My window', layout)
#
# while True:
#     event, values = window.read()
#     if event == sg.WIN_CLOSED:
#         break
#
# window.close()

def flip(thing):
    return [1 if i == 0 else 0 if i ==1 else None for i in thing]


def freed_prisoners(prison):
    free = 0
    for i in range(len(prison)):
        if prison[i] == 1:
            free += 1
            prison = flip(prison)
    print(f"{free} prisoners freed")
    return free


def get_prison():
    while True:
        prison = []
        ui = input("Enter 1s and 0s\n")
        if ui == '':
            continue
        if not ui.isnumeric():
            print("Not a prison - try again")
            continue
        if(set(list(ui)).issubset({'0', '1'})):
            for i in list(ui):
                prison.append(int(i))
        else:
            print("Wrong number - not a prison - try again")
            continue
        return prison

def run_prisoners():
    prison = get_prison()
    freed = freed_prisoners(prison)
    while True:
        ui = input("[P]lay again? or [E]xit?\n")[0].lower()
        if ui == 'p':
            run_prisoners()
        if ui =='e':
            exit()

run_prisoners()


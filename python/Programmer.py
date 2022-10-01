import subprocess
from time import sleep

from python.utils_pss.utils_pss import get_from_ods, getActiveProcesses


# make radio config class dyn. from others?

class Config:
    def __init__(self):  # config should be above radios
        self.config_ods = r"C:\AmDesp\data\AmDespConfig.ods"
        self.rads_w_bat_sers = ['hytera_pd705']

        class RadioConfig:
            def __init__(self, ods):
                radios_dict = get_from_ods(ods, 'RADIO_DICT')
                for radio, properties in radios_dict.items():
                    setattr(self, radio, properties)
                # self.radios = get_from_ods(self.config_ods, 'RADIO_DICT')
                print(f"DSGSDGSDG")

        self.radios = RadioConfig(self.config_ods)


PROG_CNFG = Config()
...

class ProgrammingAssistant:
    def __init__(self):
        self.plug_loaded = False
        ...

    def BootUp(self):
        self.Greeter()
        # self.get_bin()
        if not self.run_cps():
            print("ERROR NO CPS LOADED")
            self.BootUp()
        self.create_batch()
        self.load_plug()
        # self.batch.program_radio()

    def Greeter(self):
        while True:
            print(f"\nWelcome to AmDesp Radio Programming Assistant, please slect a radio type:")
            rads = vars(PROG_CNFG.radios)
            for c, rad in enumerate(rads, start=1):
                print(f"{c} - {rad}")
            ui = input("which radio type - enter a number \n")
            if ui.isnumeric() and 0 < int(ui) <= len(rads):
                uii = int(ui) - 1
                self.radio = list(rads.values())[uii]
                break
            else:
                continue

    def check_cps_running(self):
        processes = getActiveProcesses()
        bin = self.radio['cps']
        if bin in processes:
            cps_running = True
            print(f"{cps_running=}")
            return True


    def run_cps(self):
        bin = self.radio['cps']
        cps_running = False
        loop_count = 0
        while not cps_running:
            if self.check_cps_running():
                return True
            else:
                print(f"launching CPS program: {bin}")
                try:
                    subprocess.Popen(bin)
                except:
                    print(f"couldn't load {bin}")
                    loop_count += 1
                    if loop_count > 2:
                        raise ImportError
                sleep(1)
                continue

    def load_plug(self):
        if self.check_cps_running():
            # TODO automate this
            loaded = False
            while not loaded:
                ui = 'n'
                while ui[0].lower() != 'y':
                    ui = input("Load the correct codeplug and enter [Y] to continue\n")
                    uii = ui[0].lower()
                    if uii == 'y':
                        self.plug_loaded = True
                        return
                    else:
                        continue
        ...

    def create_batch(self):
        ui = input("How many radios to program?\n")
        self.batch = self.RadioBatch(ui)


    class RadioBatch():
        def __init__(self, quant):
            self.quant = quant
            self.rad_serials = []
            self.bat_serials = None

    def program_radio(self):
        if not self.check_cps_running():
            return False
        # prompt to continue
        # focus cps

        ...


# class RadioToProg:
#     def __init__(self, rad):
#         self.radio_type = rad
#         self.programmer_bin = PROG_CNFG.rad_prog_bins[rad_type]
#         self.battery = ...

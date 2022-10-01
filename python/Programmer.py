import subprocess

from python.utils_pss.utils_pss import get_from_ods, getActiveProcesses


# make radio config class dyn. from others?

class Config:
    def __init__(self):  # config should be above radios
        self.config_ods = r"C:\AmDesp\data\AmDespConfig.ods"

        class RadioConfig:
            def __init__(self, ods):
                radios_dict = get_from_ods(ods, 'RADIO_DICT')
                for radio, properties in radios_dict.items():
                    setattr(self, radio, properties)
                # self.radios = get_from_ods(self.config_ods, 'RADIO_DICT')
                print(f"DSGSDGSDG")

        self.radios = RadioConfig(self.config_ods)


CNFG = Config()
...

# class ProgApp:
#     def Programmer(self):
#         programmer = ProgrammingAssistant()
#         programmer.run_program_ass()
#

class ProgrammingAssistant:
    def __init__(self):
        while True:
            print(f"\nWelcome to AmDesp Radio Programming Assistant, please slect a radio type:")
            rads = vars(CNFG.radios)
            bins = []
            for c, rad in enumerate(rads, start=1):
                print(f"{c} - {rad}")
                bin = rads[rad]['cps']
                bins.append(bin)
            ui = input("which radio type - enter a number \n")
            if ui.isnumeric() and 0 < int(ui) <= len(rads):
                uii = int(ui) - 1
                self.radio_type = rad
                self.bin = bins[uii]
                break
            else:
                continue
        # do smth
    def setup_env(self):
        # launch programmer, output_file
        self.cps_running = self.cps_running_check()

    def cps_running_check(self):
        processes = getActiveProcesses()
        processes = sorted(processes)
        self.cps_running = False
        while not self.cps_running:
            if self.bin in processes:
                self.cps_running = True
                print(f"{self.cps_running=}")
                return true
            else:
                print(f"{self.cps_running=}")
                print(f"launnching {self.bin}")
                subprocess.call(self.bin)
                continue
                # run cps.bin

                ...


# class RadioToProg:
#     def __init__(self, rad):
#         self.radio_type = rad
#         self.programmer_bin = CNFG.rad_prog_bins[rad_type]
#         self.battery = ...

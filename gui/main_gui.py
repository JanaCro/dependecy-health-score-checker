import numpy as np
import tkinter as tk
from tkinter import ttk
import pandas as pd

from gui.configure_gui import open_config_gui
from calculators import CriticalityScoreCalculator

class MainGUI:
    def __init__(self):
        data = pd.read_csv('parameters.csv')
        self.keys_ordered = data['parameter'].to_numpy()
        self.W = data['weight_fixed'].to_numpy()
        self.thresh_num = data['thresh_T1'].to_numpy()
        self.thresh_den = data['thresh_T2'].to_numpy()
        self.W_type = 0

        self.set_root_gui()  # Set root gui, necessary for tkinter text variable

        self.info_box_text = tk.StringVar(self.master_frame)
        text = 'The tool calculates the health score of open-source packages. \n Additional information about the package will be displayed here. \n 100% is the healthiest result, while 0% is the worst result. \n Packages with less than 50% should be considered not properly maintained!'
        self.info_box_text.set(text)
        self.cs_calculator = CriticalityScoreCalculator(self.keys_ordered, self.thresh_num, self.thresh_den)

        self.set_gui()

    def set_root_gui(self):
        # Set window
        self.master_frame = tk.Tk()
        self.master_frame.title("Health Calculator")
        self.master_frame.resizable(False, False)
        self.master_frame.iconbitmap("icon.ico")

    def set_gui(self):
        # region MAIN PART OF THE WINDOW
        tk.Label(self.master_frame, fg='black', text='Package:').grid(row=0, column=0)
        self.package_name_entry = tk.Entry(self.master_frame, fg='black', bg='white', width=50)
        self.package_name_entry.insert(tk.END, '')
        self.package_name_entry.grid(row=0, column=1, columnspan=2)

        tk.Label(self.master_frame, fg='black', text='Platform:').grid(row=1, column=0)
        options = ['pypi', 'maven', 'npm', 'conda']
        self.platform_option = tk.StringVar()
        self.platform_option.set(options[0])
        self.platform_name_option_menu = tk.OptionMenu(self.master_frame, self.platform_option, *options)
        self.platform_name_option_menu.grid(row=1, column=1, columnspan=2)

        self.configure_button = tk.Button(self.master_frame, text='CONFIGURE', cursor='hand2')
        self.configure_button.bind('<Button-1>', self.configure_button_clicked)
        self.configure_button.grid(row=2, column=0)

        self.calc_score_button = tk.Button(self.master_frame, text='CALC HEALTH. SCORE', cursor='hand2')
        self.calc_score_button.bind('<Button-1>', self.calculate_score_button_clicked)
        self.calc_score_button.grid(row=2, column=1)

        self.crit_score_var = tk.StringVar(self.master_frame)
        self.crit_score_var.set('0')
        self.crit_score_label = tk.Label(self.master_frame, fg='black', textvariable=self.crit_score_var)
        self.crit_score_label.grid(row=2, column=2)
        # endregion

        # region INFO SPACE
        self.info_frame = tk.LabelFrame(self.master_frame, text='INFO', padx=5, pady=5, width=30)
        self.info_frame.grid(row=4, column=0, columnspan=3)

        self.info_label = tk.Label(self.info_frame, fg='black', textvariable=self.info_box_text)
        self.info_label.grid(row=0, column=0)
        # endregion

        # region DISAPPEARING PROGRESS BAR
        self.progress_bar = ttk.Progressbar(self.master_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky='news')
        #initially removed when program starts
        self.progress_bar.grid_remove()

        self.progress_bar['value'] = 0
        self.curr_update = 0
        self.cs_calculator.set_update_pb(self.update_progressbar)

    def update_progressbar(self):
        self.curr_update += 1
        self.progress_bar['value'] += float(1/len(self.keys_ordered)*100)
        self.master_frame.update_idletasks()

        if self.curr_update == len(self.keys_ordered):
            self.curr_update = 0
            self.progress_bar['value'] = 0

    def configure_button_clicked(self, event):
        open_config_gui(self.get_state, self.set_state)

    def calculate_score_button_clicked(self, event):
        # Start progress bar
        self.progress_bar.grid()

        # Calculate score
        score = 0
        try:
            score, text = self.cs_calculator.calculate_criticality_score(self.package_name_entry.get().strip(), self.platform_option.get(), self.W)
            self.info_box_text.set(text)
            self.info_label.config(fg='black')
        except Exception as e:
            print(e)
            self.info_box_text.set(e.args[0])
            self.info_label.config(fg='red')

        self.crit_score_var.set(str(score))

        # End progress bar
        self.progress_bar.grid_remove()

    # main gui sending to configure gui important only for type (so that config gui remembers the choice)
    def get_state(self) -> dict:
        return {
            'W': self.W,
            't1': self.thresh_num,
            't2': self.thresh_den,
            'W_type': self.W_type
        }

    def set_state(self, W=None, t1=None, t2=None, W_type=None):
        print(f"W: {W}")
        print(f"t1: {t1}")
        print(f"t2: {t2}")
        print(f"W_type: {W_type}")
        if t1 is not None:
            t1 = np.array(t1, dtype=np.float)
            self.cs_calculator.thresh_num = self.thresh_num = t1
        if t2 is not None:
            t2 = np.array(t2, dtype=np.float)
            self.cs_calculator.thresh_den = self.thresh_den = t2
        if W is not None:
            W = np.array(W, dtype=np.float)
            self.W = W
        if W_type is not None:
            self.W_type = W_type

    def run(self):
        self.master_frame.mainloop()

def open_GUI():
    window = MainGUI()
    window.run()
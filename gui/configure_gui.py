import tkinter as tk
from tkinter import ttk
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ai import WeightCalculatorAI
matplotlib.use('TkAgg')

parameters_file = 'parameters.csv'

class ConfigGUI():
    def __init__(self, get_state, set_state):
        self.get_state, self.set_state = get_state, set_state
        self.scrollbar_rows = 4
        self.df_parameters = self.__read_table(parameters_file)[1]
        self.df_default = self.__read_table(parameters_file)[0]

        self.set_gui()

    def set_gui(self):
        # Set window   (4 big frames in total)
        self.master_frame = tk.Tk()
        self.master_frame.title("Configurations")
        self.master_frame.resizable(False, False)
        self.master_frame.iconbitmap("icon.ico")

        # region FORMULA FRAME
        formula_str = r"$H_{project} = \frac{1}{\sum_i |\alpha_i|} \sum_i \alpha_i \frac{log(1+max(S_i, T_{1,i}))}{log(1+max(S_i, T_{2,i}))}$"

        self.formula_label = tk.Label(self.master_frame)
        self.formula_label.grid(row=0, column=0)
        fig = plt.Figure(figsize=(6,2), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=self.formula_label)
        canvas.get_tk_widget().grid(row=0, column=0)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.text(0.05, 0.4, formula_str, fontsize=20)
        canvas.draw()

        label_text = """
        Explain what this formula means here \n
        Motivate why you extended it with max in the upper part \n
        keep it simple here
        """
        self.formula_description = tk.Label(self.master_frame, fg='black', text=label_text)
        self.formula_description.grid(row=1, column=0)
        # endregion

        # region PARAMETERS FRAME
        self.parameters_frame = tk.LabelFrame(self.master_frame, text='PARAMETERS', padx=5, pady=5, width=30)
        self.parameters_frame.grid(row=2, column=0)

        # GET ALL IMPORTANT INFO FOR PARAMS FRAME
        self.calculation_option_var = tk.IntVar(self.master_frame, self.get_state()['W_type'])
        n_headers = 3
        table_color = 'white'
        n_rows, n_columns = self.df_parameters.shape[0], self.df_parameters.shape[1]
        self.n_columns_in_parameters_frame = n_columns
        df_keys = list(self.df_parameters.keys())  #weights, thresholds etc.
        widths = [85 if df_keys[j].startswith('thresh') or df_keys[j].startswith('weight') else 200 for j in range(n_columns)] #more space for reasoning less for w, t

        # ADD HEADERS(2 rows of buttons and titles)
        for i in range(n_headers):
            for j in range(n_columns):
                frame = tk.Frame(self.parameters_frame, width=widths[j])
                frame.grid(row=i, column=j, sticky='news')

                if i == 0 and j == 1:
                    self.__add_reset_weights_button()
                elif i == 0 and j == 2:
                    self.__add_calc_ai_weights_button()
                elif i == 0 and j == 3:
                    self.__add_reset_T1_button()
                elif i == 0 and j == 4:
                    self.__add_reset_T2_button()

                elif i == 1 and j == 1:
                    self.__add_fixed_weights_radio()
                elif i == 1 and j == 2:
                    self.__add_ai_weights_radio()

                elif i == 2:
                    column_name = list(self.df_parameters.keys())[j]
                    value = column_name.upper().replace('_', ' ')
                    tk.Label(frame, text=value).grid(row=0, column=0, sticky='news')

        # SET UP SCROLL VIEW    Frame(canvas(scrollview(frame(mini-frame)))))
        # Create a frame for the canvas with non-zero row&column weights
        frame_canvas = tk.Frame(self.parameters_frame)
        frame_canvas.grid(row=n_headers, column=0, pady=(5, 0), sticky='nw', columnspan=n_columns)
        frame_canvas.grid_rowconfigure(0, weight=1)
        frame_canvas.grid_columnconfigure(0, weight=1)
        # Set grid_propagate to False to allow 5-by-5 buttons resizing later
        frame_canvas.grid_propagate(False)

        # Add a canvas in that frame
        self.canvas = tk.Canvas(frame_canvas, bg="yellow")
        self.canvas.grid(row=0, column=0, sticky="news")

        # Link a scrollbar to the canvas
        vsb = tk.Scrollbar(frame_canvas, orient="vertical", command=self.canvas.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        self.canvas.configure(yscrollcommand=vsb.set)

        # Create a frame to contain the buttons
        frame_of_frames = tk.Frame(self.canvas, bg="blue")
        self.canvas.create_window((0, 0), window=frame_of_frames, anchor='nw')

        # Add 9-by-5 buttons to the frame
        frames = [[tk.Frame() for _ in range(n_columns)] for _ in range(n_rows)]
        self.fixed_weight_entries = []  #user can change entry can't change label
        self.ai_weight_labels = []
        self.thresh_T1_entries = []
        self.thresh_T2_entries = []

        for i in range(0, n_rows):
            for j in range(0, n_columns):
                # Get info about this frame
                value = self.df_parameters.iloc[i, j]
                if type(value) == str:
                    chars_per_line = 32
                    value = '\n'.join([value[i:i+chars_per_line] for i in range(0, len(value), chars_per_line)]) # Put new line every 35 chars in the value of the frame
                    height_multiplier = value.count('\n') + 1
                else:
                    height_multiplier = 1

                # Set a frame and its contents
                frames[i][j] = tk.Frame(frame_of_frames, width=widths[j], height=20 * height_multiplier, bg=table_color, highlightbackground='black', highlightthickness=1)
                frames[i][j].grid(row=i, column=j, sticky='news')
                frames[i][j].grid_propagate(False)

                if df_keys[j] in ['weight_fixed', 'thresh_T1', 'thresh_T2']:
                    # Add entries for fixed weights weights
                    w_entry = tk.Entry(frames[i][j], fg='black', width=widths[j] - 5, bg=table_color)
                    w_entry.insert(tk.END, str(value))
                    w_entry.grid(row=0, column=0)

                    if df_keys[j] == 'weight_fixed':
                        self.fixed_weight_entries.append(w_entry)
                    elif df_keys[j] == 'thresh_T1':
                        self.thresh_T1_entries.append(w_entry)
                    elif df_keys[j] == 'thresh_T2':
                        self.thresh_T2_entries.append(w_entry)
                else:
                    # Add labels for anything else
                    label = tk.Label(frames[i][j], text=value, bg=table_color)
                    label.grid(row=0, column=0, sticky='news')
                    if df_keys[j] == 'weight_ai':
                        self.ai_weight_labels.append(label)

        # Update buttons frames idle tasks to let tkinter calculate buttons sizes
        frame_of_frames.update_idletasks()

        # Resize the canvas frame to show exactly 5-by-5 buttons and the scrollbar
        first5columns_width = sum([frames[0][j].winfo_width() for j in range(len(frames[0]))])
        first5rows_height = sum([frames[i][0].winfo_height() for i in range(0, 3)])
        frame_canvas.config(width=first5columns_width + vsb.winfo_width(),
                            height=first5rows_height)

        # Set the canvas scrolling region
        self.canvas.bind_all('<MouseWheel>', lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        # endregion

        # region INFO AND SAVE BOARD
        # Set info panel
        self.info_board = tk.Label(self.master_frame, text='')
        self.info_board.grid(row=n_headers+1, column=0)

        # Set a saving button
        self.save_button = tk.Button(self.master_frame, text='SAVE', cursor='hand2')
        self.save_button.bind('<Button-1>', self.__on_save_button_clicked)
        self.save_button.grid(row=n_headers+1, column=1)

        # Set up disappearing progress bar
        self.progressbar = ttk.Progressbar(self.master_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progressbar.grid(row=n_headers + 2, column=0, columnspan=2, sticky='news')
        self.progressbar.grid_remove()
        # endregion



    def __on_save_button_clicked(self, event):
        weight_fixed = [widget.get() for widget in self.fixed_weight_entries]
        weight_ai = [widget['text'] for widget in self.ai_weight_labels]
        t1 = [t1.get() for t1 in self.thresh_T1_entries]
        t2 = [t2.get() for t2 in self.thresh_T2_entries]
        try:
            for w in weight_fixed+weight_ai+t1+t2:
                float(w)
            self.info_board.config(text='')
        except Exception:
            self.info_board.config(text='NOT ALL WEIGHTS ARE NUMBERS! TRY AGAIN!', fg='red')
            return
        weight_fixed = np.array(weight_fixed)
        weight_ai = np.array(weight_ai)
        t1 = np.array(t1)
        t2 = np.array(t2)

        # Save new results in csv
        self.__save_user_weights(weight_fixed, weight_ai, t1, t2)

        # Send state
        weights = weight_fixed if self.calculation_option_var.get() == 0 else weight_ai
        self.set_state(weights, t1, t2, self.calculation_option_var.get())

    def __save_user_weights(self, weight_fixed, weight_ai, t1, t2):
        # Update the values on the dataset
        self.df_parameters['weight_fixed'] = weight_fixed
        self.df_parameters['thresh_T1'] = t1
        self.df_parameters['thresh_T2'] = t2
        self.df_parameters['weight_ai'] = weight_ai

        # Copy and join datasets (updates the default values, because they were dropped from original dataset)
        df = self.df_parameters.copy(deep=True)
        df_default = self.df_default.copy(deep=True)
        df_to_save = df.join(df_default)

        # Save the new dataset of values
        df_to_save.to_csv(parameters_file, index=False)

    def __add_reset_weights_button(self):
        self.reset_weights_button = tk.Button(self.parameters_frame, text='DEFAULT', cursor='hand2')
        self.reset_weights_button.bind('<Button-1>', self.__reset_weights_button_clicked)
        self.reset_weights_button.grid(row=0, column=1)

    def __add_calc_ai_weights_button(self):
        self.calc_ai_weights_button = tk.Button(self.parameters_frame, text='CALCULATE', cursor='hand2')
        self.calc_ai_weights_button.bind('<Button-1>', self.__calc_ai_weights_button_clicked)
        self.calc_ai_weights_button.grid(row=0, column=2)

    def __add_reset_T1_button(self):
        self.reset_T1_button = tk.Button(self.parameters_frame, text='DEFAULT', cursor='hand2')
        self.reset_T1_button.bind('<Button-1>', self.__reset_T1_button_clicked)
        self.reset_T1_button.grid(row=0, column=3)

    def __add_reset_T2_button(self):
        self.reset_T2_button = tk.Button(self.parameters_frame, text='DEFAULT', cursor='hand2')
        self.reset_T2_button.bind('<Button-1>', self.__reset_T2_button_clicked)
        self.reset_T2_button.grid(row=0, column=4)

    def __reset_T1_button_clicked(self, event):
        t1 = self.df_default['thresh_T1_default'].to_numpy()
        for i, entry in enumerate(self.thresh_T1_entries):
            entry.delete(0, tk.END)
            entry.insert(0, str(t1[i]))

    def __reset_T2_button_clicked(self, event):
        t2 = self.df_default['thresh_T2_default'].to_numpy()
        for i, entry in enumerate(self.thresh_T2_entries):
            entry.delete(0, tk.END)
            entry.insert(0, str(t2[i]))

    def __add_fixed_weights_radio(self):
        tk.Radiobutton(self.parameters_frame, text='', variable=self.calculation_option_var, value=0).grid(row=1, column=1)

    def __add_ai_weights_radio(self):
        tk.Radiobutton(self.parameters_frame, text='', variable=self.calculation_option_var, value=1).grid(row=1, column=2)

    #separates default from user values
    def __read_table(self, parameters_file_path: str):
        df = pd.read_csv(parameters_file_path)
        default_columns = [c for c in df.columns if c.endswith('default')]
        df_default = df[default_columns]
        df = df.drop(columns=default_columns)
        return df_default, df

    def __reset_weights_button_clicked(self, event):
        W_fixed = self.df_default['weight_fixed_default'].to_numpy()
        for i, entry in enumerate(self.fixed_weight_entries):
            entry.delete(0, tk.END)
            entry.insert(0, str(W_fixed[i]))

    def __calc_ai_weights_button_clicked(self, event):
        # Get the data (and set thresholds)
        data = pd.read_csv('ai/ai-data.csv')
        #check if all packages are unique
        if len(set(data['package_name'])) != data.shape[0]:
            duplicate_indexes = data[data.duplicated(subset=['package_name'], keep=False)].index
            raise ValueError(f"The same package is mentioned multiple times on rows: {duplicate_indexes.values + 1}")
        data = data.drop(columns=['package_name'])

        # Train and test the model
        model = WeightCalculatorAI(load=False, dim=data.shape[1]-1, T=(self.df_parameters.thresh_T1.to_numpy(), self.df_parameters.thresh_T2.to_numpy()), path='')

        # Set progress bar
        self.progressbar.grid()

        # Train model
        model.evaluate(data)
        model.fit(data, epochs=100, es_patience=100, progress_bar=self.progressbar, master_frame=self.master_frame)
        model.save_model()
        model.evaluate(data)

        # Delete progress bar
        self.progressbar.grid_remove()

        # Update weights in the table
        W_ai = model.get_weights()
        for i, label in enumerate(self.ai_weight_labels):
            label.config(text=str(W_ai[i]))

    def run(self):
        self.master_frame.mainloop()

def open_config_gui(get_state, set_state):
    window = ConfigGUI(get_state, set_state)
    window.run()
import os
import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import fastf1
import threading

cache_dir = "fastf1_cache"
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

current_year = pd.Timestamp.now().year

class LapTimeTrendsVisualiser:
    def __init__(self, root):
        self.root = root
        self.root.title("Lap Time Trends Visualiser")
        self.root.geometry("1000x800")

        self.df = pd.DataFrame()

        self.selected_season = tk.IntVar(value=current_year)
        self.selected_event = tk.StringVar()
        self.selected_session = tk.StringVar(value="Q")
        self.selected_drivers = []

        self.seasons = self.get_available_seasons()
        self.events = []
        self.sessions = ["FP1", "FP2", "FP3", "Q", "R"]
        self.drivers = []

        self.setup_ui()

    def get_available_seasons(self):
        available_seasons = []

        for year in range(2018, current_year + 2):
            try:
                schedule = fastf1.get_event_schedule(year)
                if not schedule.empty:
                    available_seasons.append(year)
            except Exception as e:
                print(f"Error fetching schedule for {year}: {e}")

        return available_seasons

    def setup_ui(self):
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(side=tk.TOP, fill=tk.X, pady=10, padx=10)

        ttk.Label(controls_frame, text="Season:").pack(side=tk.LEFT, padx=5)
        season_dropdown = ttk.Combobox(
            controls_frame, values=self.seasons, textvariable=self.selected_season, state="readonly"
        )
        season_dropdown.pack(side=tk.LEFT, padx=5)
        season_dropdown.bind("<<ComboboxSelected>>", lambda e: self.run_in_thread(self.update_events))

        ttk.Label(controls_frame, text="Event:").pack(side=tk.LEFT, padx=5)
        self.event_dropdown = ttk.Combobox(
            controls_frame, values=self.events, textvariable=self.selected_event, state="readonly"
        )
        self.event_dropdown.pack(side=tk.LEFT, padx=5)
        self.event_dropdown.bind("<<ComboboxSelected>>", lambda e: self.run_in_thread(self.update_drivers))

        ttk.Label(controls_frame, text="Session:").pack(side=tk.LEFT, padx=5)
        session_dropdown = ttk.Combobox(
            controls_frame, values=self.sessions, textvariable=self.selected_session, state="readonly"
        )
        session_dropdown.pack(side=tk.LEFT, padx=5)

        ttk.Label(controls_frame, text="Drivers:").pack(side=tk.LEFT, padx=5)
        self.driver_listbox = tk.Listbox(
            controls_frame, selectmode=tk.MULTIPLE, height=5, exportselection=0
        )
        self.driver_listbox.pack(side=tk.LEFT, padx=5, fill=tk.Y)

        fetch_button = ttk.Button(controls_frame, text="Fetch and Plot Lap Times", command=lambda: self.run_in_thread(self.fetch_and_plot))
        fetch_button.pack(side=tk.LEFT, padx=10)

        self.loading_label = ttk.Label(self.root, text="", foreground="red")
        self.loading_label.pack()

        self.plot_frame = ttk.Frame(self.root)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def update_events(self):
        season = self.selected_season.get()
        self.set_loading("Loading events...")
        try:
            schedule = fastf1.get_event_schedule(season)
            self.events = schedule['EventName'].tolist()
            self.event_dropdown['values'] = self.events
            if self.events:
                self.event_dropdown.current(0)
                self.update_drivers()
        except Exception as e:
            print(f"Error fetching events: {e}")
            self.events = []
        finally:
            self.set_loading("")

    def update_drivers(self):
        season = self.selected_season.get()
        event_name = self.selected_event.get()
        self.set_loading("Loading drivers...")
        try:
            schedule = fastf1.get_event_schedule(season)
            event_round = schedule[schedule['EventName'] == event_name]['RoundNumber'].values[0]
            session = fastf1.get_session(season, event_round, self.selected_session.get())
            session.load()
            self.drivers = session.drivers
            self.driver_listbox.delete(0, tk.END)
            for driver in self.drivers:
                self.driver_listbox.insert(tk.END, driver)
        except Exception as e:
            print(f"Error fetching drivers: {e}")
            self.drivers = []
        finally:
            self.set_loading("")

    def fetch_and_plot(self):
        season = self.selected_season.get()
        event_name = self.selected_event.get()
        session_type = self.selected_session.get()

        selected_indices = self.driver_listbox.curselection()
        self.selected_drivers = [self.drivers[i] for i in selected_indices]

        if not event_name or not self.selected_drivers:
            print("Please select an event and at least one driver.")
            return

        self.set_loading("Fetching lap times...")
        self.fetch_data(season, event_name, session_type, self.selected_drivers)
        if not self.df.empty:
            self.root.after(0, self.plot_lap_times)
        else:
            self.set_loading("No lap data available.")
        self.set_loading("")

    def fetch_data(self, season, event_name, session_type, drivers):
        """Fetch lap time data for the selected event, session, and drivers."""
        try:
            schedule = fastf1.get_event_schedule(season)
            event_round = schedule[schedule['EventName'] == event_name]['RoundNumber'].values[0]

            session = fastf1.get_session(season, event_round, session_type)
            session.load()

            print(f"Session loaded successfully: {session}")
            print(f"Drivers in session: {session.drivers}")

            lap_data = {}
            for driver in drivers:
                driver_laps = session.laps.pick_drivers(driver)
                print(f"Laps for driver {driver}: {driver_laps}")

                valid_laps = driver_laps[driver_laps["LapTime"].notna()]
                if not valid_laps.empty:
                    valid_laps = valid_laps[["LapNumber", "LapTime"]]
                    valid_laps["LapTime"] = valid_laps["LapTime"].dt.total_seconds()
                    lap_data[driver] = valid_laps.set_index("LapNumber")["LapTime"]
                else:
                    print(f"No valid lap times for driver {driver}")

            if not lap_data:
                print("No valid lap data found for selected drivers.")
                self.df = pd.DataFrame()  # Clear DataFrame
                return

            self.df = pd.DataFrame(lap_data).reset_index().rename(columns={"index": "Lap"})

            print(f"Combined lap data:\n{self.df}")

        except Exception as e:
            print(f"Error fetching data: {e}")
            self.df = pd.DataFrame()

    def plot_lap_times(self):
        if "LapNumber" not in self.df.columns or self.df.empty:
            print("No lap data available to plot.")
            self.set_loading("No lap data available.")
            return

        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(10, 5))
        for column in self.df.columns[1:]:
            series = self.df.set_index("LapNumber")[column].interpolate()
            ax.plot(series.index, series.values, label=column, marker="o")
       
        ax.set_title(f"Lap Time Trends ({', '.join(self.selected_drivers)})")
        ax.set_xlabel("LapNumber")
        ax.set_ylabel("Lap Time (s)")
        ax.legend()
        ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas.draw()

    def set_loading(self, message):
        self.loading_label.config(text=message)
        self.root.update()

    def run_in_thread(self, target):
        thread = threading.Thread(target=target)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = LapTimeTrendsVisualiser(root)
    root.mainloop()

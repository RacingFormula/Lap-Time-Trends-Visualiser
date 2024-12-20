import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class LapTimeTrendsVisualiser:
    def __init__(self, root):
        self.root = root
        self.root.title("Lap Time Trends Visualiser")
        self.root.geometry("800x600")

        # Example lap time data
        self.lap_data = {
            "Lap": list(range(1, 11)),
            "Driver 1": [75.3, 74.8, 74.9, 75.1, 75.0, 74.7, 75.2, 74.6, 74.8, 74.9],
            "Driver 2": [76.1, 75.8, 75.7, 75.9, 76.0, 75.6, 75.4, 75.7, 75.8, 75.5],
        }
        self.df = pd.DataFrame(self.lap_data)

        # UI Setup
        self.setup_ui()

    def setup_ui(self):
        # Frame for Controls
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(side=tk.TOP, fill=tk.X, pady=10, padx=10)

        # Plot Button
        plot_button = ttk.Button(controls_frame, text="Plot Lap Times", command=self.plot_lap_times)
        plot_button.pack(side=tk.LEFT, padx=5)

        # Quit Button
        quit_button = ttk.Button(controls_frame, text="Quit", command=self.root.quit)
        quit_button.pack(side=tk.RIGHT, padx=5)

        # Canvas for Plot
        self.plot_frame = ttk.Frame(self.root)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def plot_lap_times(self):
        # Clear previous plots
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        # Create Figure
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(self.df["Lap"], self.df["Driver 1"], label="Driver 1", marker="o")
        ax.plot(self.df["Lap"], self.df["Driver 2"], label="Driver 2", marker="s")
        ax.set_title("Lap Time Trends")
        ax.set_xlabel("Lap")
        ax.set_ylabel("Lap Time (s)")
        ax.legend()
        ax.grid(True)

        # Embed Matplotlib Plot into Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = LapTimeTrendsVisualiser(root)
    root.mainloop()

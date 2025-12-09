import customtkinter as ctk

ctk.set_appearance_mode("dark")      # "light" or "dark"
ctk.set_default_color_theme("blue")  # can be "green", "dark-blue", etc.

# CUSTOM CIRCULAR PROGRESS BAR
class CircularProgress(ctk.CTkFrame):
    def __init__(self, master, size=120, thickness=10, progress=0.0, progress_color="#1f6aa5", **kwargs):
        super().__init__(master, fg_color="#1b1b1b", **kwargs)

        self.size = size
        self.thickness = thickness
        self.progress = max(0, min(1, progress))
        self.progress_color = progress_color

        # Use parent's fg_color if needed
        self.canvas = ctk.CTkCanvas(self, width=size, height=size, bg=self.cget("fg_color"), highlightthickness=0)
        self.canvas.pack()

        self.text_id = None
        self.draw()

    def set_progress(self, value: float):
        """Update progress value (0.0 to 1.0)"""
        self.progress = max(0, min(1, value))
        self.update_draw()

    def draw(self):
        """Initial draw of canvas items"""
        radius = self.size / 2
        start_angle = -90
        extent_angle = self.progress * 360

        # Background ring
        self.bg_ring = self.canvas.create_oval(
            self.thickness, self.thickness,
            self.size - self.thickness, self.size - self.thickness,
            width=self.thickness,
            outline="#444444"
        )

        # Progress arc
        self.progress_arc = self.canvas.create_arc(
            self.thickness, self.thickness,
            self.size - self.thickness, self.size - self.thickness,
            start=start_angle,
            extent=extent_angle,
            style="arc",
            width=self.thickness,
            outline=self.progress_color
        )

        # Center text
        percent_text = f"{int(self.progress * 100)}%"
        self.text_id = self.canvas.create_text(
            radius, radius,
            text=percent_text,
            fill="white",
            font=("Arial", 16, "bold")
        )

    def update_draw(self):
        """Update the progress arc and text without redrawing everything"""
        self.canvas.itemconfig(self.progress_arc, extent=self.progress * 360)
        self.canvas.itemconfig(self.text_id, text=f"{int(self.progress * 100)}%")


# -------------------------------------------------------------------
# MAIN APPLICATION
# -------------------------------------------------------------------
class HabitTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart Habit Tracker")
        self.geometry("900x600")
        self.configure(fg_color="#1b1b1b")

        self.create_layout()

    # -------------------------------------------------------------------
    # LAYOUT
    # -------------------------------------------------------------------
    def create_layout(self):
        self.create_sidebar()
        self.create_main_content()

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        title = ctk.CTkLabel(self.sidebar, text="Habits", font=("Arial", 22, "bold"))
        title.pack(pady=20)

        ctk.CTkButton(self.sidebar, text="Dashboard").pack(pady=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Add Habit").pack(pady=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Settings", command=self.open_settings).pack(pady=10, fill="x")


        ctk.CTkLabel(self.sidebar, text="Appearance Mode:").pack(pady=20)
        self.mode_switch = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark"], command=self.change_mode)
        self.mode_switch.pack(pady=5)
        self.mode_switch.set(ctk.get_appearance_mode().capitalize())


# Settings functionality
        
    def open_settings(self):
        # Clear current main content
        for widget in self.main.winfo_children():
            widget.destroy()

        # Header
        header = ctk.CTkLabel(self.main, text="Settings", font=("Arial", 28, "bold"))
        header.pack(pady=20)

        # Example Setting: Default Progress Increment
        ctk.CTkLabel(self.main, text="Default Progress Increment (%)", font=("Arial", 16)).pack(pady=10)
        self.progress_increment = ctk.CTkSlider(self.main, from_=1, to=50, number_of_steps=49)
        self.progress_increment.set(10)  # default 10%
        self.progress_increment.pack(pady=10)

        # Example Setting: Reset All Habits Button
        ctk.CTkButton(self.main, text="Reset All Habits", command=self.reset_all_habits).pack(pady=20)


    def reset_all_habits(self):
        for card in self.cards_frame.winfo_children():
            for widget in card.winfo_children():
                if isinstance(widget, CircularProgress):
                    widget.set_progress(0)
                elif isinstance(widget, ctk.CTkLabel):
                    # Update text too
                    lines = widget.cget("text").split("\n")
                    if "Progress" in lines[-1]:
                        widget.configure(text=f"{lines[0]}\nProgress: 0%")



    def create_main_content(self):
        self.main = ctk.CTkFrame(self, corner_radius=0)
        self.main.pack(side="left", expand=True, fill="both")

        header = ctk.CTkLabel(self.main, text="Daily Dashboard", font=("Arial", 28, "bold"))
        header.pack(pady=20)

        # Habit Cards Container
        self.cards_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.cards_frame.pack(pady=20)

        # Example Habit Cards
        self.add_habit_card("Drink Water", 0.3)
        self.add_habit_card("Exercise", 0.7)
        self.add_habit_card("Read", 0.5)

    # -------------------------------------------------------------------
    # HABIT CARD
    # -------------------------------------------------------------------
    def add_habit_card(self, habit_name, progress):
        card = ctk.CTkFrame(self.cards_frame)
        card.pack(pady=10, padx=10, fill="x")

        # Left: Circular progress
        cp = CircularProgress(card, size=90, thickness=8, progress=progress)
        cp.pack(side="left", padx=15, pady=15)

        # Right: Habit name & progress
        label = ctk.CTkLabel(card, text=f"{habit_name}\nProgress: {int(progress*100)}%", font=("Arial", 18))
        label.pack(side="left", padx=10)

        # Button to simulate progress update
        btn = ctk.CTkButton(card, text="+10%", width=80, command=lambda cp=cp: self.increase_progress(cp))
        btn.pack(side="right", padx=20)

    def increase_progress(self, cp_widget):
        new_val = min(1.0, cp_widget.progress + 0.1)
        cp_widget.set_progress(new_val)

    # -------------------------------------------------------------------
    # APPEARANCE MODE
    # -------------------------------------------------------------------
    def change_mode(self, mode):
        ctk.set_appearance_mode(mode.lower())


# Run application
if __name__ == "__main__":
    app = HabitTrackerApp()
    app.mainloop()

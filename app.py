import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")



# Circular Progress Widget

class CircularProgress(ctk.CTkFrame):
    def __init__(self, master, size=120, thickness=10, progress=0.0, progress_color="#1f6aa5", **kwargs):
        super().__init__(master, fg_color="#1b1b1b", **kwargs)

        self.size = size
        self.thickness = thickness
        self.progress = max(0, min(1, progress))
        self.progress_color = progress_color

        self.canvas = ctk.CTkCanvas(
            self, width=size, height=size, bg=self.cget("fg_color"), highlightthickness=0
        )
        self.canvas.pack()

        self.text_id = None
        self.draw()

    def set_progress(self, value: float):
        self.progress = max(0, min(1, value))
        self.update_draw()

    def draw(self):
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
        self.text_id = self.canvas.create_text(
            radius, radius,
            text=f"{int(self.progress*100)}%",
            fill="white",
            font=("Arial", 16, "bold")
        )

    def update_draw(self):
        self.canvas.itemconfig(self.progress_arc, extent=self.progress * 360)
        self.canvas.itemconfig(self.text_id, text=f"{int(self.progress*100)}%")


# -------------------------------
# Habit Card
# -------------------------------
class HabitCard(ctk.CTkFrame):
    def __init__(self, master, name, progress=0.0, increment=0.1, **kwargs):
        super().__init__(master, **kwargs)
        self.habit_name = name
        self.increment = increment
        self.progress_widget = CircularProgress(self, size=90, thickness=8, progress=progress)
        self.progress_widget.pack(side="left", padx=15, pady=15)

        # Label
        self.label = ctk.CTkLabel(
            self,
            text=f"{self.habit_name}\nProgress: {int(progress*100)}%",
            font=("Arial", 18)
        )
        self.label.pack(side="left", padx=10)

        # Increment button
        self.btn = ctk.CTkButton(self, text=f"+{int(self.increment*100)}%", width=80, command=self.increase_progress)
        self.btn.pack(side="right", padx=20)

    def increase_progress(self):
        new_val = min(1.0, self.progress_widget.progress + self.increment)
        self.progress_widget.set_progress(new_val)
        self.update_label()

    def reset_progress(self):
        self.progress_widget.set_progress(0)
        self.update_label()

    def update_label(self):
        self.label.configure(text=f"{self.habit_name}\nProgress: {int(self.progress_widget.progress*100)}%")


# -------------------------------
# Main App
# -------------------------------
class HabitTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart Habit Tracker")
        self.geometry("900x600")
        self.configure(fg_color="#1b1b1b")

        # Default increment for habits
        self.progress_increment = 0.1

        self.create_layout()

    # ---------------------------
    # Layout
    # ---------------------------
    def create_layout(self):
        self.create_sidebar()
        self.create_main_content()

    # Sidebar
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        title = ctk.CTkLabel(self.sidebar, text="Habits", font=("Arial", 22, "bold"))
        title.pack(pady=20)

        ctk.CTkButton(self.sidebar, text="Dashboard", command=self.create_main_content).pack(pady=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Add Habit", command=self.add_habit_prompt).pack(pady=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Settings", command=self.open_settings).pack(pady=10, fill="x")

        ctk.CTkLabel(self.sidebar, text="Appearance Mode:").pack(pady=20)
        self.mode_switch = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark"], command=self.change_mode)
        self.mode_switch.pack(pady=5)
        self.mode_switch.set(ctk.get_appearance_mode().capitalize())

    # Main Content
    def create_main_content(self):
        # Clear main content if exists
        if hasattr(self, 'main'):
            self.main.destroy()

        self.main = ctk.CTkFrame(self, corner_radius=0)
        self.main.pack(side="left", expand=True, fill="both")

        header = ctk.CTkLabel(self.main, text="Daily Dashboard", font=("Arial", 28, "bold"))
        header.pack(pady=20)

        # Scrollable habit list
        self.cards_frame = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self.cards_frame.pack(pady=20, padx=20, expand=True, fill="both")

        # Example habits
        self.habit_cards = []
        self.add_habit_card("Drink Water", 0.3)
        self.add_habit_card("Exercise", 0.7)
        self.add_habit_card("Read", 0.5)

    # ---------------------------
    # Habit management
    # ---------------------------
    def add_habit_card(self, name, progress=0.0):
        card = HabitCard(self.cards_frame, name, progress=progress, increment=self.progress_increment)
        card.pack(pady=10, fill="x")
        self.habit_cards.append(card)

    def add_habit_prompt(self):
        # Simple dialog prompt for new habit
        from tkinter import simpledialog
        name = simpledialog.askstring("New Habit", "Enter habit name:")
        if name:
            self.add_habit_card(name, progress=0.0)

    # ---------------------------
    # Settings
    # ---------------------------
    def open_settings(self):
        if hasattr(self, 'main'):
            self.main.destroy()

        self.main = ctk.CTkFrame(self, corner_radius=0)
        self.main.pack(side="left", expand=True, fill="both")

        header = ctk.CTkLabel(self.main, text="Settings", font=("Arial", 28, "bold"))
        header.pack(pady=20)

        # Progress increment
        ctk.CTkLabel(self.main, text="Default Progress Increment (%)", font=("Arial", 16)).pack(pady=10)
        self.increment_slider = ctk.CTkSlider(self.main, from_=1, to=50, number_of_steps=49, command=self.update_increment)
        self.increment_slider.set(int(self.progress_increment * 100))
        self.increment_slider.pack(pady=10)

        # Reset all habits
        ctk.CTkButton(self.main, text="Reset All Habits", command=self.reset_all_habits).pack(pady=20)

    def update_increment(self, value):
        self.progress_increment = value / 100
        # Update all existing habit cards increment
        for card in self.habit_cards:
            card.increment = self.progress_increment
            card.btn.configure(text=f"+{int(self.progress_increment*100)}%")

    def reset_all_habits(self):
        for card in self.habit_cards:
            card.reset_progress()

    # ---------------------------
    # Appearance Mode
    # ---------------------------
    def change_mode(self, mode):
        ctk.set_appearance_mode(mode.lower())


# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app = HabitTrackerApp()
    app.mainloop()

import customtkinter as ctk
import math

ctk.set_appearance_mode("dark")      # "light" or "dark"
ctk.set_default_color_theme("blue")  # can be "green", "dark-blue", etc.


# -------------------------------------------------------------------
# CUSTOM CIRCULAR PROGRESS BAR (drawn with CTkCanvas)
# -------------------------------------------------------------------
class CircularProgress(ctk.CTkFrame):
    def __init__(self, master, size=120, thickness=10, progress=0.0, text="0%", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.size = size
        self.thickness = thickness
        self.progress = progress

        self.canvas = ctk.CTkCanvas(self, width=size, height=size, bg=self._fg_color, highlightthickness=0)
        self.canvas.pack()

        self.text_id = None
        self.draw()

    def set_progress(self, value: float):
        self.progress = max(0, min(1, value))
        self.draw()

    def draw(self):
        self.canvas.delete("all")

        radius = self.size / 2
        start = -90
        extent = self.progress * 360

        # Background ring
        self.canvas.create_oval(
            self.thickness, self.thickness,
            self.size - self.thickness, self.size - self.thickness,
            width=self.thickness,
            outline="#444444"
        )

        # Progress ring
        self.canvas.create_arc(
            self.thickness, self.thickness,
            self.size - self.thickness, self.size - self.thickness,
            start=start,
            extent=extent,
            style="arc",
            width=self.thickness,
            outline="#1f6aa5"
        )

        # Center text
        percent_text = f"{int(self.progress * 100)}%"
        self.text_id = self.canvas.create_text(
            radius, radius,
            text=percent_text,
            fill="white",
            font=("Arial", 16, "bold")
        )


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

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        title = ctk.CTkLabel(self.sidebar, text="Habits", font=("Arial", 22, "bold"))
        title.pack(pady=20)

        ctk.CTkButton(self.sidebar, text="Dashboard").pack(pady=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Add Habit").pack(pady=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Settings").pack(pady=10, fill="x")

        # Appearance mode switch
        ctk.CTkLabel(self.sidebar, text="Appearance Mode:").pack(pady=20)
        mode_switch = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark"], command=self.change_mode)
        mode_switch.pack(pady=5)

        # Main Content Panel
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
    # Habit Card (UI component)
    # -------------------------------------------------------------------
    def add_habit_card(self, habit_name, progress):

        card = ctk.CTkFrame(self.cards_frame)
        card.pack(pady=10, padx=10, fill="x")

        # Left: Circular progress
        cp = CircularProgress(card, size=90, thickness=8, progress=progress)
        cp.pack(side="left", padx=15, pady=15)

        # Right: Text info
        label = ctk.CTkLabel(card, text=f"{habit_name}\nProgress: {int(progress*100)}%", 
                             font=("Arial", 18))
        label.pack(side="left", padx=10)

        # Button to simulate an update
        btn = ctk.CTkButton(card, text="+10%", width=80, 
                            command=lambda cp=cp: self.increase_progress(cp))
        btn.pack(side="right", padx=20)

    def increase_progress(self, cp_widget):
        new_val = min(1.0, cp_widget.progress + 0.1)
        cp_widget.set_progress(new_val)

    # -------------------------------------------------------------------
    # Appearance mode handling
    # -------------------------------------------------------------------
    def change_mode(self, mode):
        ctk.set_appearance_mode(mode.lower())


# Run app
if __name__ == "__main__":
    app = HabitTrackerApp()
    app.mainloop()

"""
Smart Habit Tracker - Refactored with Phase 1 features (quick DateTimeDisplay fix):
- Add / Delete habits
- Edit habit name
- Default starting progress 0%
- Global increment configurable in Settings
- Persistence to JSON (habits.json) - loads on startup, saves on change
- Stable page system (sidebar + pages)
- Uses user's DateTimeDisplay which packs its own label internally (do NOT call .pack() on it)
"""

import json
import os
import datetime
import customtkinter as ctk
from tkinter import simpledialog, messagebox

# Try to import user's DateTimeDisplay. If missing, provide a simple fallback.
try:
    from date_time import DateTimeDisplay
except Exception:
    # Minimal fallback - shows current date/time and updates every second
    class DateTimeDisplay(ctk.CTkLabel):
        def __init__(self, master, **kwargs):
            super().__init__(master, **kwargs)
            self.configure(font=("Arial", 12))
            self.update_clock()

        def update_clock(self):
            now = datetime.datetime.now().strftime("%A %d %B %Y, %I:%M:%S %p")
            self.configure(text=now)
            try:
                self.after(1000, self.update_clock)
            except Exception:
                pass


# ---------- Appearance defaults ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

HABITS_FILE = "habits.json"


# ---------- Circular progress widget ----------
class CircularProgress(ctk.CTkFrame):
    def __init__(self, master, size=120, thickness=10, progress=0.0, progress_color="#1f6aa5", **kwargs):
        super().__init__(master, fg_color="#1b1b1b", **kwargs)

        self.size = size
        self.thickness = thickness
        self.progress = max(0.0, min(1.0, progress))
        self.progress_color = progress_color

        self.canvas = ctk.CTkCanvas(self, width=size, height=size, bg=self.cget("fg_color"), highlightthickness=0)
        self.canvas.pack()

        self.text_id = None
        self.bg_ring = None
        self.progress_arc = None
        self.draw()

    def set_progress(self, value: float):
        self.progress = max(0.0, min(1.0, value))
        self.update_draw()

    def draw(self):
        self.canvas.delete("all")
        radius = self.size / 2
        start_angle = -90
        extent_angle = self.progress * 360

        self.bg_ring = self.canvas.create_oval(
            self.thickness, self.thickness,
            self.size - self.thickness, self.size - self.thickness,
            width=self.thickness,
            outline="#444444"
        )

        self.progress_arc = self.canvas.create_arc(
            self.thickness, self.thickness,
            self.size - self.thickness, self.size - self.thickness,
            start=start_angle,
            extent=extent_angle,
            style="arc",
            width=self.thickness,
            outline=self.progress_color
        )

        self.text_id = self.canvas.create_text(
            radius, radius,
            text=f"{int(self.progress * 100)}%",
            fill="white",
            font=("Arial", 14, "bold")
        )

    def update_draw(self):
        if self.progress_arc is None:
            self.draw()
            return
        self.canvas.itemconfig(self.progress_arc, extent=self.progress * 360)
        self.canvas.itemconfig(self.text_id, text=f"{int(self.progress * 100)}%")

    def to_dict(self):
        return {"progress": self.progress}


# ---------- HabitCard ----------
class HabitCard(ctk.CTkFrame):
    def __init__(self, master, name, progress=0.0, increment=0.1, save_callback=None, **kwargs):
        super().__init__(master, fg_color="#222222", corner_radius=8, **kwargs)

        self.habit_name = name
        self.increment = increment
        self.save_callback = save_callback  # function to call whenever this card changes

        # Layout: left = progress widget, center = label, right = controls
        self.progress_widget = CircularProgress(self, size=78, thickness=8, progress=progress)
        self.progress_widget.pack(side="left", padx=12, pady=12)

        # Middle label (name + progress)
        self.label = ctk.CTkLabel(self, text=self._label_text(), font=("Arial", 14), anchor="w", justify="left")
        self.label.pack(side="left", expand=True, fill="x", padx=6)

        # Controls frame on the right
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(side="right", padx=8, pady=8)

        # Edit button
        self.edit_btn = ctk.CTkButton(controls, text="Edit", width=64, height=30, command=self.edit_name)
        self.edit_btn.grid(row=0, column=0, padx=(0, 6), pady=2)

        # Delete button
        self.delete_btn = ctk.CTkButton(controls, text="Delete", width=64, height=30, fg_color="#a94442",
                                        hover_color="#c75b5b", command=self.delete_self)
        self.delete_btn.grid(row=0, column=1, padx=(0, 6), pady=2)

        # Increment button (increases by self.increment)
        self.inc_btn = ctk.CTkButton(controls, text=f"+{int(self.increment * 100)}%", width=80, height=30,
                                    command=self.increase_progress)
        self.inc_btn.grid(row=0, column=2, padx=(0, 6), pady=2)

        # Small reset button (reset this habit to 0)
        self.reset_btn = ctk.CTkButton(controls, text="Reset", width=64, height=30, command=self.reset_progress)
        self.reset_btn.grid(row=0, column=3, padx=(0, 0), pady=2)

    def _label_text(self):
        return f"{self.habit_name}\nProgress: {int(self.progress_widget.progress * 100)}%"

    def increase_progress(self):
        new_val = min(1.0, self.progress_widget.progress + self.increment)
        self.progress_widget.set_progress(new_val)
        self.label.configure(text=self._label_text())
        self._trigger_save()

    def reset_progress(self):
        self.progress_widget.set_progress(0.0)
        self.label.configure(text=self._label_text())
        self._trigger_save()

    def edit_name(self):
        new_name = simpledialog.askstring("Edit Habit", "Enter new habit name:", initialvalue=self.habit_name)
        if new_name:
            self.habit_name = new_name.strip()
            self.label.configure(text=self._label_text())
            self._trigger_save()

    def delete_self(self):
        confirm = messagebox.askyesno("Delete habit", f"Are you sure you want to delete '{self.habit_name}'?")
        if confirm:
            # parent should remove from list and widget tree
            parent = self.master
            # destroy the widget and call save via callback
            self.destroy()
            if callable(self.save_callback):
                self.save_callback()

    def set_increment(self, new_increment):
        self.increment = new_increment
        self.inc_btn.configure(text=f"+{int(self.increment * 100)}%")

    def to_dict(self):
        return {
            "name": self.habit_name,
            "progress": self.progress_widget.progress,
            "increment": self.increment
        }

    def _trigger_save(self):
        if callable(self.save_callback):
            try:
                self.save_callback()
            except Exception:
                pass


# ---------- Main App ----------
class HabitTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Habit Tracker")
        self.geometry("900x600")
        self.configure(fg_color="#1b1b1b")

        # default increment (0.1 = 10%)
        self.progress_increment = 0.1

        # in-memory habit card references
        self.habit_cards = []

        # pages container
        self.pages = {}

        # create UI
        self.create_sidebar()
        self.create_pages()

        # load persisted habits (if any)
        self.load_habits()

        # show dashboard by default
        self.show_page("dashboard")

    # ---------------- Sidebar ----------------
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        title = ctk.CTkLabel(self.sidebar, text="Habits", font=("Arial", 22, "bold"))
        title.pack(pady=20)

        ctk.CTkButton(self.sidebar, text="Dashboard", command=lambda: self.show_page("dashboard")).pack(pady=8,
                                                                                                      fill="x")
        ctk.CTkButton(self.sidebar, text="Add Habit", command=self.add_habit_prompt).pack(pady=8, fill="x")
        ctk.CTkButton(self.sidebar, text="Settings", command=lambda: self.show_page("settings")).pack(pady=8, fill="x")

        ctk.CTkLabel(self.sidebar, text="Appearance Mode:").pack(pady=(20, 6))
        self.mode_switch = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark"], command=self.change_mode)
        self.mode_switch.pack(pady=5)
        self.mode_switch.set(ctk.get_appearance_mode().capitalize())

        # Quick "save now" and path label for debugging
        ctk.CTkButton(self.sidebar, text="Save now", command=self.save_habits).pack(pady=(20, 6), fill="x")
        ctk.CTkLabel(self.sidebar, text=f"Data file: {HABITS_FILE}", font=("Arial", 9)).pack(pady=(6, 12))

    # ---------------- Pages ----------------
    def create_pages(self):
        # Dashboard
        dashboard = ctk.CTkFrame(self, corner_radius=0)
        self.pages["dashboard"] = dashboard

        # Date/time display
        # NOTE: Do NOT call .pack() on DateTimeDisplay here because the user's DateTimeDisplay
        # implementation packs its own internal label. We just instantiate it.
        self.datetime_display = DateTimeDisplay(dashboard)

        header = ctk.CTkLabel(dashboard, text="Daily Dashboard", font=("Arial", 28, "bold"))
        header.pack(pady=(6, 12))

        # Scrollable frame for habit cards
        self.cards_frame = ctk.CTkScrollableFrame(dashboard, fg_color="transparent")
        self.cards_frame.pack(padx=20, pady=10, expand=True, fill="both")

        # Settings page
        settings = ctk.CTkFrame(self, corner_radius=0)
        self.pages["settings"] = settings

        header = ctk.CTkLabel(settings, text="Settings", font=("Arial", 28, "bold"))
        header.pack(pady=20)

        ctk.CTkLabel(settings, text="Default Progress Increment (%)", font=("Arial", 16)).pack(pady=10)

        # Slider from 1% to 50%
        self.increment_slider = ctk.CTkSlider(settings, from_=1, to=50, number_of_steps=49, command=self.update_increment)
        self.increment_slider.set(int(self.progress_increment * 100))
        self.increment_slider.pack(pady=6, padx=20, fill="x")

        ctk.CTkButton(settings, text="Reset All Habits", command=self.reset_all_habits).pack(pady=20)

        # Add pages to UI (but don't pack them here; show_page handles packing)
        for p in self.pages.values():
            p.pack_forget()

    def show_page(self, name):
        # Hide all pages
        for page in self.pages.values():
            page.pack_forget()
        # Show requested page
        page = self.pages.get(name)
        if page:
            page.pack(side="left", expand=True, fill="both")

    # ---------------- Habit management ----------------
    def add_habit_card(self, name, progress=0.0, increment=None, save=True):
        if increment is None:
            increment = self.progress_increment
        # Create card - save_callback ensures the app persists when card state changes (like delete)
        card = HabitCard(self.cards_frame, name=name, progress=progress, increment=increment,
                         save_callback=self.save_habits)
        card.pack(pady=8, padx=12, fill="x")
        self.habit_cards.append(card)
        # Ensure increment button text matches current increment
        card.set_increment(increment)
        if save:
            self.save_habits()
        return card

    def add_habit_prompt(self):
        # Ask for name only; start progress defaults to 0%
        name = simpledialog.askstring("New Habit", "Enter habit name:")
        if not name:
            return
        name = name.strip()
        if not name:
            return
        # Add with 0 progress by default
        self.add_habit_card(name=name, progress=0.0, increment=self.progress_increment, save=True)
        # Ensure dashboard is visible after adding
        self.show_page("dashboard")

    def update_increment(self, value):
        # Slider returns float-like; convert to fraction
        try:
            self.progress_increment = float(value) / 100.0
        except Exception:
            self.progress_increment = 0.1
        # Update all existing cards' increments and button text
        for card in list(self.habit_cards):
            try:
                card.set_increment(self.progress_increment)
            except Exception:
                pass
        # Save setting to disk as part of habits file
        self.save_habits()

    def reset_all_habits(self):
        for card in list(self.habit_cards):
            try:
                card.reset_progress()
            except Exception:
                pass
        self.save_habits()
        messagebox.showinfo("Reset", "All habits have been reset to 0%.")

    # ---------------- Persistence (JSON) ----------------
    def save_habits(self):
        # Build list of habit dicts
        data = {
            "meta": {
                "saved_at": datetime.datetime.utcnow().isoformat(),
                "progress_increment": self.progress_increment
            },
            "habits": []
        }

        # Collect from current widget children in the cards_frame
        new_cards = []
        for card in self.habit_cards:
            if getattr(card, "winfo_exists", None) and card.winfo_exists():
                try:
                    data["habits"].append(card.to_dict())
                    new_cards.append(card)
                except Exception:
                    pass
        self.habit_cards = new_cards

        try:
            with open(HABITS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            messagebox.showerror("Save error", f"Failed to save habits to {HABITS_FILE}:\n{e}")

    def load_habits(self):
        if not os.path.exists(HABITS_FILE):
            sample = [
                {"name": "Drink Water", "progress": 0.0, "increment": self.progress_increment},
                {"name": "Exercise", "progress": 0.0, "increment": self.progress_increment},
                {"name": "Read", "progress": 0.0, "increment": self.progress_increment},
            ]
            for s in sample:
                self.add_habit_card(s["name"], progress=s["progress"], increment=s["increment"], save=False)
            self.save_habits()
            return

        try:
            with open(HABITS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            choice = messagebox.askyesno("Load Error", f"Could not read {HABITS_FILE}. Reset to empty?")
            if choice:
                try:
                    os.remove(HABITS_FILE)
                except Exception:
                    pass
                self.load_habits()
            return

        meta = data.get("meta", {})
        inc = meta.get("progress_increment")
        if isinstance(inc, (int, float)):
            self.progress_increment = float(inc)

        try:
            self.increment_slider.set(int(self.progress_increment * 100))
        except Exception:
            pass

        for card in list(self.habit_cards):
            try:
                card.destroy()
            except Exception:
                pass
        self.habit_cards.clear()

        for entry in data.get("habits", []):
            name = entry.get("name", "Untitled")
            progress = float(entry.get("progress", 0.0))
            increment = float(entry.get("increment", self.progress_increment))
            if progress < 0:
                progress = 0.0
            if progress > 1:
                progress = 1.0
            self.add_habit_card(name=name, progress=progress, increment=increment, save=False)

    # ---------------- Utility ----------------
    def change_mode(self, mode):
        ctk.set_appearance_mode(mode.lower())

    # When closing, ensure we save
    def on_close(self):
        self.save_habits()
        self.destroy()


# ---------------- Run App ----------------
if __name__ == "__main__":
    app = HabitTrackerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()

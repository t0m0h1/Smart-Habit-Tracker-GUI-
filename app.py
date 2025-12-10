import json
import os
import datetime
import customtkinter as ctk
from tkinter import simpledialog, messagebox

# ---------- Appearance defaults ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

HABITS_FILE = "habits.json"

# Default categories
DEFAULT_CATEGORIES = [
    "Health",
    "Fitness",
    "Productivity",
    "Learning",
    "Work",
    "Personal",
    "Finance",
    "Chores",
    "Social",
    "Other",
]


# Minimal DateTimeDisplay (keeps behavior simple and always packs)
class DateTimeDisplay(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(font=("Arial", 12))
        self.pack(pady=6)
        self.update_clock()

    def update_clock(self):
        now = datetime.datetime.now().strftime("%A %d %B %Y, %I:%M:%S %p")
        self.configure(text=now)
        try:
            self.after(1000, self.update_clock)
        except Exception:
            pass


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


# ---------- Collapsible Group Frame (for categories) ----------
class CollapsibleGroup(ctk.CTkFrame):
    def __init__(self, master, title, *args, **kwargs):
        super().__init__(master, **kwargs)
        self.title = title
        self.visible = True

        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=4, pady=(6, 0))

        self.toggle_btn = ctk.CTkButton(self.header, text=f"▼ {self.title}", anchor="w", command=self.toggle,
                                        height=28, fg_color="#2a2a2a", corner_radius=6)
        self.toggle_btn.pack(fill="x")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=8, pady=6)

    def toggle(self):
        if self.visible:
            # hide
            for w in self.content.winfo_children():
                w.pack_forget()
            self.content.forget = True
            self.toggle_btn.configure(text=f"▶ {self.title}")
            self.visible = False
        else:
            # show
            for w in self.content.winfo_children():
                w.pack(pady=8, padx=12, fill="x")
            self.toggle_btn.configure(text=f"▼ {self.title}")
            self.visible = True

    def add_widget(self, widget):
        widget.pack(pady=8, padx=12, fill="x")


# ---------- HabitCard ----------
class HabitCard(ctk.CTkFrame):
    def __init__(self, master, app, name, category="Other", progress=0.0, increment=0.1, save_callback=None,
                 **kwargs):
        super().__init__(master, fg_color="#222222", corner_radius=8, **kwargs)

        self.app = app  # reference to main app for operations like remove
        self.habit_name = name
        self.category = category
        self.increment = increment
        self.save_callback = save_callback

        # Layout: left = progress widget, center = label, right = controls
        self.progress_widget = CircularProgress(self, size=78, thickness=8, progress=progress)
        self.progress_widget.pack(side="left", padx=12, pady=12)

        # Middle label (name + category + progress)
        text = self._label_text()
        self.label = ctk.CTkLabel(self, text=text, font=("Arial", 14), anchor="w", justify="left")
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
        return f"{self.habit_name}\nCategory: {self.category}\nProgress: {int(self.progress_widget.progress * 100)}%"

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
        # Build a simple dialog box that allows editing name and category
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Habit")
        dialog.geometry("350x160")

        ctk.CTkLabel(dialog, text="Habit name:").pack(pady=(12, 2))
        name_var = ctk.StringVar(value=self.habit_name)
        name_entry = ctk.CTkEntry(dialog, textvariable=name_var)
        name_entry.pack(padx=12, fill="x")

        ctk.CTkLabel(dialog, text="Category:").pack(pady=(8, 2))
        category_var = ctk.StringVar(value=self.category)
        dropdown_values = list(self.app.categories)
        if "Custom..." not in dropdown_values:
            dropdown_values.append("Custom...")
        cat_dropdown = ctk.CTkOptionMenu(dialog, variable=category_var, values=dropdown_values)
        cat_dropdown.pack(padx=12, fill="x")

        def on_save():
            new_name = name_var.get().strip()
            new_cat = category_var.get()
            if new_cat == "Custom...":
                custom = simpledialog.askstring("Custom category", "Enter new category name:", parent=self)
                if custom:
                    new_cat = custom.strip()
                    if new_cat and new_cat not in self.app.categories:
                        self.app.categories.append(new_cat)
            if new_name:
                self.habit_name = new_name
            self.category = new_cat
            self.label.configure(text=self._label_text())
            self._trigger_save()
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=12)
        ctk.CTkButton(btn_frame, text="Save", command=on_save).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=8)

    def delete_self(self):
        confirm = messagebox.askyesno("Delete habit", f"Are you sure you want to delete '{self.habit_name}'?")
        if confirm:
            try:
                # remove from app list
                if self in self.app.habit_cards:
                    self.app.habit_cards.remove(self)
            except Exception:
                pass
            self.destroy()
            # trigger save from app
            if callable(self.save_callback):
                self.save_callback()

    def set_increment(self, new_increment):
        self.increment = new_increment
        try:
            self.inc_btn.configure(text=f"+{int(self.increment * 100)}%")
        except Exception:
            pass

    def to_dict(self):
        return {
            "name": self.habit_name,
            "progress": self.progress_widget.progress,
            "increment": self.increment,
            "category": self.category,
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

        # categories (persisted)
        self.categories = list(DEFAULT_CATEGORIES)

        # mapping category -> CollapsibleGroup
        self.category_groups = {}

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
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        title = ctk.CTkLabel(self.sidebar, text="Habits", font=("Arial", 22, "bold"))
        title.pack(pady=20)

        ctk.CTkButton(self.sidebar, text="Dashboard", command=lambda: self.show_page("dashboard")).pack(pady=8,
                                                                                                      fill="x")
        ctk.CTkButton(self.sidebar, text="Add Habit", command=self.add_habit_prompt).pack(pady=8, fill="x")
        ctk.CTkButton(self.sidebar, text="Settings", command=lambda: self.show_page("settings")).pack(pady=8,
                                                                                                     fill="x")

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
        self.datetime_display = DateTimeDisplay(dashboard)

        header = ctk.CTkLabel(dashboard, text="Daily Dashboard", font=("Arial", 28, "bold"))
        header.pack(pady=(6, 12))

        # Scrollable frame for habit groups
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
    def _ensure_category_group(self, category):
        # create a group frame for a category if missing
        if category in self.category_groups:
            return self.category_groups[category]
        grp = CollapsibleGroup(self.cards_frame, title=category)
        grp.pack(fill="x", pady=4, padx=4)
        self.category_groups[category] = grp
        return grp

    def add_habit_card(self, name, category="Other", progress=0.0, increment=None, save=True):
        if increment is None:
            increment = self.progress_increment
        # Ensure the category exists in the app categories list
        if category not in self.categories:
            self.categories.append(category)

        # Create card - save_callback ensures the app persists when card state changes (like delete)
        grp = self._ensure_category_group(category)
        card = HabitCard(grp.content, app=self, name=name, category=category, progress=progress, increment=increment,
                         save_callback=self.save_habits)
        grp.add_widget(card)
        self.habit_cards.append(card)
        # Ensure increment button text matches current increment
        card.set_increment(increment)
        if save:
            self.save_habits()
        return card

    def add_habit_prompt(self):
        # Create a small dialog to get name and category
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Habit")
        dialog.geometry("360x200")

        ctk.CTkLabel(dialog, text="Habit name:").pack(pady=(12, 2))
        name_var = ctk.StringVar(value="")
        name_entry = ctk.CTkEntry(dialog, textvariable=name_var)
        name_entry.pack(padx=12, fill="x")

        ctk.CTkLabel(dialog, text="Category:").pack(pady=(12, 2))
        category_var = ctk.StringVar(value=self.categories[0] if self.categories else "Other")
        dropdown_values = list(self.categories)
        if "Custom..." not in dropdown_values:
            dropdown_values.append("Custom...")
        cat_dropdown = ctk.CTkOptionMenu(dialog, variable=category_var, values=dropdown_values)
        cat_dropdown.pack(padx=12, fill="x")

        def on_create():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Missing name", "Please enter a habit name.")
                return
            category = category_var.get()
            if category == "Custom...":
                custom = simpledialog.askstring("Custom category", "Enter new category name:", parent=self)
                if custom:
                    category = custom.strip()
                    if category and category not in self.categories:
                        self.categories.append(category)
            self.add_habit_card(name=name, category=category, progress=0.0, increment=self.progress_increment, save=True)
            dialog.destroy()
            self.show_page("dashboard")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=12)
        ctk.CTkButton(btn_frame, text="Create", command=on_create).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=8)

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
                "progress_increment": self.progress_increment,
                "categories": self.categories,
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
                {"name": "Drink Water", "progress": 0.0, "increment": self.progress_increment, "category": "Health"},
                {"name": "Exercise", "progress": 0.0, "increment": self.progress_increment, "category": "Fitness"},
                {"name": "Read", "progress": 0.0, "increment": self.progress_increment, "category": "Learning"},
            ]
            for s in sample:
                self.add_habit_card(s["name"], category=s.get("category", "Other"), progress=s["progress"],
                                   increment=s["increment"], save=False)
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
                # restart loading (will create sample)
                return self.load_habits()
            return

        meta = data.get("meta", {})
        inc = meta.get("progress_increment")
        cats = meta.get("categories")
        if isinstance(inc, (int, float)):
            self.progress_increment = float(inc)

        if isinstance(cats, list) and cats:
            # merge saved categories, ensuring defaults are present
            for c in cats:
                if c not in self.categories:
                    self.categories.append(c)

        try:
            self.increment_slider.set(int(self.progress_increment * 100))
        except Exception:
            pass

        # Clear any existing UI
        for grp in list(self.category_groups.values()):
            try:
                grp.destroy()
            except Exception:
                pass
        self.category_groups.clear()

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
            category = entry.get("category", "Other")
            if progress < 0:
                progress = 0.0
            if progress > 1:
                progress = 1.0
            self.add_habit_card(name=name, category=category, progress=progress, increment=increment, save=False)

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
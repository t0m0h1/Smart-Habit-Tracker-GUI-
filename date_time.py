from datetime import datetime
import customtkinter as ctk

class DateTimeDisplay:
    def __init__(self, parent, font=("Arial", 16, "bold"), pady=10):
        """
        parent: parent frame to attach the label
        font: font for the label
        pady: padding
        """
        self.parent = parent
        self.label = ctk.CTkLabel(parent, text="", font=font)
        self.label.pack(pady=pady)
        self.update_datetime()

    def update_datetime(self):
        now = datetime.now()
        formatted_time = now.strftime("%A %d %B %Y, %-I:%M %p")  # Tuesday 11 September 2023, 9:44 PM
        self.label.configure(text=formatted_time)
        self.label.after(1000, self.update_datetime)

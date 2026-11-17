
import tkinter as tk
from tkinter import ttk, messagebox

from auth import register_user, login_user
from trips import open_trips_window
from itinerary import open_itinerary_window
from bookings import open_bookings_window

# Import these when the corresponding functions are available
from expenses import open_expenses_window
from reports import open_reports_window
from reminders import open_reminders_window


class TravelEaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TravelEase - Travel Management System")
        self.root.geometry("1100x750")
        self.root.minsize(850, 600)

        self.current_user = None

        self.setup_styles()
        self.show_login()

    def setup_styles(self):
        style = ttk.Style()

        style.configure(
            "Title.TLabel",
            font=("Helvetica", 27, "bold")
        )
        style.configure(
            "Subtitle.TLabel",
            font=("Helvetica", 12)
        )
        style.configure(
            "Primary.TButton",
            font=("Helvetica", 12, "bold"),
            padding=10
        )
        style.configure(
            "Dashboard.TButton",
            font=("Helvetica", 13, "bold"),
            padding=12
        )
        style.configure("TButton", padding=8)
        style.configure("TLabel", font=("Helvetica", 11))

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # ---------------- LOGIN ----------------

    def show_login(self):
        self.current_user = None
        self.clear_screen()
        self.setup_styles()

        container = ttk.Frame(self.root, padding=40)
        container.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(
            container,
            text="✈ TravelEase",
            style="Title.TLabel"
        ).pack(pady=(0, 8))

        ttk.Label(
            container,
            text="Your journey begins here",
            style="Subtitle.TLabel"
        ).pack(pady=(0, 25))

        ttk.Label(container, text="Username").pack(anchor="w")

        self.username_entry = ttk.Entry(container, width=36)
        self.username_entry.pack(pady=(5, 15), ipady=5)

        ttk.Label(container, text="Password").pack(anchor="w")

        self.password_entry = ttk.Entry(
            container,
            width=36,
            show="*"
        )
        self.password_entry.pack(pady=(5, 20), ipady=5)

        self.show_password_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            container,
            text="Show password",
            variable=self.show_password_var,
            command=self.toggle_password
        ).pack(anchor="w", pady=(0, 15))

        ttk.Button(
            container,
            text="Log In",
            style="Primary.TButton",
            command=self.handle_login
        ).pack(fill="x", pady=(0, 10))

        ttk.Button(
            container,
            text="Create Account",
            command=self.show_register
        ).pack(fill="x")

        ttk.Label(
            container,
            text="Plan trips. Manage bookings. Track expenses."
        ).pack(pady=(22, 0))

        self.username_entry.focus_set()
        self.root.bind("<Return>", self.handle_enter)

    def handle_enter(self, event=None):
        if self.current_user is None:
            self.handle_login()

    def toggle_password(self):
        self.password_entry.configure(
            show="" if self.show_password_var.get() else "*"
        )

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Information",
                "Please enter your username and password."
            )
            return

        user = login_user(username, password)

        if user is None:
            messagebox.showerror(
                "Login Failed",
                "Incorrect username or password."
            )
            return

        self.current_user = user
        self.show_dashboard()

    # ---------------- REGISTRATION ----------------

    def show_register(self):
        self.clear_screen()
        self.setup_styles()

        container = ttk.Frame(self.root, padding=40)
        container.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(
            container,
            text="Create Your Account",
            style="Title.TLabel"
        ).pack(pady=(0, 25))

        ttk.Label(container, text="Username").pack(anchor="w")

        self.register_username = ttk.Entry(
            container,
            width=36
        )
        self.register_username.pack(pady=(5, 15), ipady=5)

        ttk.Label(container, text="Password").pack(anchor="w")

        self.register_password = ttk.Entry(
            container,
            width=36,
            show="*"
        )
        self.register_password.pack(pady=(5, 15), ipady=5)

        ttk.Label(
            container,
            text="Confirm Password"
        ).pack(anchor="w")

        self.confirm_password = ttk.Entry(
            container,
            width=36,
            show="*"
        )
        self.confirm_password.pack(pady=(5, 20), ipady=5)

        ttk.Button(
            container,
            text="Create Account",
            style="Primary.TButton",
            command=self.handle_register
        ).pack(fill="x", pady=(0, 10))

        ttk.Button(
            container,
            text="Back to Login",
            command=self.show_login
        ).pack(fill="x")

    def handle_register(self):
        username = self.register_username.get().strip()
        password = self.register_password.get()
        confirmation = self.confirm_password.get()

        if not username or not password or not confirmation:
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all fields."
            )
            return

        if password != confirmation:
            messagebox.showerror(
                "Password Mismatch",
                "The passwords do not match."
            )
            return

        success, message = register_user(username, password)

        if success:
            messagebox.showinfo("Success", message)
            self.show_login()
        else:
            messagebox.showerror(
                "Registration Failed",
                message
            )

    # ---------------- DASHBOARD ----------------

    def show_dashboard(self):
        self.clear_screen()
        self.setup_styles()

        self.root.unbind("<Return>")

        header = ttk.Frame(self.root, padding=(25, 20))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="✈ TravelEase",
            style="Title.TLabel"
        ).pack(side="left")

        ttk.Button(
            header,
            text="Switch Account / Log Out",
            command=self.switch_account
        ).pack(side="right")

        content = ttk.Frame(self.root, padding=(35, 15))
        content.pack(fill="both", expand=True)

        ttk.Label(
            content,
            text=f"Welcome, {self.current_user['username']}!",
            style="Title.TLabel"
        ).pack(pady=(10, 5))

        ttk.Label(
            content,
            text="Your personal travel management dashboard",
            style="Subtitle.TLabel"
        ).pack(pady=(0, 20))

        ttk.Label(
            content,
            text="WHAT WOULD YOU LIKE TO DO?",
            font=("Helvetica", 15, "bold")
        ).pack(pady=(0, 15))

        user_id = self.current_user["user_id"]

        buttons = [
            (
                "✈ My Trips — Add and Manage Trips",
                lambda: open_trips_window(self.root, user_id)
            ),
            (
                "🗓 Itinerary Planner — Manage Activities",
                lambda: open_itinerary_window(self.root, user_id)
            ),
            (
                "🎫 Bookings — Manage Reservations",
                lambda: open_bookings_window(self.root, user_id)
            ),
            (
                "💰 Expenses — Track Travel Spending",
                lambda: open_expenses_window(self.root, user_id)
            ),
            (
                "📊 Reports — View Travel Summary",
                lambda: open_reports_window(self.root, user_id)
            ),
            (
                "🔔 Reminders — Upcoming Travel Plans",
                lambda: open_reminders_window(self.root, user_id)
            )
        ]

        for label, action in buttons:
            ttk.Button(
                content,
                text=label,
                style="Dashboard.TButton",
                command=action
            ).pack(fill="x", pady=9, ipady=3)

        ttk.Label(
            content,
            text="Plan smarter. Travel better.",
            style="Subtitle.TLabel"
        ).pack(pady=(15, 0))

    # ---------------- ACCOUNT SWITCHING ----------------

    def switch_account(self):
        if not messagebox.askyesno(
            "Switch Account",
            "Return to the login page? Your saved data will remain."
        ):
            return

        self.show_login()


if __name__ == "__main__":
    root = tk.Tk()
    app = TravelEaseApp(root)
    root.mainloop()

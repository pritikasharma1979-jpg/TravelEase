import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from database import get_connection


class TripsManager:
    def __init__(self, parent, user_id):
        self.parent = parent
        self.user_id = user_id
        self.selected_trip_id = None

        self.window = tk.Toplevel(parent)
        self.window.title("TravelEase - My Trips")
        self.window.geometry("1150x720")
        self.window.minsize(900, 600)

        self.setup_styles()
        self.build_interface()
        self.load_trips()

    def setup_styles(self):
        style = ttk.Style(self.window)
        style.configure(
            "PageTitle.TLabel",
            font=("Helvetica", 23, "bold")
        )
        style.configure(
            "Action.TButton",
            font=("Helvetica", 10, "bold"),
            padding=7
        )

    def build_interface(self):
        # Header
        header = ttk.Frame(self.window, padding=20)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="✈ My Trips",
            style="PageTitle.TLabel"
        ).pack(side="left")

        ttk.Button(
            header,
            text="Close",
            command=self.window.destroy
        ).pack(side="right")

        ttk.Label(
            self.window,
            text="Plan, organize, and manage your journeys.",
            font=("Helvetica", 11)
        ).pack(anchor="w", padx=22)

        # Search area
        search_frame = ttk.Frame(self.window, padding=(20, 15))
        search_frame.pack(fill="x")

        ttk.Label(
            search_frame,
            text="Search trips:"
        ).pack(side="left", padx=(0, 8))

        self.search_var = tk.StringVar()

        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=35
        )
        search_entry.pack(side="left", padx=(0, 8))

        search_entry.bind(
            "<Return>",
            lambda event: self.load_trips()
        )

        ttk.Button(
            search_frame,
            text="Search",
            command=self.load_trips
        ).pack(side="left", padx=3)

        ttk.Button(
            search_frame,
            text="Show All",
            command=self.clear_search
        ).pack(side="left", padx=3)

        # Trips table
        table_frame = ttk.Frame(self.window, padding=(20, 0))
        table_frame.pack(fill="both", expand=True)

        columns = (
            "trip_id",
            "trip_name",
            "destination",
            "start_date",
            "end_date",
            "travelers",
            "budget",
            "status"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        headings = {
            "trip_id": "ID",
            "trip_name": "Trip Name",
            "destination": "Destination",
            "start_date": "Start Date",
            "end_date": "End Date",
            "travelers": "Travellers",
            "budget": "Budget",
            "status": "Status"
        }

        widths = {
            "trip_id": 45,
            "trip_name": 150,
            "destination": 160,
            "start_date": 105,
            "end_date": 105,
            "travelers": 80,
            "budget": 100,
            "status": 100
        }

        for column in columns:
            self.tree.heading(
                column,
                text=headings[column]
            )
            self.tree.column(
                column,
                width=widths[column],
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(side="right", fill="y")

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.on_trip_select
        )

        # Action buttons
        actions = ttk.Frame(self.window, padding=20)
        actions.pack(fill="x")

        ttk.Button(
            actions,
            text="+ Add Trip",
            style="Action.TButton",
            command=self.add_trip
        ).pack(side="left", padx=5)

        ttk.Button(
            actions,
            text="Edit Selected",
            style="Action.TButton",
            command=self.edit_trip
        ).pack(side="left", padx=5)

        ttk.Button(
            actions,
            text="Delete Selected",
            style="Action.TButton",
            command=self.delete_trip
        ).pack(side="left", padx=5)

        ttk.Button(
            actions,
            text="Refresh",
            style="Action.TButton",
            command=self.load_trips
        ).pack(side="left", padx=5)

        self.status_label = ttk.Label(
            self.window,
            text="Ready",
            padding=(20, 0, 20, 12)
        )
        self.status_label.pack(anchor="w")

    def clear_search(self):
        self.search_var.set("")
        self.load_trips()

    def load_trips(self):
        """Load only trips belonging to the logged-in user."""

        for item in self.tree.get_children():
            self.tree.delete(item)

        connection = get_connection()

        if connection is None:
            messagebox.showerror(
                "Database Error",
                "Unable to connect to the database.",
                parent=self.window
            )
            return

        cursor = None

        try:
            cursor = connection.cursor()

            search_text = self.search_var.get().strip()

            query = """
                SELECT
                    trip_id,
                    trip_name,
                    destination,
                    start_date,
                    end_date,
                    travelers,
                    budget,
                    status
                FROM trips
                WHERE user_id = %s
            """

            params = [self.user_id]

            if search_text:
                query += """
                    AND (
                        trip_name LIKE %s
                        OR destination LIKE %s
                    )
                """
                search_pattern = f"%{search_text}%"
                params.extend([
                    search_pattern,
                    search_pattern
                ])

            query += " ORDER BY start_date ASC"

            cursor.execute(query, tuple(params))

            rows = cursor.fetchall()

            for row in rows:
                display_row = list(row)

                # Format budget for display.
                display_row[6] = (
                    f"{Decimal(str(row[6] or 0)):.2f}"
                )

                self.tree.insert(
                    "",
                    "end",
                    values=display_row
                )

            self.status_label.config(
                text=f"{len(rows)} trip(s) found"
            )

        except Exception as error:
            print("Error loading trips:", error)

            messagebox.showerror(
                "Error",
                "Could not load trips. Check the terminal for details.",
                parent=self.window
            )

        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

    def on_trip_select(self, event=None):
        selection = self.tree.selection()

        if selection:
            values = self.tree.item(
                selection[0],
                "values"
            )

            self.selected_trip_id = int(values[0])
        else:
            self.selected_trip_id = None

    def add_trip(self):
        self.open_trip_form()

    def edit_trip(self):
        selection = self.tree.selection()

        if not selection:
            messagebox.showwarning(
                "Select a Trip",
                "Please select a trip to edit.",
                parent=self.window
            )
            return

        values = self.tree.item(
            selection[0],
            "values"
        )

        trip_id = int(values[0])

        # Verify ownership before loading the edit form.
        connection = get_connection()

        if connection is None:
            messagebox.showerror(
                "Database Error",
                "Unable to connect to the database.",
                parent=self.window
            )
            return

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT *
                FROM trips
                WHERE trip_id = %s AND user_id = %s
                """,
                (trip_id, self.user_id)
            )

            trip = cursor.fetchone()

            if trip is None:
                messagebox.showerror(
                    "Not Found",
                    "This trip could not be found in your account.",
                    parent=self.window
                )
                self.load_trips()
                return

            self.open_trip_form(trip)

        except Exception as error:
            print("Error opening trip:", error)

            messagebox.showerror(
                "Error",
                "Could not open the selected trip.",
                parent=self.window
            )

        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

    def open_trip_form(self, trip=None):
        """Display the Add Trip or Edit Trip form."""

        editing = trip is not None

        form = tk.Toplevel(self.window)
        form.title("Edit Trip" if editing else "Add New Trip")
        form.geometry("520x690")
        form.resizable(False, False)
        form.transient(self.window)
        form.grab_set()

        container = ttk.Frame(form, padding=22)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Edit Trip" if editing else "Plan a New Trip",
            font=("Helvetica", 20, "bold")
        ).pack(anchor="w", pady=(0, 18))

        fields = {}

        field_specs = [
            ("Trip Name", "trip_name", ""),
            ("Destination", "destination", ""),
            ("Start Date (YYYY-MM-DD)", "start_date", ""),
            ("End Date (YYYY-MM-DD)", "end_date", ""),
            ("Number of Travellers", "travelers", "1"),
            ("Budget", "budget", "0.00"),
            ("Purpose", "purpose", "Leisure"),
            ("Notes", "notes", "")
        ]

        for label_text, field_name, default in field_specs:
            ttk.Label(
                container,
                text=label_text
            ).pack(anchor="w", pady=(5, 2))

            if field_name == "purpose":
                widget = ttk.Combobox(
                    container,
                    values=[
                        "Leisure",
                        "Business",
                        "Education",
                        "Adventure",
                        "Family",
                        "Other"
                    ],
                    state="readonly"
                )
                widget.set(default)

            elif field_name == "notes":
                widget = tk.Text(
                    container,
                    height=3,
                    width=45,
                    wrap="word"
                )
                widget.insert("1.0", default)

            else:
                widget = ttk.Entry(container)
                widget.insert(0, default)

            widget.pack(fill="x", pady=(0, 4))

            fields[field_name] = widget

        # Fill in existing trip data when editing.
        if editing:
            for field_name, widget in fields.items():
                value = trip.get(field_name)

                if value is None:
                    value = ""

                if field_name == "notes":
                    widget.delete("1.0", "end")
                    widget.insert("1.0", str(value))

                elif field_name == "purpose":
                    widget.set(str(value or "Other"))

                else:
                    widget.delete(0, "end")
                    widget.insert(0, str(value))

        def save_trip():
            trip_name = fields["trip_name"].get().strip()
            destination = fields["destination"].get().strip()
            start_text = fields["start_date"].get().strip()
            end_text = fields["end_date"].get().strip()
            travelers_text = fields["travelers"].get().strip()
            budget_text = fields["budget"].get().strip()
            purpose = fields["purpose"].get().strip()
            notes = fields["notes"].get("1.0", "end").strip()

            if not trip_name or not destination:
                messagebox.showwarning(
                    "Missing Information",
                    "Trip name and destination are required.",
                    parent=form
                )
                return

            try:
                start_date = datetime.strptime(
                    start_text,
                    "%Y-%m-%d"
                ).date()

                end_date = datetime.strptime(
                    end_text,
                    "%Y-%m-%d"
                ).date()

            except ValueError:
                messagebox.showerror(
                    "Invalid Date",
                    "Enter dates in YYYY-MM-DD format.\n"
                    "Example: 2026-12-25",
                    parent=form
                )
                return

            if end_date < start_date:
                messagebox.showerror(
                    "Invalid Dates",
                    "The end date cannot be before the start date.",
                    parent=form
                )
                return

            try:
                travelers = int(travelers_text)

                if travelers < 1:
                    raise ValueError

            except ValueError:
                messagebox.showerror(
                    "Invalid Travellers",
                    "Number of travellers must be a positive whole number.",
                    parent=form
                )
                return

            try:
                budget = Decimal(budget_text)

                if not budget.is_finite() or budget < 0:
                    raise InvalidOperation

            except (InvalidOperation, ValueError):
                messagebox.showerror(
                    "Invalid Budget",
                    "Enter a valid non-negative budget.",
                    parent=form
                )
                return

            connection = get_connection()

            if connection is None:
                messagebox.showerror(
                    "Database Error",
                    "Unable to connect to the database.",
                    parent=form
                )
                return

            cursor = None

            try:
                cursor = connection.cursor()

                if editing:
                    cursor.execute(
                        """
                        UPDATE trips
                        SET trip_name = %s,
                            destination = %s,
                            start_date = %s,
                            end_date = %s,
                            travelers = %s,
                            budget = %s,
                            purpose = %s,
                            notes = %s
                        WHERE trip_id = %s AND user_id = %s
                        """,
                        (
                            trip_name,
                            destination,
                            start_date,
                            end_date,
                            travelers,
                            budget,
                            purpose,
                            notes,
                            trip["trip_id"],
                            self.user_id
                        )
                    )

                    if cursor.rowcount == 0:
                        # The record may be unchanged or no longer exist.
                        cursor.execute(
                            """
                            SELECT trip_id
                            FROM trips
                            WHERE trip_id = %s AND user_id = %s
                            """,
                            (trip["trip_id"], self.user_id)
                        )

                        if cursor.fetchone() is None:
                            messagebox.showerror(
                                "Not Found",
                                "This trip no longer exists.",
                                parent=form
                            )
                            return

                else:
                    cursor.execute(
                        """
                        INSERT INTO trips (
                            user_id,
                            trip_name,
                            destination,
                            start_date,
                            end_date,
                            travelers,
                            budget,
                            purpose,
                            notes,
                            status
                        )
                        VALUES (%s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s)
                        """,
                        (
                            self.user_id,
                            trip_name,
                            destination,
                            start_date,
                            end_date,
                            travelers,
                            budget,
                            purpose,
                            notes,
                            "Upcoming"
                        )
                    )

                connection.commit()

                messagebox.showinfo(
                    "Success",
                    "Trip saved successfully!",
                    parent=form
                )

                form.destroy()
                self.load_trips()

            except Exception as error:
                connection.rollback()
                print("Error saving trip:", error)

                messagebox.showerror(
                    "Save Failed",
                    "Could not save the trip. Check the terminal for details.",
                    parent=form
                )

            finally:
                if cursor is not None:
                    cursor.close()
                connection.close()

        buttons = ttk.Frame(container)
        buttons.pack(fill="x", pady=(18, 0))

        ttk.Button(
            buttons,
            text="Save Trip",
            command=save_trip
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            buttons,
            text="Cancel",
            command=form.destroy
        ).pack(side="left")

    def delete_trip(self):
        selection = self.tree.selection()

        if not selection:
            messagebox.showwarning(
                "Select a Trip",
                "Please select a trip to delete.",
                parent=self.window
            )
            return

        values = self.tree.item(
            selection[0],
            "values"
        )

        trip_id = int(values[0])
        trip_name = values[1]

        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete '{trip_name}'?\n\n"
            "Its associated itinerary activities, bookings, and "
            "expenses will also be deleted.",
            parent=self.window
        )

        if not confirmed:
            return

        connection = get_connection()

        if connection is None:
            messagebox.showerror(
                "Database Error",
                "Unable to connect to the database.",
                parent=self.window
            )
            return

        cursor = None

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM trips
                WHERE trip_id = %s AND user_id = %s
                """,
                (trip_id, self.user_id)
            )

            if cursor.rowcount == 0:
                messagebox.showwarning(
                    "Not Found",
                    "The selected trip no longer exists.",
                    parent=self.window
                )

            connection.commit()
            self.load_trips()

        except Exception as error:
            connection.rollback()
            print("Error deleting trip:", error)

            messagebox.showerror(
                "Delete Failed",
                "Could not delete the trip.",
                parent=self.window
            )

        finally:
            if cursor is not None:
                cursor.close()
            connection.close()


def open_trips_window(parent, user_id):
    """Open the trip management window."""
    return TripsManager(parent, user_id)
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal, InvalidOperation

from database import get_connection


class ItineraryManager:
    def __init__(self, parent, user_id):
        self.parent = parent
        self.user_id = user_id

        self.window = tk.Toplevel(parent)
        self.window.title("TravelEase - Itinerary Planner")
        self.window.geometry("1100x680")

        self.selected_activity_id = None

        self.build_interface()
        self.load_trips()

    def build_interface(self):
        header = ttk.Frame(self.window, padding=20)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="🗓️ Itinerary Planner",
            font=("Helvetica", 22, "bold")
        ).pack(side="left")

        ttk.Button(
            header,
            text="Close",
            command=self.window.destroy
        ).pack(side="right")

        selection_frame = ttk.Frame(
            self.window,
            padding=(20, 5)
        )
        selection_frame.pack(fill="x")

        ttk.Label(
            selection_frame,
            text="Select Trip:"
        ).pack(side="left", padx=(0, 10))

        self.trip_var = tk.StringVar()

        self.trip_box = ttk.Combobox(
            selection_frame,
            textvariable=self.trip_var,
            state="readonly",
            width=45
        )
        self.trip_box.pack(side="left", padx=(0, 10))

        self.trip_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.load_activities()
        )

        ttk.Button(
            selection_frame,
            text="Refresh",
            command=self.load_trips
        ).pack(side="left")

        table_frame = ttk.Frame(
            self.window,
            padding=20
        )
        table_frame.pack(fill="both", expand=True)

        columns = (
            "activity_id",
            "activity_date",
            "activity_name",
            "location",
            "start_time",
            "end_time",
            "estimated_cost"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        headings = {
            "activity_id": "ID",
            "activity_date": "Date",
            "activity_name": "Activity",
            "location": "Location",
            "start_time": "Start",
            "end_time": "End",
            "estimated_cost": "Estimated Cost"
        }

        widths = {
            "activity_id": 50,
            "activity_date": 110,
            "activity_name": 210,
            "location": 200,
            "start_time": 100,
            "end_time": 100,
            "estimated_cost": 130
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

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.on_select
        )

        buttons = ttk.Frame(
            self.window,
            padding=20
        )
        buttons.pack(fill="x")

        ttk.Button(
            buttons,
            text="+ Add Activity",
            command=self.add_activity
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Edit Selected",
            command=self.edit_activity
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Delete Selected",
            command=self.delete_activity
        ).pack(side="left", padx=5)

        self.status_label = ttk.Label(
            self.window,
            text="Select a trip to view its itinerary.",
            padding=(20, 0, 20, 12)
        )
        self.status_label.pack(anchor="w")

    def get_selected_trip_id(self):
        selected = self.trip_box.current()

        if selected < 0:
            return None

        return self.trip_options[selected][0]

    def load_trips(self):
        connection = get_connection()

        if connection is None:
            messagebox.showerror(
                "Database Error",
                "Could not connect to the database.",
                parent=self.window
            )
            return

        cursor = None

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT trip_id, trip_name, destination
                FROM trips
                WHERE user_id = %s
                ORDER BY start_date
                """,
                (self.user_id,)
            )

            self.trip_options = cursor.fetchall()

            self.trip_box["values"] = [
                f"{trip[1]} — {trip[2]}"
                for trip in self.trip_options
            ]

            if self.trip_options:
                if self.trip_box.current() < 0:
                    self.trip_box.current(0)

                self.load_activities()

            else:
                self.trip_box.set("")
                self.clear_table()
                self.status_label.config(
                    text="No trips found. Add a trip first."
                )

        except Exception as error:
            print("Error loading trips:", error)

            messagebox.showerror(
                "Error",
                "Could not load trips. Check the terminal.",
                parent=self.window
            )

        finally:
            if cursor is not None:
                cursor.close()

            connection.close()

    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def load_activities(self):
        self.clear_table()

        trip_id = self.get_selected_trip_id()

        if trip_id is None:
            return

        connection = get_connection()

        if connection is None:
            return

        cursor = None

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    i.activity_id,
                    i.activity_date,
                    i.activity_name,
                    i.location,
                    i.start_time,
                    i.end_time,
                    i.estimated_cost
                FROM itinerary AS i
                INNER JOIN trips AS t
                    ON i.trip_id = t.trip_id
                WHERE t.trip_id = %s
                  AND t.user_id = %s
                ORDER BY i.activity_date, i.start_time
                """,
                (trip_id, self.user_id)
            )

            rows = cursor.fetchall()

            for row in rows:
                display = list(row)

                for index in (1, 4, 5):
                    if display[index] is not None:
                        display[index] = str(display[index])

                display[6] = (
                    f"{Decimal(str(display[6] or 0)):.2f}"
                )

                self.tree.insert(
                    "",
                    "end",
                    values=display
                )

            self.status_label.config(
                text=f"{len(rows)} activities found"
            )

        except Exception as error:
            print("Error loading itinerary:", error)

            messagebox.showerror(
                "Error",
                "Could not load activities. Check the terminal.",
                parent=self.window
            )

        finally:
            if cursor is not None:
                cursor.close()

            connection.close()

    def on_select(self, event=None):
        selected = self.tree.selection()

        self.selected_activity_id = None

        if selected:
            values = self.tree.item(
                selected[0],
                "values"
            )

            self.selected_activity_id = int(values[0])

    def add_activity(self):
        trip_id = self.get_selected_trip_id()

        if trip_id is None:
            messagebox.showwarning(
                "Select a Trip",
                "Create or select a trip before adding activities.",
                parent=self.window
            )
            return

        self.open_activity_form(trip_id)

    def edit_activity(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select an Activity",
                "Select an activity to edit.",
                parent=self.window
            )
            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        activity_id = int(values[0])
        trip_id = self.get_selected_trip_id()

        connection = get_connection()

        if connection is None:
            return

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT i.*
                FROM itinerary AS i
                INNER JOIN trips AS t
                    ON i.trip_id = t.trip_id
                WHERE i.activity_id = %s
                  AND t.user_id = %s
                """,
                (activity_id, self.user_id)
            )

            activity = cursor.fetchone()

            if activity is None:
                messagebox.showerror(
                    "Not Found",
                    "Activity not found in your account.",
                    parent=self.window
                )
                self.load_activities()
                return

            self.open_activity_form(
                activity["trip_id"],
                activity
            )

        except Exception as error:
            print("Error editing activity:", error)

            messagebox.showerror(
                "Error",
                "Could not open activity.",
                parent=self.window
            )

        finally:
            if cursor is not None:
                cursor.close()

            connection.close()

    def open_activity_form(self, trip_id, activity=None):
        editing = activity is not None

        form = tk.Toplevel(self.window)
        form.title(
            "Edit Activity" if editing else "Add Activity"
        )
        form.geometry("480x590")
        form.transient(self.window)
        form.grab_set()

        container = ttk.Frame(form, padding=20)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Edit Activity" if editing else "Plan Activity",
            font=("Helvetica", 19, "bold")
        ).pack(anchor="w", pady=(0, 15))

        specs = [
            ("Activity Name", "activity_name", ""),
            ("Date (YYYY-MM-DD)", "activity_date", ""),
            ("Location", "location", ""),
            ("Start Time (HH:MM)", "start_time", "09:00"),
            ("End Time (HH:MM)", "end_time", "10:00"),
            ("Estimated Cost", "estimated_cost", "0.00"),
            ("Notes", "notes", "")
        ]

        fields = {}

        for label, name, default in specs:
            ttk.Label(
                container,
                text=label
            ).pack(anchor="w", pady=(5, 2))

            if name == "notes":
                widget = tk.Text(
                    container,
                    height=3,
                    width=40
                )
                widget.insert("1.0", default)
            else:
                widget = ttk.Entry(container)
                widget.insert(0, default)

            widget.pack(fill="x", pady=(0, 3))
            fields[name] = widget

        if editing:
            for name, widget in fields.items():
                value = activity.get(name)

                if value is None:
                    value = ""

                if name == "notes":
                    widget.delete("1.0", "end")
                    widget.insert("1.0", str(value))
                else:
                    widget.delete(0, "end")
                    widget.insert(0, str(value))

        def save():
            name = fields["activity_name"].get().strip()
            date_text = fields["activity_date"].get().strip()
            location = fields["location"].get().strip()
            start_text = fields["start_time"].get().strip()
            end_text = fields["end_time"].get().strip()
            cost_text = fields["estimated_cost"].get().strip()
            notes = fields["notes"].get("1.0", "end").strip()

            if not name or not date_text:
                messagebox.showwarning(
                    "Required Fields",
                    "Activity name and date are required.",
                    parent=form
                )
                return

            try:
                activity_date = datetime.strptime(
                    date_text,
                    "%Y-%m-%d"
                ).date()

                start_time = datetime.strptime(
                    start_text,
                    "%H:%M"
                ).time()

                end_time = datetime.strptime(
                    end_text,
                    "%H:%M"
                ).time()

            except ValueError:
                messagebox.showerror(
                    "Invalid Input",
                    "Use YYYY-MM-DD for dates and HH:MM for times.",
                    parent=form
                )
                return

            if end_time <= start_time:
                messagebox.showerror(
                    "Invalid Time",
                    "End time must be later than start time.",
                    parent=form
                )
                return

            try:
                cost = Decimal(cost_text)

                if not cost.is_finite() or cost < 0:
                    raise InvalidOperation

            except (InvalidOperation, ValueError):
                messagebox.showerror(
                    "Invalid Cost",
                    "Enter a valid non-negative cost.",
                    parent=form
                )
                return

            # Ensure the activity date belongs to the selected trip.
            connection = get_connection()

            if connection is None:
                return

            cursor = None

            try:
                cursor = connection.cursor()

                cursor.execute(
                    """
                    SELECT start_date, end_date
                    FROM trips
                    WHERE trip_id = %s AND user_id = %s
                    """,
                    (trip_id, self.user_id)
                )

                trip_dates = cursor.fetchone()

                if trip_dates is None:
                    messagebox.showerror(
                        "Trip Not Found",
                        "The selected trip is no longer available.",
                        parent=form
                    )
                    return

                if not (
                    trip_dates[0] <= activity_date <= trip_dates[1]
                ):
                    messagebox.showerror(
                        "Date Outside Trip",
                        "The activity date must fall within the trip dates.",
                        parent=form
                    )
                    return

                if editing:
                    cursor.execute(
                        """
                        UPDATE itinerary
                        SET activity_date = %s,
                            activity_name = %s,
                            location = %s,
                            start_time = %s,
                            end_time = %s,
                            estimated_cost = %s,
                            notes = %s
                        WHERE activity_id = %s
                          AND trip_id = %s
                        """,
                        (
                            activity_date,
                            name,
                            location,
                            start_time,
                            end_time,
                            cost,
                            notes,
                            activity["activity_id"],
                            trip_id
                        )
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO itinerary (
                            trip_id,
                            activity_date,
                            activity_name,
                            location,
                            start_time,
                            end_time,
                            estimated_cost,
                            notes
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            trip_id,
                            activity_date,
                            name,
                            location,
                            start_time,
                            end_time,
                            cost,
                            notes
                        )
                    )

                connection.commit()

                messagebox.showinfo(
                    "Success",
                    "Activity saved successfully!",
                    parent=form
                )

                form.destroy()
                self.load_activities()

            except Exception as error:
                connection.rollback()
                print("Error saving activity:", error)

                messagebox.showerror(
                    "Save Failed",
                    "Could not save the activity. Check the terminal.",
                    parent=form
                )

            finally:
                if cursor is not None:
                    cursor.close()

                connection.close()

        buttons = ttk.Frame(container)
        buttons.pack(fill="x", pady=15)

        ttk.Button(
            buttons,
            text="Save Activity",
            command=save
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            buttons,
            text="Cancel",
            command=form.destroy
        ).pack(side="left")

    def delete_activity(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select an Activity",
                "Select an activity to delete.",
                parent=self.window
            )
            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        activity_id = int(values[0])

        if not messagebox.askyesno(
            "Confirm Deletion",
            "Delete this itinerary activity?",
            parent=self.window
        ):
            return

        connection = get_connection()

        if connection is None:
            return

        cursor = None

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE i
                FROM itinerary AS i
                INNER JOIN trips AS t
                    ON i.trip_id = t.trip_id
                WHERE i.activity_id = %s
                  AND t.user_id = %s
                """,
                (activity_id, self.user_id)
            )

            connection.commit()
            self.load_activities()

        except Exception as error:
            connection.rollback()
            print("Error deleting activity:", error)

            messagebox.showerror(
                "Delete Failed",
                "Could not delete activity.",
                parent=self.window
            )

        finally:
            if cursor is not None:
                cursor.close()

            connection.close()


def open_itinerary_window(parent, user_id):
    return ItineraryManager(parent, user_id)
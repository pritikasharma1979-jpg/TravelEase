import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from decimal import Decimal, InvalidOperation

from database import get_connection


class BookingsWindow:
    """Bookings CRUD window, restricted to trips owned by the logged-in user."""

    def __init__(self, parent, user_id):
        self.parent = parent
        self.user_id = user_id
        self.window = tk.Toplevel(parent)
        self.window.title("TravelEase - Bookings")
        self.window.geometry("1180x720")
        self.window.minsize(950, 600)

        self.trip_map = {}
        self._build_ui()
        self.load_trips()
        self.load_bookings()

    def _build_ui(self):
        style = ttk.Style(self.window)
        style.configure("Heading.TLabel", font=("Helvetica", 22, "bold"))

        header = ttk.Frame(self.window, padding=(18, 14))
        header.pack(fill="x")
        ttk.Label(header, text="🎫 Bookings", style="Heading.TLabel").pack(side="left")
        ttk.Button(header, text="Close", command=self.window.destroy).pack(side="right")

        ttk.Label(
            self.window,
            text="Add and manage flight, train, bus, hotel, and other reservations.",
            padding=(20, 0, 20, 10)
        ).pack(anchor="w")

        form = ttk.LabelFrame(self.window, text="Booking details", padding=12)
        form.pack(fill="x", padx=18, pady=8)

        self.trip_var = tk.StringVar()
        self.type_var = tk.StringVar(value="Flight")
        self.provider_var = tk.StringVar()
        self.reference_var = tk.StringVar()
        self.booking_date_var = tk.StringVar(value=date.today().isoformat())
        self.departure_var = tk.StringVar()
        self.arrival_var = tk.StringVar()
        self.amount_var = tk.StringVar(value="0.00")
        self.status_var = tk.StringVar(value="Planned")

        fields = [
            ("Trip *", self.trip_var, "trip"),
            ("Booking type *", self.type_var, "type"),
            ("Provider", self.provider_var, "entry"),
            ("Reference number", self.reference_var, "entry"),
            ("Booking date (YYYY-MM-DD)", self.booking_date_var, "entry"),
            ("Departure details", self.departure_var, "entry"),
            ("Arrival details", self.arrival_var, "entry"),
            ("Amount", self.amount_var, "entry"),
            ("Status", self.status_var, "status"),
        ]

        self.trip_combo = None
        for i, (label, var, kind) in enumerate(fields):
            row, col = divmod(i, 3)
            cell = ttk.Frame(form)
            cell.grid(row=row, column=col, sticky="ew", padx=7, pady=5)
            ttk.Label(cell, text=label).pack(anchor="w")
            if kind == "trip":
                widget = ttk.Combobox(cell, textvariable=var, state="readonly", width=32)
                self.trip_combo = widget
            elif kind == "type":
                widget = ttk.Combobox(
                    cell, textvariable=var, state="readonly", width=30,
                    values=("Flight", "Train", "Bus", "Hotel", "Car Rental", "Activity", "Other")
                )
            elif kind == "status":
                widget = ttk.Combobox(
                    cell, textvariable=var, state="readonly", width=30,
                    values=("Planned", "Booked", "Confirmed", "Cancelled", "Completed")
                )
            else:
                widget = ttk.Entry(cell, textvariable=var, width=34)
            widget.pack(fill="x", pady=(3, 0), ipady=3)

        for col in range(3):
            form.columnconfigure(col, weight=1)

        notes_frame = ttk.Frame(form)
        notes_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=7, pady=5)
        ttk.Label(notes_frame, text="Notes").pack(anchor="w")
        self.notes_text = tk.Text(notes_frame, height=3, wrap="word")
        self.notes_text.pack(fill="x", pady=(3, 0))

        buttons = ttk.Frame(self.window, padding=(18, 5))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="+ Add Booking", command=self.add_booking).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Update Selected", command=self.update_booking).pack(side="left", padx=8)
        ttk.Button(buttons, text="Clear Form", command=self.clear_form).pack(side="left", padx=8)
        ttk.Button(buttons, text="Delete Selected", command=self.delete_booking).pack(side="left", padx=8)

        search_frame = ttk.Frame(self.window, padding=(18, 8))
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=(0, 8))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=38)
        search_entry.pack(side="left", padx=(0, 8), ipady=3)
        search_entry.bind("<Return>", lambda event: self.load_bookings())
        ttk.Button(search_frame, text="Search", command=self.load_bookings).pack(side="left", padx=4)
        ttk.Button(search_frame, text="Show All", command=self.show_all).pack(side="left", padx=4)
        ttk.Button(search_frame, text="Refresh", command=self.refresh).pack(side="left", padx=4)

        table_frame = ttk.Frame(self.window, padding=(18, 4, 18, 8))
        table_frame.pack(fill="both", expand=True)
        columns = ("id", "trip", "type", "provider", "reference", "date",
                   "departure", "arrival", "amount", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        headings = {
            "id": "ID", "trip": "Trip", "type": "Type", "provider": "Provider",
            "reference": "Reference", "date": "Booking Date", "departure": "Departure",
            "arrival": "Arrival", "amount": "Amount", "status": "Status"
        }
        widths = {
            "id": 50, "trip": 150, "type": 95, "provider": 125, "reference": 115,
            "date": 105, "departure": 145, "arrival": 145, "amount": 85, "status": 95
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], minwidth=45, anchor="center")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.count_label = ttk.Label(self.window, text="0 booking(s)", padding=(20, 0, 20, 12))
        self.count_label.pack(anchor="w")

    def _query(self, sql, params=(), fetch=False):
        connection = cursor = None
        try:
            connection = get_connection()
            if connection is None or not connection.is_connected():
                raise RuntimeError("Could not connect to MySQL. Check database.py.")
            cursor = connection.cursor(dictionary=True)
            cursor.execute(sql, params)
            result = cursor.fetchall() if fetch else None
            if not fetch:
                connection.commit()
            return result
        except Exception as exc:
            if connection:
                try:
                    connection.rollback()
                except Exception:
                    pass
            messagebox.showerror("Database Error", str(exc), parent=self.window)
            return None if fetch else False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def load_trips(self):
        rows = self._query(
            """SELECT trip_id, trip_name, destination FROM trips
               WHERE user_id=%s ORDER BY start_date DESC""",
            (self.user_id,), fetch=True
        )
        if rows is None:
            return
        self.trip_map = {
            f"{r['trip_name']} — {r['destination']} (ID {r['trip_id']})": r["trip_id"]
            for r in rows
        }
        self.trip_combo["values"] = list(self.trip_map.keys())
        if self.trip_map and self.trip_var.get() not in self.trip_map:
            self.trip_var.set(next(iter(self.trip_map)))
        elif not self.trip_map:
            self.trip_var.set("")
            messagebox.showinfo(
                "No Trips Found", "Add a trip in My Trips before creating a booking.",
                parent=self.window
            )

    def _form_values(self):
        trip_id = self.trip_map.get(self.trip_var.get())
        if not trip_id:
            messagebox.showwarning("Required", "Select one of your trips first.", parent=self.window)
            return None
        booking_type = self.type_var.get().strip()
        booking_date = self.booking_date_var.get().strip()
        if not booking_type:
            messagebox.showwarning("Required", "Select a booking type.", parent=self.window)
            return None
        try:
            date.fromisoformat(booking_date)
        except ValueError:
            messagebox.showwarning("Invalid Date", "Enter the date as YYYY-MM-DD.", parent=self.window)
            return None
        try:
            amount = Decimal(self.amount_var.get().strip())
            if not amount.is_finite() or amount < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            messagebox.showwarning("Invalid Amount", "Enter a valid non-negative amount.", parent=self.window)
            return None
        return (
            trip_id, booking_type, self.provider_var.get().strip() or None,
            self.reference_var.get().strip() or None, booking_date,
            self.departure_var.get().strip() or None, self.arrival_var.get().strip() or None,
            amount, self.status_var.get().strip() or "Planned",
            self.notes_text.get("1.0", "end").strip() or None
        )

    def add_booking(self):
        values = self._form_values()
        if values is None:
            return
        ok = self._query(
            """INSERT INTO bookings
               (trip_id, booking_type, provider_name, reference_number, booking_date,
                departure_details, arrival_details, amount, status, notes)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", values
        )
        if ok:
            messagebox.showinfo("Success", "Booking added successfully.", parent=self.window)
            self.clear_form(keep_trip=True)
            self.load_bookings()

    def update_booking(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Booking", "Select a booking to update.", parent=self.window)
            return
        booking_id = int(self.tree.item(selected[0], "values")[0])
        values = self._form_values()
        if values is None:
            return
        ok = self._query(
            """UPDATE bookings b JOIN trips t ON b.trip_id=t.trip_id
               SET b.trip_id=%s, b.booking_type=%s, b.provider_name=%s,
                   b.reference_number=%s, b.booking_date=%s, b.departure_details=%s,
                   b.arrival_details=%s, b.amount=%s, b.status=%s, b.notes=%s
               WHERE b.booking_id=%s AND t.user_id=%s""",
            values + (booking_id, self.user_id)
        )
        if ok:
            messagebox.showinfo("Success", "Booking updated.", parent=self.window)
            self.clear_form(keep_trip=True)
            self.load_bookings()

    def delete_booking(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Booking", "Select a booking to delete.", parent=self.window)
            return
        booking_id = int(self.tree.item(selected[0], "values")[0])
        if not messagebox.askyesno("Confirm Delete", "Delete this booking permanently?", parent=self.window):
            return
        ok = self._query(
            """DELETE b FROM bookings b JOIN trips t ON b.trip_id=t.trip_id
               WHERE b.booking_id=%s AND t.user_id=%s""",
            (booking_id, self.user_id)
        )
        if ok:
            self.clear_form(keep_trip=True)
            self.load_bookings()

    def load_bookings(self):
        search = self.search_var.get().strip()
        sql = """SELECT b.booking_id, t.trip_name, b.booking_type, b.provider_name,
                        b.reference_number, b.booking_date, b.departure_details,
                        b.arrival_details, b.amount, b.status
                 FROM bookings b JOIN trips t ON b.trip_id=t.trip_id
                 WHERE t.user_id=%s"""
        params = [self.user_id]
        if search:
            like = f"%{search}%"
            sql += """ AND (t.trip_name LIKE %s OR t.destination LIKE %s
                        OR b.booking_type LIKE %s OR b.provider_name LIKE %s
                        OR b.reference_number LIKE %s OR b.status LIKE %s)"""
            params.extend([like] * 6)
        sql += " ORDER BY b.booking_date DESC, b.booking_id DESC"
        rows = self._query(sql, tuple(params), fetch=True)
        if rows is None:
            return
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", values=(
                r["booking_id"], r["trip_name"], r["booking_type"],
                r["provider_name"] or "", r["reference_number"] or "",
                str(r["booking_date"]) if r["booking_date"] else "",
                r["departure_details"] or "", r["arrival_details"] or "",
                f"{Decimal(str(r['amount'] or 0)):.2f}", r["status"] or "Planned"
            ))
        self.count_label.configure(text=f"{len(rows)} booking(s) found")

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        booking_id = int(self.tree.item(selected[0], "values")[0])
        rows = self._query(
            """SELECT b.* FROM bookings b JOIN trips t ON b.trip_id=t.trip_id
               WHERE b.booking_id=%s AND t.user_id=%s""",
            (booking_id, self.user_id), fetch=True
        )
        if not rows:
            return
        b = rows[0]
        for label, trip_id in self.trip_map.items():
            if trip_id == b["trip_id"]:
                self.trip_var.set(label)
                break
        self.type_var.set(b["booking_type"] or "Flight")
        self.provider_var.set(b["provider_name"] or "")
        self.reference_var.set(b["reference_number"] or "")
        self.booking_date_var.set(str(b["booking_date"]) if b["booking_date"] else "")
        self.departure_var.set(b["departure_details"] or "")
        self.arrival_var.set(b["arrival_details"] or "")
        self.amount_var.set(str(b["amount"] or "0.00"))
        self.status_var.set(b["status"] or "Planned")
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", b["notes"] or "")

    def clear_form(self, keep_trip=False):
        previous_trip = self.trip_var.get() if keep_trip else ""
        self.type_var.set("Flight")
        self.provider_var.set("")
        self.reference_var.set("")
        self.booking_date_var.set(date.today().isoformat())
        self.departure_var.set("")
        self.arrival_var.set("")
        self.amount_var.set("0.00")
        self.status_var.set("Planned")
        self.notes_text.delete("1.0", "end")
        self.tree.selection_remove(self.tree.selection())
        self.trip_var.set(previous_trip)

    def show_all(self):
        self.search_var.set("")
        self.load_bookings()

    def refresh(self):
        self.load_trips()
        self.load_bookings()


def open_bookings_window(parent, user_id):
    BookingsWindow(parent, user_id)

import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection

def table_exists(cur, name):
    cur.execute("SHOW TABLES LIKE %s", (name,))
    return cur.fetchone() is not None

class ReportsWindow:
    def __init__(self, parent, user_id):
        self.user_id=user_id
        self.win=tk.Toplevel(parent)
        self.win.title("TravelEase - Reports")
        self.win.geometry("850x570")
        self.win.configure(bg="#f7f4ef")
        tk.Label(self.win,text="Travel Reports",font=("Arial",22,"bold"),bg="#f7f4ef",fg="#245747").pack(pady=14)
        self.summary=tk.Label(self.win,text="",justify="left",font=("Arial",13),bg="#f7f4ef",fg="#24352f")
        self.summary.pack(anchor="w",padx=22,pady=8)
        ttk.Label(self.win,text="Your Trips",font=("Arial",14,"bold")).pack(anchor="w",padx=22,pady=(10,4))
        self.tree=ttk.Treeview(self.win,columns=("id","details"),show="headings",height=10)
        self.tree.heading("id",text="Trip ID"); self.tree.heading("details",text="Trip details")
        self.tree.column("id",width=80); self.tree.column("details",width=700)
        self.tree.pack(fill="both",expand=True,padx=22,pady=8)
        ttk.Button(self.win,text="Refresh Report",command=self.load_report).pack(pady=10)
        self.load_report()

    def load_report(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        conn=get_connection()
        try:
            cur=conn.cursor()
            cur.execute("SELECT * FROM trips WHERE user_id=%s ORDER BY trip_id DESC",(self.user_id,))
            trips=cur.fetchall()
            trip_columns=[d[0] for d in cur.description]
            cur.execute("SELECT COUNT(*) FROM trips WHERE user_id=%s",(self.user_id,))
            trip_count=cur.fetchone()[0]
            booking_count=0; booking_total=0
            if table_exists(cur,"bookings"):
                cur.execute("SELECT COUNT(*),COALESCE(SUM(amount),0) FROM bookings WHERE trip_id IN (SELECT trip_id FROM trips WHERE user_id=%s)",(self.user_id,))
                booking_count,booking_total=cur.fetchone()
            expense_count=0; expense_total=0
            if table_exists(cur,"expenses"):
                cur.execute("SELECT COUNT(*),COALESCE(SUM(amount),0) FROM expenses WHERE user_id=%s",(self.user_id,))
                expense_count,expense_total=cur.fetchone()
            self.summary.config(text=f"Trips: {trip_count}\nBookings: {booking_count} | Booking total: {float(booking_total or 0):.2f}\nExpense records: {expense_count} | Total expenses: {float(expense_total or 0):.2f}")
            for trip in trips:
                values=dict(zip(trip_columns,trip))
                details=" | ".join(f"{k}: {v}" for k,v in values.items() if k!="trip_id")
                self.tree.insert("","end",values=(values.get("trip_id",""),details))
        except Exception as exc:
            messagebox.showerror("Report error",str(exc),parent=self.win)
        finally: conn.close()

def open_reports_window(parent, user_id):
    ReportsWindow(parent, user_id)

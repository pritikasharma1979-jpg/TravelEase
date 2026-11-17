import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection

def ensure_table():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS expenses (
            expense_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL, trip_id INT NULL,
            category VARCHAR(100) NOT NULL, amount DECIMAL(10,2) NOT NULL,
            expense_date DATE NOT NULL, description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX (user_id), INDEX (trip_id))""")
        conn.commit()
    finally:
        conn.close()

class ExpensesWindow:
    def __init__(self, parent, user_id):
        self.user_id = user_id
        ensure_table()
        self.win = tk.Toplevel(parent)
        self.win.title("TravelEase - Expenses")
        self.win.geometry("850x570")
        self.win.configure(bg="#f7f4ef")
        tk.Label(self.win, text="Expense Manager", font=("Arial", 22, "bold"),
                 bg="#f7f4ef", fg="#245747").pack(pady=14)
        form = ttk.Frame(self.win, padding=10)
        form.pack(fill="x", padx=15)
        self.category = tk.StringVar(value="Food")
        self.amount = tk.StringVar()
        self.date = tk.StringVar()
        self.trip_id = tk.StringVar()
        self.description = tk.StringVar()
        fields = [
            ("Category", ttk.Combobox(form, textvariable=self.category,
             values=["Food","Transport","Hotel","Activities","Shopping","Other"], state="readonly", width=17)),
            ("Amount", ttk.Entry(form, textvariable=self.amount, width=19)),
            ("Date YYYY-MM-DD", ttk.Entry(form, textvariable=self.date, width=19)),
            ("Trip ID optional", ttk.Entry(form, textvariable=self.trip_id, width=16))]
        for i, (label, widget) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i, padx=5, sticky="w")
            widget.grid(row=1, column=i, padx=5, pady=5)
        ttk.Label(form, text="Description").grid(row=2, column=0, sticky="w", padx=5)
        ttk.Entry(form, textvariable=self.description, width=65).grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        ttk.Button(form, text="Add Expense", command=self.add_expense).grid(row=3, column=3, padx=5)
        ttk.Button(form, text="Delete Selected", command=self.delete_expense).grid(row=4, column=3, padx=5, pady=5)
        cols = ("id","date","category","amount","trip","description")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings", height=14)
        for col, label, width in [("id","ID",50),("date","Date",100),("category","Category",120),("amount","Amount",90),("trip","Trip ID",75),("description","Description",350)]:
            self.tree.heading(col, text=label); self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=15, pady=10)
        self.total = tk.Label(self.win, text="Total expenses: 0.00", font=("Arial",14,"bold"), bg="#f7f4ef", fg="#245747")
        self.total.pack(pady=8)
        self.load_expenses()

    def add_expense(self):
        try:
            amount = float(self.amount.get().strip())
            if amount <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid amount", "Enter an amount greater than zero.", parent=self.win); return
        date_text = self.date.get().strip()
        if not date_text:
            messagebox.showerror("Missing date", "Enter date as YYYY-MM-DD.", parent=self.win); return
        trip_text = self.trip_id.get().strip()
        trip_id = None
        conn = get_connection()
        try:
            cur = conn.cursor()
            if trip_text:
                try: trip_id = int(trip_text)
                except ValueError:
                    messagebox.showerror("Invalid trip ID", "Trip ID must be a number.", parent=self.win); return
                cur.execute("SELECT trip_id FROM trips WHERE trip_id=%s AND user_id=%s", (trip_id,self.user_id))
                if not cur.fetchone():
                    messagebox.showerror("Invalid trip", "Trip does not belong to your account.", parent=self.win); return
            cur.execute("INSERT INTO expenses (user_id,trip_id,category,amount,expense_date,description) VALUES (%s,%s,%s,%s,%s,%s)",
                        (self.user_id,trip_id,self.category.get(),amount,date_text,self.description.get().strip() or None))
            conn.commit()
        except Exception as exc:
            messagebox.showerror("Could not add expense", str(exc), parent=self.win); return
        finally: conn.close()
        self.amount.set(""); self.trip_id.set(""); self.description.set("")
        self.load_expenses()
        messagebox.showinfo("Saved", "Expense added successfully.", parent=self.win)

    def load_expenses(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT expense_id,expense_date,category,amount,trip_id,description FROM expenses WHERE user_id=%s ORDER BY expense_date DESC,expense_id DESC",(self.user_id,))
            rows = cur.fetchall()
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=%s",(self.user_id,))
            total = cur.fetchone()[0] or 0
            for row in rows: self.tree.insert("", "end", values=tuple("" if v is None else v for v in row))
            self.total.config(text=f"Total expenses: {float(total):.2f}")
        except Exception as exc: messagebox.showerror("Database error", str(exc), parent=self.win)
        finally: conn.close()

    def delete_expense(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select expense","Select an expense first.",parent=self.win); return
        expense_id = self.tree.item(selected[0],"values")[0]
        if not messagebox.askyesno("Confirm","Delete selected expense?",parent=self.win): return
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM expenses WHERE expense_id=%s AND user_id=%s",(expense_id,self.user_id)); conn.commit()
        except Exception as exc: messagebox.showerror("Delete failed",str(exc),parent=self.win)
        finally: conn.close()
        self.load_expenses()

def open_expenses_window(parent, user_id):
    ExpensesWindow(parent, user_id)

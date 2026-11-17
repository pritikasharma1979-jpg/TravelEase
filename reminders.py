import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection

def ensure_table():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS reminders (
            reminder_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL, title VARCHAR(180) NOT NULL,
            reminder_date DATETIME NOT NULL, notes VARCHAR(500),
            status VARCHAR(20) NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, INDEX (user_id))""")
        conn.commit()
    finally: conn.close()

class RemindersWindow:
    def __init__(self, parent, user_id):
        self.user_id = user_id
        ensure_table()
        self.win = tk.Toplevel(parent)
        self.win.title("TravelEase - Reminders")
        self.win.geometry("820x550")
        self.win.configure(bg="#f7f4ef")
        tk.Label(self.win,text="Travel Reminders",font=("Arial",22,"bold"),bg="#f7f4ef",fg="#245747").pack(pady=14)
        form = ttk.Frame(self.win,padding=10); form.pack(fill="x",padx=15)
        self.title_var=tk.StringVar(); self.date_var=tk.StringVar(); self.notes_var=tk.StringVar()
        for i,(label,var,width) in enumerate([("Reminder",self.title_var,26),("Date/time YYYY-MM-DD HH:MM",self.date_var,25),("Notes (optional)",self.notes_var,26)]):
            ttk.Label(form,text=label).grid(row=0,column=i,sticky="w",padx=5)
            ttk.Entry(form,textvariable=var,width=width).grid(row=1,column=i,padx=5,pady=5)
        ttk.Button(form,text="Add Reminder",command=self.add_reminder).grid(row=2,column=0,pady=8)
        ttk.Button(form,text="Mark Complete",command=self.complete_reminder).grid(row=2,column=1,pady=8)
        ttk.Button(form,text="Delete Selected",command=self.delete_reminder).grid(row=2,column=2,pady=8)
        cols=("id","title","date","status","notes")
        self.tree=ttk.Treeview(self.win,columns=cols,show="headings",height=16)
        for col,label,width in [("id","ID",50),("title","Reminder",210),("date","Date & Time",160),("status","Status",100),("notes","Notes",260)]:
            self.tree.heading(col,text=label); self.tree.column(col,width=width,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=15,pady=10)
        self.load_reminders()

    def add_reminder(self):
        title=self.title_var.get().strip(); date_text=self.date_var.get().strip(); notes=self.notes_var.get().strip()
        if not title or not date_text:
            messagebox.showerror("Missing information","Enter a title and date/time.",parent=self.win); return
        conn=get_connection()
        try:
            cur=conn.cursor()
            cur.execute("INSERT INTO reminders (user_id,title,reminder_date,notes) VALUES (%s,%s,%s,%s)",(self.user_id,title,date_text,notes or None))
            conn.commit()
        except Exception as exc:
            messagebox.showerror("Could not add reminder",f"Use date format YYYY-MM-DD HH:MM.\n{exc}",parent=self.win); return
        finally: conn.close()
        self.title_var.set(""); self.date_var.set(""); self.notes_var.set(""); self.load_reminders()

    def load_reminders(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        conn=get_connection()
        try:
            cur=conn.cursor()
            cur.execute("SELECT reminder_id,title,reminder_date,status,notes FROM reminders WHERE user_id=%s ORDER BY (status='Pending') DESC, reminder_date ASC",(self.user_id,))
            rows=cur.fetchall()
            for row in rows: self.tree.insert("","end",values=tuple("" if v is None else v for v in row))
        except Exception as exc: messagebox.showerror("Database error",str(exc),parent=self.win)
        finally: conn.close()

    def complete_reminder(self):
        selected=self.tree.selection()
        if not selected:
            messagebox.showwarning("Select reminder","Select a reminder first.",parent=self.win); return
        reminder_id=self.tree.item(selected[0],"values")[0]
        conn=get_connection()
        try:
            cur=conn.cursor(); cur.execute("UPDATE reminders SET status='Completed' WHERE reminder_id=%s AND user_id=%s",(reminder_id,self.user_id)); conn.commit()
        except Exception as exc: messagebox.showerror("Update failed",str(exc),parent=self.win)
        finally: conn.close()
        self.load_reminders()

    def delete_reminder(self):
        selected=self.tree.selection()
        if not selected:
            messagebox.showwarning("Select reminder","Select a reminder first.",parent=self.win); return
        reminder_id=self.tree.item(selected[0],"values")[0]
        if not messagebox.askyesno("Confirm","Delete selected reminder?",parent=self.win): return
        conn=get_connection()
        try:
            cur=conn.cursor(); cur.execute("DELETE FROM reminders WHERE reminder_id=%s AND user_id=%s",(reminder_id,self.user_id)); conn.commit()
        except Exception as exc: messagebox.showerror("Delete failed",str(exc),parent=self.win)
        finally: conn.close()
        self.load_reminders()

def open_reminders_window(parent, user_id):
    RemindersWindow(parent, user_id)

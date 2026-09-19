import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import secrets
import time
import csv
import shutil
import os
from tkinter import filedialog


# ============================================================
# DATABASE
# ============================================================

DB_NAME = "expenses.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            mobile TEXT
        )
    """)

    # Existing expenses.db files may already have the users table without
    # the mobile column. Add it safely without deleting existing accounts.
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [row[1] for row in cursor.fetchall()]
    if "mobile" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN mobile TEXT")

    # Existing databases may already have expenses/income tables without user_id.
    cursor.execute("PRAGMA table_info(expenses)")
    expense_columns = [row[1] for row in cursor.fetchall()]
    if "user_id" not in expense_columns:
        cursor.execute("ALTER TABLE expenses ADD COLUMN user_id INTEGER")

    cursor.execute("PRAGMA table_info(income)")
    income_columns = [row[1] for row in cursor.fetchall()]
    if "user_id" not in income_columns:
        cursor.execute("ALTER TABLE income ADD COLUMN user_id INTEGER")

    # This app was originally single-user. Keep old records by assigning
    # unowned legacy records to the first registered account.
    cursor.execute("SELECT id FROM users ORDER BY id LIMIT 1")
    first_user = cursor.fetchone()
    if first_user:
        cursor.execute("UPDATE expenses SET user_id=? WHERE user_id IS NULL", (first_user[0],))
        cursor.execute("UPDATE income SET user_id=? WHERE user_id IS NULL", (first_user[0],))

    conn.commit()
    conn.close()


# ============================================================
# HELPERS
# ============================================================

def today():
    return datetime.now().strftime("%Y-%m-%d")


def money(value):
    return f"₹{value:,.2f}"


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()
root.title("Personal Expense Tracker")
root.geometry("1200x750")
root.minsize(950, 650)
root.configure(bg="#f4f6f8")

try:
    root.state("zoomed")
except:
    pass


# ============================================================
# COLORS
# ============================================================

BG = "#f4f6f8"
CARD = "#ffffff"
PRIMARY = "#2563eb"
SUCCESS = "#16a34a"
DANGER = "#dc2626"
WARNING = "#d97706"
TEXT = "#1f2937"
SUBTEXT = "#6b7280"
BORDER = "#e5e7eb"


# ============================================================
# STYLE
# ============================================================

style = ttk.Style()

try:
    style.theme_use("clam")
except:
    pass

style.configure(
    "TButton",
    font=("Segoe UI", 10),
    padding=(12, 7)
)

style.configure(
    "Treeview",
    font=("Segoe UI", 10),
    rowheight=32,
    background="white",
    fieldbackground="white"
)

style.configure(
    "Treeview.Heading",
    font=("Segoe UI", 10, "bold")
)

style.configure(
    "TEntry",
    padding=7,
    font=("Segoe UI", 10)
)

style.configure(
    "TCombobox",
    padding=7,
    font=("Segoe UI", 10)
)


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(
    root,
    bg=PRIMARY,
    height=70
)

header.pack(fill="x")
header.pack_propagate(False)

tk.Label(
    header,
    text="PERSONAL EXPENSE TRACKER",
    bg=PRIMARY,
    fg="white",
    font=("Segoe UI", 20, "bold")
).pack(
    side="left",
    padx=25
)

# Logged-in user label (updated after login)
current_username = ""

user_label = tk.Label(
    header,
    text="User: -",
    bg=PRIMARY,
    fg="white",
    font=("Segoe UI", 10, "bold")
)
user_label.pack(
    side="right",
    padx=12
)

tk.Label(
    header,
    text=datetime.now().strftime("%d %B %Y"),
    bg=PRIMARY,
    fg="white",
    font=("Segoe UI", 10)
).pack(
    side="right",
    padx=15
)


def logout_user():
    global current_user_id, current_username

    if not messagebox.askyesno(
        "Logout",
        "Kya aap logout karna chahte hain?",
        parent=root
    ):
        return

    current_user_id = None
    current_username = ""
    user_label.config(text="User: -")
    show_login()


tk.Button(
    header,
    text="LOGOUT",
    command=logout_user,
    bg="white",
    fg=PRIMARY,
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    cursor="hand2",
    padx=12,
    pady=5
).pack(
    side="right",
    padx=10
)

# Profile button
tk.Button(
    header,
    text="PROFILE",
    command=lambda: open_profile(),
    bg="white",
    fg=PRIMARY,
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    cursor="hand2",
    padx=12,
    pady=5
).pack(
    side="right",
    padx=5
)


# ============================================================
# MAIN
# ============================================================

main = tk.Frame(
    root,
    bg=BG
)

main.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=15
)


# ============================================================
# DASHBOARD
# ============================================================

dashboard = tk.Frame(
    main,
    bg=BG
)

dashboard.pack(
    fill="x",
    pady=(0, 15)
)


def create_card(parent, title, value, color):

    card = tk.Frame(
        parent,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    card.pack(
        side="left",
        fill="both",
        expand=True,
        padx=6
    )

    tk.Label(
        card,
        text=title,
        bg=CARD,
        fg=SUBTEXT,
        font=("Segoe UI", 10)
    ).pack(
        anchor="w",
        padx=15,
        pady=(12, 3)
    )

    value_label = tk.Label(
        card,
        text=value,
        bg=CARD,
        fg=color,
        font=("Segoe UI", 18, "bold")
    )

    value_label.pack(
        anchor="w",
        padx=15,
        pady=(0, 12)
    )

    return value_label


income_card = create_card(
    dashboard,
    "TOTAL INCOME",
    "₹0.00",
    SUCCESS
)

expense_card = create_card(
    dashboard,
    "TOTAL EXPENSE",
    "₹0.00",
    DANGER
)

transaction_card = create_card(
    dashboard,
    "TRANSACTIONS",
    "0",
    PRIMARY
)

today_card = create_card(
    dashboard,
    "TODAY'S EXPENSE",
    "₹0.00",
    WARNING
)

balance_card = create_card(
    dashboard,
    "BALANCE",
    "₹0.00",
    SUCCESS
)


# ============================================================
# INPUT SECTION
# ============================================================

input_frame = tk.Frame(
    main,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)

input_frame.pack(
    fill="x",
    pady=(0, 12)
)


# ---------------- INCOME ----------------

tk.Label(
    input_frame,
    text="ADD INCOME",
    bg=CARD,
    fg=TEXT,
    font=("Segoe UI", 11, "bold")
).grid(
    row=0,
    column=0,
    padx=15,
    pady=(12, 5),
    sticky="w"
)

income_amount_entry = ttk.Entry(
    input_frame,
    width=18
)

income_amount_entry.grid(
    row=1,
    column=0,
    padx=15,
    pady=(0, 12)
)

income_button = ttk.Button(
    input_frame,
    text="Add Income",
    command=lambda: add_income()
)

income_button.grid(
    row=1,
    column=1,
    padx=5,
    pady=(0, 12)
)

edit_income_button = ttk.Button(
    input_frame,
    text="Edit Income",
    command=lambda: edit_income()
)

edit_income_button.grid(
    row=1,
    column=2,
    padx=5,
    pady=(0, 12)
)

delete_income_button = ttk.Button(
    input_frame,
    text="Delete Income",
    command=lambda: delete_income()
)

delete_income_button.grid(
    row=1,
    column=3,
    padx=5,
    pady=(0, 12)
)

income_history_button = ttk.Button(
    input_frame,
    text="Income History",
    command=lambda: income_history()
)

income_history_button.grid(
    row=1,
    column=4,
    padx=5,
    pady=(0, 12)
)


# Separator

separator = ttk.Separator(
    input_frame,
    orient="vertical"
)

separator.grid(
    row=0,
    column=5,
    rowspan=2,
    sticky="ns",
    padx=20
)


# ---------------- EXPENSE ----------------

tk.Label(
    input_frame,
    text="ADD EXPENSE",
    bg=CARD,
    fg=TEXT,
    font=("Segoe UI", 11, "bold")
).grid(
    row=0,
    column=6,
    padx=10,
    pady=(12, 5),
    sticky="w"
)

amount_entry = ttk.Entry(
    input_frame,
    width=16
)

amount_entry.grid(
    row=1,
    column=6,
    padx=10,
    pady=(0, 12)
)

category_combo = ttk.Combobox(
    input_frame,
    values=[
        "Food",
        "Travel",
        "Shopping",
        "Bills",
        "Education",
        "Entertainment",
        "Health",
        "Mobile",
        "Internet",
        "Other"
    ],
    width=16,
    state="readonly"
)

category_combo.grid(
    row=1,
    column=7,
    padx=10,
    pady=(0, 12)
)

category_combo.set("Food")

description_entry = ttk.Entry(
    input_frame,
    width=25
)

description_entry.grid(
    row=1,
    column=8,
    padx=10,
    pady=(0, 12)
)

add_expense_button = ttk.Button(
    input_frame,
    text="Add Expense",
    command=lambda: add_expense()
)

add_expense_button.grid(
    row=1,
    column=9,
    padx=10,
    pady=(0, 12)
)


# ============================================================
# SEARCH / ACTIONS
# ============================================================

action_frame = tk.Frame(
    main,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)

action_frame.pack(
    fill="x",
    pady=(0, 12)
)

tk.Label(
    action_frame,
    text="Search:",
    bg=CARD,
    fg=TEXT,
    font=("Segoe UI", 10, "bold")
).grid(
    row=0,
    column=0,
    padx=(15, 5),
    pady=10
)

search_entry = ttk.Entry(
    action_frame,
    width=28
)

search_entry.grid(
    row=0,
    column=1,
    padx=5,
    pady=10
)

search_button = ttk.Button(
    action_frame,
    text="Search",
    command=lambda: search_expenses()
)

search_button.grid(
    row=0,
    column=2,
    padx=5,
    pady=10
)

refresh_button = ttk.Button(
    action_frame,
    text="Refresh",
    command=lambda: refresh_table()
)

refresh_button.grid(
    row=0,
    column=3,
    padx=5,
    pady=10
)

analytics_button = ttk.Button(
    action_frame,
    text="Analytics",
    command=lambda: show_analytics()
)

analytics_button.grid(
    row=0,
    column=4,
    padx=5,
    pady=10
)

edit_button = ttk.Button(
    action_frame,
    text="Edit Selected",
    command=lambda: edit_selected()
)

edit_button.grid(
    row=0,
    column=5,
    padx=5,
    pady=10
)

delete_button = ttk.Button(
    action_frame,
    text="Delete Selected",
    command=lambda: delete_selected()
)

delete_button.grid(
    row=0,
    column=6,
    padx=5,
    pady=10
)

total_button = ttk.Button(
    action_frame,
    text="Show Total",
    command=lambda: show_total()
)

total_button.grid(
    row=0,
    column=7,
    padx=5,
    pady=10
)

charts_button = ttk.Button(
    action_frame,
    text="Charts",
    command=lambda: show_charts()
)

charts_button.grid(
    row=0,
    column=8,
    padx=5,
    pady=10
)

export_button = ttk.Button(
    action_frame,
    text="Export",
    command=lambda: open_export_center()
)

export_button.grid(
    row=0,
    column=9,
    padx=5,
    pady=10
)

about_button = ttk.Button(
    action_frame,
    text="About",
    command=lambda: show_about()
)

about_button.grid(
    row=0,
    column=10,
    padx=5,
    pady=10
)


# ============================================================
# EXPENSE TABLE
# ============================================================

table_frame = tk.Frame(
    main,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)

table_frame.pack(
    fill="both",
    expand=True
)

columns = (
    "ID",
    "Amount",
    "Category",
    "Description",
    "Date"
)

tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

tree.heading("ID", text="ID")
tree.heading("Amount", text="Amount")
tree.heading("Category", text="Category")
tree.heading("Description", text="Description")
tree.heading("Date", text="Date")

tree.column(
    "ID",
    width=60,
    anchor="center"
)

tree.column(
    "Amount",
    width=130,
    anchor="center"
)

tree.column(
    "Category",
    width=150,
    anchor="center"
)

tree.column(
    "Description",
    width=400
)

tree.column(
    "Date",
    width=130,
    anchor="center"
)

scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=tree.yview
)

tree.configure(
    yscrollcommand=scrollbar.set
)

tree.pack(
    side="left",
    fill="both",
    expand=True
)

scrollbar.pack(
    side="right",
    fill="y"
)


# ============================================================
# STATUS BAR
# ============================================================

status_var = tk.StringVar(
    value="Ready"
)

status_bar = tk.Label(
    root,
    textvariable=status_var,
    bg="#e5e7eb",
    fg=TEXT,
    anchor="w",
    padx=15,
    font=("Segoe UI", 9)
)

status_bar.pack(
    fill="x"
)


current_user_id = None

# ============================================================
# DASHBOARD UPDATE
# ============================================================

def update_dashboard():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM income WHERE user_id = ?",
        (current_user_id,)
    )

    total_income = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
        (current_user_id,)
    )

    total_expense = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id = ?",
        (current_user_id,)
    )

    transaction_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) "
        "FROM expenses WHERE date = ? AND user_id = ?",
        (today(), current_user_id)
    )

    today_expense = cursor.fetchone()[0]

    conn.close()

    balance = total_income - total_expense

    income_card.config(
        text=money(total_income)
    )

    expense_card.config(
        text=money(total_expense)
    )

    transaction_card.config(
        text=str(transaction_count)
    )

    today_card.config(
        text=money(today_expense)
    )

    balance_card.config(
        text=money(balance),
        fg=SUCCESS if balance >= 0 else DANGER
    )


# ============================================================
# REFRESH EXPENSE TABLE
# ============================================================

def refresh_table(search_text=""):

    for item in tree.get_children():
        tree.delete(item)

    conn = get_connection()
    cursor = conn.cursor()

    if search_text.strip():

        value = f"%{search_text}%"

        cursor.execute("""
            SELECT id, amount, category, description, date
            FROM expenses
            WHERE user_id = ?
              AND (category LIKE ? OR description LIKE ?)
            ORDER BY date DESC, id DESC
        """, (current_user_id, value, value))

    else:

        cursor.execute("""
            SELECT id, amount, category, description, date
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
        """, (current_user_id,))

    rows = cursor.fetchall()

    conn.close()

    for row in rows:

        tree.insert(
            "",
            "end",
            values=(
                row[0],
                money(row[1]),
                row[2],
                row[3] if row[3] else "",
                row[4]
            )
        )

    update_dashboard()

    status_var.set(
        f"{len(rows)} expense record(s) displayed"
    )


# ============================================================
# ADD INCOME
# ============================================================

def add_income():

    value = income_amount_entry.get().strip()

    if not value:

        messagebox.showwarning(
            "Missing Amount",
            "Please enter income amount."
        )

        income_amount_entry.focus()
        return

    try:

        amount = float(value)

        if amount <= 0:
            raise ValueError

    except ValueError:

        messagebox.showerror(
            "Invalid Amount",
            "Please enter a valid positive amount."
        )

        income_amount_entry.focus()
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO income (user_id, amount, date) VALUES (?, ?, ?)",
        (current_user_id, amount, today())
    )

    conn.commit()
    conn.close()

    income_amount_entry.delete(
        0,
        tk.END
    )

    update_dashboard()

    status_var.set(
        f"Income {money(amount)} added successfully."
    )

    income_amount_entry.focus()


# ============================================================
# INCOME HISTORY
# ============================================================

def income_history():

    window = tk.Toplevel(root)
    window.title("Income History")
    window.geometry("650x500")
    window.minsize(550, 400)
    window.configure(bg=BG)
    window.transient(root)

    tk.Label(
        window,
        text="INCOME HISTORY",
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 16, "bold")
    ).pack(
        pady=15
    )

    frame = tk.Frame(
        window,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=5
    )

    columns = (
        "ID",
        "Amount",
        "Date"
    )

    income_tree = ttk.Treeview(
        frame,
        columns=columns,
        show="headings"
    )

    income_tree.heading(
        "ID",
        text="ID"
    )

    income_tree.heading(
        "Amount",
        text="Amount"
    )

    income_tree.heading(
        "Date",
        text="Date"
    )

    income_tree.column(
        "ID",
        width=80,
        anchor="center"
    )

    income_tree.column(
        "Amount",
        width=200,
        anchor="center"
    )

    income_tree.column(
        "Date",
        width=180,
        anchor="center"
    )

    income_scroll = ttk.Scrollbar(
        frame,
        orient="vertical",
        command=income_tree.yview
    )

    income_tree.configure(
        yscrollcommand=income_scroll.set
    )

    income_tree.pack(
        side="left",
        fill="both",
        expand=True
    )

    income_scroll.pack(
        side="right",
        fill="y"
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, amount, date
        FROM income
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (current_user_id,))

    rows = cursor.fetchall()

    conn.close()

    for row in rows:

        income_tree.insert(
            "",
            "end",
            values=(
                row[0],
                money(row[1]),
                row[2]
            )
        )

    total = sum(row[1] for row in rows)

    tk.Label(
        window,
        text=f"Total Income: {money(total)}",
        bg=BG,
        fg=SUCCESS,
        font=("Segoe UI", 12, "bold")
    ).pack(
        pady=15
    )

    income_tree.bind(
        "<Escape>",
        lambda event: window.destroy()
    )


# ============================================================
# DELETE INCOME
# ============================================================

def delete_income():

    window = tk.Toplevel(root)
    window.title("Delete Income")
    window.geometry("600x450")
    window.minsize(500, 350)
    window.configure(bg=BG)
    window.transient(root)
    window.grab_set()

    tk.Label(
        window,
        text="DELETE INCOME",
        bg=BG,
        fg=DANGER,
        font=("Segoe UI", 16, "bold")
    ).pack(
        pady=15
    )

    frame = tk.Frame(
        window,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=5
    )

    columns = (
        "ID",
        "Amount",
        "Date"
    )

    income_tree = ttk.Treeview(
        frame,
        columns=columns,
        show="headings",
        selectmode="browse"
    )

    income_tree.heading(
        "ID",
        text="ID"
    )

    income_tree.heading(
        "Amount",
        text="Amount"
    )

    income_tree.heading(
        "Date",
        text="Date"
    )

    income_tree.column(
        "ID",
        width=80,
        anchor="center"
    )

    income_tree.column(
        "Amount",
        width=180,
        anchor="center"
    )

    income_tree.column(
        "Date",
        width=160,
        anchor="center"
    )

    income_tree.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, amount, date
        FROM income
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (current_user_id,))

    rows = cursor.fetchall()

    conn.close()

    for row in rows:

        income_tree.insert(
            "",
            "end",
            values=(
                row[0],
                money(row[1]),
                row[2]
            )
        )

    def remove_income():

        selected = income_tree.selection()

        if not selected:

            messagebox.showwarning(
                "Select Income",
                "Please select an income record.",
                parent=window
            )

            income_tree.focus_set()
            return

        values = income_tree.item(
            selected[0],
            "values"
        )

        income_id = int(values[0])

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete:\n\n"
            f"Amount: {values[1]}\n"
            f"Date: {values[2]}",
            parent=window
        )

        if not confirm:
            income_tree.focus_set()
            return

        conn2 = get_connection()
        cursor2 = conn2.cursor()

        cursor2.execute(
            "DELETE FROM income WHERE id = ? AND user_id = ?",
            (income_id, current_user_id)
        )

        conn2.commit()
        conn2.close()

        window.destroy()

        update_dashboard()

        status_var.set(
            "Income deleted successfully."
        )

    ttk.Button(
        window,
        text="Delete Selected Income",
        command=remove_income
    ).pack(
        pady=15
    )

    # ========================================================
    # IMPORTANT:
    # ENTER KEY = DELETE SELECTED INCOME
    # ========================================================

    income_tree.bind(
        "<Return>",
        lambda event: remove_income()
    )

    # DELETE KEY = DELETE SELECTED INCOME

    income_tree.bind(
        "<Delete>",
        lambda event: remove_income()
    )

    # ESC KEY = CLOSE WINDOW

    income_tree.bind(
        "<Escape>",
        lambda event: window.destroy()
    )

    income_tree.focus_set()


# ============================================================
# EDIT INCOME
# ============================================================

def edit_income():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, amount, date
        FROM income
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (current_user_id,))

    rows = cursor.fetchall()

    conn.close()

    if not rows:

        messagebox.showinfo(
            "No Income",
            "No income record available."
        )

        return

    window = tk.Toplevel(root)
    window.title("Edit Income")
    window.geometry("600x500")
    window.minsize(500, 400)
    window.configure(bg=BG)
    window.transient(root)
    window.grab_set()

    tk.Label(
        window,
        text="EDIT INCOME",
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 16, "bold")
    ).pack(
        pady=15
    )

    listbox = tk.Listbox(
        window,
        font=("Segoe UI", 11),
        height=8
    )

    listbox.pack(
        fill="both",
        expand=True,
        padx=20
    )

    for row in rows:

        listbox.insert(
            tk.END,
            f"ID {row[0]}     {money(row[1])}     {row[2]}"
        )

    tk.Label(
        window,
        text="New Amount:",
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 10, "bold")
    ).pack(
        pady=(15, 5)
    )

    new_amount_entry = ttk.Entry(
        window,
        width=25
    )

    new_amount_entry.pack()

    def save_income():

        selected = listbox.curselection()

        if not selected:

            messagebox.showwarning(
                "Select Record",
                "Please select an income record.",
                parent=window
            )

            return

        value = new_amount_entry.get().strip()

        try:

            new_amount = float(value)

            if new_amount <= 0:
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Invalid Amount",
                "Enter a valid positive amount.",
                parent=window
            )

            return

        income_id = rows[selected[0]][0]

        conn2 = get_connection()
        cursor2 = conn2.cursor()

        cursor2.execute(
            "UPDATE income SET amount = ? WHERE id = ? AND user_id = ?",
            (new_amount, income_id, current_user_id)
        )

        conn2.commit()
        conn2.close()

        window.destroy()

        update_dashboard()

        status_var.set(
            "Income updated successfully."
        )

    ttk.Button(
        window,
        text="Save Changes",
        command=save_income
    ).pack(
        pady=15
    )

    listbox.bind(
        "<Return>",
        lambda event: new_amount_entry.focus()
    )

    new_amount_entry.bind(
        "<Return>",
        lambda event: save_income()
    )

    window.bind(
        "<Escape>",
        lambda event: window.destroy()
    )


# ============================================================
# ADD EXPENSE
# ============================================================

def add_expense():

    amount_value = amount_entry.get().strip()
    category = category_combo.get().strip()
    description = description_entry.get().strip()

    if not amount_value:

        messagebox.showwarning(
            "Missing Amount",
            "Please enter expense amount."
        )

        amount_entry.focus()
        return

    try:

        amount = float(amount_value)

        if amount <= 0:
            raise ValueError

    except ValueError:

        messagebox.showerror(
            "Invalid Amount",
            "Please enter a valid positive amount."
        )

        amount_entry.focus()
        return

    if not category:

        messagebox.showwarning(
            "Missing Category",
            "Please select a category."
        )

        category_combo.focus()
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses
        (user_id, amount, category, description, date)
        VALUES (?, ?, ?, ?, ?)
    """, (
        current_user_id,
        amount,
        category,
        description,
        today()
    ))

    conn.commit()
    conn.close()

    amount_entry.delete(
        0,
        tk.END
    )

    description_entry.delete(
        0,
        tk.END
    )

    refresh_table()

    status_var.set(
        f"Expense {money(amount)} added successfully."
    )

    amount_entry.focus()


# ============================================================
# SELECTED EXPENSE ID
# ============================================================

def get_selected_id():

    selected = tree.selection()

    if not selected:

        messagebox.showwarning(
            "No Selection",
            "Please select an expense record first."
        )

        return None

    values = tree.item(
        selected[0],
        "values"
    )

    return int(values[0])


# ============================================================
# EDIT EXPENSE
# ============================================================

def edit_selected():

    expense_id = get_selected_id()

    if expense_id is None:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT amount, category, description, date
        FROM expenses
        WHERE id = ? AND user_id = ?
    """, (expense_id, current_user_id))

    row = cursor.fetchone()

    conn.close()

    if not row:

        messagebox.showerror(
            "Error",
            "Expense record not found."
        )

        return

    window = tk.Toplevel(root)
    window.title("Edit Expense")
    window.geometry("550x450")
    window.configure(bg=BG)
    window.transient(root)
    window.grab_set()

    tk.Label(
        window,
        text="EDIT EXPENSE",
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 16, "bold")
    ).pack(
        pady=15
    )

    form = tk.Frame(
        window,
        bg=BG
    )

    form.pack(
        padx=30
    )

    tk.Label(
        form,
        text="Amount:",
        bg=BG,
        fg=TEXT
    ).grid(
        row=0,
        column=0,
        sticky="w",
        pady=8
    )

    edit_amount = ttk.Entry(
        form,
        width=30
    )

    edit_amount.grid(
        row=0,
        column=1,
        pady=8
    )

    edit_amount.insert(
        0,
        str(row[0])
    )

    tk.Label(
        form,
        text="Category:",
        bg=BG,
        fg=TEXT
    ).grid(
        row=1,
        column=0,
        sticky="w",
        pady=8
    )

    edit_category = ttk.Combobox(
        form,
        values=[
            "Food",
            "Travel",
            "Shopping",
            "Bills",
            "Education",
            "Entertainment",
            "Health",
            "Mobile",
            "Internet",
            "Other"
        ],
        width=27,
        state="readonly"
    )

    edit_category.grid(
        row=1,
        column=1,
        pady=8
    )

    edit_category.set(row[1])

    tk.Label(
        form,
        text="Description:",
        bg=BG,
        fg=TEXT
    ).grid(
        row=2,
        column=0,
        sticky="w",
        pady=8
    )

    edit_description = ttk.Entry(
        form,
        width=30
    )

    edit_description.grid(
        row=2,
        column=1,
        pady=8
    )

    edit_description.insert(
        0,
        row[2] if row[2] else ""
    )

    tk.Label(
        form,
        text="Date:",
        bg=BG,
        fg=TEXT
    ).grid(
        row=3,
        column=0,
        sticky="w",
        pady=8
    )

    edit_date = ttk.Entry(
        form,
        width=30
    )

    edit_date.grid(
        row=3,
        column=1,
        pady=8
    )

    edit_date.insert(
        0,
        row[3]
    )

    def save_changes():

        try:

            amount = float(
                edit_amount.get().strip()
            )

            if amount <= 0:
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Invalid Amount",
                "Enter a valid positive amount.",
                parent=window
            )

            return

        category = edit_category.get().strip()
        description = edit_description.get().strip()
        date_value = edit_date.get().strip()

        if not category or not date_value:

            messagebox.showwarning(
                "Missing Information",
                "Category and Date are required.",
                parent=window
            )

            return

        conn2 = get_connection()
        cursor2 = conn2.cursor()

        cursor2.execute("""
            UPDATE expenses
            SET amount = ?,
                category = ?,
                description = ?,
                date = ?
            WHERE id = ? AND user_id = ?
        """, (
            amount,
            category,
            description,
            date_value,
            expense_id,
            current_user_id
        ))

        conn2.commit()
        conn2.close()

        window.destroy()

        refresh_table()

        status_var.set(
            "Expense updated successfully."
        )

    ttk.Button(
        window,
        text="Save Changes",
        command=save_changes
    ).pack(
        pady=20
    )

    edit_amount.bind(
        "<Return>",
        lambda event: edit_category.focus()
    )

    edit_category.bind(
        "<Return>",
        lambda event: edit_description.focus()
    )

    edit_description.bind(
        "<Return>",
        lambda event: edit_date.focus()
    )

    edit_date.bind(
        "<Return>",
        lambda event: save_changes()
    )

    window.bind(
        "<Escape>",
        lambda event: window.destroy()
    )


# ============================================================
# DELETE EXPENSE
# ============================================================

def delete_selected():

    expense_id = get_selected_id()

    if expense_id is None:
        return

    selected = tree.selection()[0]

    values = tree.item(
        selected,
        "values"
    )

    confirm = messagebox.askyesno(
        "Confirm Delete",
        f"Delete this expense?\n\n"
        f"Amount: {values[1]}\n"
        f"Category: {values[2]}\n"
        f"Description: {values[3]}"
    )

    if not confirm:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, current_user_id)
    )

    conn.commit()
    conn.close()

    refresh_table()

    status_var.set(
        "Expense deleted successfully."
    )


# ============================================================
# SEARCH
# ============================================================

def search_expenses():

    text = search_entry.get().strip()

    refresh_table(text)

    if text:

        status_var.set(
            f"Search results for: {text}"
        )


# ============================================================
# TOTAL
# ============================================================

def show_total():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
        (current_user_id,)
    )

    total_expense = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM income WHERE user_id = ?",
        (current_user_id,)
    )

    total_income = cursor.fetchone()[0]

    conn.close()

    balance = total_income - total_expense

    messagebox.showinfo(
        "Financial Summary",
        f"Total Income: {money(total_income)}\n\n"
        f"Total Expense: {money(total_expense)}\n\n"
        f"Balance: {money(balance)}"
    )


# ============================================================
# ANALYTICS
# ============================================================

def show_analytics():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (current_user_id,))

    category_data = cursor.fetchall()

    cursor.execute("""
        SELECT substr(date, 1, 7), SUM(amount)
        FROM expenses
        WHERE user_id = ?
        GROUP BY substr(date, 1, 7)
        ORDER BY substr(date, 1, 7)
    """, (current_user_id,))

    monthly_data = cursor.fetchall()

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
        (current_user_id,)
    )

    total_expense = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM income WHERE user_id = ?",
        (current_user_id,)
    )

    total_income = cursor.fetchone()[0]

    conn.close()

    if not category_data:

        messagebox.showinfo(
            "Analytics",
            "No expense data available yet."
        )

        return

    window = tk.Toplevel(root)
    window.title("Expense Analytics")
    window.geometry("1000x700")
    window.minsize(800, 600)
    window.configure(bg=BG)

    header2 = tk.Frame(
        window,
        bg=PRIMARY,
        height=65
    )

    header2.pack(fill="x")
    header2.pack_propagate(False)

    tk.Label(
        header2,
        text="EXPENSE ANALYTICS",
        bg=PRIMARY,
        fg="white",
        font=("Segoe UI", 18, "bold")
    ).pack(
        side="left",
        padx=20,
        pady=15
    )

    summary = tk.Frame(
        window,
        bg=BG
    )

    summary.pack(
        fill="x",
        padx=20,
        pady=15
    )

    balance = total_income - total_expense

    data = [
        ("Total Income", money(total_income), SUCCESS),
        ("Total Expense", money(total_expense), DANGER),
        (
            "Balance",
            money(balance),
            SUCCESS if balance >= 0 else DANGER
        )
    ]

    for title, value, color in data:

        card = tk.Frame(
            summary,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=5
        )

        tk.Label(
            card,
            text=title,
            bg=CARD,
            fg=SUBTEXT
        ).pack(
            pady=(10, 2)
        )

        tk.Label(
            card,
            text=value,
            bg=CARD,
            fg=color,
            font=("Segoe UI", 15, "bold")
        ).pack(
            pady=(0, 10)
        )

    content = tk.Frame(
        window,
        bg=BG
    )

    content.pack(
        fill="both",
        expand=True,
        padx=20
    )

    # CATEGORY

    category_frame = tk.Frame(
        content,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    category_frame.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 7)
    )

    tk.Label(
        category_frame,
        text="CATEGORY-WISE SPENDING",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 12, "bold")
    ).pack(
        pady=12
    )

    category_tree = ttk.Treeview(
        category_frame,
        columns=("Category", "Amount", "Percent"),
        show="headings"
    )

    category_tree.heading(
        "Category",
        text="Category"
    )

    category_tree.heading(
        "Amount",
        text="Amount"
    )

    category_tree.heading(
        "Percent",
        text="%"
    )

    category_tree.column(
        "Category",
        width=150,
        anchor="center"
    )

    category_tree.column(
        "Amount",
        width=120,
        anchor="center"
    )

    category_tree.column(
        "Percent",
        width=80,
        anchor="center"
    )

    category_tree.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=(0, 15)
    )

    for category, amount in category_data:

        percent = (
            amount / total_expense * 100
            if total_expense > 0
            else 0
        )

        category_tree.insert(
            "",
            "end",
            values=(
                category,
                money(amount),
                f"{percent:.1f}%"
            )
        )

    # MONTHLY

    monthly_frame = tk.Frame(
        content,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    monthly_frame.pack(
        side="right",
        fill="both",
        expand=True,
        padx=(7, 0)
    )

    tk.Label(
        monthly_frame,
        text="MONTHLY SPENDING",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 12, "bold")
    ).pack(
        pady=12
    )

    monthly_tree = ttk.Treeview(
        monthly_frame,
        columns=("Month", "Amount"),
        show="headings"
    )

    monthly_tree.heading(
        "Month",
        text="Month"
    )

    monthly_tree.heading(
        "Amount",
        text="Amount"
    )

    monthly_tree.column(
        "Month",
        width=150,
        anchor="center"
    )

    monthly_tree.column(
        "Amount",
        width=150,
        anchor="center"
    )

    monthly_tree.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=(0, 15)
    )

    for month, amount in monthly_data:

        monthly_tree.insert(
            "",
            "end",
            values=(
                month,
                money(amount)
            )
        )

    # INSIGHTS

    insights_frame = tk.Frame(
        window,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    insights_frame.pack(
        fill="x",
        padx=20,
        pady=15
    )

    top_category = category_data[0]

    highest_month = None

    if monthly_data:

        highest_month = max(
            monthly_data,
            key=lambda x: x[1]
        )

    insight = (
        f"• Highest spending category: "
        f"{top_category[0]} ({money(top_category[1])})\n"
    )

    if highest_month:

        insight += (
            f"• Highest spending month: "
            f"{highest_month[0]} ({money(highest_month[1])})\n"
        )

    if total_income > 0:

        saving_percent = (
            balance / total_income
        ) * 100

        insight += (
            f"• Balance percentage: "
            f"{saving_percent:.1f}%"
        )

    tk.Label(
        insights_frame,
        text="SMART INSIGHTS",
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 12, "bold")
    ).pack(
        anchor="w",
        padx=15,
        pady=(10, 5)
    )

    tk.Label(
        insights_frame,
        text=insight,
        bg=CARD,
        fg=SUBTEXT,
        justify="left",
        anchor="w",
        font=("Segoe UI", 10)
    ).pack(
        anchor="w",
        padx=15,
        pady=(0, 12)
    )

    window.bind(
        "<Escape>",
        lambda event: window.destroy()
    )


# ============================================================
# VISUAL CHARTS
# ============================================================

def show_charts():
    if current_user_id is None:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (current_user_id,))
    category_data = cursor.fetchall()

    cursor.execute("""
        SELECT substr(date, 1, 7), COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = ?
        GROUP BY substr(date, 1, 7)
        ORDER BY substr(date, 1, 7)
    """, (current_user_id,))
    monthly_expense = cursor.fetchall()

    cursor.execute("""
        SELECT substr(date, 1, 7), COALESCE(SUM(amount), 0)
        FROM income
        WHERE user_id = ?
        GROUP BY substr(date, 1, 7)
        ORDER BY substr(date, 1, 7)
    """, (current_user_id,))
    monthly_income = cursor.fetchall()

    conn.close()

    if not category_data and not monthly_expense and not monthly_income:
        messagebox.showinfo("Charts", "Abhi chart dikhane ke liye data available nahi hai.")
        return

    window = tk.Toplevel(root)
    window.title("Financial Charts")
    window.geometry("1100x680")
    window.minsize(900, 600)
    window.configure(bg=BG)
    window.transient(root)

    top = tk.Frame(window, bg=PRIMARY, height=65)
    top.pack(fill="x")
    top.pack_propagate(False)

    tk.Label(
        top, text="FINANCIAL CHARTS", bg=PRIMARY, fg="white",
        font=("Segoe UI", 18, "bold")
    ).pack(side="left", padx=20, pady=15)

    chart_area = tk.Frame(window, bg=BG)
    chart_area.pack(fill="both", expand=True, padx=15, pady=15)

    left = tk.Frame(chart_area, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    left.pack(side="left", fill="both", expand=True, padx=(0, 8))

    right = tk.Frame(chart_area, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    right.pack(side="right", fill="both", expand=True, padx=(8, 0))

    tk.Label(left, text="CATEGORY-WISE EXPENSE", bg=CARD, fg=TEXT,
             font=("Segoe UI", 12, "bold")).pack(pady=10)
    pie = tk.Canvas(left, bg=CARD, highlightthickness=0)
    pie.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Label(right, text="MONTHLY INCOME VS EXPENSE", bg=CARD, fg=TEXT,
             font=("Segoe UI", 12, "bold")).pack(pady=10)
    bar = tk.Canvas(right, bg=CARD, highlightthickness=0)
    bar.pack(fill="both", expand=True, padx=10, pady=10)

    def draw_pie(event=None):
        pie.delete("all")
        if not category_data:
            pie.create_text(300, 220, text="No expense data", fill=SUBTEXT, font=("Segoe UI", 12))
            return

        total = sum(amount for _, amount in category_data)
        cx, cy, r = 245, 210, 125
        start = 0
        chart_colors = ["#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed",
                        "#0891b2", "#db2777", "#65a30d", "#9333ea", "#475569"]

        for i, (category, amount) in enumerate(category_data):
            extent = (amount / total) * 360 if total else 0
            pie.create_arc(cx-r, cy-r, cx+r, cy+r, start=start, extent=extent,
                           fill=chart_colors[i % len(chart_colors)], outline="white", width=2)
            start += extent

        legend_y = 380
        for i, (category, amount) in enumerate(category_data[:10]):
            color = chart_colors[i % len(chart_colors)]
            percent = amount / total * 100 if total else 0
            pie.create_rectangle(30, legend_y, 45, legend_y+15, fill=color, outline=color)
            pie.create_text(55, legend_y+7, anchor="w", text=f"{category}: {percent:.1f}%",
                            fill=TEXT, font=("Segoe UI", 9))
            legend_y += 22

    def draw_bar(event=None):
        bar.delete("all")
        months = sorted(set([m for m, _ in monthly_expense] + [m for m, _ in monthly_income]))
        if not months:
            bar.create_text(300, 220, text="No monthly data", fill=SUBTEXT, font=("Segoe UI", 12))
            return

        expense_map = dict(monthly_expense)
        income_map = dict(monthly_income)
        max_value = max([expense_map.get(m, 0) for m in months] + [income_map.get(m, 0) for m in months] + [1])

        width = max(bar.winfo_width(), 500)
        height = max(bar.winfo_height(), 450)
        left_x, bottom_y, top_y = 55, height - 70, 35
        chart_w, chart_h = width - 90, bottom_y - top_y
        slot = chart_w / max(len(months), 1)
        bar_w = min(24, slot / 3)

        bar.create_line(left_x, top_y, left_x, bottom_y, fill=BORDER)
        bar.create_line(left_x, bottom_y, width-25, bottom_y, fill=BORDER)

        for i, month in enumerate(months):
            x = left_x + slot * i + slot / 2
            inc = income_map.get(month, 0)
            exp = expense_map.get(month, 0)
            inc_h = (inc / max_value) * chart_h
            exp_h = (exp / max_value) * chart_h

            bar.create_rectangle(x-bar_w-2, bottom_y-inc_h, x-2, bottom_y, fill="#16a34a", outline="")
            bar.create_rectangle(x+2, bottom_y-exp_h, x+bar_w+2, bottom_y, fill="#dc2626", outline="")
            bar.create_text(x, bottom_y+18, text=month, fill=TEXT, font=("Segoe UI", 8))

        bar.create_rectangle(25, 12, 40, 27, fill="#16a34a", outline="")
        bar.create_text(48, 20, anchor="w", text="Income", fill=TEXT, font=("Segoe UI", 9))
        bar.create_rectangle(105, 12, 120, 27, fill="#dc2626", outline="")
        bar.create_text(128, 20, anchor="w", text="Expense", fill=TEXT, font=("Segoe UI", 9))

    pie.bind("<Configure>", draw_pie)
    bar.bind("<Configure>", draw_bar)
    window.bind("<Escape>", lambda event: window.destroy())
    window.after(100, lambda: (draw_pie(), draw_bar()))


# ============================================================
# EXPORT / BACKUP / REPORT FEATURES
# ============================================================

def export_expenses_csv():
    if current_user_id is None:
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT amount, category, description, date
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (current_user_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        messagebox.showinfo("Export", "No expense records available.")
        return

    filename = filedialog.asksaveasfilename(
        title="Export Expenses",
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )
    if not filename:
        return

    try:
        with open(filename, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["Amount", "Category", "Description", "Date"])
            writer.writerows(rows)

        messagebox.showinfo(
            "Export Successful",
            f"Expenses exported successfully.\n\n{filename}"
        )
        status_var.set("Expense report exported successfully.")
    except Exception as e:
        messagebox.showerror("Export Error", f"Could not export expenses.\n\n{e}")


def export_income_csv():
    if current_user_id is None:
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT amount, date
        FROM income
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (current_user_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        messagebox.showinfo("Export", "No income records available.")
        return

    filename = filedialog.asksaveasfilename(
        title="Export Income",
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )
    if not filename:
        return

    try:
        with open(filename, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["Amount", "Date"])
            writer.writerows(rows)

        messagebox.showinfo(
            "Export Successful",
            f"Income exported successfully.\n\n{filename}"
        )
        status_var.set("Income report exported successfully.")
    except Exception as e:
        messagebox.showerror("Export Error", f"Could not export income.\n\n{e}")


def export_full_report():
    if current_user_id is None:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT amount, category, description, date
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (current_user_id,))
    expenses = cursor.fetchall()

    cursor.execute("""
        SELECT amount, date
        FROM income
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (current_user_id,))
    incomes = cursor.fetchall()

    cursor.execute(
        "SELECT username, mobile FROM users WHERE id = ?",
        (current_user_id,)
    )
    user = cursor.fetchone()
    conn.close()

    if not expenses and not incomes:
        messagebox.showinfo("Report", "No financial records available.")
        return

    filename = filedialog.asksaveasfilename(
        title="Export Complete Financial Report",
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )
    if not filename:
        return

    try:
        total_income = sum(float(row[0]) for row in incomes)
        total_expense = sum(float(row[0]) for row in expenses)
        balance = total_income - total_expense

        with open(filename, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)

            writer.writerow(["PERSONAL EXPENSE TRACKER - FINANCIAL REPORT"])
            writer.writerow(["Username", user[0] if user else ""])
            writer.writerow(["Mobile", user[1] if user and len(user) > 1 else ""])
            writer.writerow([])
            writer.writerow(["SUMMARY"])
            writer.writerow(["Total Income", total_income])
            writer.writerow(["Total Expense", total_expense])
            writer.writerow(["Balance", balance])
            writer.writerow([])

            writer.writerow(["INCOME"])
            writer.writerow(["Amount", "Date"])
            writer.writerows(incomes)
            writer.writerow([])

            writer.writerow(["EXPENSES"])
            writer.writerow(["Amount", "Category", "Description", "Date"])
            writer.writerows(expenses)

        messagebox.showinfo(
            "Report Exported",
            f"Complete financial report exported successfully.\n\n{filename}"
        )
        status_var.set("Complete financial report exported.")
    except Exception as e:
        messagebox.showerror("Export Error", f"Could not export report.\n\n{e}")


def open_export_center():
    window = tk.Toplevel(root)
    window.title("Export & Reports")
    window.geometry("520x430")
    window.resizable(False, False)
    window.configure(bg=BG)
    window.transient(root)
    window.grab_set()

    tk.Label(
        window,
        text="EXPORT & REPORTS",
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 18, "bold")
    ).pack(pady=(25, 8))

    tk.Label(
        window,
        text="Export only the currently logged-in user's data.",
        bg=BG,
        fg=SUBTEXT,
        font=("Segoe UI", 10)
    ).pack(pady=(0, 20))

    box = tk.Frame(
        window,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    box.pack(fill="both", expand=True, padx=30, pady=5)

    ttk.Button(
        box,
        text="Export Expenses (CSV)",
        command=export_expenses_csv
    ).pack(fill="x", padx=35, pady=(25, 8))

    ttk.Button(
        box,
        text="Export Income (CSV)",
        command=export_income_csv
    ).pack(fill="x", padx=35, pady=8)

    ttk.Button(
        box,
        text="Export Complete Financial Report",
        command=export_full_report
    ).pack(fill="x", padx=35, pady=8)

    ttk.Button(
        box,
        text="Backup Database",
        command=backup_database
    ).pack(fill="x", padx=35, pady=8)

    ttk.Button(
        box,
        text="Close",
        command=window.destroy
    ).pack(pady=(8, 20))

    window.bind("<Escape>", lambda event: window.destroy())


def backup_database():
    if not os.path.exists(DB_NAME):
        messagebox.showerror("Backup Error", "Database file not found.")
        return

    filename = filedialog.asksaveasfilename(
        title="Backup Expense Tracker Database",
        initialfile=f"expenses_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
        defaultextension=".db",
        filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
    )
    if not filename:
        return

    try:
        # Make sure pending database writes are flushed.
        conn = get_connection()
        conn.execute("PRAGMA wal_checkpoint(FULL)")
        conn.close()

        shutil.copy2(DB_NAME, filename)

        messagebox.showinfo(
            "Backup Successful",
            f"Database backup created successfully.\n\n{filename}"
        )
        status_var.set("Database backup created successfully.")
    except Exception as e:
        messagebox.showerror("Backup Error", f"Could not create backup.\n\n{e}")


def show_about():
    messagebox.showinfo(
        "About Expense Tracker",
        "PERSONAL EXPENSE TRACKER\n\n"
        "A Python Tkinter + SQLite project.\n\n"
        "Features:\n"
        "• Multi-user Login / Register\n"
        "• OTP-based demo verification\n"
        "• Forgot Password\n"
        "• Income & Expense Management\n"
        "• Dashboard & Analytics\n"
        "• Charts\n"
        "• Profile & Change Password\n"
        "• Search / Edit / Delete\n"
        "• CSV Financial Reports\n"
        "• Database Backup\n"
        "• Logout\n\n"
        "Developed as a Diploma Computer Engineering project."
    )


# ============================================================
# KEYBOARD SHORTCUTS
# ============================================================


income_amount_entry.bind(
    "<Return>",
    lambda event: add_income()
)

amount_entry.bind(
    "<Return>",
    lambda event: category_combo.focus()
)

category_combo.bind(
    "<Return>",
    lambda event: description_entry.focus()
)

description_entry.bind(
    "<Return>",
    lambda event: add_expense()
)

search_entry.bind(
    "<Return>",
    lambda event: search_expenses()
)

tree.bind(
    "<Double-1>",
    lambda event: edit_selected()
)

tree.bind(
    "<Return>",
    lambda event: edit_selected()
)

root.bind(
    "<Delete>",
    lambda event: delete_selected()
)

root.bind(
    "<Control-f>",
    lambda event: search_entry.focus()
)

root.bind(
    "<F5>",
    lambda event: refresh_table()
)

# ============================================================
# PROFILE / ACCOUNT SETTINGS
# ============================================================

def open_profile():
    """Show the current user's profile and account settings."""
    if current_user_id is None:
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, mobile FROM users WHERE id=?",
        (current_user_id,)
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        messagebox.showerror("Error", "Current user account nahi mila.", parent=root)
        return

    username, mobile = user

    window = tk.Toplevel(root)
    window.title("My Profile - Expense Tracker")
    window.geometry("430x430")
    window.resizable(False, False)
    window.configure(bg=BG)
    window.transient(root)
    window.grab_set()

    tk.Label(
        window,
        text="MY PROFILE",
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 20, "bold")
    ).pack(pady=(22, 18))

    card = tk.Frame(
        window,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    card.pack(fill="x", padx=25, pady=5)

    tk.Label(
        card, text="Username", bg=CARD, fg=SUBTEXT,
        font=("Segoe UI", 10, "bold")
    ).pack(anchor="w", padx=18, pady=(15, 2))

    tk.Label(
        card, text=username, bg=CARD, fg=TEXT,
        font=("Segoe UI", 13)
    ).pack(anchor="w", padx=18, pady=(0, 12))

    tk.Label(
        card, text="Mobile Number", bg=CARD, fg=SUBTEXT,
        font=("Segoe UI", 10, "bold")
    ).pack(anchor="w", padx=18, pady=(0, 2))

    tk.Label(
        card, text=mobile if mobile else "Not added", bg=CARD, fg=TEXT,
        font=("Segoe UI", 13)
    ).pack(anchor="w", padx=18, pady=(0, 15))

    tk.Button(
        window,
        text="CHANGE PASSWORD",
        width=24,
        command=lambda: open_change_password(window),
        bg=PRIMARY,
        fg="white",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=8
    ).pack(pady=18)

    tk.Button(
        window,
        text="CLOSE",
        width=24,
        command=window.destroy,
        bg="#e5e7eb",
        fg=TEXT,
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=8
    ).pack()

    window.bind("<Escape>", lambda event: window.destroy())


def open_change_password(parent_window=None):
    """Open a secure current-password/new-password change dialog."""
    if current_user_id is None:
        return

    window = tk.Toplevel(parent_window if parent_window else root)
    window.title("Change Password")
    window.geometry("430x410")
    window.resizable(False, False)
    window.configure(bg=BG)
    window.transient(parent_window if parent_window else root)
    window.grab_set()

    tk.Label(
        window, text="CHANGE PASSWORD", bg=BG, fg=TEXT,
        font=("Segoe UI", 19, "bold")
    ).pack(pady=(22, 18))

    tk.Label(window, text="Current Password", bg=BG, fg=TEXT).pack()
    current_entry = tk.Entry(window, width=32, show="*")
    current_entry.pack(pady=7)

    tk.Label(window, text="New Password", bg=BG, fg=TEXT).pack()
    new_entry = tk.Entry(window, width=32, show="*")
    new_entry.pack(pady=7)

    tk.Label(window, text="Confirm New Password", bg=BG, fg=TEXT).pack()
    confirm_entry = tk.Entry(window, width=32, show="*")
    confirm_entry.pack(pady=7)

    def change_password():
        current = current_entry.get()
        new_password = new_entry.get()
        confirm = confirm_entry.get()

        if not current or not new_password or not confirm:
            messagebox.showwarning(
                "Missing Fields",
                "Sabhi password fields bharo.",
                parent=window
            )
            return

        if new_password != confirm:
            messagebox.showerror(
                "Password Error",
                "New password aur confirm password same nahi hain.",
                parent=window
            )
            return

        if len(new_password) < 6:
            messagebox.showwarning(
                "Weak Password",
                "Password kam se kam 6 characters ka rakho.",
                parent=window
            )
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password FROM users WHERE id=?",
            (current_user_id,)
        )
        row = cursor.fetchone()

        if not row or row[0] != current:
            conn.close()
            messagebox.showerror(
                "Incorrect Password",
                "Current password galat hai.",
                parent=window
            )
            current_entry.focus_set()
            return

        cursor.execute(
            "UPDATE users SET password=? WHERE id=?",
            (new_password, current_user_id)
        )
        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Success",
            "Password successfully change ho gaya.",
            parent=window
        )
        window.destroy()

    tk.Button(
        window, text="UPDATE PASSWORD", width=24, command=change_password,
        bg=PRIMARY, fg="white", font=("Segoe UI", 10, "bold"),
        relief="flat", cursor="hand2", padx=10, pady=8
    ).pack(pady=16)

    current_entry.focus_set()
    confirm_entry.bind("<Return>", lambda event: change_password())
    window.bind("<Escape>", lambda event: window.destroy())


# ============================================================
# LOGIN / REGISTER SYSTEM
# ============================================================

# FREE DEMO OTP SYSTEM
# No paid SMS/WhatsApp service is used.
# OTP is generated locally and printed ONLY in the VS Code/terminal console.
# It is NOT shown in the application, so the app does not auto-suggest the OTP.
registration_otp = None
registration_otp_time = 0
forgot_otp = None
forgot_otp_time = 0


def generate_otp():
    return str(secrets.randbelow(900000) + 100000)


def valid_mobile(mobile):
    return mobile.isdigit() and len(mobile) == 10 and mobile[0] in "6789"


def send_registration_otp():
    global registration_otp, registration_otp_time

    mobile = register_mobile_entry.get().strip()

    if not valid_mobile(mobile):
        messagebox.showwarning(
            "Invalid Mobile",
            "10 digit valid mobile number enter karo.",
            parent=register_window
        )
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE mobile=?", (mobile,))
    existing = cursor.fetchone()
    conn.close()

    if existing:
        messagebox.showerror(
            "Error",
            "Ye mobile number already registered hai.",
            parent=register_window
        )
        return

    registration_otp = generate_otp()
    registration_otp_time = time.time()

    # FREE TEST MODE: do not display the OTP inside the app.
    # It is printed to the terminal so the user can manually type it.
    print("\n" + "=" * 50)
    print("EXPENSE TRACKER - REGISTRATION OTP")
    print("Mobile:", mobile)
    print("OTP:", registration_otp)
    print("Valid for: 5 minutes")
    print("=" * 50 + "\n")

    messagebox.showinfo(
        "OTP Generated",
        "OTP generate ho gaya.\n\n"
        "VS Code/Terminal console me OTP dekho aur yahan manually enter karo.",
        parent=register_window
    )
    register_otp_entry.focus_set()


def register_user():
    global registration_otp, registration_otp_time

    username = register_username_entry.get().strip()
    password = register_password_entry.get().strip()
    mobile = register_mobile_entry.get().strip()
    otp = register_otp_entry.get().strip()

    if username == "" or password == "" or mobile == "" or otp == "":
        messagebox.showwarning(
            "Warning",
            "Username, Password, Mobile Number aur OTP sab bharo.",
            parent=register_window
        )
        return

    if not valid_mobile(mobile):
        messagebox.showwarning(
            "Invalid Mobile",
            "10 digit valid mobile number enter karo.",
            parent=register_window
        )
        return

    if registration_otp is None:
        messagebox.showwarning(
            "OTP Required",
            "Pehle SEND OTP button dabao.",
            parent=register_window
        )
        return

    if time.time() - registration_otp_time > 300:
        registration_otp = None
        messagebox.showerror(
            "OTP Expired",
            "OTP expire ho gaya. Dobara SEND OTP karo.",
            parent=register_window
        )
        return

    if otp != registration_otp:
        messagebox.showerror(
            "Wrong OTP",
            "OTP galat hai.",
            parent=register_window
        )
        register_otp_entry.focus_set()
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password, mobile) VALUES (?, ?, ?)",
            (username, password, mobile)
        )
        conn.commit()

        messagebox.showinfo(
            "Success",
            "Account successfully create ho gaya! Ab Login karo.",
            parent=register_window
        )

        registration_otp = None
        registration_otp_time = 0
        register_window.destroy()

    except sqlite3.IntegrityError as e:
        if "username" in str(e).lower():
            msg = "Ye username already exist karta hai."
        elif "mobile" in str(e).lower():
            msg = "Ye mobile number already registered hai."
        else:
            msg = "Account create nahi ho saka."
        messagebox.showerror("Error", msg, parent=register_window)

    finally:
        conn.close()


def open_register():
    global register_window
    global register_username_entry
    global register_password_entry
    global register_mobile_entry
    global register_otp_entry

    register_window = tk.Toplevel(login_window)
    register_window.title("Register - Expense Tracker")
    register_window.geometry("430x470")
    register_window.resizable(False, False)
    register_window.transient(login_window)
    register_window.grab_set()

    tk.Label(
        register_window,
        text="CREATE ACCOUNT",
        font=("Arial", 20, "bold")
    ).pack(pady=18)

    tk.Label(register_window, text="Username").pack()
    register_username_entry = tk.Entry(register_window, width=32)
    register_username_entry.pack(pady=5)

    tk.Label(register_window, text="Password").pack()
    register_password_entry = tk.Entry(
        register_window,
        width=32,
        show="*"
    )
    register_password_entry.pack(pady=5)

    tk.Label(register_window, text="Mobile Number").pack()
    register_mobile_entry = tk.Entry(register_window, width=32)
    register_mobile_entry.pack(pady=5)

    tk.Button(
        register_window,
        text="SEND OTP",
        width=18,
        command=send_registration_otp
    ).pack(pady=7)

    tk.Label(register_window, text="Enter OTP").pack()
    register_otp_entry = tk.Entry(register_window, width=32)
    register_otp_entry.pack(pady=5)

    tk.Button(
        register_window,
        text="CREATE ACCOUNT",
        width=20,
        command=register_user
    ).pack(pady=15)

    register_username_entry.focus_set()

    register_window.bind(
        "<Escape>",
        lambda event: register_window.destroy()
    )


def send_forgot_otp():
    global forgot_otp, forgot_otp_time

    mobile = forgot_mobile_entry.get().strip()

    if not valid_mobile(mobile):
        messagebox.showwarning(
            "Invalid Mobile",
            "10 digit valid mobile number enter karo.",
            parent=forgot_window
        )
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE mobile=?", (mobile,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        messagebox.showerror(
            "Not Found",
            "Is mobile number se koi account nahi mila.",
            parent=forgot_window
        )
        return

    forgot_otp = generate_otp()
    forgot_otp_time = time.time()

    # FREE TEST MODE: do not display the OTP inside the app.
    print("\n" + "=" * 50)
    print("EXPENSE TRACKER - PASSWORD RESET OTP")
    print("Mobile:", mobile)
    print("OTP:", forgot_otp)
    print("Valid for: 5 minutes")
    print("=" * 50 + "\n")

    messagebox.showinfo(
        "OTP Generated",
        "OTP generate ho gaya.\n\n"
        "VS Code/Terminal console me OTP dekho aur yahan manually enter karo.",
        parent=forgot_window
    )
    forgot_otp_entry.focus_set()


def reset_password():
    global forgot_otp, forgot_otp_time

    mobile = forgot_mobile_entry.get().strip()
    otp = forgot_otp_entry.get().strip()
    new_password = forgot_new_password_entry.get().strip()
    confirm_password = forgot_confirm_password_entry.get().strip()

    if mobile == "" or otp == "" or new_password == "" or confirm_password == "":
        messagebox.showwarning(
            "Warning",
            "Mobile, OTP aur new password ki fields bharo.",
            parent=forgot_window
        )
        return

    if forgot_otp is None:
        messagebox.showwarning(
            "OTP Required",
            "Pehle SEND OTP button dabao.",
            parent=forgot_window
        )
        return

    if time.time() - forgot_otp_time > 300:
        forgot_otp = None
        messagebox.showerror(
            "OTP Expired",
            "OTP expire ho gaya. Dobara SEND OTP karo.",
            parent=forgot_window
        )
        return

    if otp != forgot_otp:
        messagebox.showerror(
            "Wrong OTP",
            "OTP galat hai.",
            parent=forgot_window
        )
        return

    if new_password != confirm_password:
        messagebox.showerror(
            "Password Error",
            "New password aur confirm password same nahi hain.",
            parent=forgot_window
        )
        return

    if len(new_password) < 6:
        messagebox.showwarning(
            "Weak Password",
            "Password kam se kam 6 characters ka rakho.",
            parent=forgot_window
        )
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password=? WHERE mobile=?",
        (new_password, mobile)
    )
    conn.commit()
    updated = cursor.rowcount
    conn.close()

    if updated:
        forgot_otp = None
        forgot_otp_time = 0
        messagebox.showinfo(
            "Success",
            "Password successfully reset ho gaya. Ab new password se Login karo.",
            parent=forgot_window
        )
        forgot_window.destroy()
    else:
        messagebox.showerror(
            "Error",
            "Password reset nahi ho saka.",
            parent=forgot_window
        )


def open_forgot_password():
    global forgot_window
    global forgot_mobile_entry
    global forgot_otp_entry
    global forgot_new_password_entry
    global forgot_confirm_password_entry

    forgot_window = tk.Toplevel(login_window)
    forgot_window.title("Forgot Password - Expense Tracker")
    forgot_window.geometry("430x450")
    forgot_window.resizable(False, False)
    forgot_window.transient(login_window)
    forgot_window.grab_set()

    tk.Label(
        forgot_window,
        text="FORGOT PASSWORD",
        font=("Arial", 20, "bold")
    ).pack(pady=20)

    tk.Label(forgot_window, text="Registered Mobile Number").pack()
    forgot_mobile_entry = tk.Entry(forgot_window, width=32)
    forgot_mobile_entry.pack(pady=6)

    tk.Button(
        forgot_window,
        text="SEND OTP",
        width=18,
        command=send_forgot_otp
    ).pack(pady=8)

    tk.Label(forgot_window, text="Enter OTP").pack()
    forgot_otp_entry = tk.Entry(forgot_window, width=32)
    forgot_otp_entry.pack(pady=6)

    tk.Label(forgot_window, text="New Password").pack()
    forgot_new_password_entry = tk.Entry(
        forgot_window,
        width=32,
        show="*"
    )
    forgot_new_password_entry.pack(pady=6)

    tk.Label(forgot_window, text="Confirm New Password").pack()
    forgot_confirm_password_entry = tk.Entry(
        forgot_window,
        width=32,
        show="*"
    )
    forgot_confirm_password_entry.pack(pady=6)

    tk.Button(
        forgot_window,
        text="RESET PASSWORD",
        width=20,
        command=reset_password
    ).pack(pady=15)

    forgot_mobile_entry.focus_set()

    forgot_window.bind(
        "<Escape>",
        lambda event: forgot_window.destroy()
    )


def login_user():
    global current_user_id
    global current_username

    username = login_username_entry.get().strip()
    password = login_password_entry.get().strip()

    if username == "" or password == "":
        messagebox.showwarning(
            "Warning",
            "Username aur Password dono bharo.",
            parent=login_window
        )
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        current_user_id = user[0]
        current_username = username
        user_label.config(text=f"User: {username}")
        refresh_table()
        update_dashboard()
        messagebox.showinfo(
            "Login Successful",
            "Welcome, " + username + "!",
            parent=login_window
        )

        login_window.destroy()
        root.deiconify()
        root.lift()
        root.focus_force()
        income_amount_entry.focus_set()

    else:
        messagebox.showerror(
            "Login Failed",
            "Username ya Password galat hai.",
            parent=login_window
        )
        login_password_entry.focus_set()


def show_login():
    global login_window
    global login_username_entry
    global login_password_entry

    # Dashboard is completely hidden until successful login.
    root.withdraw()

    login_window = tk.Toplevel(root)
    login_window.title("Login - Expense Tracker")
    login_window.geometry("400x410")
    login_window.resizable(False, False)

    login_window.protocol(
        "WM_DELETE_WINDOW",
        root.destroy
    )

    tk.Label(
        login_window,
        text="PERSONAL EXPENSE TRACKER",
        font=("Arial", 18, "bold")
    ).pack(pady=25)

    tk.Label(login_window, text="Username").pack()
    login_username_entry = tk.Entry(login_window, width=30)
    login_username_entry.pack(pady=7)

    tk.Label(login_window, text="Password").pack()
    login_password_entry = tk.Entry(
        login_window,
        width=30,
        show="*"
    )
    login_password_entry.pack(pady=7)

    tk.Button(
        login_window,
        text="LOGIN",
        width=20,
        command=login_user
    ).pack(pady=15)

    tk.Button(
        login_window,
        text="CREATE ACCOUNT",
        width=20,
        command=open_register
    ).pack(pady=4)

    tk.Button(
        login_window,
        text="FORGOT PASSWORD?",
        width=20,
        command=open_forgot_password
    ).pack(pady=4)

    login_window.update_idletasks()
    login_window.deiconify()
    login_window.lift()
    login_window.focus_force()
    login_username_entry.focus_set()

    login_password_entry.bind(
        "<Return>",
        lambda event: login_user()
    )

    login_username_entry.bind(
        "<Return>",
        lambda event: login_password_entry.focus_set()
    )


# ============================================================
# START APPLICATION
# ============================================================

create_database()
refresh_table()

show_login()

root.mainloop()
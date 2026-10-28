import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import math
from datetime import date, datetime
from tkcalendar import Calendar

# ---------------- DATABASE ----------------

DB_NAME = "expenses.db"
USER_ID = 1


def connect_db():
    return sqlite3.connect(DB_NAME)


def setup_database():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payment_methods (
            payment_method_id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_name TEXT UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            payment_method_id INTEGER,
            amount REAL NOT NULL,
            description TEXT,
            expense_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id),
            FOREIGN KEY (payment_method_id)
                REFERENCES payment_methods(payment_method_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS income (
            income_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            income_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS monthly_budgets (
            budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            budget_amount REAL NOT NULL,
            UNIQUE(user_id, month),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS savings_goals (
            goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            saved_amount REAL DEFAULT 0,
            target_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS monthly_summary (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            total_income REAL DEFAULT 0,
            total_expenses REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            UNIQUE(user_id, month),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Create a default user if one does not exist
    cur.execute("""
        INSERT OR IGNORE INTO users (user_id, username, email)
        VALUES (?, ?, ?)
    """, (USER_ID, "User", ""))

    # Default expense categories
    for category in [
        "Food", "Travel", "Shopping", "Bills",
        "Education", "Health", "Entertainment", "Others"
    ]:
        cur.execute(
            "INSERT OR IGNORE INTO categories (category_name) VALUES (?)",
            (category,)
        )

    # Default payment methods
    for method in ["Cash", "UPI", "Card", "Bank Transfer", "Others"]:
        cur.execute(
            "INSERT OR IGNORE INTO payment_methods (method_name) VALUES (?)",
            (method,)
        )

    cur.execute("""
        UPDATE expenses
        SET category_id = (
            SELECT category_id FROM categories WHERE category_name = 'Others'
        )
        WHERE category_id IN (
            SELECT category_id FROM categories WHERE category_name = 'Other'
        )
    """)
    cur.execute("DELETE FROM categories WHERE category_name = 'Other'")

    cur.execute("""
        UPDATE expenses
        SET payment_method_id = (
            SELECT payment_method_id FROM payment_methods
            WHERE method_name = 'Others'
        )
        WHERE payment_method_id IN (
            SELECT payment_method_id FROM payment_methods
            WHERE method_name = 'Other'
        )
    """)
    cur.execute("DELETE FROM payment_methods WHERE method_name = 'Other'")

    conn.commit()
    conn.close()


# ---------------- DATABASE HELPERS ----------------

def get_categories():
    conn = connect_db()
    rows = conn.execute(
        "SELECT category_name FROM categories ORDER BY category_name"
    ).fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_payment_methods():
    conn = connect_db()
    rows = conn.execute(
        "SELECT method_name FROM payment_methods ORDER BY method_name"
    ).fetchall()
    conn.close()
    return [row[0] for row in rows]


def valid_amount(value):
    try:
        amount = float(value)
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError
        return amount
    except (ValueError, TypeError):
        messagebox.showerror(
            "Invalid Amount",
            "Enter a finite amount greater than zero."
        )
        return None


def valid_date(value):
    try:
        parsed_date = datetime.strptime(value, "%Y-%m-%d")
        return parsed_date.strftime("%Y-%m-%d") == value
    except (ValueError, TypeError):
        messagebox.showerror(
            "Invalid Date",
            "Enter the date in YYYY-MM-DD format."
        )
        return False


def valid_month(value):
    try:
        parsed_month = datetime.strptime(value, "%Y-%m")
        return parsed_month.strftime("%Y-%m") == value
    except (ValueError, TypeError):
        messagebox.showerror(
            "Invalid Month",
            "Enter the month in YYYY-MM format."
        )
        return False


def center_popup(popup):
    root.update_idletasks()
    popup.update_idletasks()

    x = root.winfo_rootx() + (
        root.winfo_width() - popup.winfo_width()
    ) // 2
    y = root.winfo_rooty() + (
        root.winfo_height() - popup.winfo_height()
    ) // 2
    popup.geometry(f"+{x}+{y}")


def choose_date(entry):
    try:
        initial_date = datetime.strptime(entry.get(), "%Y-%m-%d").date()
    except ValueError:
        initial_date = date.today()

    popup = tk.Toplevel(root)
    popup.title("Select Date")
    popup.transient(root)

    month_names = tuple(
        datetime(2000, month, 1).strftime("%B")
        for month in range(1, 13)
    )
    month_var = tk.StringVar(value=month_names[initial_date.month - 1])
    year_var = tk.StringVar(value=str(initial_date.year))

    date_controls = ttk.Frame(popup, padding=(10, 10, 10, 0))
    date_controls.pack(fill="x")
    ttk.Label(date_controls, text="Month:").grid(row=0, column=0, padx=(0, 5))
    month_picker = ttk.Combobox(
        date_controls, textvariable=month_var, values=month_names,
        state="readonly", width=12
    )
    month_picker.grid(row=0, column=1, padx=(0, 12))
    ttk.Label(date_controls, text="Year:").grid(row=0, column=2, padx=(0, 5))
    year_picker = ttk.Spinbox(
        date_controls, textvariable=year_var, from_=1, to=9999, width=6
    )
    year_picker.grid(row=0, column=3)

    calendar = Calendar(
        popup, year=initial_date.year, month=initial_date.month,
        day=initial_date.day, selectmode="day", date_pattern="yyyy-mm-dd"
    )
    calendar.pack(padx=10, pady=10)

    def update_calendar(event=None):
        try:
            selected_year = int(year_var.get())
            selected_month = month_names.index(month_var.get()) + 1
            selected_month_start = date(selected_year, selected_month, 1)
            calendar.see(selected_month_start)
            calendar.selection_set(selected_month_start)
        except (ValueError, tk.TclError):
            return

    month_picker.bind("<<ComboboxSelected>>", update_calendar)
    year_picker.bind("<FocusOut>", update_calendar)
    year_picker.bind("<Return>", update_calendar)
    year_picker.configure(command=update_calendar)

    def apply_date():
        entry.delete(0, "end")
        entry.insert(0, calendar.get_date())
        popup.destroy()

    ttk.Button(
        popup, text="Select Date", command=apply_date
    ).pack(pady=(0, 10))
    center_popup(popup)
    popup.grab_set()


def choose_month(entry):
    try:
        initial_month = datetime.strptime(entry.get(), "%Y-%m").date()
    except ValueError:
        initial_month = date.today()

    popup = tk.Toplevel(root)
    popup.title("Select Month")
    popup.transient(root)

    month_names = tuple(
        datetime(2000, month, 1).strftime("%B")
        for month in range(1, 13)
    )
    month_var = tk.StringVar(value=month_names[initial_month.month - 1])
    year_var = tk.StringVar(value=str(initial_month.year))

    controls = ttk.Frame(popup, padding=10)
    controls.pack(fill="x")
    ttk.Label(controls, text="Month:").grid(row=0, column=0, padx=(0, 5))
    month_picker = ttk.Combobox(
        controls, textvariable=month_var, values=month_names,
        state="readonly", width=12
    )
    month_picker.grid(row=0, column=1, padx=(0, 12))
    ttk.Label(controls, text="Year:").grid(row=0, column=2, padx=(0, 5))
    year_picker = ttk.Spinbox(
        controls, textvariable=year_var, from_=1, to=9999, width=6
    )
    year_picker.grid(row=0, column=3)

    def apply_month():
        try:
            selected_year = int(year_var.get())
            selected_month = month_names.index(month_var.get()) + 1
            selected_date = date(selected_year, selected_month, 1)
        except (ValueError, TypeError):
            messagebox.showerror(
                "Invalid Month", "Select a valid month and year.", parent=popup
            )
            return

        entry.delete(0, "end")
        entry.insert(0, selected_date.strftime("%Y-%m"))
        popup.destroy()

    ttk.Button(
        popup, text="Select Month", command=apply_month
    ).pack(pady=(0, 10))
    center_popup(popup)
    popup.grab_set()


# ---------------- MAIN WINDOW ----------------

setup_database()

root = tk.Tk()
root.title("Astra | Personal Expense Tracker")
root.geometry("1180x780")
root.minsize(960, 650)

# ---------------- MODERN COLOR THEME ----------------
# Deep navy + mint + warm off-white palette
COLORS = {
    "background": "#F4F7FB",
    "surface": "#FFFFFF",
    "navy": "#172B4D",
    "navy_light": "#243F68",
    "text": "#26364A",
    "muted": "#718096",
    "border": "#DCE4EF",
    "mint": "#17A589",
    "mint_dark": "#12806B",
    "mint_light": "#E2F7F1",
    "red": "#D9534F",
    "red_light": "#FCEBEA",
    "blue_light": "#EAF1FF",
    "selected": "#D8F3EC",
}

root.configure(bg=COLORS["background"])
style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure("TFrame", background=COLORS["background"])
style.configure("Card.TFrame", background=COLORS["surface"])
style.configure("TLabel", background=COLORS["background"], foreground=COLORS["text"], font=("Segoe UI", 10))
style.configure("Title.TLabel", background=COLORS["background"], foreground=COLORS["navy"], font=("Segoe UI", 23, "bold"))
style.configure("Subtitle.TLabel", background=COLORS["background"], foreground=COLORS["muted"], font=("Segoe UI", 10))
style.configure("CardTitle.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=("Segoe UI", 10, "bold"))
style.configure("IncomeValue.TLabel", background=COLORS["surface"], foreground=COLORS["mint_dark"], font=("Segoe UI", 16, "bold"))
style.configure("ExpenseValue.TLabel", background=COLORS["surface"], foreground=COLORS["red"], font=("Segoe UI", 16, "bold"))
style.configure("BalanceValue.TLabel", background=COLORS["surface"], foreground=COLORS["navy"], font=("Segoe UI", 16, "bold"))
style.configure("TLabelframe", background=COLORS["background"], bordercolor=COLORS["border"], relief="solid")
style.configure("TLabelframe.Label", background=COLORS["background"], foreground=COLORS["navy"], font=("Segoe UI", 11, "bold"))
style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=(11, 7), background=COLORS["navy_light"], foreground="#FFFFFF", borderwidth=0)
style.map("TButton", background=[("active", COLORS["mint_dark"]), ("pressed", COLORS["navy"])], foreground=[("disabled", "#D5DCE5")])
style.configure("Accent.TButton", background=COLORS["mint"], foreground="#FFFFFF")
style.map("Accent.TButton", background=[("active", COLORS["mint_dark"])])
style.configure("TEntry", fieldbackground=COLORS["surface"], foreground=COLORS["text"], padding=7, bordercolor=COLORS["border"])
style.configure("TCombobox", fieldbackground=COLORS["surface"], background=COLORS["surface"], foreground=COLORS["text"], padding=6, arrowcolor=COLORS["navy"])
style.map("TCombobox", fieldbackground=[("readonly", COLORS["surface"])], selectbackground=[("readonly", COLORS["surface"])], selectforeground=[("readonly", COLORS["text"])])
style.configure("TNotebook", background=COLORS["background"], borderwidth=0, tabmargins=(3, 5, 3, 0))
style.configure("TNotebook.Tab", background="#E8EEF6", foreground=COLORS["navy"], padding=(18, 10), font=("Segoe UI", 10, "bold"))
style.map("TNotebook.Tab", background=[("selected", COLORS["navy_light"]), ("active", COLORS["selected"])], foreground=[("selected", "#FFFFFF"), ("active", COLORS["navy"])])
style.configure("Treeview", rowheight=31, background=COLORS["surface"], fieldbackground=COLORS["surface"], foreground=COLORS["text"], bordercolor=COLORS["border"], font=("Segoe UI", 9))
style.configure("Treeview.Heading", background=COLORS["navy_light"], foreground="#FFFFFF", font=("Segoe UI", 9, "bold"), padding=8, relief="flat")
style.map("Treeview", background=[("selected", COLORS["selected"])], foreground=[("selected", COLORS["navy"])])

header = ttk.Frame(root, padding=(24, 20, 24, 8))
header.pack(fill="x")
heading = ttk.Label(header, text="Astra", style="Title.TLabel")
heading.pack(anchor="w")
subtitle = ttk.Label(header, text="Your money, clearly managed. Track spending, plan budgets, and reach your savings goals.", style="Subtitle.TLabel")
subtitle.pack(anchor="w", pady=(3, 0))

# Dashboard summary cards
dashboard = ttk.Frame(root, padding=(20, 10, 20, 12))
dashboard.pack(fill="x")
for column in range(3):
    dashboard.grid_columnconfigure(column, weight=1, uniform="summary")

income_card = ttk.Frame(dashboard, style="Card.TFrame", padding=(16, 12))
income_card.grid(row=0, column=0, sticky="ew", padx=(0, 8))
expense_card = ttk.Frame(dashboard, style="Card.TFrame", padding=(16, 12))
expense_card.grid(row=0, column=1, sticky="ew", padx=8)
balance_card = ttk.Frame(dashboard, style="Card.TFrame", padding=(16, 12))
balance_card.grid(row=0, column=2, sticky="ew", padx=(8, 0))

ttk.Label(income_card, text="TOTAL INCOME  ↗", style="CardTitle.TLabel").pack(anchor="w")
income_total_label = ttk.Label(income_card, text="₹0.00", style="IncomeValue.TLabel")
income_total_label.pack(anchor="w", pady=(5, 0))

ttk.Label(expense_card, text="TOTAL EXPENSES  ↘", style="CardTitle.TLabel").pack(anchor="w")
expense_total_label = ttk.Label(expense_card, text="₹0.00", style="ExpenseValue.TLabel")
expense_total_label.pack(anchor="w", pady=(5, 0))

ttk.Label(balance_card, text="AVAILABLE BALANCE  ◈", style="CardTitle.TLabel").pack(anchor="w")
balance_label = ttk.Label(balance_card, text="₹0.00", style="BalanceValue.TLabel")
balance_label.pack(anchor="w", pady=(5, 0))

content = ttk.Frame(root, padding=(20, 0, 20, 18))
content.pack(fill="both", expand=True)
notebook = ttk.Notebook(content)
notebook.pack(fill="both", expand=True)


def create_tab(name):
    frame = ttk.Frame(notebook, padding=12)
    notebook.add(frame, text=name)
    return frame


# ==================================================
# TAB 1: EXPENSES
# ==================================================

exp_tab = create_tab("Expenses")

ttk.Label(exp_tab, text="Amount (₹):").grid(
    row=0, column=0, sticky="w", padx=5, pady=5
)
exp_amount = ttk.Entry(exp_tab, width=25)
exp_amount.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

ttk.Label(exp_tab, text="Category:").grid(
    row=0, column=2, sticky="w", padx=5, pady=5
)
exp_category = ttk.Combobox(
    exp_tab, values=get_categories(), state="readonly", width=22
)
exp_category.grid(row=0, column=3, sticky="ew", padx=5, pady=5)
exp_category.set("Food")

ttk.Label(exp_tab, text="Payment Method:").grid(
    row=1, column=0, sticky="w", padx=5, pady=5
)
exp_payment = ttk.Combobox(
    exp_tab, values=get_payment_methods(), state="readonly", width=22
)
exp_payment.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
exp_payment.set("Cash")

ttk.Label(exp_tab, text="Date (YYYY-MM-DD):").grid(
    row=1, column=2, sticky="w", padx=5, pady=5
)
exp_date = ttk.Entry(exp_tab, width=22)
exp_date.grid(row=1, column=3, sticky="ew", padx=5, pady=5)
exp_date.insert(0, date.today().isoformat())
ttk.Button(
    exp_tab, text="Calendar", command=lambda: choose_date(exp_date)
).grid(row=1, column=4, padx=5, pady=5)

ttk.Label(exp_tab, text="Description:").grid(
    row=2, column=0, sticky="w", padx=5, pady=5
)
exp_description = ttk.Entry(exp_tab)
exp_description.grid(
    row=2, column=1, columnspan=3, sticky="ew", padx=5, pady=5
)

expense_table = ttk.Treeview(
    exp_tab,
    columns=("ID", "Amount", "Category", "Payment", "Date", "Description"),
    show="headings"
)

for col in ("ID", "Amount", "Category", "Payment", "Date", "Description"):
    expense_table.heading(col, text=col)
    expense_table.column(col, width=130, anchor="center")

expense_table.grid(
    row=4, column=0, columnspan=4,
    sticky="nsew", padx=5, pady=12
)


def refresh_expenses():
    for item in expense_table.get_children():
        expense_table.delete(item)

    conn = connect_db()
    rows = conn.execute("""
        SELECT e.expense_id, e.amount, c.category_name,
               p.method_name, e.expense_date, e.description
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.category_id
        LEFT JOIN payment_methods p
            ON e.payment_method_id = p.payment_method_id
        WHERE e.user_id = ?
        ORDER BY e.expense_date ASC, e.expense_id ASC
    """, (USER_ID,)).fetchall()
    conn.close()

    for row in rows:
        expense_table.insert(
            "", "end",
            values=(
                row[0], f"{row[1]:.2f}", row[2],
                row[3], row[4], row[5] or ""
            )
        )


def add_expense():
    amount = valid_amount(exp_amount.get())
    if amount is None:
        return

    category = exp_category.get()
    payment = exp_payment.get()
    expense_day = exp_date.get().strip()
    description = exp_description.get().strip()

    if not category or not payment:
        messagebox.showerror("Error", "Select a category and payment method.")
        return

    if not valid_date(expense_day):
        return

    conn = connect_db()
    cur = conn.cursor()

    category_id = cur.execute(
        "SELECT category_id FROM categories WHERE category_name = ?",
        (category,)
    ).fetchone()[0]

    payment_id = cur.execute(
        "SELECT payment_method_id FROM payment_methods WHERE method_name = ?",
        (payment,)
    ).fetchone()[0]

    cur.execute("""
        INSERT INTO expenses
        (user_id, category_id, payment_method_id, amount,
         description, expense_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        USER_ID, category_id, payment_id,
        amount, description, expense_day
    ))

    conn.commit()
    conn.close()

    exp_amount.delete(0, "end")
    exp_description.delete(0, "end")
    exp_date.delete(0, "end")
    exp_date.insert(0, date.today().isoformat())

    refresh_all()
    messagebox.showinfo("Success", "Expense added successfully.")


def delete_expense():
    selected = expense_table.selection()
    if not selected:
        messagebox.showwarning("Select Expense", "Select an expense to delete.")
        return

    expense_id = expense_table.item(selected[0], "values")[0]

    if not messagebox.askyesno("Confirm", "Delete this expense?"):
        return

    conn = connect_db()
    conn.execute(
        "DELETE FROM expenses WHERE expense_id = ? AND user_id = ?",
        (expense_id, USER_ID)
    )
    conn.commit()
    conn.close()
    refresh_all()


ttk.Button(
    exp_tab, text="＋ Add Expense", command=add_expense, style="Accent.TButton"
).grid(row=3, column=0, padx=5, pady=5, sticky="w")

ttk.Button(
    exp_tab, text="Delete Selected", command=delete_expense
).grid(row=3, column=1, padx=5, pady=5, sticky="w")

exp_tab.grid_columnconfigure(1, weight=1)
exp_tab.grid_columnconfigure(3, weight=1)
exp_tab.grid_rowconfigure(4, weight=1)


# ==================================================
# TAB 2: INCOME
# ==================================================

inc_tab = create_tab("Income")

ttk.Label(inc_tab, text="Income Source:").grid(
    row=0, column=0, sticky="w", padx=5, pady=5
)
income_source = ttk.Entry(inc_tab, width=25)
income_source.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

ttk.Label(inc_tab, text="Amount (₹):").grid(
    row=0, column=2, sticky="w", padx=5, pady=5
)
income_amount = ttk.Entry(inc_tab, width=25)
income_amount.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

ttk.Label(inc_tab, text="Date (YYYY-MM-DD):").grid(
    row=1, column=0, sticky="w", padx=5, pady=5
)
income_date = ttk.Entry(inc_tab, width=22)
income_date.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
income_date.insert(0, date.today().isoformat())
ttk.Button(
    inc_tab, text="Calendar", command=lambda: choose_date(income_date)
).grid(row=1, column=2, padx=5, pady=5)

income_table = ttk.Treeview(
    inc_tab,
    columns=("ID", "Source", "Amount", "Date"),
    show="headings"
)

for col in ("ID", "Source", "Amount", "Date"):
    income_table.heading(col, text=col)
    income_table.column(col, width=170, anchor="center")

income_table.grid(
    row=3, column=0, columnspan=4,
    sticky="nsew", padx=5, pady=12
)


def refresh_income():
    for item in income_table.get_children():
        income_table.delete(item)

    conn = connect_db()
    rows = conn.execute("""
        SELECT income_id, source, amount, income_date
        FROM income
        WHERE user_id = ?
        ORDER BY income_date ASC, income_id ASC
    """, (USER_ID,)).fetchall()
    conn.close()

    for row in rows:
        income_table.insert(
            "", "end",
            values=(row[0], row[1], f"{row[2]:.2f}", row[3])
        )


def add_income():
    source = income_source.get().strip()
    amount = valid_amount(income_amount.get())
    income_day = income_date.get().strip()

    if not source:
        messagebox.showerror("Error", "Enter an income source.")
        return

    if amount is None:
        return

    if not valid_date(income_day):
        return

    conn = connect_db()
    conn.execute("""
        INSERT INTO income (user_id, source, amount, income_date)
        VALUES (?, ?, ?, ?)
    """, (USER_ID, source, amount, income_day))
    conn.commit()
    conn.close()

    income_source.delete(0, "end")
    income_amount.delete(0, "end")
    income_date.delete(0, "end")
    income_date.insert(0, date.today().isoformat())

    refresh_all()
    messagebox.showinfo("Success", "Income added successfully.")


def delete_income():
    selected = income_table.selection()
    if not selected:
        messagebox.showwarning("Select Income", "Select income to delete.")
        return

    income_id = income_table.item(selected[0], "values")[0]

    if not messagebox.askyesno("Confirm", "Delete this income entry?"):
        return

    conn = connect_db()
    conn.execute(
        "DELETE FROM income WHERE income_id = ? AND user_id = ?",
        (income_id, USER_ID)
    )
    conn.commit()
    conn.close()
    refresh_all()


ttk.Button(
    inc_tab, text="＋ Add Income", command=add_income, style="Accent.TButton"
).grid(row=2, column=0, padx=5, pady=5, sticky="w")

ttk.Button(
    inc_tab, text="Delete Selected", command=delete_income
).grid(row=2, column=1, padx=5, pady=5, sticky="w")

inc_tab.grid_columnconfigure(1, weight=1)
inc_tab.grid_columnconfigure(3, weight=1)
inc_tab.grid_rowconfigure(3, weight=1)


# ==================================================
# TAB 3: MONTHLY BUDGET
# ==================================================

budget_tab = create_tab("Monthly Budget")

ttk.Label(budget_tab, text="Month (YYYY-MM):").grid(
    row=0, column=0, sticky="w", padx=5, pady=8
)
budget_month = ttk.Entry(budget_tab, width=25)
budget_month.grid(row=0, column=1, sticky="ew", padx=5, pady=8)
budget_month.insert(0, date.today().strftime("%Y-%m"))
ttk.Button(
    budget_tab, text="Calendar", command=lambda: choose_month(budget_month)
).grid(row=0, column=2, padx=5, pady=8)

ttk.Label(budget_tab, text="Budget Amount (₹):").grid(
    row=1, column=0, sticky="w", padx=5, pady=8
)
budget_amount = ttk.Entry(budget_tab, width=25)
budget_amount.grid(row=1, column=1, sticky="ew", padx=5, pady=8)

budget_status = ttk.Label(
    budget_tab, text="Enter a monthly budget.",
    font=("Arial", 12)
)
budget_status.grid(
    row=3, column=0, columnspan=3, sticky="w", padx=5, pady=12
)

budget_table = ttk.Treeview(
    budget_tab, columns=("Month", "Budget", "Spent", "Remaining"),
    show="headings"
)

for col in ("Month", "Budget", "Spent", "Remaining"):
    budget_table.heading(col, text=col)
    budget_table.column(col, width=180, anchor="center")

budget_table.grid(
    row=4, column=0, columnspan=3,
    sticky="nsew", padx=5, pady=12
)


def refresh_budgets():
    for item in budget_table.get_children():
        budget_table.delete(item)

    conn = connect_db()
    budgets = conn.execute("""
        SELECT month, budget_amount
        FROM monthly_budgets
        WHERE user_id = ?
        ORDER BY month ASC
    """, (USER_ID,)).fetchall()

    for month, amount in budgets:
        spent = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE user_id = ? AND substr(expense_date, 1, 7) = ?
        """, (USER_ID, month)).fetchone()[0]

        remaining = amount - spent

        budget_table.insert(
            "", "end",
            values=(
                month, f"{amount:.2f}",
                f"{spent:.2f}", f"{remaining:.2f}"
            )
        )

    conn.close()


def save_budget():
    month = budget_month.get().strip()
    amount = valid_amount(budget_amount.get())

    if not valid_month(month):
        return

    if amount is None:
        return

    conn = connect_db()
    conn.execute("""
        INSERT INTO monthly_budgets (user_id, month, budget_amount)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, month)
        DO UPDATE SET budget_amount = excluded.budget_amount
    """, (USER_ID, month, amount))
    conn.commit()
    conn.close()

    refresh_budgets()
    budget_amount.delete(0, "end")
    messagebox.showinfo("Success", "Monthly budget saved.")


ttk.Button(
    budget_tab, text="Save Budget", command=save_budget, style="Accent.TButton"
).grid(row=2, column=0, padx=5, pady=8, sticky="w")

budget_tab.grid_columnconfigure(1, weight=1)
budget_tab.grid_rowconfigure(4, weight=1)


# ==================================================
# TAB 4: SAVINGS GOALS
# ==================================================

goals_tab = create_tab("Savings Goals")

ttk.Label(goals_tab, text="Goal Name:").grid(
    row=0, column=0, sticky="w", padx=5, pady=5
)
goal_name = ttk.Entry(goals_tab, width=25)
goal_name.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

ttk.Label(goals_tab, text="Target Amount (₹):").grid(
    row=0, column=2, sticky="w", padx=5, pady=5
)
goal_target = ttk.Entry(goals_tab, width=25)
goal_target.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

ttk.Label(goals_tab, text="Already Saved (₹):").grid(
    row=1, column=0, sticky="w", padx=5, pady=5
)
goal_saved = ttk.Entry(goals_tab, width=25)
goal_saved.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
goal_saved.insert(0, "0")

ttk.Label(goals_tab, text="Target Date (YYYY-MM-DD, optional):").grid(
    row=1, column=2, sticky="w", padx=5, pady=5
)
goal_date = ttk.Entry(goals_tab, width=25)
goal_date.grid(row=1, column=3, sticky="ew", padx=5, pady=5)
ttk.Button(
    goals_tab, text="Calendar", command=lambda: choose_date(goal_date)
).grid(row=1, column=4, padx=5, pady=5)

goals_table = ttk.Treeview(
    goals_tab,
    columns=("ID", "Goal", "Target", "Saved", "Remaining", "Target Date"),
    show="headings"
)

for col in ("ID", "Goal", "Target", "Saved", "Remaining", "Target Date"):
    goals_table.heading(col, text=col)
    goals_table.column(col, width=140, anchor="center")

goals_table.grid(
    row=3, column=0, columnspan=4,
    sticky="nsew", padx=5, pady=12
)


def refresh_goals():
    for item in goals_table.get_children():
        goals_table.delete(item)

    conn = connect_db()
    rows = conn.execute("""
        SELECT goal_id, goal_name, target_amount, saved_amount, target_date
        FROM savings_goals
        WHERE user_id = ?
        ORDER BY goal_id ASC
    """, (USER_ID,)).fetchall()
    conn.close()

    for goal_id, name, target, saved, target_day in rows:
        goals_table.insert(
            "", "end",
            values=(
                goal_id, name, f"{target:.2f}", f"{saved:.2f}",
                f"{target - saved:.2f}", target_day or ""
            )
        )


def add_goal():
    name = goal_name.get().strip()
    target = valid_amount(goal_target.get())

    try:
        saved = float(goal_saved.get())
        if not math.isfinite(saved) or saved < 0:
            raise ValueError
    except (ValueError, TypeError):
        messagebox.showerror(
            "Invalid Amount",
            "Saved amount must be finite and zero or more."
        )
        return

    target_day = goal_date.get().strip()

    if not name:
        messagebox.showerror("Error", "Enter a goal name.")
        return

    if target is None:
        return

    if saved > target:
        messagebox.showerror(
            "Invalid Amount", "Saved amount cannot exceed the target."
        )
        return

    if target_day and not valid_date(target_day):
        return

    conn = connect_db()
    conn.execute("""
        INSERT INTO savings_goals
        (user_id, goal_name, target_amount, saved_amount, target_date)
        VALUES (?, ?, ?, ?, ?)
    """, (USER_ID, name, target, saved, target_day or None))
    conn.commit()
    conn.close()

    goal_name.delete(0, "end")
    goal_target.delete(0, "end")
    goal_saved.delete(0, "end")
    goal_saved.insert(0, "0")
    goal_date.delete(0, "end")

    refresh_goals()
    messagebox.showinfo("Success", "Savings goal added.")


def delete_goal():
    selected = goals_table.selection()
    if not selected:
        messagebox.showwarning("Select Goal", "Select a goal to delete.")
        return

    goal_id = goals_table.item(selected[0], "values")[0]

    if not messagebox.askyesno("Confirm", "Delete this savings goal?"):
        return

    conn = connect_db()
    conn.execute(
        "DELETE FROM savings_goals WHERE goal_id = ? AND user_id = ?",
        (goal_id, USER_ID)
    )
    conn.commit()
    conn.close()
    refresh_goals()


ttk.Button(
    goals_tab, text="Add Goal", command=add_goal
).grid(row=2, column=0, padx=5, pady=5, sticky="w")

ttk.Button(
    goals_tab, text="Delete Selected", command=delete_goal
).grid(row=2, column=1, padx=5, pady=5, sticky="w")

goals_tab.grid_columnconfigure(1, weight=1)
goals_tab.grid_columnconfigure(3, weight=1)
goals_tab.grid_rowconfigure(3, weight=1)


# ==================================================
# TAB 5: MONTHLY REPORTS
# ==================================================

report_tab = create_tab("Monthly Reports")

ttk.Label(report_tab, text="Month (YYYY-MM):").grid(
    row=0, column=0, sticky="w", padx=5, pady=8
)

report_month = ttk.Entry(report_tab, width=25)
report_month.grid(row=0, column=1, sticky="w", padx=5, pady=8)
report_month.insert(0, date.today().strftime("%Y-%m"))
ttk.Button(
    report_tab, text="Calendar", command=lambda: choose_month(report_month)
).grid(row=0, column=2, padx=5, pady=8)

report_result = ttk.Label(
    report_tab, text="Select a month and click Generate Report.",
    font=("Arial", 12)
)
report_result.grid(
    row=2, column=0, columnspan=3, sticky="w", padx=5, pady=12
)

report_table = ttk.Treeview(
    report_tab,
    columns=("Category", "Total"),
    show="headings"
)

report_table.heading("Category", text="Expense Category")
report_table.heading("Total", text="Total Spent (₹)")
report_table.column("Category", width=250, anchor="center")
report_table.column("Total", width=200, anchor="center")

report_table.grid(
    row=3, column=0, columnspan=3,
    sticky="nsew", padx=5, pady=12
)


def generate_report():
    month = report_month.get().strip()

    if not valid_month(month):
        return

    conn = connect_db()
    cur = conn.cursor()

    total_income = cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM income
        WHERE user_id = ? AND substr(income_date, 1, 7) = ?
    """, (USER_ID, month)).fetchone()[0]

    total_expenses = cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = ? AND substr(expense_date, 1, 7) = ?
    """, (USER_ID, month)).fetchone()[0]

    balance = total_income - total_expenses

    cur.execute("""
        INSERT INTO monthly_summary
        (user_id, month, total_income, total_expenses, balance)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, month)
        DO UPDATE SET
            total_income = excluded.total_income,
            total_expenses = excluded.total_expenses,
            balance = excluded.balance
    """, (USER_ID, month, total_income, total_expenses, balance))

    category_rows = cur.execute("""
        SELECT COALESCE(c.category_name, 'Others'), SUM(e.amount)
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ? AND substr(e.expense_date, 1, 7) = ?
        GROUP BY c.category_name
        ORDER BY SUM(e.amount) DESC
    """, (USER_ID, month)).fetchall()

    conn.commit()
    conn.close()

    for item in report_table.get_children():
        report_table.delete(item)

    for category, amount in category_rows:
        report_table.insert(
            "", "end", values=(category, f"{amount:.2f}")
        )

    report_result.config(
        text=(
            f"Report for {month}  |  "
            f"Income: ₹{total_income:.2f}  |  "
            f"Expenses: ₹{total_expenses:.2f}  |  "
            f"Balance: ₹{balance:.2f}"
        )
    )


ttk.Button(
    report_tab, text="Generate Report", command=generate_report
).grid(row=1, column=0, padx=5, pady=8, sticky="w")

report_tab.grid_columnconfigure(1, weight=1)
report_tab.grid_rowconfigure(3, weight=1)


# ---------------- DASHBOARD ----------------

def refresh_dashboard():
    conn = connect_db()

    total_income = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM income WHERE user_id = ?
    """, (USER_ID,)).fetchone()[0]

    total_expenses = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses WHERE user_id = ?
    """, (USER_ID,)).fetchone()[0]

    conn.close()

    income_total_label.config(
        text=f"₹{total_income:,.2f}"
    )
    expense_total_label.config(
        text=f"₹{total_expenses:,.2f}"
    )
    balance_label.config(
        text=f"₹{total_income - total_expenses:,.2f}"
    )


def refresh_all():
    refresh_expenses()
    refresh_income()
    refresh_budgets()
    refresh_goals()
    refresh_dashboard()


# ---------------- START APPLICATION ----------------

refresh_all()
root.mainloop()
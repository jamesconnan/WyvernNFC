import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from user_management import UserManagement
from decimal import Decimal
import sqlite3
from datetime import datetime, timedelta
import os

class UserManagementUI:
    def __init__(self, root):
        self.root = root
        self.root.title("User Management System")
        self.root.geometry("800x600")
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure("Danger.TButton", foreground="red")
        
        self.user_management = UserManagement()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_control = ttk.Notebook(self.main_frame)
        
        # Users tab
        self.users_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.users_tab, text="Users")
        
        # Transactions tab
        self.transactions_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.transactions_tab, text="Transactions")
        
        # Sales Report tab
        self.sales_report_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.sales_report_tab, text="Wyvern Card Sales")
        
        # Menu Items Report tab
        self.menu_items_report_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.menu_items_report_tab, text="Menu Items Report")
        
        self.tab_control.pack(expand=True, fill=tk.BOTH)
        
        # Initialize UI components
        self.setup_users_tab()
        self.setup_transactions_tab()
        self.setup_sales_report_tab()
        self.setup_menu_items_report_tab()
        self.create_reports_tab()
        
        # Load initial data
        self.load_users()

    def setup_users_tab(self):
        # Create user list frame
        list_frame = ttk.LabelFrame(self.users_tab, text="Users", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create search frame
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        # Search label
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_users)  # Call filter_users when text changes
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Search type combobox
        self.search_type = ttk.Combobox(search_frame, values=["Name", "Phone", "RFID Tag"], width=10)
        self.search_type.set("Name")
        self.search_type.pack(side=tk.LEFT, padx=5)
        self.search_type.bind('<<ComboboxSelected>>', lambda e: self.filter_users())
        
        # Clear search button
        ttk.Button(
            search_frame,
            text="Clear",
            command=self.clear_search
        ).pack(side=tk.LEFT, padx=5)
        
        # Create treeview
        self.user_tree = ttk.Treeview(list_frame, columns=("Name", "Phone", "Email", "RFID Tags", "Balance", "Discount"), show="headings")
        self.user_tree.heading("Name", text="Name")
        self.user_tree.heading("Phone", text="Phone")
        self.user_tree.heading("Email", text="Email")
        self.user_tree.heading("RFID Tags", text="RFID Tags")
        self.user_tree.heading("Balance", text="Balance")
        self.user_tree.heading("Discount", text="Discount %")
        
        # Set column widths
        self.user_tree.column("Name", width=150)
        self.user_tree.column("Phone", width=100)
        self.user_tree.column("Email", width=200)
        self.user_tree.column("RFID Tags", width=200)
        self.user_tree.column("Balance", width=100)
        self.user_tree.column("Discount", width=80)
        
        self.user_tree.pack(fill=tk.BOTH, expand=True)
        
        # Create buttons frame
        button_frame = ttk.Frame(self.users_tab)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add user button
        ttk.Button(button_frame, text="Add User", command=self.show_add_user_dialog).pack(side=tk.LEFT, padx=5)
        
        # Edit user button
        ttk.Button(button_frame, text="Edit User", command=self.show_edit_user_dialog).pack(side=tk.LEFT, padx=5)
        
        # Manage RFID Tags button
        ttk.Button(button_frame, text="Manage RFID Tags", command=self.show_manage_rfid_dialog).pack(side=tk.LEFT, padx=5)
        
        # Delete user button
        ttk.Button(button_frame, text="Delete User", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        
        # Load money button
        ttk.Button(button_frame, text="Load Money", command=self.show_load_money_dialog).pack(side=tk.LEFT, padx=5)
        
        # Clear all data button
        ttk.Button(
            button_frame,
            text="Clear All Data",
            command=self.show_clear_data_dialog,
            style="Danger.TButton"
        ).pack(side=tk.RIGHT, padx=5)

    def setup_transactions_tab(self):
        # Create transaction list frame
        list_frame = ttk.LabelFrame(self.transactions_tab, text="Transaction History", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create filter frame
        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        # User filter
        ttk.Label(filter_frame, text="User:").pack(side=tk.LEFT, padx=5)
        self.user_filter = ttk.Combobox(filter_frame, width=20)
        self.user_filter.pack(side=tk.LEFT, padx=5)
        self.user_filter.bind('<<ComboboxSelected>>', lambda e: self.load_transactions())
        
        # Type filter
        ttk.Label(filter_frame, text="Type:").pack(side=tk.LEFT, padx=5)
        self.type_filter = ttk.Combobox(filter_frame, width=15)
        self.type_filter['values'] = ['All', 'load', 'purchase']
        self.type_filter.set('All')
        self.type_filter.pack(side=tk.LEFT, padx=5)
        self.type_filter.bind('<<ComboboxSelected>>', lambda e: self.load_transactions())
        
        # Date filter
        ttk.Label(filter_frame, text="Date:").pack(side=tk.LEFT, padx=5)
        self.date_filter = ttk.Entry(filter_frame, width=15)
        self.date_filter.pack(side=tk.LEFT, padx=5)
        self.date_filter.bind('<Return>', lambda e: self.load_transactions())
        
        # Clear filters button
        ttk.Button(
            filter_frame,
            text="Clear Filters",
            command=self.clear_filters
        ).pack(side=tk.LEFT, padx=5)
        
        # Create main content frame
        content_frame = ttk.Frame(list_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview frame
        tree_frame = ttk.Frame(content_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        self.transaction_tree = ttk.Treeview(tree_frame, columns=("User", "Amount", "Type", "Date", "Balance"), show="headings")
        self.transaction_tree.heading("User", text="User")
        self.transaction_tree.heading("Amount", text="Amount")
        self.transaction_tree.heading("Type", text="Type")
        self.transaction_tree.heading("Date", text="Date")
        self.transaction_tree.heading("Balance", text="Balance After")
        
        # Set column widths
        self.transaction_tree.column("User", width=150)
        self.transaction_tree.column("Amount", width=100)
        self.transaction_tree.column("Type", width=100)
        self.transaction_tree.column("Date", width=150)
        self.transaction_tree.column("Balance", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.transaction_tree.yview)
        self.transaction_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.transaction_tree.pack(fill=tk.BOTH, expand=True)
        
        # Create details frame with paned window
        details_paned = ttk.PanedWindow(content_frame, orient=tk.VERTICAL)
        details_paned.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create details frame
        details_frame = ttk.LabelFrame(details_paned, text="Transaction Details", padding="5")
        details_paned.add(details_frame, weight=1)  # Make it resizable
        
        # Create text widget with scrollbar for details
        text_frame = ttk.Frame(details_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create text widget
        self.details_text = tk.Text(text_frame, wrap=tk.WORD, font=('Arial', 10))
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add vertical scrollbar
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=text_scrollbar.set)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(details_frame, orient="horizontal", command=self.details_text.xview)
        self.details_text.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind selection event
        self.transaction_tree.bind('<<TreeviewSelect>>', self.show_transaction_details)
        
        # Add refresh button
        refresh_button = ttk.Button(
            list_frame,
            text="Refresh Transactions",
            command=self.load_transactions
        )
        refresh_button.pack(pady=5)
        
        # Load initial data
        self.load_user_filter()
        self.load_transactions()

    def setup_sales_report_tab(self):
        # Create main frame
        main_frame = ttk.Frame(self.sales_report_tab, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create date range frame
        date_frame = ttk.LabelFrame(main_frame, text="Date Range", padding="5")
        date_frame.pack(fill=tk.X, pady=5)
        
        # Get available dates from transaction logs
        available_dates = []
        if os.path.exists('transactions'):
            for file in os.listdir('transactions'):
                if file.startswith('transactions_') and file.endswith('.log'):
                    try:
                        date_str = file.replace('transactions_', '').replace('.log', '')
                        date = datetime.strptime(date_str, "%Y-%m-%d")
                        available_dates.append(date)
                    except ValueError:
                        continue
        
        # Sort dates
        available_dates.sort()
        date_strings = [date.strftime("%Y-%m-%d") for date in available_dates]
        
        if not date_strings:
            date_strings = [datetime.now().strftime("%Y-%m-%d")]
        
        # Start date
        ttk.Label(date_frame, text="Start Date:").pack(side=tk.LEFT, padx=5)
        self.wyvern_start_date = ttk.Combobox(date_frame, values=date_strings, width=15, state="readonly")
        self.wyvern_start_date.pack(side=tk.LEFT, padx=5)
        self.wyvern_start_date.set(date_strings[0])
        
        # End date
        ttk.Label(date_frame, text="End Date:").pack(side=tk.LEFT, padx=5)
        self.wyvern_end_date = ttk.Combobox(date_frame, values=date_strings, width=15, state="readonly")
        self.wyvern_end_date.pack(side=tk.LEFT, padx=5)
        self.wyvern_end_date.set(date_strings[-1])
        
        # Generate report button
        ttk.Button(
            date_frame,
            text="Generate Report",
            command=self.generate_sales_report
        ).pack(side=tk.LEFT, padx=5)
        
        # Create report frame
        report_frame = ttk.LabelFrame(main_frame, text="Sales Report", padding="5")
        report_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create text widget for report
        self.sales_report_text = tk.Text(report_frame, wrap=tk.WORD, font=('Arial', 10))
        self.sales_report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=self.sales_report_text.yview)
        self.sales_report_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_menu_items_report_tab(self):
        # Create main frame
        main_frame = ttk.Frame(self.menu_items_report_tab, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create date range frame
        date_frame = ttk.LabelFrame(main_frame, text="Date Range", padding="5")
        date_frame.pack(fill=tk.X, pady=5)
        
        # Get available dates from transaction logs
        available_dates = []
        if os.path.exists('transactions'):
            for file in os.listdir('transactions'):
                if file.startswith('transactions_') and file.endswith('.log'):
                    try:
                        date_str = file.replace('transactions_', '').replace('.log', '')
                        date = datetime.strptime(date_str, "%Y-%m-%d")
                        available_dates.append(date)
                    except ValueError:
                        continue
        
        # Sort dates
        available_dates.sort()
        date_strings = [date.strftime("%Y-%m-%d") for date in available_dates]
        
        if not date_strings:
            date_strings = [datetime.now().strftime("%Y-%m-%d")]
        
        # Start date
        ttk.Label(date_frame, text="Start Date:").pack(side=tk.LEFT, padx=5)
        self.menu_start_date = ttk.Combobox(date_frame, values=date_strings, width=15, state="readonly")
        self.menu_start_date.pack(side=tk.LEFT, padx=5)
        self.menu_start_date.set(date_strings[0])
        
        # End date
        ttk.Label(date_frame, text="End Date:").pack(side=tk.LEFT, padx=5)
        self.menu_end_date = ttk.Combobox(date_frame, values=date_strings, width=15, state="readonly")
        self.menu_end_date.pack(side=tk.LEFT, padx=5)
        self.menu_end_date.set(date_strings[-1])
        
        # Generate report button
        ttk.Button(
            date_frame,
            text="Generate Report",
            command=self.generate_menu_items_report
        ).pack(side=tk.LEFT, padx=5)
        
        # Create report frame
        report_frame = ttk.LabelFrame(main_frame, text="Menu Items Report", padding="5")
        report_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create text widget for report
        self.menu_items_report_text = tk.Text(report_frame, wrap=tk.WORD, font=('Arial', 10))
        self.menu_items_report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=self.menu_items_report_text.yview)
        self.menu_items_report_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def show_transaction_details(self, event):
        """Show details for the selected transaction."""
        selected = self.transaction_tree.selection()
        if not selected:
            return
        
        # Get the selected item's values
        item = self.transaction_tree.item(selected[0])
        values = item['values']
        
        # Clear the details text
        self.details_text.delete(1.0, tk.END)
        
        # Get the full transaction details from the database
        try:
            conn = sqlite3.connect(self.user_management.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT t.description, t.type, t.amount, t.timestamp,
                       (SELECT SUM(amount) FROM transactions 
                        WHERE user_id = t.user_id 
                        AND timestamp <= t.timestamp) as balance
                FROM transactions t
                JOIN users u ON t.user_id = u.id
                WHERE u.name = ? AND t.timestamp = ?
            ''', (values[0], values[3]))  # User name and timestamp
            
            transaction = cursor.fetchone()
            if transaction:
                description, type_, amount, timestamp, balance = transaction
                
                # Format the details with proper spacing
                self.details_text.insert(tk.END, f"Transaction Type: {type_.title()}\n")
                self.details_text.insert(tk.END, f"Amount: R{amount}\n")
                self.details_text.insert(tk.END, f"Date: {timestamp}\n")
                self.details_text.insert(tk.END, f"Balance After: R{balance}\n\n")
                
                # Add description with proper formatting
                if description:
                    self.details_text.insert(tk.END, "Details:\n")
                    self.details_text.insert(tk.END, description)
                
                # Configure tags for better formatting
                self.details_text.tag_configure("bold", font=('Arial', 10, 'bold'))
                self.details_text.tag_add("bold", "1.0", "1.end")
                self.details_text.tag_add("bold", "2.0", "2.end")
                self.details_text.tag_add("bold", "3.0", "3.end")
                self.details_text.tag_add("bold", "4.0", "4.end")
                self.details_text.tag_add("bold", "6.0", "6.end")
            
        except Exception as e:
            print(f"Error loading transaction details: {str(e)}")
            self.details_text.insert(tk.END, "Error loading transaction details")
        finally:
            conn.close()

    def load_transactions(self):
        # Clear existing items
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)
        
        # Clear details
        self.details_text.delete(1.0, tk.END)
        
        try:
            conn = sqlite3.connect(self.user_management.db_name)
            cursor = conn.cursor()
            
            # Build the query with filters
            query = '''
                SELECT t.id, u.name, t.amount, t.type, t.timestamp,
                       (SELECT SUM(amount) FROM transactions 
                        WHERE user_id = t.user_id 
                        AND timestamp <= t.timestamp) as balance
                FROM transactions t
                JOIN users u ON t.user_id = u.id
                WHERE 1=1
            '''
            params = []
            
            # Add user filter
            if self.user_filter.get() != 'All':
                query += " AND u.name = ?"
                params.append(self.user_filter.get())
            
            # Add type filter
            if self.type_filter.get() != 'All':
                query += " AND t.type = ?"
                params.append(self.type_filter.get())
            
            # Add date filter
            date_filter = self.date_filter.get().strip()
            if date_filter:
                try:
                    # Try to parse the date
                    datetime.strptime(date_filter, '%Y-%m-%d')
                    query += " AND DATE(t.timestamp) = ?"
                    params.append(date_filter)
                except ValueError:
                    messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
                    return
            
            # Add ordering and limit
            query += " ORDER BY t.timestamp DESC LIMIT 100"
            
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                self.transaction_tree.insert("", "end", values=(
                    row[1],  # User name
                    f"R{row[2]}",  # Amount
                    row[3],  # Type
                    row[4],  # Date
                    f"R{row[5]}"  # Balance
                ))
                
        except Exception as e:
            print(f"Error loading transactions: {str(e)}")
            messagebox.showerror("Error", f"Failed to load transactions: {str(e)}")
        finally:
            conn.close()

    def load_user_filter(self):
        """Load users into the user filter combobox."""
        try:
            conn = sqlite3.connect(self.user_management.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT name FROM users ORDER BY name')
            users = ['All'] + [row[0] for row in cursor.fetchall()]
            
            self.user_filter['values'] = users
            self.user_filter.set('All')
            
        except Exception as e:
            print(f"Error loading user filter: {str(e)}")
        finally:
            conn.close()

    def clear_filters(self):
        """Clear all filters and reload transactions."""
        self.user_filter.set('All')
        self.type_filter.set('All')
        self.date_filter.delete(0, tk.END)
        self.load_transactions()

    def load_users(self):
        """Load users from database and display them in the tree."""
        try:
            # Clear existing items
            for item in self.user_tree.get_children():
                self.user_tree.delete(item)
            
            # Load users from database
            conn = sqlite3.connect(self.user_management.db_name)
            cursor = conn.cursor()
            
            # Get all users
            cursor.execute('''
                SELECT id, name, phone, email, balance, discount_rate
                FROM users
                ORDER BY name
            ''')
            
            users = cursor.fetchall()
            print(f"Loaded {len(users)} users from database")
            
            for user in users:
                # Get RFID tags for this user
                cursor.execute('''
                    SELECT rfid
                    FROM rfid_tags
                    WHERE user_id = ?
                ''', (user[0],))
                
                rfid_tags = [row[0] for row in cursor.fetchall()]
                rfid_tags_str = ", ".join(rfid_tags) if rfid_tags else "No tags"
                
                # Format balance with 2 decimal places
                balance = f"R{float(user[4]):.2f}"
                
                # Format discount rate
                discount = f"{float(user[5]):.1f}%"
                
                # Insert user into tree
                self.user_tree.insert("", "end", values=(
                    user[1],  # name
                    user[2] or "",  # phone
                    user[3] or "",  # email
                    rfid_tags_str,
                    balance,
                    discount
                ), tags=(str(user[0]),))  # Store user ID in tags
            
            # Set column widths
            self.user_tree.column("Name", width=150)
            self.user_tree.column("Phone", width=100)
            self.user_tree.column("Email", width=200)
            self.user_tree.column("RFID Tags", width=200)
            self.user_tree.column("Balance", width=100)
            self.user_tree.column("Discount", width=80)
            
            print("Users loaded successfully")
            
        except Exception as e:
            print(f"Error loading users: {str(e)}")
            messagebox.showerror("Error", f"Failed to load users: {str(e)}")
        finally:
            conn.close()

    def show_add_user_dialog(self):
        self.add_user_window()

    def show_edit_user_dialog(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user to edit")
            return
        
        # Get the selected item's values and tags
        item = self.user_tree.item(selected[0])
        user_id = item['tags'][0]
        
        try:
            conn = sqlite3.connect(self.user_management.db_name)
            cursor = conn.cursor()
            
            # Get user information
            cursor.execute('''
                SELECT name, phone, email, discount_rate
                FROM users
                WHERE id = ?
            ''', (int(user_id),))
            
            user = cursor.fetchone()
            if not user:
                messagebox.showerror("Error", "User not found")
                return
            
            user_data = {
                'name': user[0],
                'phone': user[1] or "",
                'email': user[2] or "",
                'discount_rate': user[3]
            }
            
            dialog = tk.Toplevel(self.root)
            dialog.title("Edit User")
            dialog.geometry("400x350")
            
            # Create form
            ttk.Label(dialog, text="Name:").pack(pady=5)
            name_entry = ttk.Entry(dialog)
            name_entry.insert(0, user_data['name'])
            name_entry.pack(pady=5)
            
            ttk.Label(dialog, text="Phone:").pack(pady=5)
            phone_entry = ttk.Entry(dialog)
            phone_entry.insert(0, user_data['phone'])
            phone_entry.pack(pady=5)
            
            ttk.Label(dialog, text="Email:").pack(pady=5)
            email_entry = ttk.Entry(dialog)
            email_entry.insert(0, user_data['email'])
            email_entry.pack(pady=5)
            
            ttk.Label(dialog, text="Discount Rate (%):").pack(pady=5)
            discount_entry = ttk.Entry(dialog)
            discount_entry.insert(0, f"{user_data['discount_rate']:.1f}")
            discount_entry.pack(pady=5)
            
            def save_changes():
                name = name_entry.get().strip()
                phone = phone_entry.get().strip()
                email = email_entry.get().strip()
                
                try:
                    discount_rate = float(discount_entry.get().strip())
                    if discount_rate < 0 or discount_rate > 100:
                        messagebox.showerror("Error", "Discount rate must be between 0 and 100")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid discount rate")
                    return
                
                if not name:
                    messagebox.showerror("Error", "Name is required")
                    return
                
                success, message = self.user_management.update_user(
                    int(user_id),
                    name=name,
                    phone=phone,
                    email=email,
                    discount_rate=discount_rate
                )
                
                if success:
                    messagebox.showinfo("Success", message)
                    self.load_users()
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", message)
            
            ttk.Button(dialog, text="Save Changes", command=save_changes).pack(pady=20)
            
        except Exception as e:
            print(f"Error in edit user dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to edit user: {str(e)}")
        finally:
            conn.close()

    def delete_user(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return
        
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this user?"):
            return
        
        user_id = self.user_tree.item(selected[0])['tags'][0]
        success, message = self.user_management.delete_user(int(user_id))
        
        if success:
            messagebox.showinfo("Success", message)
            self.load_users()
        else:
            messagebox.showerror("Error", message)

    def show_load_money_dialog(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user to load money")
            return
        
        # Get the selected item's values
        item = self.user_tree.item(selected[0])
        user_id = item['tags'][0]
        print(f"Selected user ID: {user_id}")
        
        # Get user directly from database
        try:
            conn = sqlite3.connect(self.user_management.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, balance
                FROM users
                WHERE id = ?
            ''', (int(user_id),))
            
            user = cursor.fetchone()
            if not user:
                messagebox.showerror("Error", "User not found in database")
                return
            
            user_data = {
                'id': user[0],
                'name': user[1],
                'balance': Decimal(str(user[2]))
            }
            
            dialog = tk.Toplevel(self.root)
            dialog.title("Load Money")
            dialog.geometry("300x200")
            
            ttk.Label(dialog, text=f"User: {user_data['name']}").pack(pady=5)
            ttk.Label(dialog, text=f"Current Balance: R{user_data['balance']}").pack(pady=5)
            
            ttk.Label(dialog, text="Amount to Load:").pack(pady=5)
            amount_entry = ttk.Entry(dialog)
            amount_entry.pack(pady=5)
            
            def load_money():
                try:
                    # Convert input to string first to handle any format
                    amount_str = amount_entry.get().strip()
                    if not amount_str:
                        messagebox.showerror("Error", "Please enter an amount")
                        return
                    
                    # Convert to Decimal
                    try:
                        amount = Decimal(amount_str)
                    except:
                        messagebox.showerror("Error", "Please enter a valid number")
                        return
                    
                    if amount <= 0:
                        messagebox.showerror("Error", "Amount must be greater than 0")
                        return
                    
                    print(f"Loading amount: {amount} for user {user_data['id']}")
                    
                    success, message = self.user_management.update_balance(
                        int(user_data['id']),  # Ensure ID is integer
                        float(amount),  # Convert Decimal to float for database
                        "load",
                        "Money loaded to account"
                    )
                    
                    if success:
                        messagebox.showinfo("Success", message)
                        self.load_users()
                        dialog.destroy()
                    else:
                        messagebox.showerror("Error", message)
                except Exception as e:
                    print(f"Error in load_money: {str(e)}")
                    messagebox.showerror("Error", f"Failed to load money: {str(e)}")
            
            ttk.Button(dialog, text="Load Money", command=load_money).pack(pady=20)
            
        except Exception as e:
            print(f"Error loading money dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to load money dialog: {str(e)}")
        finally:
            conn.close()

    def show_manage_rfid_dialog(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user to manage RFID tags")
            return
        
        # Get the selected item's values and tags
        item = self.user_tree.item(selected[0])
        user_id = item['tags'][0]
        
        try:
            conn = sqlite3.connect(self.user_management.db_name)
            cursor = conn.cursor()
            
            # Get user information
            cursor.execute('''
                SELECT name
                FROM users
                WHERE id = ?
            ''', (int(user_id),))
            
            user = cursor.fetchone()
            if not user:
                messagebox.showerror("Error", "User not found")
                return
            
            dialog = tk.Toplevel(self.root)
            dialog.title(f"Manage RFID Tags - {user[0]}")
            dialog.geometry("400x500")
            
            # Create listbox for existing tags
            ttk.Label(dialog, text="Current RFID Tags:").pack(pady=5)
            tag_listbox = tk.Listbox(dialog, height=10)
            tag_listbox.pack(fill=tk.X, padx=5, pady=5)
            
            # Load existing tags
            rfid_tags = self.user_management.get_user_rfid_tags(int(user_id))
            for tag in rfid_tags:
                tag_listbox.insert(tk.END, tag)
            
            # Add new tag frame
            add_frame = ttk.Frame(dialog)
            add_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(add_frame, text="New Tag:").pack(side=tk.LEFT)
            new_tag_entry = ttk.Entry(add_frame)
            new_tag_entry.pack(side=tk.LEFT, padx=5)
            
            def add_tag():
                new_tag = new_tag_entry.get().strip()
                if not new_tag:
                    messagebox.showerror("Error", "Please enter a tag ID")
                    return
                
                success, message = self.user_management.add_rfid_tag(int(user_id), new_tag)
                if success:
                    tag_listbox.insert(tk.END, new_tag)
                    new_tag_entry.delete(0, tk.END)
                    self.load_users()  # Refresh the main view
                else:
                    messagebox.showerror("Error", message)
            
            ttk.Button(add_frame, text="Add Tag", command=add_tag).pack(side=tk.LEFT)
            
            def remove_tag():
                selected = tag_listbox.curselection()
                if not selected:
                    messagebox.showwarning("Warning", "Please select a tag to remove")
                    return
                
                tag = tag_listbox.get(selected[0])
                if messagebox.askyesno("Confirm", f"Remove tag {tag}?"):
                    success, message = self.user_management.remove_rfid_tag(int(user_id), tag)
                    if success:
                        tag_listbox.delete(selected[0])
                        self.load_users()  # Refresh the main view
                    else:
                        messagebox.showerror("Error", message)
            
            ttk.Button(dialog, text="Remove Selected Tag", command=remove_tag).pack(pady=5)
            
        except Exception as e:
            print(f"Error in manage RFID dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to manage RFID tags: {str(e)}")
        finally:
            conn.close()

    def show_clear_data_dialog(self):
        """Show confirmation dialog before clearing all data."""
        if not messagebox.askyesno(
            "Confirm Clear All Data",
            "WARNING: This will delete ALL users, RFID tags, and transaction history.\n\n"
            "This action cannot be undone.\n\n"
            "Are you sure you want to proceed?"
        ):
            return
        
        # Double confirmation
        if not messagebox.askyesno(
            "Final Confirmation",
            "Are you absolutely sure you want to delete all data?\n\n"
            "Type 'YES' to confirm:"
        ):
            return
        
        success, message = self.user_management.clear_all_data()
        if success:
            messagebox.showinfo("Success", message)
            self.load_users()
            self.load_transactions()
        else:
            messagebox.showerror("Error", message)

    def filter_users(self, *args):
        """Filter users based on search criteria."""
        search_text = self.search_var.get().lower()
        search_type = self.search_type.get()
        
        # Clear existing items
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        # Load users from database
        users = self.user_management.get_all_users()
        
        for user in users:
            # Get RFID tags for this user
            rfid_tags = self.user_management.get_user_rfid_tags(user['id'])
            rfid_tags_str = ", ".join(rfid_tags) if rfid_tags else "No tags"
            
            # Format balance with 2 decimal places
            balance = f"R{user['balance']:.2f}"
            
            # Format discount rate
            discount = f"{user['discount_rate']:.1f}%"
            
            # Check if user matches search criteria
            if search_text:
                if search_type == "Name" and search_text not in user['name'].lower():
                    continue
                elif search_type == "Phone" and search_text not in (user['phone'] or "").lower():
                    continue
                elif search_type == "RFID Tag" and search_text not in rfid_tags_str.lower():
                    continue
            
            self.user_tree.insert("", "end", values=(
                user['name'],
                user['phone'],
                user['email'],
                rfid_tags_str,
                balance,
                discount
            ), tags=(str(user['id']),))

    def clear_search(self):
        """Clear the search field and reset the view."""
        self.search_var.set("")
        self.search_type.set("Name")
        self.load_users()

    def generate_sales_report(self):
        """Generate sales report for Wyvern card transactions."""
        try:
            # Get dates from comboboxes
            start_date_str = self.wyvern_start_date.get()
            end_date_str = self.wyvern_end_date.get()
            
            # Parse dates
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            # Set end date to end of day
            end_date = end_date.replace(hour=23, minute=59, second=59)
            
            print(f"Generating Wyvern card sales report for period: {start_date} to {end_date}")
            
            # Clear previous report
            self.sales_report_text.delete(1.0, tk.END)
            
            # Initialize data structures
            wyvern_transactions = []
            total_sales = Decimal('0.00')
            total_discounts = Decimal('0.00')
            
            # Process all transaction log files in the date range
            current_date = start_date
            while current_date.date() <= end_date.date():
                log_file = os.path.join('transactions', f'transactions_{current_date.strftime("%Y-%m-%d")}.log')
                
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        content = f.read()
                        transactions = content.split('=' * 80)
                        
                        for transaction in transactions:
                            if not transaction.strip():
                                continue
                                
                            # Parse transaction details
                            lines = transaction.strip().split('\n')
                            payment_method = None
                            total_amount = None
                            discount_amount = None
                            items = []
                            timestamp = None
                            card_id = None
                            
                            for line in lines:
                                if line.startswith('Timestamp:'):
                                    timestamp = line.split(': ')[1].strip()
                                elif line.startswith('Payment Method:'):
                                    payment_method = line.split(': ')[1].strip()
                                    if payment_method.startswith('wyvern_card_'):
                                        card_id = payment_method.replace('wyvern_card_', '')
                                        payment_method = 'wyvern'
                                elif line.startswith('Total Amount:'):
                                    total_amount = Decimal(line.split('R')[1].strip())
                                elif line.startswith('Discount Amount:'):
                                    discount_amount = Decimal(line.split('R')[1].strip())
                                elif line.startswith('- '):
                                    item_line = line[2:].strip()
                                    if ' - ' in item_line:
                                        item_name, item_price = item_line.split(' - ')
                                        items.append((item_name.strip(), item_price.strip()))
                            
                            if payment_method == 'wyvern' and total_amount and timestamp:
                                trans_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                                
                                # Skip if not in date range
                                if not (start_date <= trans_time <= end_date):
                                    continue
                                
                                # Create transaction record
                                trans_record = {
                                    'timestamp': trans_time,
                                    'card_id': card_id,
                                    'amount': total_amount,
                                    'discount_amount': discount_amount or Decimal('0.00'),
                                    'items': items
                                }
                                
                                wyvern_transactions.append(trans_record)
                                total_sales += total_amount
                                if discount_amount:
                                    total_discounts += discount_amount
                
                # Increment date by one day
                current_date = current_date + timedelta(days=1)
            
            # Format and display report header
            self.sales_report_text.insert(tk.END, f"Wyvern Card Sales Report for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n")
            self.sales_report_text.insert(tk.END, "=" * 80 + "\n\n")
            
            # Display transactions
            if wyvern_transactions:
                self.sales_report_text.insert(tk.END, "Transactions:\n")
                self.sales_report_text.insert(tk.END, "-" * 80 + "\n")
                
                for trans in sorted(wyvern_transactions, key=lambda x: x['timestamp']):
                    self.sales_report_text.insert(tk.END, f"Time: {trans['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    self.sales_report_text.insert(tk.END, f"Card ID: {trans['card_id']}\n")
                    self.sales_report_text.insert(tk.END, f"Total Amount: R{trans['amount']:.2f}\n")
                    if trans['discount_amount'] > 0:
                        self.sales_report_text.insert(tk.END, f"Discount Amount: R{trans['discount_amount']:.2f}\n")
                        self.sales_report_text.insert(tk.END, f"Amount After Discount: R{(trans['amount'] - trans['discount_amount']):.2f}\n")
                    self.sales_report_text.insert(tk.END, "Items:\n")
                    for item_name, item_price in trans['items']:
                        self.sales_report_text.insert(tk.END, f"  - {item_name}: {item_price}\n")
                    self.sales_report_text.insert(tk.END, "-" * 80 + "\n")
                
                # Display summary
                self.sales_report_text.insert(tk.END, "\nSummary:\n")
                self.sales_report_text.insert(tk.END, "=" * 80 + "\n")
                self.sales_report_text.insert(tk.END, f"Total Transactions: {len(wyvern_transactions)}\n")
                self.sales_report_text.insert(tk.END, f"Total Sales: R{total_sales:.2f}\n")
                self.sales_report_text.insert(tk.END, f"Total Discounts: R{total_discounts:.2f}\n")
                self.sales_report_text.insert(tk.END, f"Net Sales: R{(total_sales - total_discounts):.2f}\n")
            else:
                self.sales_report_text.insert(tk.END, "No Wyvern card transactions found for the selected period.\n")
            
        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid dates in YYYY-MM-DD format")
        except Exception as e:
            print(f"Error generating Wyvern card sales report: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def generate_menu_items_report(self):
        """Generate menu items report for all sales in the selected date range."""
        try:
            # Get dates from comboboxes
            start_date_str = self.menu_start_date.get()
            end_date_str = self.menu_end_date.get()
            
            # Parse dates
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            # Set end date to end of day
            end_date = end_date.replace(hour=23, minute=59, second=59)
            
            print(f"Generating menu items report for period: {start_date} to {end_date}")
            
            # Clear previous report
            self.menu_items_report_text.delete(1.0, tk.END)
            
            # Initialize data structures
            payment_methods = {'cash': 0, 'card': 0, 'wyvern': 0}
            payment_totals = {'cash': Decimal('0.00'), 'card': Decimal('0.00'), 'wyvern': Decimal('0.00')}
            item_counts = {}
            total_items = 0
            
            # Process all transaction log files in the date range
            current_date = start_date
            while current_date.date() <= end_date.date():
                log_file = os.path.join('transactions', f'transactions_{current_date.strftime("%Y-%m-%d")}.log')
                
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        content = f.read()
                        transactions = content.split('=' * 80)
                        
                        for transaction in transactions:
                            if not transaction.strip():
                                continue
                                
                            # Parse transaction details
                            lines = transaction.strip().split('\n')
                            payment_method = None
                            total_amount = None
                            discount_amount = None
                            items = []
                            timestamp = None
                            
                            for line in lines:
                                if line.startswith('Timestamp:'):
                                    timestamp = line.split(': ')[1].strip()
                                elif line.startswith('Payment Method:'):
                                    payment_method = line.split(': ')[1].strip()
                                    if payment_method.startswith('wyvern_card_'):
                                        payment_method = 'wyvern'
                                elif line.startswith('Total Amount:'):
                                    total_amount = Decimal(line.split('R')[1].strip())
                                elif line.startswith('Discount Amount:'):
                                    discount_amount = Decimal(line.split('R')[1].strip())
                                elif line.startswith('- '):
                                    item_line = line[2:].strip()
                                    if ' - ' in item_line:
                                        item_name, item_price = item_line.split(' - ')
                                        items.append((item_name.strip(), item_price.strip()))
                            
                            if payment_method and total_amount and timestamp:
                                trans_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                                
                                # Skip if not in date range
                                if not (start_date <= trans_time <= end_date):
                                    continue
                                
                                # Update payment method totals
                                if payment_method in payment_methods:
                                    payment_methods[payment_method] += 1
                                    payment_totals[payment_method] += total_amount
                                
                                # Update item counts
                                for item_name, item_price in items:
                                    item_key = f"{item_name} ({payment_method})"
                                    item_counts[item_key] = item_counts.get(item_key, 0) + 1
                                    total_items += 1
                
                # Increment date by one day
                current_date = current_date + timedelta(days=1)
            
            # Format and display report header
            self.menu_items_report_text.insert(tk.END, f"Menu Items Report for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n")
            self.menu_items_report_text.insert(tk.END, "=" * 80 + "\n\n")
            
            # Display payment method summary
            self.menu_items_report_text.insert(tk.END, "Payment Method Summary:\n")
            self.menu_items_report_text.insert(tk.END, "-" * 80 + "\n")
            self.menu_items_report_text.insert(tk.END, f"Cash Sales: {payment_methods['cash']} transactions (R{payment_totals['cash']:.2f})\n")
            self.menu_items_report_text.insert(tk.END, f"Card Sales: {payment_methods['card']} transactions (R{payment_totals['card']:.2f})\n")
            self.menu_items_report_text.insert(tk.END, f"Wyvern Card Sales: {payment_methods['wyvern']} transactions (R{payment_totals['wyvern']:.2f})\n")
            self.menu_items_report_text.insert(tk.END, f"Total Sales: R{sum(payment_totals.values()):.2f}\n\n")
            
            # Display item sales by payment method
            if item_counts:
                self.menu_items_report_text.insert(tk.END, "Item Sales by Payment Method:\n")
                self.menu_items_report_text.insert(tk.END, "-" * 80 + "\n")
                
                # Sort items by count
                sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)
                
                for item_name, count in sorted_items:
                    self.menu_items_report_text.insert(tk.END, f"{item_name}: {count} sold\n")
                
                self.menu_items_report_text.insert(tk.END, f"\nTotal Items Sold: {total_items}\n")
                self.menu_items_report_text.insert(tk.END, f"Unique Items: {len(item_counts)}\n")
            else:
                self.menu_items_report_text.insert(tk.END, "No sales found for the selected period.\n")
            
        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid dates in YYYY-MM-DD format")
        except Exception as e:
            print(f"Error generating menu items report: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def create_reports_tab(self):
        """Create the reports tab with cash and card sales report."""
        reports_frame = ttk.Frame(self.tab_control)
        self.tab_control.add(reports_frame, text="Cash & Card Sales")
        
        # Date range selection
        date_frame = ttk.LabelFrame(reports_frame, text="Date Range", padding="10")
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Get available dates from transaction logs
        available_dates = []
        if os.path.exists('transactions'):
            for file in os.listdir('transactions'):
                if file.startswith('transactions_') and file.endswith('.log'):
                    try:
                        date_str = file.replace('transactions_', '').replace('.log', '')
                        date = datetime.strptime(date_str, "%Y-%m-%d")
                        available_dates.append(date)
                    except ValueError:
                        continue
        
        # Sort dates
        available_dates.sort()
        date_strings = [date.strftime("%Y-%m-%d") for date in available_dates]
        
        if not date_strings:
            date_strings = [datetime.now().strftime("%Y-%m-%d")]
        
        # Start date
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, padx=5, pady=5)
        self.start_date = ttk.Combobox(date_frame, values=date_strings, width=15, state="readonly")
        self.start_date.grid(row=0, column=1, padx=5, pady=5)
        self.start_date.set(date_strings[0])
        
        # End date
        ttk.Label(date_frame, text="End Date:").grid(row=0, column=2, padx=5, pady=5)
        self.end_date = ttk.Combobox(date_frame, values=date_strings, width=15, state="readonly")
        self.end_date.grid(row=0, column=3, padx=5, pady=5)
        self.end_date.set(date_strings[-1])
        
        # Generate button
        ttk.Button(reports_frame, text="Generate Report", command=self.generate_cash_card_report).pack(pady=10)
        
        # Report display area
        self.report_text = scrolledtext.ScrolledText(reports_frame, height=20, width=80)
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def generate_cash_card_report(self):
        """Generate report for cash and bank card transactions."""
        try:
            # Get dates from comboboxes
            start_date_str = self.start_date.get()
            end_date_str = self.end_date.get()
            
            # Parse dates
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            # Set end date to end of day
            end_date = end_date.replace(hour=23, minute=59, second=59)
            
            print(f"Generating cash & card report for period: {start_date} to {end_date}")
            
            # Clear previous report
            self.report_text.delete(1.0, tk.END)
            
            # Initialize data structures
            cash_transactions = []
            card_transactions = []
            total_cash = Decimal('0.00')
            total_card = Decimal('0.00')
            
            # Process all transaction log files in the date range
            current_date = start_date
            while current_date.date() <= end_date.date():
                log_file = os.path.join('transactions', f'transactions_{current_date.strftime("%Y-%m-%d")}.log')
                
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        content = f.read()
                        transactions = content.split('=' * 80)
                        
                        for transaction in transactions:
                            if not transaction.strip():
                                continue
                                
                            # Parse transaction details
                            lines = transaction.strip().split('\n')
                            payment_method = None
                            total_amount = None
                            items = []
                            timestamp = None
                            
                            for line in lines:
                                if line.startswith('Timestamp:'):
                                    timestamp = line.split(': ')[1].strip()
                                elif line.startswith('Payment Method:'):
                                    payment_method = line.split(': ')[1].strip()
                                    if payment_method.startswith('wyvern_card_'):
                                        payment_method = 'wyvern'
                                elif line.startswith('Total Amount:'):
                                    total_amount = Decimal(line.split('R')[1].strip())
                                elif line.startswith('- '):
                                    item_line = line[2:].strip()
                                    if ' - ' in item_line:
                                        item_name, item_price = item_line.split(' - ')
                                        items.append((item_name.strip(), item_price.strip()))
                            
                            if payment_method and total_amount and timestamp:
                                trans_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                                
                                # Skip if not in date range
                                if not (start_date <= trans_time <= end_date):
                                    continue
                                
                                # Skip Wyvern card transactions
                                if payment_method == 'wyvern':
                                    continue
                                
                                # Create transaction record
                                trans_record = {
                                    'timestamp': trans_time,
                                    'payment_method': payment_method,
                                    'amount': total_amount,
                                    'items': items
                                }
                                
                                # Add to appropriate list
                                if payment_method == 'cash':
                                    cash_transactions.append(trans_record)
                                    total_cash += total_amount
                                elif payment_method == 'card':
                                    card_transactions.append(trans_record)
                                    total_card += total_amount
                
                # Increment date by one day
                current_date = current_date + timedelta(days=1)
            
            # Format and display report header
            self.report_text.insert(tk.END, f"Cash & Card Transactions Report\n")
            self.report_text.insert(tk.END, f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n")
            self.report_text.insert(tk.END, "=" * 80 + "\n\n")
            
            # Display cash transactions
            if cash_transactions:
                self.report_text.insert(tk.END, "Cash Transactions:\n")
                self.report_text.insert(tk.END, "-" * 80 + "\n")
                for trans in sorted(cash_transactions, key=lambda x: x['timestamp']):
                    self.report_text.insert(tk.END, f"Time: {trans['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    self.report_text.insert(tk.END, f"Amount: R{trans['amount']:.2f}\n")
                    self.report_text.insert(tk.END, "Items:\n")
                    for item_name, item_price in trans['items']:
                        self.report_text.insert(tk.END, f"  - {item_name}: {item_price}\n")
                    self.report_text.insert(tk.END, "-" * 80 + "\n")
            
            # Display card transactions
            if card_transactions:
                self.report_text.insert(tk.END, "\nCard Transactions:\n")
                self.report_text.insert(tk.END, "-" * 80 + "\n")
                for trans in sorted(card_transactions, key=lambda x: x['timestamp']):
                    self.report_text.insert(tk.END, f"Time: {trans['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    self.report_text.insert(tk.END, f"Amount: R{trans['amount']:.2f}\n")
                    self.report_text.insert(tk.END, "Items:\n")
                    for item_name, item_price in trans['items']:
                        self.report_text.insert(tk.END, f"  - {item_name}: {item_price}\n")
                    self.report_text.insert(tk.END, "-" * 80 + "\n")
            
            # Display summary
            self.report_text.insert(tk.END, "\nSummary:\n")
            self.report_text.insert(tk.END, "=" * 80 + "\n")
            self.report_text.insert(tk.END, f"Total Cash Transactions: {len(cash_transactions)} (R{total_cash:.2f})\n")
            self.report_text.insert(tk.END, f"Total Card Transactions: {len(card_transactions)} (R{total_card:.2f})\n")
            self.report_text.insert(tk.END, f"Total Transactions: {len(cash_transactions) + len(card_transactions)}\n")
            self.report_text.insert(tk.END, f"Total Sales: R{(total_cash + total_card):.2f}\n")
            
        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid dates in YYYY-MM-DD format")
        except Exception as e:
            print(f"Error generating cash & card report: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def show_payment_buttons(self):
        if not self.order_tree.get_children():
            messagebox.showwarning("Warning", "Your order is empty")
            return
        
        # Hide cash frame if visible
        self.cash_frame.pack_forget()
        
        # Show payment buttons
        self.payment_frame.pack(fill=tk.X, pady=10)
        
        # Load and resize the card image
        try:
            card_image = tk.PhotoImage(file="MC_VISA.png")
            # Resize image to fit button (adjust size as needed)
            card_image = card_image.subsample(2, 2)  # Reduce size by half
            self.card_button.configure(image=card_image, compound=tk.LEFT)
            self.card_button.image = card_image  # Keep a reference to prevent garbage collection
        except Exception as e:
            print(f"Error loading card image: {str(e)}")
            # If image loading fails, just use text
            self.card_button.configure(image="", text="Pay with Bank Card")

    def add_user_window(self):
        """Create a window for adding a new user."""
        add_window = tk.Toplevel(self.root)
        add_window.title("Add New User")
        add_window.geometry("400x500")  # Increased height to accommodate all fields
        add_window.resizable(False, False)
        
        # Create main frame with padding
        main_frame = ttk.Frame(add_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create form fields with consistent spacing
        ttk.Label(main_frame, text="Name:").pack(anchor=tk.W, pady=(0, 5))
        name_entry = ttk.Entry(main_frame, width=40)
        name_entry.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(main_frame, text="Phone:").pack(anchor=tk.W, pady=(0, 5))
        phone_entry = ttk.Entry(main_frame, width=40)
        phone_entry.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(main_frame, text="Email:").pack(anchor=tk.W, pady=(0, 5))
        email_entry = ttk.Entry(main_frame, width=40)
        email_entry.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(main_frame, text="RFID Tag:").pack(anchor=tk.W, pady=(0, 5))
        rfid_entry = ttk.Entry(main_frame, width=40)
        rfid_entry.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(main_frame, text="Discount Rate (%):").pack(anchor=tk.W, pady=(0, 5))
        discount_entry = ttk.Entry(main_frame, width=40)
        discount_entry.insert(0, "0.00")
        discount_entry.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(main_frame, text="Opening Balance:").pack(anchor=tk.W, pady=(0, 5))
        balance_entry = ttk.Entry(main_frame, width=40)
        balance_entry.insert(0, "0.00")
        balance_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def add_user():
            try:
                name = name_entry.get().strip()
                phone = phone_entry.get().strip()
                email = email_entry.get().strip()
                rfid = rfid_entry.get().strip()
                discount_rate = float(discount_entry.get().strip())
                opening_balance = float(balance_entry.get().strip())
                
                if not name or not rfid:
                    messagebox.showerror("Error", "Name and RFID tag are required")
                    return
                
                success, message = self.user_management.add_user(
                    name, phone, email, rfid, discount_rate, opening_balance
                )
                
                if success:
                    messagebox.showinfo("Success", message)
                    self.load_users()  # Changed from refresh_user_list to load_users
                    add_window.destroy()  # Ensure window is destroyed after successful addition
                else:
                    messagebox.showerror("Error", message)
            except ValueError:
                messagebox.showerror("Error", "Invalid number format for discount rate or opening balance")
        
        # Add buttons with consistent spacing
        ttk.Button(button_frame, text="Add User", command=add_user).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=add_window.destroy).pack(side=tk.LEFT)
        
        # Center the window
        add_window.update_idletasks()
        width = add_window.winfo_width()
        height = add_window.winfo_height()
        x = (add_window.winfo_screenwidth() // 2) - (width // 2)
        y = (add_window.winfo_screenheight() // 2) - (height // 2)
        add_window.geometry(f'{width}x{height}+{x}+{y}')

def main():
    root = tk.Tk()
    app = UserManagementUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
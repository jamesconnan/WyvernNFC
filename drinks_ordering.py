import tkinter as tk
from tkinter import ttk, messagebox
import json
from decimal import Decimal
from datetime import datetime
import os
import socket
import threading
import time

class DrinksOrderingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Drinks Ordering System")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Make window fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Load menu data
        with open('drinks_menu.json', 'r') as file:
            self.menu_data = json.load(file)
        
        # Initialize order
        self.current_order = []
        self.total_amount = Decimal('0.00')
        
        # Network status
        self.network_status = tk.StringVar()
        self.network_status.set("Checking network...")
        self.is_online = False
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=20, font=('Arial', 16))
        self.style.configure("TLabel", font=('Arial', 16))
        self.style.configure("Header.TLabel", font=('Arial', 24, 'bold'))
        self.style.configure("Price.TLabel", font=('Arial', 20, 'bold'))
        self.style.configure("Treeview", font=('Arial', 16))
        self.style.configure("Treeview.Heading", font=('Arial', 16, 'bold'))
        self.style.configure("TRadiobutton", font=('Arial', 16))
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="30")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header with exit button
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=20)
        
        header = ttk.Label(header_frame, text="Drinks Menu", style="Header.TLabel")
        header.pack(side=tk.LEFT, expand=True)
        
        exit_button = ttk.Button(header_frame, text="Exit", command=self.root.destroy)
        exit_button.pack(side=tk.RIGHT, padx=20)
        
        # Create main content area
        self.create_content_area()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to take orders")
        status_bar = ttk.Frame(root)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status message
        status_label = ttk.Label(status_bar, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 16))
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Network status indicator
        self.network_label = ttk.Label(status_bar, textvariable=self.network_status, relief=tk.SUNKEN, anchor=tk.E, font=('Arial', 16))
        self.network_label.pack(side=tk.RIGHT, fill=tk.X, padx=(10, 0))
        
        # Start network monitoring
        self.start_network_monitoring()
    
    def check_network_connection(self):
        try:
            # Try to connect to a reliable server (Google's DNS)
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False
    
    def update_network_status(self):
        while True:
            is_connected = self.check_network_connection()
            if is_connected != self.is_online:
                self.is_online = is_connected
                if is_connected:
                    self.network_status.set("Online")
                    self.network_label.configure(foreground="green")
                else:
                    self.network_status.set("Offline")
                    self.network_label.configure(foreground="red")
            time.sleep(5)  # Check every 5 seconds
    
    def start_network_monitoring(self):
        # Start network monitoring in a separate thread
        network_thread = threading.Thread(target=self.update_network_status, daemon=True)
        network_thread.start()
    
    def create_content_area(self):
        # Create main content frame
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Create menu frame with scrollbar
        menu_frame = ttk.Frame(content_frame)
        menu_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(menu_frame)
        scrollbar = ttk.Scrollbar(menu_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create navigation history
        self.navigation_history = []
        
        # Create category buttons
        self.show_level(self.menu_data)
        
        # Create order summary frame
        summary_frame = ttk.LabelFrame(content_frame, text="Order Summary", padding="20")
        summary_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Order list with increased row height
        self.order_tree = ttk.Treeview(summary_frame, columns=("Description", "Price"), show="headings", height=15)
        self.order_tree.heading("Description", text="Description")
        self.order_tree.heading("Price", text="Price")
        self.order_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Buttons frame
        buttons_frame = ttk.Frame(summary_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Undo button
        undo_button = ttk.Button(buttons_frame, text="Undo Last Item", command=self.undo_last_item, width=20)
        undo_button.pack(side=tk.LEFT, padx=5)
        
        # Checkout button
        checkout_button = ttk.Button(buttons_frame, text="Checkout", command=self.show_payment_buttons, width=20)
        checkout_button.pack(side=tk.RIGHT, padx=5)
        
        # Total amount
        self.total_label = ttk.Label(summary_frame, text="Total: R0.00", style="Price.TLabel")
        self.total_label.pack(pady=20)
        
        # Payment buttons frame (initially hidden)
        self.payment_frame = ttk.Frame(summary_frame)
        self.payment_frame.pack(fill=tk.X, pady=10)
        
        # Card payment button
        self.card_button = ttk.Button(
            self.payment_frame,
            text="Pay by Card",
            command=lambda: self.process_payment("card"),
            width=20
        )
        self.card_button.pack(side=tk.LEFT, padx=5)
        
        # Cash payment button
        self.cash_button = ttk.Button(
            self.payment_frame,
            text="Pay by Cash",
            command=self.show_cash_payment,
            width=20
        )
        self.cash_button.pack(side=tk.RIGHT, padx=5)
        
        # Initially hide payment buttons
        self.payment_frame.pack_forget()
        
        # Create cash payment frame (initially hidden)
        self.cash_frame = ttk.Frame(self.main_frame)
        self.cash_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        self.cash_frame.pack_forget()
        
        # Total amount for cash payment
        self.cash_total_label = ttk.Label(self.cash_frame, text="", font=('Arial', 16, 'bold'))
        self.cash_total_label.pack(pady=10)
        
        # Amount received
        amount_frame = ttk.Frame(self.cash_frame)
        amount_frame.pack(pady=20)
        
        ttk.Label(amount_frame, text="Amount Received:").pack(side=tk.LEFT, padx=5)
        self.amount_entry = ttk.Entry(amount_frame, font=('Arial', 16))
        self.amount_entry.pack(side=tk.LEFT, padx=5)
        
        # Change amount
        self.change_label = ttk.Label(self.cash_frame, text="Change: R0.00", font=('Arial', 16))
        self.change_label.pack(pady=10)
        
        # Calculate/Complete button
        self.calculate_button = ttk.Button(
            self.cash_frame,
            text="Calculate Change",
            command=self.calculate_change,
            width=20
        )
        self.calculate_button.pack(pady=10)
    
    def show_level(self, items, level_name=None):
        # Clear current view
        for widget in self.scrollable_frame.winfo_children():
            widget.pack_forget()
        
        # Add back button if not at root level
        if self.navigation_history:
            back_button = ttk.Button(
                self.scrollable_frame,
                text="← Back",
                command=self.go_back,
                width=30
            )
            back_button.pack(fill=tk.X, pady=5, padx=5)
        
        # Add level title if provided
        if level_name:
            title_label = ttk.Label(
                self.scrollable_frame,
                text=level_name,
                font=('Arial', 16, 'bold')
            )
            title_label.pack(fill=tk.X, pady=10, padx=5)
        
        # Create buttons for each item at this level
        if isinstance(items, dict):
            for name, subitems in items.items():
                if isinstance(subitems, dict):
                    if "price" in subitems or "single_price" in subitems:
                        # It's a drink item
                        self.create_drink_button(self.scrollable_frame, name, subitems)
                    else:
                        # It's a category
                        btn = ttk.Button(
                            self.scrollable_frame,
                            text=name,
                            command=lambda n=name, i=subitems: self.navigate_to(n, i),
                            width=30
                        )
                        btn.pack(fill=tk.X, pady=5, padx=5)
    
    def navigate_to(self, name, items):
        # Add current level to history
        self.navigation_history.append((name, items))
        # Show the new level
        self.show_level(items, name)
    
    def go_back(self):
        if self.navigation_history:
            # Remove current level from history
            self.navigation_history.pop()
            if self.navigation_history:
                # Go back to previous level
                name, items = self.navigation_history[-1]
                self.show_level(items, name)
            else:
                # Go back to root level
                self.show_level(self.menu_data)
    
    def create_drink_button(self, parent, name, details):
        if "price" in details:
            price = details["price"]
        elif "single_price" in details:
            price = details["single_price"]
        else:
            return
        
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=5)
        
        button = ttk.Button(
            button_frame,
            text=f"{name} - R{price}",
            command=lambda: self.add_to_order(name, details),
            width=30
        )
        button.pack(side=tk.LEFT, padx=5)
    
    def add_to_order(self, name, details):
        # Get price
        price = details.get('price', details.get('single_price'))
        
        if price is None:
            messagebox.showerror("Error", "Could not determine price for selected item")
            return
        
        # Add to order tree
        self.order_tree.insert("", "end", values=(name, f"R{price}"))
        
        # Update total amount
        self.total_amount += Decimal(str(price))
        self.total_label.config(text=f"Total: R{self.total_amount}")
        
        # Update status
        self.status_var.set(f"Added {name} to order")
    
    def undo_last_item(self):
        if not self.order_tree.get_children():
            messagebox.showwarning("Warning", "No items to undo")
            return
        
        # Get the last item
        last_item = self.order_tree.get_children()[-1]
        values = self.order_tree.item(last_item)['values']
        
        # Subtract the price from the running total
        price = Decimal(values[1].replace('R', ''))
        self.total_amount -= price
        
        # Remove the item
        self.order_tree.delete(last_item)
        
        # Update the total label
        self.total_label.config(text=f"Total: R{self.total_amount}")
        
        # Update status
        self.status_var.set("Last item removed from order")
    
    def show_payment_buttons(self):
        if not self.order_tree.get_children():
            messagebox.showwarning("Warning", "Your order is empty")
            return
        
        # Hide cash frame if visible
        self.cash_frame.pack_forget()
        
        # Show payment buttons
        self.payment_frame.pack(fill=tk.X, pady=10)
    
    def process_payment(self, payment_method):
        if payment_method == "card":
            self.complete_transaction("card")
        else:
            self.show_cash_payment()
    
    def show_cash_payment(self):
        # Hide payment buttons
        self.payment_frame.pack_forget()
        
        # Update total amount label
        self.cash_total_label.config(text=f"Total Amount: R{self.total_amount}")
        
        # Reset cash payment interface
        self.amount_entry.delete(0, tk.END)
        self.change_label.config(text="Change: R0.00")
        self.calculate_button.config(
            text="Calculate Change",
            command=self.calculate_change
        )
        
        # Show cash payment frame
        self.cash_frame.pack(fill=tk.BOTH, expand=True, pady=20)
    
    def calculate_change(self):
        try:
            amount_received = Decimal(self.amount_entry.get())
            if amount_received < self.total_amount:
                messagebox.showerror("Error", "Amount received is less than total amount")
                return
            
            change = amount_received - self.total_amount
            self.change_label.config(text=f"Change: R{change}")
            
            # Change button to Complete Transaction
            self.calculate_button.config(
                text="Complete Transaction",
                command=lambda: self.complete_transaction("cash", self.amount_entry.get())
            )
            
        except (ValueError, InvalidOperation):
            messagebox.showerror("Error", "Please enter a valid amount")
    
    def complete_transaction(self, payment_method, amount_received=None):
        # Create transaction log entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items = []
        for item in self.order_tree.get_children():
            values = self.order_tree.item(item)['values']
            items.append(f"{values[0]} - {values[1]}")
        
        transaction = {
            "timestamp": timestamp,
            "payment_method": payment_method,
            "total_amount": float(self.total_amount),
            "amount_received": float(amount_received) if amount_received else None,
            "items": items
        }
        
        # Save transaction to log file
        self.save_transaction(transaction)
        
        # Show success message
        message = f"Transaction completed successfully!\n\n"
        message += f"Payment Method: {'Bank Card' if payment_method == 'card' else 'Cash'}\n"
        message += f"Total Amount: R{self.total_amount}\n"
        if payment_method == "cash":
            message += f"Amount Received: R{amount_received}\n"
            message += f"Change: R{Decimal(amount_received) - self.total_amount}\n"
        
        messagebox.showinfo("Success", message)
        
        # Reset the interface
        self.reset_interface()
    
    def reset_interface(self):
        # Clear order
        self.order_tree.delete(*self.order_tree.get_children())
        self.total_amount = Decimal('0.00')
        self.total_label.config(text="Total: R0.00")
        
        # Hide payment frames
        self.payment_frame.pack_forget()
        self.cash_frame.pack_forget()
        
        # Reset status
        self.status_var.set("Ready for next order")
    
    def save_transaction(self, transaction):
        # Ensure transactions directory exists
        if not os.path.exists('transactions'):
            os.makedirs('transactions')
        
        # Save to daily log file
        date = datetime.now().strftime("%Y-%m-%d")
        log_file = f'transactions/transactions_{date}.json'
        
        try:
            # Load existing transactions
            if os.path.exists(log_file):
                with open(log_file, 'r') as file:
                    transactions = json.load(file)
            else:
                transactions = []
            
            # Add new transaction
            transactions.append(transaction)
            
            # Save updated transactions
            with open(log_file, 'w') as file:
                json.dump(transactions, file, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save transaction: {str(e)}")

def main():
    root = tk.Tk()
    app = DrinksOrderingSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main() 

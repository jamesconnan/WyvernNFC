import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import json
from datetime import datetime
import configparser
import os

class KitchenDisplay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Kitchen Display")
        self.root.geometry("800x600")
        
        # Load configuration
        self.config = self.load_config()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create orders frame
        self.orders_frame = ttk.Frame(self.main_frame)
        self.orders_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(self.orders_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create canvas for orders
        self.canvas = tk.Canvas(self.orders_frame, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        self.scrollbar.config(command=self.canvas.yview)
        
        # Create frame inside canvas for orders
        self.orders_container = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.orders_container, anchor=tk.NW)
        
        # Bind canvas to scrollbar
        self.orders_container.bind('<Configure>', 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Initialize orders list
        self.orders = []
        
        # Create refresh button
        self.refresh_button = ttk.Button(self.main_frame, text="Refresh Orders", 
                                       command=self.refresh_orders)
        self.refresh_button.grid(row=1, column=0, pady=10)
        
        # Initial load of orders
        self.refresh_orders()
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
    def load_config(self):
        """Load configuration from settings.cfg file."""
        config = configparser.ConfigParser()
        if not os.path.exists('settings.cfg'):
            raise FileNotFoundError("settings.cfg file not found")
        
        config.read('settings.cfg')
        return {
            'mysql_host': config.get('MySQL', 'host'),
            'mysql_database': config.get('MySQL', 'database'),
            'mysql_user': config.get('MySQL', 'user'),
            'mysql_password': config.get('MySQL', 'password')
        }
    
    def get_mysql_connection(self):
        """Create and return a MySQL connection."""
        try:
            connection = mysql.connector.connect(
                host=self.config['mysql_host'],
                database=self.config['mysql_database'],
                user=self.config['mysql_user'],
                password=self.config['mysql_password']
            )
            return connection
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error connecting to MySQL: {err}")
            return None
    
    def refresh_orders(self):
        """Refresh the orders display."""
        # Clear existing orders
        for widget in self.orders_container.winfo_children():
            widget.destroy()
        
        # Get new orders from database
        connection = self.get_mysql_connection()
        if not connection:
            return
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # First, check if status column exists
            cursor.execute("SHOW COLUMNS FROM transactions LIKE 'status'")
            status_exists = cursor.fetchone()
            
            if not status_exists:
                # Add status column if it doesn't exist
                cursor.execute('''
                    ALTER TABLE transactions 
                    ADD COLUMN status VARCHAR(20) DEFAULT 'pending'
                ''')
                connection.commit()
            
            # First, let's see all orders without the kitchen filter
            cursor.execute('''
                SELECT id, timestamp, items, status
                FROM transactions
                ORDER BY timestamp DESC
            ''')
            
            all_orders = cursor.fetchall()
            print(f"Total orders found: {len(all_orders)}")
            
            # Now fetch kitchen orders - search in the entire items JSON
            cursor.execute('''
                SELECT id, timestamp, items, status
                FROM transactions
                WHERE LOWER(items) LIKE '%kitchen%'
                AND status IN ('pending', 'accepted')
                ORDER BY timestamp DESC
            ''')
            
            self.orders = cursor.fetchall()
            print(f"Kitchen orders found: {len(self.orders)}")
            
            # Display orders
            for order in self.orders:
                print(f"Processing order {order['id']}")
                print(f"Items: {order['items']}")
                self.create_order_widget(order)
                
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error fetching orders: {err}")
        finally:
            connection.close()
    
    def create_order_widget(self, order):
        """Create a widget for displaying an order."""
        # Create frame for order
        order_frame = ttk.LabelFrame(self.orders_container, padding="5")
        order_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Parse items
        try:
            items = json.loads(order['items'])
            print(f"Parsed items for order {order['id']}: {items}")
            # Show all items since we know this is a kitchen order
            kitchen_items = items
            print(f"Items to display: {kitchen_items}")
        except json.JSONDecodeError as e:
            print(f"Error parsing items for order {order['id']}: {e}")
            print(f"Raw items data: {order['items']}")
            return
        
        # Create order details
        ttk.Label(order_frame, 
                 text=f"Order #{order['id']} - {order['timestamp']}").pack(anchor=tk.W)
        
        # Create items list
        items_frame = ttk.Frame(order_frame)
        items_frame.pack(fill=tk.X, pady=5)
        
        for item in kitchen_items:
            # Show both name and description if available
            item_text = item['name']
            if 'description' in item and item['description']:
                item_text += f" - {item['description']}"
            ttk.Label(items_frame, 
                     text=f"• {item_text}").pack(anchor=tk.W)
        
        # Create buttons frame
        buttons_frame = ttk.Frame(order_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        if order['status'] == 'pending':
            ttk.Button(buttons_frame, text="Accept Order",
                      command=lambda: self.accept_order(order['id'])).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Button(buttons_frame, text="Mark Complete",
                      command=lambda: self.complete_order(order['id'])).pack(side=tk.LEFT, padx=5)
    
    def accept_order(self, order_id):
        """Accept an order."""
        connection = self.get_mysql_connection()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE transactions
                SET status = 'accepted'
                WHERE id = %s
            ''', (order_id,))
            connection.commit()
            messagebox.showinfo("Success", "Order accepted!")
            self.refresh_orders()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error accepting order: {err}")
        finally:
            connection.close()
    
    def complete_order(self, order_id):
        """Mark an order as complete."""
        connection = self.get_mysql_connection()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE transactions
                SET status = 'completed'
                WHERE id = %s
            ''', (order_id,))
            connection.commit()
            messagebox.showinfo("Success", "Order marked as complete!")
            self.refresh_orders()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error completing order: {err}")
        finally:
            connection.close()
    
    def run(self):
        """Start the application."""
        self.root.mainloop()

if __name__ == "__main__":
    app = KitchenDisplay()
    app.run() 
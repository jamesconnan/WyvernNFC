import tkinter as tk
from tkinter import ttk, messagebox
import json
from decimal import Decimal
from datetime import datetime
import os
import socket
import threading
import time
from google_drive_utils import download_credentials_file
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pickle
from user_management import UserManagement
from PIL import Image, ImageTk
import base64

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DrinksOrderingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Drinks Ordering System")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Make window fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Add keyboard shortcut to close program (Ctrl+J)
        self.root.bind('<Control-j>', lambda e: self.root.destroy())
        
        # Initialize order
        self.current_order = []
        self.total_amount = Decimal('0.00')
        
        # Initialize user management
        self.user_management = UserManagement()
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=20, font=('Arial', 16))
        self.style.configure("TLabel", font=('Arial', 16))
        self.style.configure("Header.TLabel", font=('Arial', 24, 'bold'))
        self.style.configure("Price.TLabel", font=('Arial', 20, 'bold'))
        self.style.configure("Treeview", font=('Arial', 16))
        self.style.configure("Treeview.Heading", font=('Arial', 16, 'bold'))
        self.style.configure("TRadiobutton", font=('Arial', 16))
        # Add green button style
        self.style.configure("Green.TButton", background="green", foreground="white")
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="30")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header with exit button
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=20)
        
        # Network status
        self.network_status = tk.StringVar()
        self.network_status.set("Checking network...")
        self.is_online = False
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Initializing...")
        status_bar = ttk.Frame(root)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status message
        status_label = ttk.Label(status_bar, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 16))
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Network status indicator
        self.network_label = ttk.Label(status_bar, textvariable=self.network_status, relief=tk.SUNKEN, anchor=tk.E, font=('Arial', 16))
        self.network_label.pack(side=tk.RIGHT, fill=tk.X, padx=(10, 0))
        
        # Create default menu if it doesn't exist
        if not os.path.exists('bar_menu.csv'):
            self.create_default_menu()
        
        # Load menu data
        self.load_menu_data()
        
        # Create content area
        self.create_content_area()
        
        # Start network monitoring after UI is set up
        self.start_network_monitoring()
    
    def create_default_menu(self):
        """Creates a default menu file if it doesn't exist."""
        default_menu = """BEER:,BLACK LABEL,340ML BOTTLE,25
BEER:,CASTLE LAGER,340ML BOTTLE,25
BEER:,CASTLE LITE,340ML BOTTLE,20
BEER:,CASTLE LITE,QUART,40
BEER:,CORONA,340ML BOTTLE,35
BEER:,HANSA,340ML BOTTLE,20
BEER:,HANSA,QUART,35
BEER:,AMSTEL RADLER,340ML BOTTLE,30
BEER:,LION LAGER,QUART,30
BEER:,HEINEKEN LAGER,340ML BOTTLE,35
BEER:,HEINEKEN FREE,340ML BOTTLE,35
BEER:,HEINEKEN SILVER,340ML BOTTLE,35
BEER:,WINDHOEK DRAFT,440ML BOTTLE,30
BEER:,WINDHOEK LAGER,340ML BOTTLE,35
BEER:,STELLA ARTOIS,BOTTLE,30
BEER:,TAFEL LAGER,340ML BOTTLE,25"""
        
        with open('bar_menu.csv', 'w') as file:
            file.write(default_menu)
        print("Created default menu file")
    
    def check_network_connection(self):
        try:
            # Try to connect to a reliable server (Google's DNS)
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False
    
    def update_network_status(self):
        """Updates the network status in a thread-safe way."""
        while True:
            try:
                is_connected = self.check_network_connection()
                if is_connected != self.is_online:
                    self.is_online = is_connected
                    if is_connected:
                        self.root.after(0, lambda: self.network_status.set("Online"))
                        self.root.after(0, lambda: self.network_label.configure(foreground="green"))
                        self.root.after(0, self.load_menu_data)
                    else:
                        self.root.after(0, lambda: self.network_status.set("Offline"))
                        self.root.after(0, lambda: self.network_label.configure(foreground="red"))
                time.sleep(5)
            except Exception as e:
                print(f"Error in network status update: {e}")
                time.sleep(5)  # Wait before retrying
    
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
        
        # Configure canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add mouse wheel scrolling
        def _on_mousewheel(event):
            # For Linux systems
            if event.num == 4:  # Scroll up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Scroll down
                self.canvas.yview_scroll(1, "units")
            # For Windows/Mac systems
            else:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind mousewheel to canvas for both Linux and Windows/Mac
        self.canvas.bind_all("<Button-4>", _on_mousewheel)  # Linux scroll up
        self.canvas.bind_all("<Button-5>", _on_mousewheel)  # Linux scroll down
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows/Mac
        
        # Function to update canvas width
        def _configure_canvas(event):
            # Update the width of the frame inside canvas
            self.canvas.itemconfig(self.canvas_frame, width=event.width)
        
        # Create the frame inside canvas
        self.canvas_frame = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw",
            width=self.canvas.winfo_width()
        )
        
        # Bind configure event to update canvas width
        self.canvas.bind('<Configure>', _configure_canvas)
        
        # Configure scrollable frame
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
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
        
        # Check Balance button
        check_balance_button = ttk.Button(
            buttons_frame,
            text="Check Wyvern Balance",
            command=self.show_check_balance_dialog,
            width=20
        )
        check_balance_button.pack(side=tk.LEFT, padx=5)
        
        # Checkout button
        checkout_button = ttk.Button(
            buttons_frame,
            text="Checkout",
            command=self.show_payment_buttons,
            width=20,
            style="Green.TButton"
        )
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
            text="Pay with Bank Card",
            command=lambda: self.process_payment("card"),
            width=20
        )
        # Load and resize the card image
        try:
            card_image = tk.PhotoImage(file="MC_VISAs.png")
            self.card_button.configure(image=card_image, compound=tk.LEFT)
            self.card_button.image = card_image  # Keep a reference to prevent garbage collection
        except Exception as e:
            print(f"Error loading card image: {str(e)}")
            # If image loading fails, just use text
            self.card_button.configure(image="", text="Pay with Bank Card")
        self.card_button.pack(side=tk.LEFT, padx=5)
        
        # Wyvern Card payment button
        self.wyvern_button = ttk.Button(
            self.payment_frame,
            text="Pay with Wyvern Card",
            command=lambda: self.process_payment("wyvern"),
            width=20
        )
        # Load and resize the Wyvern image
        try:
            wyvern_image = tk.PhotoImage(file="wyvern.png")
            self.wyvern_button.configure(image=wyvern_image, compound=tk.LEFT)
            self.wyvern_button.image = wyvern_image  # Keep a reference to prevent garbage collection
        except Exception as e:
            print(f"Error loading Wyvern image: {str(e)}")
            # If image loading fails, just use text
            self.wyvern_button.configure(image="", text="Pay with Wyvern Card")
        self.wyvern_button.pack(side=tk.LEFT, padx=5)

        # Cash payment button
        self.cash_button = ttk.Button(
            self.payment_frame,
            text="Pay with Cash",
            command=self.show_cash_payment,
            width=20
        )
        # Load and resize the cash image
        try:
            cash_image = tk.PhotoImage(file="cash.png")
            self.cash_button.configure(image=cash_image, compound=tk.LEFT)
            self.cash_button.image = cash_image  # Keep a reference to prevent garbage collection
        except Exception as e:
            print(f"Error loading cash image: {str(e)}")
            # If image loading fails, just use text
            self.cash_button.configure(image="", text="Pay with Cash")
        self.cash_button.pack(side=tk.LEFT, padx=5)
        
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
        button_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Calculate button width based on window width
        window_width = self.root.winfo_width()
        button_width = min(50, max(30, window_width // 20))  # Adjust width based on window size
        
        # Create a frame for the button content
        content_frame = ttk.Frame(button_frame)
        content_frame.pack(fill=tk.X, expand=True)
        
        # Try to load the product image
        try:
            # Extract product name from the full name (remove size info)
            product_name = name.split(" (")[0].strip()
            
            # Try different variations of the image name
            possible_names = [
                product_name.lower().replace(" ", "_") + ".jpeg",
                product_name.lower().replace(" ", "_") + ".jpg",
                product_name.lower().replace(" ", "") + ".jpeg",
                product_name.lower().replace(" ", "") + ".jpg",
                product_name.lower() + ".jpeg",  # Try exact name
                product_name.lower() + ".jpg"    # Try exact name with jpg
            ]
            
            # Add special cases (all lowercase)
            if "black label" in product_name.lower():
                possible_names.append("black label.jpeg")
            elif "castle lager" in product_name.lower():
                possible_names.append("castle lager.jpeg")
            elif "castle lite" in product_name.lower():
                possible_names.append("castle lite pic.jpeg")
            elif "heineken" in product_name.lower():
                possible_names.append("heineken lager.jpeg")
            elif "stella" in product_name.lower():
                possible_names.append("stella.jpeg")
            elif "tafel" in product_name.lower():
                possible_names.append("tafel.jpeg")
            
            # Try to find a matching image
            image_found = False
            for image_name in possible_names:
                image_path = os.path.join("images", image_name)
                # Check if file exists (case-insensitive)
                if any(os.path.exists(os.path.join("images", f)) and f.lower() == image_name.lower() 
                      for f in os.listdir("images")):
                    try:
                        # Get the actual filename with correct case
                        actual_filename = next(f for f in os.listdir("images") 
                                            if f.lower() == image_name.lower())
                        image_path = os.path.join("images", actual_filename)
                        
                        # Open and resize the image using PIL
                        pil_image = Image.open(image_path)
                        # Calculate new size (e.g., 50x50 pixels)
                        target_size = (50, 50)
                        pil_image = pil_image.resize(target_size, Image.Resampling.LANCZOS)
                        # Convert PIL image to PhotoImage
                        product_image = ImageTk.PhotoImage(pil_image)
                        image_found = True
                        break
                    except Exception as e:
                        print(f"Error loading image {image_path}: {str(e)}")
                        continue
            
            if not image_found:
                # Use notfound.jpeg if no product image found
                try:
                    # Find notfound.jpeg case-insensitively
                    notfound_files = [f for f in os.listdir("images") 
                                    if f.lower() == "notfound.jpeg"]
                    if notfound_files:
                        notfound_path = os.path.join("images", notfound_files[0])
                        pil_image = Image.open(notfound_path)
                        target_size = (50, 50)
                        pil_image = pil_image.resize(target_size, Image.Resampling.LANCZOS)
                        product_image = ImageTk.PhotoImage(pil_image)
                    else:
                        print("notfound.jpeg not found in images directory")
                        return
                except Exception as e:
                    print(f"Error loading notfound.jpeg: {str(e)}")
                    return
            
            # Create image label
            image_label = ttk.Label(content_frame, image=product_image)
            image_label.image = product_image  # Keep a reference
            image_label.pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            print(f"Error loading image for {name}: {str(e)}")
        
        # Create button with text
        button = ttk.Button(
            content_frame,
            text=f"{name} - R{price}",
            command=lambda: self.add_to_order(name, details),
            width=button_width
        )
        button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    def add_to_order(self, name, details):
        # Get price
        price = details.get('price', details.get('single_price'))
        
        if price is None:
            messagebox.showerror("Error", "Could not determine price for selected item")
            return
        
        # Build full menu path
        menu_path = []
        current_level = self.menu_data
        for level_name, _ in self.navigation_history:
            menu_path.append(level_name)
        menu_path.append(name)
        full_path = " > ".join(menu_path)
        
        # Add to order tree
        self.order_tree.insert("", "end", values=(full_path, f"R{price}"))
        
        # Update total amount
        self.total_amount += Decimal(str(price))
        self.total_label.config(text=f"Total: R{self.total_amount}")
        
        # Update status
        self.status_var.set(f"Added {full_path} to order")
    
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
        elif payment_method == "wyvern":
            self.show_wyvern_payment()
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
    
    def show_wyvern_payment(self):
        # Hide payment buttons
        self.payment_frame.pack_forget()
        
        # Create Wyvern payment frame
        self.wyvern_frame = ttk.Frame(self.main_frame)
        self.wyvern_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Instructions label
        ttk.Label(
            self.wyvern_frame,
            text="Please enter your Wyvern Card ID",
            font=('Arial', 16, 'bold')
        ).pack(pady=20)
        
        # Card ID entry frame
        entry_frame = ttk.Frame(self.wyvern_frame)
        entry_frame.pack(pady=10)
        
        # Card ID entry field
        self.card_id_entry = ttk.Entry(entry_frame, font=('Arial', 16), width=20)
        self.card_id_entry.pack(side=tk.LEFT, padx=5)
        
        # Submit button
        submit_button = ttk.Button(
            entry_frame,
            text="Submit",
            command=self.read_wyvern_card,
            width=10
        )
        submit_button.pack(side=tk.LEFT, padx=5)
        
        # Card ID and balance display
        self.card_id_var = tk.StringVar()
        self.card_id_var.set("Waiting for card ID...")
        ttk.Label(
            self.wyvern_frame,
            textvariable=self.card_id_var,
            font=('Arial', 16)
        ).pack(pady=10)
        
        # Transaction summary
        self.transaction_summary_var = tk.StringVar()
        self.transaction_summary_var.set(f"Total Amount: R{self.total_amount}")
        ttk.Label(
            self.wyvern_frame,
            textvariable=self.transaction_summary_var,
            font=('Arial', 16)
        ).pack(pady=10)
        
        # Set focus to card ID entry and bind Enter key
        self.card_id_entry.focus_set()
        self.card_id_entry.bind('<Return>', lambda e: self.read_wyvern_card())
        
        # Clear any existing text
        self.card_id_entry.delete(0, tk.END)

    def show_check_balance_dialog(self):
        """Show dialog to check Wyvern card balance."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Check Wyvern Card Balance")
        dialog.geometry("400x200")
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create form
        ttk.Label(
            dialog,
            text="Enter Wyvern Card ID:",
            font=('Arial', 16)
        ).pack(pady=20)
        
        # Card ID entry frame
        entry_frame = ttk.Frame(dialog)
        entry_frame.pack(pady=10)
        
        # Card ID entry field
        card_id_entry = ttk.Entry(entry_frame, font=('Arial', 16), width=20)
        card_id_entry.pack(side=tk.LEFT, padx=5)
        
        # Check button
        check_button = ttk.Button(
            entry_frame,
            text="Check",
            command=lambda: self.check_balance(card_id_entry.get().strip(), dialog),
            width=10
        )
        check_button.pack(side=tk.LEFT, padx=5)
        
        # Set focus to card ID entry and bind Enter key
        card_id_entry.focus_set()
        card_id_entry.bind('<Return>', lambda e: self.check_balance(card_id_entry.get().strip(), dialog))
        
        # Make dialog modal
        self.root.wait_window(dialog)

    def check_balance(self, card_id, dialog=None):
        """Check the balance for a Wyvern card."""
        try:
            if not card_id:
                messagebox.showerror("Error", "Please enter a card ID")
                return
            
            # Get user information
            user = self.user_management.get_user_by_rfid(card_id)
            if not user:
                messagebox.showerror("Error", "Card not registered")
                return
            
            # Show balance message
            messagebox.showinfo(
                "Balance Check",
                f"Card ID: {card_id}\n"
                f"User: {user['name']}\n"
                f"Current Balance: R{user['balance']}"
            )
            
            # Close the dialog if it exists
            if dialog:
                dialog.destroy()
            
        except Exception as e:
            print(f"Error checking balance: {str(e)}")
            messagebox.showerror("Error", f"Failed to check balance: {str(e)}")

    def read_wyvern_card(self):
        try:
            # Get card ID from entry field
            card_id = self.card_id_entry.get().strip()
            print(f"Received card ID: {card_id}")
            
            if not card_id:
                raise ValueError("Please enter a card ID")
            
            # Get user information
            user = self.user_management.get_user_by_rfid(card_id)
            if not user:
                raise ValueError("Card not registered")
            
            # Calculate discounted amount
            original_amount = self.total_amount
            discount_amount = original_amount * (user['discount_rate'] / 100)
            discounted_amount = original_amount - discount_amount
            
            # Check if user has sufficient balance
            if user['balance'] < discounted_amount:
                raise ValueError(f"Insufficient balance. Current balance: R{user['balance']}")
            
            # Update UI with user info and balance
            self.card_id_var.set(
                f"Card ID: {card_id}\n"
                f"User: {user['name']}\n"
                f"Current Balance: R{user['balance']}\n"
                f"Discount Rate: {user['discount_rate']}%"
            )
            
            # Update transaction summary
            self.transaction_summary_var.set(
                f"Original Amount: R{original_amount}\n"
                f"Discount: R{discount_amount}\n"
                f"Amount After Discount: R{discounted_amount}\n"
                f"Balance After Transaction: R{user['balance'] - discounted_amount}"
            )
            
            print(f"Processing payment of R{discounted_amount} for user {user['id']}")
            
            # Create order summary
            order_items = []
            for item in self.order_tree.get_children():
                values = self.order_tree.item(item)['values']
                order_items.append(f"{values[0]} - {values[1]}")
            order_summary = "\n".join(order_items)
            
            # Process payment
            success, message = self.user_management.update_balance(
                int(user['id']),  # Ensure ID is integer
                float(-discounted_amount),  # Convert Decimal to float for database
                "purchase",
                f"Purchase at drinks ordering system\n"
                f"Original Amount: R{original_amount}\n"
                f"Discount Rate: {user['discount_rate']}%\n"
                f"Discount Amount: R{discount_amount}\n"
                f"Amount After Discount: R{discounted_amount}",
                card_id,  # Pass the card ID
                order_summary  # Pass the order summary
            )
            
            if not success:
                raise ValueError(message)
            
            self.complete_transaction("wyvern", card_id)
            
        except Exception as e:
            print(f"Error processing payment: {str(e)}")
            messagebox.showerror("Error", f"Failed to process payment: {str(e)}")
            self.reset_interface()

    def complete_transaction(self, payment_method, amount_received=None):
        # Get user information for Wyvern card payments
        user = None
        discount_amount = None
        if payment_method == "wyvern" and amount_received:
            user = self.user_management.get_user_by_rfid(amount_received)
            if user:
                discount_amount = float(self.total_amount * (user['discount_rate'] / 100))

        # Log transaction to file
        self.log_transaction(
            payment_method=payment_method,
            total_amount=float(self.total_amount),
            items=self.order_tree.get_children(),
            card_id=amount_received if payment_method == "wyvern" else None,
            discount_amount=discount_amount
        )
        
        # Show success message
        message = f"Transaction completed successfully!\n\n"
        message += f"Payment Method: {payment_method.title()}\n"
        message += f"Total Amount: R{self.total_amount}\n"
        if payment_method == "cash":
            message += f"Amount Received: R{amount_received}\n"
            message += f"Change: R{Decimal(amount_received) - self.total_amount}\n"
        elif payment_method == "wyvern" and user:
            message += f"Card ID: {amount_received}\n"
            message += f"Discount Rate: {user['discount_rate']}%\n"
            message += f"Discount Amount: R{discount_amount}\n"
            message += f"Amount After Discount: R{(float(self.total_amount) - discount_amount)}\n"
        
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
        if hasattr(self, 'wyvern_frame'):
            self.wyvern_frame.pack_forget()
        
        # Reset status
        self.status_var.set("Ready for next order")
        
        # Reset navigation history
        self.navigation_history = []
        
        # Reset menu to initial state
        self.show_level(self.menu_data)
        
        # Show main content
        self.main_frame.pack(fill=tk.BOTH, expand=True)
    
    def log_transaction(self, payment_method, total_amount, items, card_id=None, discount_amount=None):
        """Log transaction details to a flat file."""
        try:
            # Create transactions directory if it doesn't exist
            if not os.path.exists('transactions'):
                os.makedirs('transactions')
            
            # Generate log filename using current date
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join('transactions', f'transactions_{date_str}.log')
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format payment method to include card ID if it's a Wyvern card
            if payment_method == "wyvern" and card_id:
                payment_method = f"wyvern_card_{card_id}"
            
            # Create log entry
            log_entry = [
                f"Timestamp: {timestamp}",
                f"Payment Method: {payment_method}",
                f"Total Amount: R{total_amount:.2f}"
            ]
            
            # Add discount if applicable
            if discount_amount:
                log_entry.append(f"Discount Amount: R{discount_amount:.2f}")
                log_entry.append(f"Amount After Discount: R{(total_amount - discount_amount):.2f}")
            
            # Add items with full menu path
            log_entry.append("\nItems:")
            for item in items:
                values = self.order_tree.item(item)['values']
                item_name = values[0]
                item_price = values[1]
                # Get the full menu path for this item
                menu_path = self.get_menu_path(item_name)
                log_entry.append(f"- {menu_path} - {item_price}")
            
            # Write to log file
            with open(log_file, "a") as f:
                f.write("\n".join(log_entry) + "\n" + "="*80 + "\n")
            
        except Exception as e:
            print(f"Error logging transaction: {str(e)}")

    def get_menu_path(self, item_name):
        """Get the full menu path for an item."""
        def search_menu(menu, target, current_path=None):
            if current_path is None:
                current_path = []
            
            if isinstance(menu, dict):
                for key, value in menu.items():
                    if key == target:
                        return current_path + [key]
                    if isinstance(value, (dict, list)):
                        result = search_menu(value, target, current_path + [key])
                        if result:
                            return result
            elif isinstance(menu, list):
                for item in menu:
                    if isinstance(item, (dict, list)):
                        result = search_menu(item, target, current_path)
                        if result:
                            return result
            return None
        
        path = search_menu(self.menu_data, item_name)
        if path:
            return " > ".join(path)
        return item_name

    def download_latest_menu(self):
        """Downloads the latest menu file from Google Drive."""
        try:
            print("Attempting to download latest menu...")
            creds = self.get_credentials()
            if not creds:
                print("Failed to get credentials")
                return False
            
            print("Building Drive service...")
            service = build('drive', 'v3', credentials=creds)
            
            print("Searching for menu file...")
            results = service.files().list(
                q="name='bar_menu.csv'",
                spaces='drive',
                fields='files(id, name, modifiedTime)'
            ).execute()
            
            items = results.get('files', [])
            
            if not items:
                print("No menu file found in Google Drive")
                return False
            
            print(f"Found {len(items)} menu files")
            # Get the most recently modified file
            latest_file = max(items, key=lambda x: x['modifiedTime'])
            print(f"Latest file: {latest_file['name']} (modified: {latest_file['modifiedTime']})")
            
            # Check if we already have this version
            if os.path.exists('bar_menu.csv'):
                local_mtime = os.path.getmtime('bar_menu.csv')
                drive_mtime = datetime.strptime(latest_file['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
                print(f"Local file time: {local_mtime}, Drive file time: {drive_mtime}")
                
                # Force download if timestamps are within 5 minutes of each other
                # or if local file is newer (which shouldn't happen)
                time_diff = abs(local_mtime - drive_mtime)
                if time_diff < 300 or local_mtime > drive_mtime:
                    print("Forcing download due to timestamp discrepancy")
                else:
                    print("Local file is up to date")
                    return False  # Local file is up to date
            
            print("Downloading new menu file...")
            # Download the file
            request = service.files().get_media(fileId=latest_file['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download progress: {int(status.progress() * 100)}%")
            
            print("Saving menu file...")
            # Save the file
            with open('bar_menu.csv', 'wb') as f:
                f.write(fh.getvalue())
            
            print("Menu download completed successfully")
            return True
            
        except Exception as e:
            print(f"Error downloading menu: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def get_credentials(self):
        """Gets valid user credentials from storage."""
        try:
            print("Getting credentials...")
            creds = None
            if os.path.exists('token.pickle'):
                print("Loading existing token...")
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("Refreshing expired token...")
                    creds.refresh(Request())
                else:
                    print("No valid credentials found, starting OAuth flow...")
                    if not os.path.exists('credentials.json'):
                        print("Downloading credentials file...")
                        if not download_credentials_file():
                            print("Failed to download credentials file")
                            return None
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                print("Saving new token...")
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            
            print("Credentials obtained successfully")
            return creds
        except Exception as e:
            print(f"Error getting credentials: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def load_menu_data(self):
        """Loads menu data from CSV file."""
        try:
            print("Reading menu file...")
            self.menu_data = {}
            
            with open('bar_menu.csv', 'r') as file:
                for line in file:
                    # Skip empty lines
                    if not line.strip():
                        continue
                    
                    # Parse CSV line
                    parts = line.strip().split(',')
                    if len(parts) >= 4:
                        category = parts[0].replace(':', '')  # Remove colon from category
                        name = parts[1]
                        size = parts[2]
                        price = parts[3]
                        
                        # Create category if it doesn't exist
                        if category not in self.menu_data:
                            self.menu_data[category] = {}
                        
                        # Add item to category
                        item_name = f"{name} ({size})"
                        self.menu_data[category][item_name] = {"price": price}
            
            print(f"Menu loaded successfully (categories: {len(self.menu_data)})")
            
            # If we're in the main content area, refresh the view
            if hasattr(self, 'scrollable_frame'):
                print("Refreshing menu view...")
                self.show_level(self.menu_data)
                
        except Exception as e:
            print(f"Error loading menu: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to load menu: {str(e)}")
            self.root.destroy()

def main():
    root = tk.Tk()
    app = DrinksOrderingSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main() 

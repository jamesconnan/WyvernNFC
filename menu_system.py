import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime

class MenuSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("System Management")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=10, font=('Arial', 10))
        self.style.configure("TLabel", font=('Arial', 12))
        self.style.configure("Header.TLabel", font=('Arial', 16, 'bold'))
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(self.main_frame, text="System Management", style="Header.TLabel")
        header.pack(pady=20)
        
        # Create buttons
        self.create_buttons()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_buttons(self):
        # Create button frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=20)
        
        # Define buttons
        buttons = [
            ("User Management", self.user_management),
            ("Settings", self.settings),
            ("Logs", self.logs),
            ("Transactions", self.transactions)
        ]
        
        # Create and pack buttons
        for text, command in buttons:
            btn = ttk.Button(button_frame, text=text, command=command, width=20)
            btn.pack(pady=10)
    
    def user_management(self):
        self.show_submenu("User Management", [
            ("Add User", self.add_user),
            ("Edit User", self.edit_user),
            ("Delete User", self.delete_user),
            ("List Users", self.list_users)
        ])
    
    def settings(self):
        self.show_submenu("Settings", [
            ("System Settings", self.system_settings),
            ("Security Settings", self.security_settings),
            ("Notification Settings", self.notification_settings)
        ])
    
    def logs(self):
        self.show_submenu("Logs", [
            ("View System Logs", self.view_system_logs),
            ("View User Logs", self.view_user_logs),
            ("View Error Logs", self.view_error_logs)
        ])
    
    def transactions(self):
        self.show_submenu("Transactions", [
            ("View All Transactions", self.view_all_transactions),
            ("View Recent Transactions", self.view_recent_transactions),
            ("Search Transactions", self.search_transactions)
        ])
    
    def show_submenu(self, title, options):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Create back button
        back_btn = ttk.Button(self.main_frame, text="← Back to Main Menu", 
                            command=self.create_buttons)
        back_btn.pack(anchor=tk.W, pady=10)
        
        # Show title
        header = ttk.Label(self.main_frame, text=title, style="Header.TLabel")
        header.pack(pady=20)
        
        # Create options frame
        options_frame = ttk.Frame(self.main_frame)
        options_frame.pack(pady=20)
        
        # Create option buttons
        for text, command in options:
            btn = ttk.Button(options_frame, text=text, command=command, width=20)
            btn.pack(pady=10)
    
    # Placeholder methods for all operations
    def add_user(self):
        messagebox.showinfo("Add User", "Add User functionality will be implemented here")
    
    def edit_user(self):
        messagebox.showinfo("Edit User", "Edit User functionality will be implemented here")
    
    def delete_user(self):
        messagebox.showinfo("Delete User", "Delete User functionality will be implemented here")
    
    def list_users(self):
        messagebox.showinfo("List Users", "List Users functionality will be implemented here")
    
    def system_settings(self):
        messagebox.showinfo("System Settings", "System Settings functionality will be implemented here")
    
    def security_settings(self):
        messagebox.showinfo("Security Settings", "Security Settings functionality will be implemented here")
    
    def notification_settings(self):
        messagebox.showinfo("Notification Settings", "Notification Settings functionality will be implemented here")
    
    def view_system_logs(self):
        messagebox.showinfo("System Logs", "View System Logs functionality will be implemented here")
    
    def view_user_logs(self):
        messagebox.showinfo("User Logs", "View User Logs functionality will be implemented here")
    
    def view_error_logs(self):
        messagebox.showinfo("Error Logs", "View Error Logs functionality will be implemented here")
    
    def view_all_transactions(self):
        messagebox.showinfo("All Transactions", "View All Transactions functionality will be implemented here")
    
    def view_recent_transactions(self):
        messagebox.showinfo("Recent Transactions", "View Recent Transactions functionality will be implemented here")
    
    def search_transactions(self):
        messagebox.showinfo("Search Transactions", "Search Transactions functionality will be implemented here")

def main():
    root = tk.Tk()
    app = MenuSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from decimal import Decimal

class MenuEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Drinks Menu Editor")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Load menu data
        self.load_menu()
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=10, font=('Arial', 12))
        self.style.configure("TLabel", font=('Arial', 12))
        self.style.configure("Header.TLabel", font=('Arial', 16, 'bold'))
        self.style.configure("Treeview", font=('Arial', 12))
        self.style.configure("Treeview.Heading", font=('Arial', 12, 'bold'))
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(header_frame, text="Drinks Menu Editor", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Save button
        save_button = ttk.Button(header_frame, text="Save Menu", command=self.save_menu)
        save_button.pack(side=tk.RIGHT, padx=10)
        
        # Create content area
        self.create_content_area()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_menu(self):
        try:
            with open('drinks_menu.json', 'r') as file:
                self.menu_data = json.load(file)
        except FileNotFoundError:
            self.menu_data = {}
            messagebox.showwarning("Warning", "Menu file not found. Starting with empty menu.")
    
    def save_menu(self):
        try:
            with open('drinks_menu.json', 'w') as file:
                json.dump(self.menu_data, file, indent=2)
            self.status_var.set("Menu saved successfully")
            messagebox.showinfo("Success", "Menu saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save menu: {str(e)}")
    
    def create_content_area(self):
        # Create main content frame
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create tree view
        self.tree = ttk.Treeview(content_frame, columns=("Price",), show="tree")
        self.tree.heading("#0", text="Item")
        self.tree.heading("Price", text="Price")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Create buttons frame
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add category button
        ttk.Button(buttons_frame, text="Add Category", command=self.add_category).pack(fill=tk.X, pady=5)
        
        # Add item button
        ttk.Button(buttons_frame, text="Add Item", command=self.add_item).pack(fill=tk.X, pady=5)
        
        # Edit button
        ttk.Button(buttons_frame, text="Edit", command=self.edit_item).pack(fill=tk.X, pady=5)
        
        # Delete button
        ttk.Button(buttons_frame, text="Delete", command=self.delete_item).pack(fill=tk.X, pady=5)
        
        # Populate tree
        self.populate_tree()
    
    def populate_tree(self, parent="", items=None):
        if items is None:
            items = self.menu_data
        
        for name, details in items.items():
            if isinstance(details, dict):
                if "price" in details or "single_price" in details:
                    # It's a drink item
                    price = details.get("price", details.get("single_price", "N/A"))
                    self.tree.insert(parent, "end", text=name, values=(f"R{price}",))
                else:
                    # It's a category
                    item_id = self.tree.insert(parent, "end", text=name)
                    self.populate_tree(item_id, details)
    
    def add_category(self):
        selected = self.tree.selection()
        parent = selected[0] if selected else ""
        
        name = simpledialog.askstring("Add Category", "Enter category name:")
        if name:
            if parent:
                # Get the path to the parent
                path = self.get_path(parent)
                current = self.menu_data
                for p in path[:-1]:
                    current = current[p]
                current[path[-1]][name] = {}
            else:
                self.menu_data[name] = {}
            
            # Refresh tree
            self.refresh_tree()
            self.status_var.set(f"Category '{name}' added")
    
    def add_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a category first")
            return
        
        parent = selected[0]
        name = simpledialog.askstring("Add Item", "Enter item name:")
        if name:
            try:
                price = int(simpledialog.askstring("Add Item", "Enter price:"))
                if price <= 0:
                    raise ValueError("Price must be positive")
                
                # Get the path to the parent
                path = self.get_path(parent)
                current = self.menu_data
                for p in path:
                    current = current[p]
                
                current[name] = {"price": price}
                
                # Refresh tree
                self.refresh_tree()
                self.status_var.set(f"Item '{name}' added")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
    
    def edit_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to edit")
            return
        
        item_id = selected[0]
        item = self.tree.item(item_id)
        name = item['text']
        
        # Get the path to the item
        path = self.get_path(item_id)
        current = self.menu_data
        for p in path[:-1]:
            current = current[p]
        
        if "price" in current[path[-1]] or "single_price" in current[path[-1]]:
            # It's a drink item
            try:
                new_price = int(simpledialog.askstring("Edit Price", f"Enter new price for {name}:", 
                                                       initialvalue=current[path[-1]].get("price", current[path[-1]].get("single_price"))))
                if new_price <= 0:
                    raise ValueError("Price must be positive")
                
                if "price" in current[path[-1]]:
                    current[path[-1]]["price"] = new_price
                else:
                    current[path[-1]]["single_price"] = new_price
                
                # Refresh tree
                self.refresh_tree()
                self.status_var.set(f"Price updated for '{name}'")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        else:
            # It's a category
            new_name = simpledialog.askstring("Rename Category", f"Enter new name for {name}:", initialvalue=name)
            if new_name and new_name != name:
                current[new_name] = current.pop(path[-1])
                # Refresh tree
                self.refresh_tree()
                self.status_var.set(f"Category renamed to '{new_name}'")
    
    def delete_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to delete")
            return
        
        item_id = selected[0]
        item = self.tree.item(item_id)
        name = item['text']
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{name}'?"):
            # Get the path to the item
            path = self.get_path(item_id)
            current = self.menu_data
            for p in path[:-1]:
                current = current[p]
            
            del current[path[-1]]
            
            # Refresh tree
            self.refresh_tree()
            self.status_var.set(f"'{name}' deleted")
    
    def get_path(self, item_id):
        path = []
        while item_id:
            item = self.tree.item(item_id)
            path.insert(0, item['text'])
            item_id = self.tree.parent(item_id)
        return path
    
    def refresh_tree(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Repopulate
        self.populate_tree()

def main():
    root = tk.Tk()
    app = MenuEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main() 

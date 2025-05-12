import sqlite3
from decimal import Decimal
import json
from datetime import datetime

class UserManagement:
    def __init__(self):
        self.db_name = 'users.db'
        self.initialize_database()
        self.migrate_database()

    def migrate_database(self):
        """Migrate the database to add new columns if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Check if discount_rate column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'discount_rate' not in columns:
                print("Adding discount_rate column to users table...")
                cursor.execute('''
                    ALTER TABLE users
                    ADD COLUMN discount_rate DECIMAL(5,2) DEFAULT 0.00
                ''')
                conn.commit()
                print("Migration completed successfully")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
        finally:
            conn.close()

    def initialize_database(self):
        """Create the database and tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    balance DECIMAL(10,2) DEFAULT 0.00,
                    discount_rate DECIMAL(5,2) DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create RFID tags table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rfid_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    rfid TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Create transaction history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount DECIMAL(10,2),
                    type TEXT,
                    description TEXT,
                    payment_method TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            conn.commit()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            raise
        finally:
            conn.close()

    def add_user(self, name, phone, email, rfid_tag, discount_rate=0.00, opening_balance=0.00):
        """Add a new user to the database."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Insert user with opening balance
            cursor.execute('''
                INSERT INTO users (name, phone, email, discount_rate, balance)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, phone, email, discount_rate, opening_balance))
            
            user_id = cursor.lastrowid
            
            # Insert RFID tag
            cursor.execute('''
                INSERT INTO rfid_tags (user_id, rfid)
                VALUES (?, ?)
            ''', (user_id, rfid_tag))
            
            # If there's an opening balance, record it as a transaction
            if opening_balance > 0:
                cursor.execute('''
                    INSERT INTO transactions (user_id, amount, type, description, payment_method)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, opening_balance, 'deposit', 'Opening balance', 'cash'))
            
            conn.commit()
            return True, "User added successfully"
        except sqlite3.IntegrityError:
            conn.rollback()
            return False, "RFID tag already exists"
        except Exception as e:
            conn.rollback()
            return False, f"Error adding user: {str(e)}"
        finally:
            conn.close()

    def get_user_by_rfid(self, rfid_tag):
        """Get user information by RFID tag."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.name, u.phone, u.email, u.balance, u.discount_rate
                FROM users u
                JOIN rfid_tags r ON u.id = r.user_id
                WHERE r.rfid = ?
            ''', (rfid_tag,))
            
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'name': user[1],
                    'phone': user[2],
                    'email': user[3],
                    'balance': Decimal(str(user[4])),
                    'discount_rate': Decimal(str(user[5]))
                }
            return None
        except Exception as e:
            print(f"Error getting user: {str(e)}")
            return None
        finally:
            conn.close()

    def get_user_rfid_tags(self, user_id):
        """Get all RFID tags for a user."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT rfid
                FROM rfid_tags
                WHERE user_id = ?
                ORDER BY created_at
            ''', (user_id,))
            
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting RFID tags: {str(e)}")
            return []
        finally:
            conn.close()

    def add_rfid_tag(self, user_id, rfid_tag):
        """Add a new RFID tag to a user."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO rfid_tags (user_id, rfid)
                VALUES (?, ?)
            ''', (user_id, rfid_tag))
            
            conn.commit()
            return True, "RFID tag added successfully"
        except sqlite3.IntegrityError:
            return False, "RFID tag already exists"
        except Exception as e:
            return False, f"Error adding RFID tag: {str(e)}"
        finally:
            conn.close()

    def remove_rfid_tag(self, user_id, rfid_tag):
        """Remove an RFID tag from a user."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM rfid_tags
                WHERE user_id = ? AND rfid = ?
            ''', (user_id, rfid_tag))
            
            if cursor.rowcount == 0:
                return False, "RFID tag not found"
            
            conn.commit()
            return True, "RFID tag removed successfully"
        except Exception as e:
            return False, f"Error removing RFID tag: {str(e)}"
        finally:
            conn.close()

    def update_user(self, user_id, name=None, phone=None, email=None, discount_rate=None):
        """Update user information."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            updates = []
            values = []
            
            if name is not None:
                updates.append("name = ?")
                values.append(name)
            if phone is not None:
                updates.append("phone = ?")
                values.append(phone)
            if email is not None:
                updates.append("email = ?")
                values.append(email)
            if discount_rate is not None:
                updates.append("discount_rate = ?")
                values.append(discount_rate)
            
            if not updates:
                return False, "No updates provided"
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            return True, "User updated successfully"
        except Exception as e:
            return False, f"Error updating user: {str(e)}"
        finally:
            conn.close()

    def update_balance(self, user_id, amount, transaction_type, description="", card_id=None, order_summary=None):
        """Update user balance and record transaction."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Update user balance
            cursor.execute('''
                UPDATE users
                SET balance = balance + ?
                WHERE id = ?
            ''', (amount, user_id))
            
            # Build transaction description
            full_description = description
            if card_id:
                full_description += f"\nCard ID: {card_id}"
            if order_summary:
                full_description += f"\nOrder Summary:\n{order_summary}"
            
            # Record transaction
            cursor.execute('''
                INSERT INTO transactions (user_id, amount, type, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, transaction_type, full_description))
            
            # Commit transaction
            conn.commit()
            return True, "Balance updated successfully"
        except Exception as e:
            conn.rollback()
            return False, f"Error updating balance: {str(e)}"
        finally:
            conn.close()

    def get_transaction_history(self, user_id, limit=10):
        """Get transaction history for a user."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT amount, type, description, timestamp
                FROM transactions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    'amount': Decimal(str(row[0])),
                    'type': row[1],
                    'description': row[2],
                    'timestamp': row[3]
                })
            
            return transactions
        except Exception as e:
            print(f"Error getting transaction history: {str(e)}")
            return []
        finally:
            conn.close()

    def get_all_users(self):
        """Get all users from the database."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, phone, email, rfid_tag, balance, discount_rate
                FROM users
                ORDER BY name
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'name': row[1],
                    'phone': row[2],
                    'email': row[3],
                    'rfid_tag': row[4],
                    'balance': Decimal(str(row[5])),
                    'discount_rate': Decimal(str(row[6]))
                })
            
            return users
        except Exception as e:
            print(f"Error getting users: {str(e)}")
            return []
        finally:
            conn.close()

    def delete_user(self, user_id):
        """Delete a user from the database."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            return True, "User deleted successfully"
        except Exception as e:
            return False, f"Error deleting user: {str(e)}"
        finally:
            conn.close()

    def clear_all_data(self):
        """Clear all data from the database."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Delete all data from tables in correct order (respecting foreign keys)
            cursor.execute("DELETE FROM transactions")
            cursor.execute("DELETE FROM rfid_tags")
            cursor.execute("DELETE FROM users")
            
            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('users', 'rfid_tags', 'transactions')")
            
            # Commit transaction
            conn.commit()
            return True, "All data cleared successfully"
        except Exception as e:
            conn.rollback()
            return False, f"Error clearing data: {str(e)}"
        finally:
            conn.close() 
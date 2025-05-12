import os
import time
import mysql.connector
from datetime import datetime
import configparser
import logging
import json

class TransactionSync:
    def __init__(self):
        self.config = self.load_config()
        self.last_sync_time = 0
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('transaction_sync.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Load configuration from settings.cfg file."""
        config = configparser.ConfigParser()
        if not os.path.exists('settings.cfg'):
            raise FileNotFoundError("settings.cfg file not found")
        
        config.read('settings.cfg')
        return {
            'pos_id': config.get('POS', 'id'),
            'mysql_host': config.get('MySQL', 'host'),
            'mysql_database': config.get('MySQL', 'database'),
            'mysql_user': config.get('MySQL', 'user'),
            'mysql_password': config.get('MySQL', 'password'),
            'update_interval': config.getint('Sync', 'update_interval')
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
            self.logger.error(f"Error connecting to MySQL: {err}")
            return None

    def parse_transaction_file(self, file_path):
        """Parse a transaction log file and return list of transactions."""
        transactions = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                transaction_blocks = content.split('=' * 80)
                
                for block in transaction_blocks:
                    if not block.strip():
                        continue
                    
                    lines = block.strip().split('\n')
                    transaction = {
                        'timestamp': None,
                        'payment_method': None,
                        'total_amount': None,
                        'discount_amount': None,
                        'items': []
                    }
                    
                    for line in lines:
                        if line.startswith('Timestamp:'):
                            transaction['timestamp'] = line.split(': ')[1].strip()
                        elif line.startswith('Payment Method:'):
                            transaction['payment_method'] = line.split(': ')[1].strip()
                        elif line.startswith('Total Amount:'):
                            transaction['total_amount'] = float(line.split('R')[1].strip())
                        elif line.startswith('Discount Amount:'):
                            transaction['discount_amount'] = float(line.split('R')[1].strip())
                        elif line.startswith('- '):
                            item_line = line[2:].strip()
                            if ' - ' in item_line:
                                item_name, item_price = item_line.split(' - ')
                                transaction['items'].append({
                                    'name': item_name.strip(),
                                    'price': float(item_price.replace('R', '').strip())
                                })
                    
                    if transaction['timestamp'] and transaction['payment_method'] and transaction['total_amount']:
                        transactions.append(transaction)
            
            return transactions
        except Exception as e:
            self.logger.error(f"Error parsing transaction file {file_path}: {e}")
            return []

    def upload_transactions(self):
        """Upload new transactions to MySQL server."""
        try:
            # Get list of transaction files
            transaction_files = []
            if os.path.exists('transactions'):
                transaction_files = [f for f in os.listdir('transactions') 
                                  if f.startswith('transactions_') and f.endswith('.log')]
            
            if not transaction_files:
                self.logger.info("No transaction files found")
                return
            
            # Connect to MySQL
            connection = self.get_mysql_connection()
            if not connection:
                return
            
            cursor = connection.cursor()
            
            # Create transactions table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    pos_id VARCHAR(50),
                    timestamp DATETIME,
                    payment_method VARCHAR(50),
                    total_amount DECIMAL(10,2),
                    discount_amount DECIMAL(10,2),
                    items JSON,
                    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Process each transaction file
            for file_name in transaction_files:
                file_path = os.path.join('transactions', file_name)
                transactions = self.parse_transaction_file(file_path)
                
                for transaction in transactions:
                    # Check if transaction already exists
                    cursor.execute('''
                        SELECT id FROM transactions 
                        WHERE pos_id = %s AND timestamp = %s AND payment_method = %s
                    ''', (
                        self.config['pos_id'],
                        transaction['timestamp'],
                        transaction['payment_method']
                    ))
                    
                    if not cursor.fetchone():
                        # Insert new transaction
                        cursor.execute('''
                            INSERT INTO transactions 
                            (pos_id, timestamp, payment_method, total_amount, discount_amount, items)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        ''', (
                            self.config['pos_id'],
                            transaction['timestamp'],
                            transaction['payment_method'],
                            transaction['total_amount'],
                            transaction.get('discount_amount'),
                            json.dumps(transaction['items'])
                        ))
            
            connection.commit()
            self.logger.info("Successfully uploaded transactions to MySQL server")
            
        except Exception as e:
            self.logger.error(f"Error uploading transactions: {e}")
            if connection:
                connection.rollback()
        finally:
            if connection:
                connection.close()

    def run_sync_loop(self):
        """Run the sync loop continuously."""
        self.logger.info("Starting transaction sync service")
        while True:
            try:
                current_time = time.time()
                if current_time - self.last_sync_time >= self.config['update_interval']:
                    self.upload_transactions()
                    self.last_sync_time = current_time
                time.sleep(1)  # Sleep for 1 second before next check
            except KeyboardInterrupt:
                self.logger.info("Transaction sync service stopped")
                break
            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
                time.sleep(5)  # Sleep for 5 seconds on error before retrying

if __name__ == "__main__":
    sync_service = TransactionSync()
    sync_service.run_sync_loop() 
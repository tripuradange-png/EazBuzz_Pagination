import requests
import json
from datetime import datetime
from tabulate import tabulate
from sshtunnel import SSHTunnelForwarder
from clickhouse_driver import Client


class ClickHouseDB:
    def __init__(self):
        # SSH Configuration
        self.ssh_host = '3.7.169.181'
        self.ssh_port = 22
        self.ssh_username = 'ubuntu'
        self.ssh_key_path = r'D:\ClickHouse\SML_Castlecraft.pem'

        # ClickHouse Configuration
        self.ch_host = '127.0.0.1'
        self.ch_port = 9000
        self.ch_user = 'default'
        self.ch_password = 'aSh49aVjfy8P'
        self.ch_database = 'default'

        self.tunnel = None
        self.client = None

    def connect(self):
        """Establish SSH tunnel and ClickHouse connection"""
        try:
            # Create SSH tunnel
            print("Establishing SSH tunnel...")
            self.tunnel = SSHTunnelForwarder(
                (self.ssh_host, self.ssh_port),
                ssh_username=self.ssh_username,
                ssh_pkey=self.ssh_key_path,
                remote_bind_address=(self.ch_host, self.ch_port),
                local_bind_address=(self.ch_host, self.ch_port)
            )
            self.tunnel.start()
            print(f"SSH tunnel established on {self.tunnel.local_bind_port}")

            # Connect to ClickHouse
            print("Connecting to ClickHouse...")
            self.client = Client(
                host=self.ch_host,
                port=self.tunnel.local_bind_port,
                user=self.ch_user,
                password=self.ch_password,
                database=self.ch_database
            )
            print("Connected to ClickHouse successfully!")
            return True

        except Exception as e:
            print(f"Error connecting to ClickHouse: {e}")
            return False

    def disconnect(self):
        """Close ClickHouse connection and SSH tunnel"""
        if self.client:
            self.client.disconnect()
            print("ClickHouse connection closed")

        if self.tunnel:
            self.tunnel.stop()
            print("SSH tunnel closed")

    def create_table(self):
        """Create payment_transactions table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS payment_transactions (
            status String,
            total_debit_amount Decimal(18, 2),
            net_debit_amount Decimal(18, 2),
            easepayid String,
            firstname String,
            phone String,
            udf1 String,
            udf2 String,
            udf3 String,
            udf4 String,
            udf5 String,
            txnid String,
            email String,
            created_at DateTime
        ) ENGINE = MergeTree()
        ORDER BY created_at
        """
        try:
            self.client.execute(create_table_query)
            print("Table 'payment_transactions' ready")
        except Exception as e:
            print(f"Error creating table: {e}")

    def insert_transactions(self, transactions):
        """Insert transactions into ClickHouse, skipping duplicates"""
        if not transactions:
            print("No transactions to insert")
            return 0

        insert_query = """
        INSERT INTO payment_transactions
        (status, total_debit_amount, net_debit_amount, easepayid, firstname,
         phone, udf1, udf2, udf3, udf4, udf5, txnid, email, created_at)
        VALUES
        """

        inserted_count = 0
        duplicate_count = 0

        for txn in transactions:
            txnid = txn.get('txnid', '')

            # Check if transaction already exists
            if self.transaction_exists(txnid):
                duplicate_count += 1
                continue

            try:
                data = [(
                    txn.get('status', ''),
                    float(txn.get('total_debit_amount', 0)),
                    float(txn.get('net_debit_amount', 0)),
                    txn.get('easepayid', ''),
                    txn.get('firstname', ''),
                    txn.get('phone', ''),
                    txn.get('udf1', ''),
                    txn.get('udf2', ''),
                    txn.get('udf3', ''),
                    txn.get('udf4', ''),
                    txn.get('udf5', ''),
                    txnid,
                    txn.get('email', ''),
                    datetime.now()
                )]

                self.client.execute(insert_query, data)
                inserted_count += 1
            except Exception as e:
                print(f"Error inserting transaction {txnid}: {e}")

        print(f"Successfully inserted {inserted_count} transactions into ClickHouse")
        if duplicate_count > 0:
            print(f"Skipped {duplicate_count} duplicate transactions")
        return inserted_count

    def get_transaction_count(self):
        """Get total transaction count from database"""
        try:
            result = self.client.execute("SELECT count() FROM payment_transactions")
            return result[0][0]
        except Exception as e:
            print(f"Error getting transaction count: {e}")
            return 0

    def transaction_exists(self, txnid):
        """Check if a transaction with given txnid already exists in database"""
        try:
            query = "SELECT count() FROM payment_transactions WHERE txnid = %(txnid)s"
            result = self.client.execute(query, {'txnid': txnid})
            return result[0][0] > 0
        except Exception as e:
            print(f"Error checking transaction existence: {e}")
            return False


class EasebuzzAPI:
    def __init__(self):
        self.base_url = "https://dashboard.easebuzz.in"
        self.auth_header = "d13d4c1b99204b66af9cf102e7c354c9"
        self.email = "ashwani@rapidmoney.in"
        self.password = "Ash19771$"
        self.token = None
        self.token_expiry = None
        self.merchant_key = "3POWAUBPC"

    def _parse_datetime(self, datetime_str):
        """
        Parse datetime string from API response.
        Expected format: "2025-12-19 11:25 AM"
        """
        try:
            return datetime.strptime(datetime_str, "%Y-%m-%d %I:%M %p")
        except Exception:
            return None

    def is_token_expired(self):
        """
        Check if the current token has expired.
        Returns True if token is expired or doesn't exist.
        """
        if not self.token or not self.token_expiry:
            return True

        return datetime.now() >= self.token_expiry

    def get_auth_token(self, force_refresh=False):
        """
        Authenticate and retrieve the access token from Easebuzz API.
        Automatically refreshes token if expired.

        Args:
            force_refresh (bool): Force token refresh even if not expired

        Returns:
            str: Token if successful, None otherwise.
        """
        # Return existing token if still valid
        if not force_refresh and not self.is_token_expired():
            print(f"Using existing token (expires at: {self.token_expiry.strftime('%Y-%m-%d %I:%M %p')})")
            return self.token

        url = f"{self.base_url}/auth/v1/token"

        headers = {
            "Accept": "application/json",
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
            "Cookie": "Path=/"
        }

        payload = {
            "email": self.email,
            "password": self.password
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            self.token = data.get("token")

            # Parse and store expiry time
            expiry_str = data.get("expiry_at")
            if expiry_str:
                self.token_expiry = self._parse_datetime(expiry_str)

            print(f"Authentication successful!")
            print(f"MID: {data.get('mid')}")
            print(f"Token: {self.token}")
            print(f"Created at: {data.get('created_at')}")
            print(f"Expires at: {expiry_str}")

            return self.token

        except requests.exceptions.RequestException as e:
            print(f"Error during authentication: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def get_transactions_by_date(self, start_date, end_date, hash_value, page_token=None):
        """
        Retrieve transactions for a given date range.
        Automatically refreshes token if expired.

        Args:
            start_date (str): Start date in format "DD-MM-YYYY"
            end_date (str): End date in format "DD-MM-YYYY"
            hash_value (str): Hash value for request authentication
            page_token (str, optional): Next page token for pagination

        Returns:
            dict: Transaction data if successful, None otherwise
        """
        # Check if token is expired and refresh if needed
        if self.is_token_expired():
            print("Token expired or not found. Fetching new token...")
            if not self.get_auth_token():
                print("Failed to get authentication token.")
                return None

        url = f"{self.base_url}/transaction/v2/retrieve/date"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cookie": "/'; Path=/"
        }

        payload = {
            "key": self.merchant_key,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "hash": hash_value,
            "additional_data": "transaction_date",
            "token": self.token
        }

        # Add page token if provided for pagination
        if page_token:
            payload["page"] = page_token

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            print(f"\nTransactions retrieved successfully!")
            print(f"Count: {data.get('count')}")
            print(f"Has next page: {'Yes' if data.get('next') else 'No'}")

            return data

        except requests.exceptions.RequestException as e:
            print(f"Error retrieving transactions: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def get_all_transactions(self, start_date, end_date, hash_value, show_page_tables=True, db_handler=None):
        """
        Retrieve all transactions for a given date range with automatic pagination.

        Args:
            start_date (str): Start date in format "DD-MM-YYYY"
            end_date (str): End date in format "DD-MM-YYYY"
            hash_value (str): Hash value for request authentication
            show_page_tables (bool): Display table for each page (default: True)
            db_handler: ClickHouseDB instance to push data immediately (optional)

        Returns:
            list: All transaction data across all pages
        """
        all_transactions = []
        page_token = None
        page_number = 1

        while True:
            print(f"\n{'='*80}")
            print(f"--- Fetching page {page_number} ---")
            print(f"{'='*80}")

            result = self.get_transactions_by_date(
                start_date=start_date,
                end_date=end_date,
                hash_value=hash_value,
                page_token=page_token
            )

            if not result or not result.get('status'):
                print("Failed to fetch transactions or no more data")
                break

            # Add current page transactions to the list
            transactions = result.get('data', [])
            all_transactions.extend(transactions)
            print(f"Retrieved {len(transactions)} transactions (Total so far: {len(all_transactions)})")

            # Push to database immediately if handler provided
            if db_handler and transactions:
                print(f"Pushing page {page_number} data to database...")
                inserted = db_handler.insert_transactions(transactions)
                print(f"Inserted {inserted} transactions from page {page_number}")

            # Display table for this page
            if show_page_tables and transactions:
                print(f"\n--- Page {page_number} Transaction Details ---")
                table_data = []
                for idx, txn in enumerate(transactions, 1):
                    table_data.append([
                        idx,
                        txn.get('txnid', 'N/A')[:30],  # Truncate long IDs
                        txn.get('firstname', 'N/A')[:20],
                        txn.get('phone', 'N/A'),
                        txn.get('status', 'N/A'),
                        f"Rs.{txn.get('net_debit_amount', 0)}",
                        txn.get('easepayid', 'N/A')
                    ])

                headers = ['#', 'Transaction ID', 'Name', 'Phone', 'Status', 'Amount', 'Easepay ID']
                print(tabulate(table_data, headers=headers, tablefmt='grid'))

            # Check if there's a next page
            next_token = result.get('next')
            if not next_token:
                print(f"\n{'='*80}")
                print("No more pages. All transactions fetched!")
                print(f"{'='*80}")
                break

            # Use the next token for the next iteration
            page_token = next_token
            page_number += 1

        return all_transactions


def main():
    # Initialize the API client
    easebuzz = EasebuzzAPI()

    # Initialize ClickHouse database
    db = ClickHouseDB()

    try:
        # Step 1: Connect to ClickHouse
        print("\n=== Connecting to ClickHouse Database ===")
        if not db.connect():
            print("Failed to connect to ClickHouse. Exiting...")
            return

        # Create table if not exists
        db.create_table()

        # Step 2: Authenticate and get token
        print("\n=== Authenticating with Easebuzz ===")
        token = easebuzz.get_auth_token()

        if token:
            # Step 3: Retrieve transactions
            hash_value = "b80cdee1da064dc20f50d4fd87b70a2d81bf4cb3fc6945fa50072498d77dae75e7158bcdbad619e03fa8f524fa4ddcf742a54b61a6798fb9fa3dc43fd99bcf94"

            print("\n=== Fetching ALL transactions with pagination ===")
            all_transactions = easebuzz.get_all_transactions(
                start_date="09-09-2025",
                end_date="11-12-2025",
                hash_value=hash_value,
                db_handler=db  # Pass database handler for immediate insertion
            )

            if all_transactions:
                print(f"\n✓ Successfully fetched {len(all_transactions)} total transactions!")

                # Display summary
                print("\n=== Transaction Summary ===")
                success_count = sum(1 for t in all_transactions if t.get('status') == 'success')
                failed_count = sum(1 for t in all_transactions if t.get('status') in ['failure', 'bounced'])
                dropped_count = sum(1 for t in all_transactions if t.get('status') == 'dropped')

                print(f"Total: {len(all_transactions)}")
                print(f"Success: {success_count}")
                print(f"Failed/Bounced: {failed_count}")
                print(f"Dropped: {dropped_count}")

                # Get total count from database
                total_in_db = db.get_transaction_count()
                print(f"\n=== Database Summary ===")
                print(f"Total transactions in database: {total_in_db}")

                # Save to JSON file
                with open('transactions.json', 'w') as f:
                    json.dump(all_transactions, f, indent=2)
                print("\n✓ All transactions saved to 'transactions.json'")
            else:
                print("\n✗ Failed to retrieve transactions")
        else:
            print("\n✗ Authentication failed")

    except Exception as e:
        print(f"\n✗ Error in main execution: {e}")

    finally:
        # Always disconnect from database
        print("\n=== Closing connections ===")
        db.disconnect()


if __name__ == "__main__":
    main()

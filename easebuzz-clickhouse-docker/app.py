import requests
import json
import os
from datetime import datetime
from tabulate import tabulate
from sshtunnel import SSHTunnelForwarder
from clickhouse_driver import Client


class ClickHouseDB:
    def __init__(self):
        # SSH Configuration - Use environment variables with fallback to defaults
        self.ssh_host = os.getenv("SSH_HOST", "3.7.169.181")
        self.ssh_port = int(os.getenv("SSH_PORT", "22"))
        self.ssh_username = os.getenv("SSH_USER", "ubuntu")
        self.ssh_key_path = os.getenv("SSH_KEY_PATH", r"D:\ClickHouse\SML_Castlecraft.pem")

        # ClickHouse Configuration - Use environment variables with fallback to defaults
        self.ch_host = os.getenv("CH_HOST", "127.0.0.1")
        self.ch_port = int(os.getenv("CH_PORT", "9000"))
        self.ch_user = os.getenv("CH_USER", "default")
        self.ch_password = os.getenv("CH_PASSWORD", "aSh49aVjfy8P")
        self.ch_database = os.getenv("CH_DATABASE", "default")

        self.tunnel = None
        self.client = None

    def connect(self):
        """Establish SSH tunnel and ClickHouse connection"""
        try:
            # Load SSH private key
            import paramiko
            print(f"Loading SSH key from: {self.ssh_key_path}")
            ssh_key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)

            # Create SSH tunnel
            print("Establishing SSH tunnel...")
            self.tunnel = SSHTunnelForwarder(
                (self.ssh_host, self.ssh_port),
                ssh_username=self.ssh_username,
                ssh_pkey=ssh_key,
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
        """Create test_payment_transactions table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS test_payment_transactions (
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
            addedon String,
            error_message String,
            created_at DateTime
        ) ENGINE = MergeTree()
        ORDER BY created_at
        """
        try:
            self.client.execute(create_table_query)
            print("Table 'test_payment_transactions' ready")

            # Add new columns if they don't exist
            self.add_missing_columns()
        except Exception as e:
            print(f"Error creating table: {e}")

    def add_missing_columns(self):
        """Add addedon and error_message columns to existing table if they don't exist"""
        try:
            # Check if addedon column exists
            check_query = """
            SELECT name FROM system.columns
            WHERE table = 'test_payment_transactions'
            AND database = 'default'
            AND name IN ('addedon', 'error_message')
            """
            existing_columns = self.client.execute(check_query)
            existing_column_names = [col[0] for col in existing_columns]

            # Add addedon column if it doesn't exist
            if 'addedon' not in existing_column_names:
                print("Adding 'addedon' column to table...")
                alter_query = "ALTER TABLE test_payment_transactions ADD COLUMN IF NOT EXISTS addedon String"
                self.client.execute(alter_query)
                print("[OK] Column 'addedon' added successfully")

            # Add error_message column if it doesn't exist
            if 'error_message' not in existing_column_names:
                print("Adding 'error_message' column to table...")
                alter_query = "ALTER TABLE test_payment_transactions ADD COLUMN IF NOT EXISTS error_message String"
                self.client.execute(alter_query)
                print("[OK] Column 'error_message' added successfully")

            if 'addedon' in existing_column_names and 'error_message' in existing_column_names:
                print("[OK] Columns 'addedon' and 'error_message' already exist")

        except Exception as e:
            print(f"Error adding columns: {e}")

    def insert_transactions(self, transactions):
        """Insert transactions into ClickHouse, skipping duplicates"""
        if not transactions:
            print("No transactions to insert")
            return 0

        insert_query = """
        INSERT INTO test_payment_transactions
        (status, total_debit_amount, net_debit_amount, easepayid, firstname,
         phone, udf1, udf2, udf3, udf4, udf5, txnid, email, addedon, error_message, created_at)
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
                    float(txn.get('amount', txn.get('total_debit_amount', 0))),
                    float(txn.get('net_amount_debit', txn.get('net_debit_amount', 0))),
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
                    txn.get('addedon', ''),
                    txn.get('error_message', ''),
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
            result = self.client.execute("SELECT count() FROM test_payment_transactions")
            return result[0][0]
        except Exception as e:
            print(f"Error getting transaction count: {e}")
            return 0

    def transaction_exists(self, txnid):
        """Check if a transaction with given txnid already exists in database"""
        try:
            query = "SELECT count() FROM test_payment_transactions WHERE txnid = %(txnid)s"
            result = self.client.execute(query, {'txnid': txnid})
            return result[0][0] > 0
        except Exception as e:
            print(f"Error checking transaction existence: {e}")
            return False

    def get_transaction_status(self, txnid):
        """Get the current status of a transaction"""
        try:
            query = "SELECT status FROM test_payment_transactions WHERE txnid = %(txnid)s LIMIT 1"
            result = self.client.execute(query, {'txnid': txnid})
            if result and len(result) > 0:
                return result[0][0]
            return None
        except Exception as e:
            print(f"Error getting transaction status: {e}")
            return None

    def update_transaction(self, txnid, transaction_data):
        """Update an existing transaction with new data"""
        try:
            # Extract transaction data from the API response
            # The response structure can be: {"status": true/1, "data": {...}} or {"status": true, "msg": {...}}
            if isinstance(transaction_data, dict) and transaction_data.get('status') in [1, True, 'true']:
                # Try 'data' first, then 'msg'
                txn = transaction_data.get('data') or transaction_data.get('msg')
                if not txn:
                    print(f"No data/msg in response for {txnid}")
                    return False
            else:
                # Assume transaction_data is already the transaction object
                txn = transaction_data

            query = """
            ALTER TABLE test_payment_transactions
            UPDATE
                status = %(status)s,
                total_debit_amount = %(total_debit_amount)s,
                net_debit_amount = %(net_debit_amount)s,
                addedon = %(addedon)s,
                error_message = %(error_message)s
            WHERE txnid = %(txnid)s
            """

            # Handle both 'error_Message' (from API) and 'error_message'
            error_msg = txn.get('error_message') or txn.get('error_Message', 'NA')

            params = {
                'txnid': txnid,
                'status': txn.get('status', ''),
                'total_debit_amount': float(txn.get('amount', txn.get('total_debit_amount', 0))),
                'net_debit_amount': float(txn.get('net_amount_debit', txn.get('net_debit_amount', 0))),
                'addedon': txn.get('addedon', ''),
                'error_message': error_msg
            }

            self.client.execute(query, params)
            return True
        except Exception as e:
            print(f"Error updating transaction {txnid}: {e}")
            return False

    def get_intermediate_status_transactions(self, hours_lookback=48):
        """
        Get all transactions with intermediate statuses from the last N hours

        Returns:
            list: List of (txnid, status, addedon, amount) tuples
        """
        try:
            query = f"""
            SELECT txnid, status, addedon, total_debit_amount
            FROM test_payment_transactions
            WHERE status IN ('initiated', 'pending', 'preinitiated', 'true', 'True')
              AND parseDateTimeBestEffort(addedon) >= subtractHours(now(), {hours_lookback})
            ORDER BY parseDateTimeBestEffort(addedon) DESC
            """
            return self.client.execute(query)
        except Exception as e:
            print(f"Error getting intermediate status transactions: {e}")
            return []

    def insert_detailed_transactions(self, detailed_responses):
        """Insert detailed transaction responses into ClickHouse, skipping duplicates"""
        if not detailed_responses:
            print("No detailed transactions to insert")
            return 0

        insert_query = """
        INSERT INTO test_payment_transactions
        (status, total_debit_amount, net_debit_amount, easepayid, firstname,
         phone, udf1, udf2, udf3, udf4, udf5, txnid, email, addedon, error_message, created_at)
        VALUES
        """

        inserted_count = 0
        duplicate_count = 0

        for response in detailed_responses:
            # Extract transaction data from the API response
            # The response structure can be: {"status": true/1, "data": {...}} or {"status": true, "msg": {...}}
            if not isinstance(response, dict):
                continue

            # Check if response has 'data' or 'msg' key (successful response)
            if response.get('status') in [1, True, 'true']:
                # Try 'data' first, then 'msg'
                txn = response.get('data') or response.get('msg')
                if not txn:
                    print(f"Skipping transaction - No data/msg in response")
                    continue
            else:
                # If no data, skip this transaction
                print(f"Skipping transaction - Failed response: {response.get('msg', 'Unknown error')}")
                continue

            txnid = txn.get('txnid', '')

            # Check if transaction already exists
            if self.transaction_exists(txnid):
                duplicate_count += 1
                print(f"Skipping duplicate transaction: {txnid}")
                continue

            try:
                # Handle both 'error_Message' (from API) and 'error_message'
                error_msg = txn.get('error_message') or txn.get('error_Message', '')

                data = [(
                    txn.get('status', ''),
                    float(txn.get('amount', txn.get('total_debit_amount', 0))),
                    float(txn.get('net_amount_debit', txn.get('net_debit_amount', 0))),
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
                    txn.get('addedon', ''),
                    error_msg,
                    datetime.now()
                )]

                self.client.execute(insert_query, data)
                inserted_count += 1
                print(f"[OK] Inserted transaction {txnid}")
                print(f"     addedon: {txn.get('addedon', 'N/A')}")
                print(f"     error_message: {error_msg or 'N/A'}")
            except Exception as e:
                print(f"Error inserting detailed transaction {txnid}: {e}")

        print(f"\n{'='*80}")
        print(f"Successfully inserted {inserted_count} detailed transactions into ClickHouse")
        if duplicate_count > 0:
            print(f"Skipped {duplicate_count} duplicate transactions")
        print(f"{'='*80}\n")
        return inserted_count

    def get_transactions_with_details(self, limit=10):
        """Retrieve and display transactions with addedon and error_message fields"""
        try:
            query = f"""
            SELECT txnid, firstname, phone, status, addedon, error_message, created_at
            FROM test_payment_transactions
            ORDER BY created_at DESC
            LIMIT {limit}
            """
            result = self.client.execute(query)

            if result:
                print(f"\n{'='*120}")
                print(f"{'RECENT TRANSACTIONS WITH ADDEDON & ERROR_MESSAGE':^120}")
                print(f"{'='*120}")

                headers = ['TxnID', 'Name', 'Phone', 'Status', 'Added On', 'Error Message', 'Created At']
                table_data = []

                for row in result:
                    table_data.append([
                        row[0][:30] if row[0] else 'N/A',  # txnid
                        row[1][:20] if row[1] else 'N/A',  # firstname
                        row[2] if row[2] else 'N/A',       # phone
                        row[3] if row[3] else 'N/A',       # status
                        row[4] if row[4] else 'N/A',       # addedon
                        row[5][:30] if row[5] else 'N/A',  # error_message
                        str(row[6]) if row[6] else 'N/A'   # created_at
                    ])

                print(tabulate(table_data, headers=headers, tablefmt='grid'))
                print(f"{'='*120}\n")

                return result
            else:
                print("No transactions found in database")
                return []

        except Exception as e:
            print(f"Error retrieving transactions with details: {e}")
            return []


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
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            print(f"\nTransactions retrieved successfully!")
            print(f"Count: {data.get('count')}")
            print(f"Has next page: {'Yes' if data.get('next') else 'No'}")

            return data

        except requests.exceptions.Timeout:
            print(f"Error: Request timed out after 30 seconds")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving transactions: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def retrieve_transaction_details(self, txnid, hash_value):
        """
        Retrieve detailed information for a specific transaction.

        Args:
            txnid (str): Transaction ID to retrieve
            hash_value (str): Hash value for request authentication

        Returns:
            dict: Transaction details if successful, None otherwise
        """
        # Check if token is expired and refresh if needed
        if self.is_token_expired():
            print("Token expired or not found. Fetching new token...")
            if not self.get_auth_token():
                print("Failed to get authentication token.")
                return None

        url = f"{self.base_url}/transaction/v2/retrieve"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cookie": "/'; Path=/"
        }

        payload = {
            "key": self.merchant_key,
            "txnid": txnid,
            "hash": hash_value,
            "additional_data": "transaction_date",
            "token": self.token
        }

        try:
            print(f"\nMaking API request to: {url}")
            print(f"Request Payload:\n{json.dumps(payload, indent=2)}")

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Enhanced console output with full details
            print("\n" + "="*100)
            print("=" * 100)
            print(f"{'TRANSACTION DETAILS - FULL RESPONSE':^100}")
            print("=" * 100)
            print(f"Transaction ID: {txnid}")
            print(f"HTTP Status Code: {response.status_code}")
            print(f"Response Time: {response.elapsed.total_seconds():.2f} seconds")
            print("-" * 100)

            # Pretty print the full JSON response
            print("\nCOMPLETE API RESPONSE:")
            print("-" * 100)
            response_str = json.dumps(data, indent=4, ensure_ascii=False)
            print(response_str)
            print("-" * 100)

            # If there's transaction data, display it in a structured format
            if isinstance(data, dict):
                if data.get('status') == 1 and data.get('data'):
                    txn_data = data.get('data', {})
                    print("\nDETAILED TRANSACTION FIELDS:")
                    print("-" * 100)
                    for key, value in sorted(txn_data.items()):
                        print(f"{key:30s} : {value}")
                    print("-" * 100)

                    # Highlight addedon and error_message
                    print("\n" + "!"*100)
                    print(f"{'KEY FIELDS FOR DATABASE':^100}")
                    print("!"*100)
                    print(f"addedon        : {txn_data.get('addedon', 'NOT FOUND')}")
                    print(f"error_message  : {txn_data.get('error_message', 'NOT FOUND')}")
                    print("!"*100)
                elif data.get('msg'):
                    print(f"\nAPI Message: {data.get('msg')}")
                    print("-" * 100)

            print("=" * 100)
            print("\n")

            return data

        except requests.exceptions.RequestException as e:
            print("\n" + "="*80)
            print(f"ERROR retrieving transaction details for {txnid}")
            print(f"Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status Code: {e.response.status_code}")
                print(f"Response: {e.response.text}")
            print("="*80 + "\n")
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

    def get_and_retrieve_transaction_details(self, start_date, end_date, hash_value, limit=None, db_handler=None):
        """
        Fetch transactions by date and retrieve detailed information for each transaction.
        Now supports pagination to fetch ALL transactions with automatic token refresh.

        Args:
            start_date (str): Start date in format "DD-MM-YYYY"
            end_date (str): End date in format "DD-MM-YYYY"
            hash_value (str): Hash value for request authentication
            limit (int, optional): Limit number of transactions to retrieve details for
            db_handler: ClickHouseDB instance to push data in batches (optional)

        Returns:
            list: List of detailed transaction data
        """
        print("\n=== Step 1: Fetching ALL transactions by date with pagination ===")

        all_transactions = []
        page_token = None
        page_number = 1

        # Fetch all pages
        while True:
            print(f"\n{'='*80}")
            print(f"--- Fetching transaction list page {page_number} ---")
            print(f"{'='*80}")

            # Get transactions from date API
            result = self.get_transactions_by_date(
                start_date=start_date,
                end_date=end_date,
                hash_value=hash_value,
                page_token=page_token
            )

            if not result or not result.get('status'):
                print("Failed to fetch transactions")
                break

            transactions = result.get('data', [])
            all_transactions.extend(transactions)
            print(f"Retrieved {len(transactions)} transactions from page {page_number}")
            print(f"Total transactions so far: {len(all_transactions)}")

            # Check if there's a next page
            next_token = result.get('next')
            if not next_token:
                print(f"\nNo more pages. Total transactions found: {len(all_transactions)}")
                break

            # Use the next token for the next iteration
            page_token = next_token
            page_number += 1

        if not all_transactions:
            print("No transactions found")
            return []

        # Apply limit if specified
        transactions_to_process = all_transactions
        if limit:
            transactions_to_process = all_transactions[:limit]
            print(f"\nLimiting to first {limit} transactions out of {len(all_transactions)} total")

        print(f"\n{'='*100}")
        print(f"=== Step 2: Retrieving detailed information for {len(transactions_to_process)} transactions ===")
        print(f"{'='*100}")

        detailed_transactions = []
        batch_size = 50  # Insert to DB every 50 transactions

        for idx, txn in enumerate(transactions_to_process, 1):
            txnid = txn.get('txnid')
            if not txnid:
                print(f"[{idx}/{len(transactions_to_process)}] Skipping - No txnid found")
                continue

            # Check if already in database
            if db_handler and db_handler.transaction_exists(txnid):
                # Get current status
                current_status = db_handler.get_transaction_status(txnid)

                # If status is intermediate (initiated, pending, preinitiated, true), check for updates
                if current_status in ['initiated', 'pending', 'preinitiated', 'true', 'True']:
                    # Fetch latest details to check for status change
                    latest_details = self.retrieve_transaction_details(txnid, hash_value)

                    if latest_details:
                        # Extract actual transaction data from API response
                        if isinstance(latest_details, dict) and latest_details.get('status') in [1, True, 'true']:
                            txn = latest_details.get('data') or latest_details.get('msg')
                            latest_status = txn.get('status', '') if txn else ''
                        else:
                            latest_status = latest_details.get('status', '')

                        # If status changed to a final state, update the transaction
                        if latest_status != current_status and latest_status not in ['initiated', 'pending', 'preinitiated', 'true', 'True']:
                            if db_handler.update_transaction(txnid, latest_details):
                                print(f"[{idx}/{len(transactions_to_process)}] Updated: {txnid} ({current_status} -> {latest_status})")
                            else:
                                print(f"[{idx}/{len(transactions_to_process)}] Update failed: {txnid}")
                        else:
                            print(f"[{idx}/{len(transactions_to_process)}] No status change: {txnid} (still {current_status})")
                    else:
                        print(f"[{idx}/{len(transactions_to_process)}] Could not fetch latest details: {txnid}")
                else:
                    print(f"[{idx}/{len(transactions_to_process)}] Skipping - Already in database with final status: {txnid} ({current_status})")

                continue

            # Refresh token every 100 transactions or if expired
            if idx % 100 == 0 or self.is_token_expired():
                print(f"\n[Token Refresh] Refreshing authentication token...")
                if not self.get_auth_token(force_refresh=True):
                    print(f"[ERROR] Failed to refresh token at transaction {idx}")
                    break

            print(f"\n{'*'*80}")
            print(f"[{idx}/{len(transactions_to_process)}] Fetching details for txnid: {txnid}")
            print(f"{'*'*80}")

            # Retrieve detailed transaction information
            details = self.retrieve_transaction_details(txnid, hash_value)

            if details:
                detailed_transactions.append(details)
                print(f"[OK] Successfully retrieved details for transaction {idx}/{len(transactions_to_process)}")

                # Insert in batches if db_handler provided
                if db_handler and len(detailed_transactions) >= batch_size:
                    print(f"\n[Batch Insert] Inserting {len(detailed_transactions)} transactions to database...")
                    inserted = db_handler.insert_detailed_transactions(detailed_transactions)
                    print(f"[Batch Insert] Successfully inserted {inserted} transactions")
                    detailed_transactions = []  # Clear batch
            else:
                print(f"[FAIL] Failed to retrieve details for transaction {idx}/{len(transactions_to_process)}")

        # Insert any remaining transactions in final batch
        if db_handler and len(detailed_transactions) > 0:
            print(f"\n[Final Batch Insert] Inserting remaining {len(detailed_transactions)} transactions to database...")
            inserted = db_handler.insert_detailed_transactions(detailed_transactions)
            print(f"[Final Batch Insert] Successfully inserted {inserted} transactions")

        print(f"\n{'='*100}")
        print(f"{'='*100}")
        print(f"{'FINAL SUMMARY':^100}")
        print(f"{'='*100}")
        print(f"Total transactions found across all pages: {len(all_transactions)}")
        print(f"Transactions processed for details: {len(transactions_to_process)}")
        print(f"Successfully retrieved details: {len(detailed_transactions) if not db_handler else 'Inserted in batches'}")
        print(f"{'='*100}\n")

        # Display consolidated view of all retrieved transactions
        if detailed_transactions:
            print("\n" + "="*100)
            print(f"{'CONSOLIDATED VIEW - ALL RETRIEVED TRANSACTIONS':^100}")
            print("="*100)

            for idx, detail in enumerate(detailed_transactions, 1):
                print(f"\n[Transaction {idx}]")
                print("-"*100)
                print(json.dumps(detail, indent=4, ensure_ascii=False))
                print("-"*100)

            print("="*100)
            print(f"Total: {len(detailed_transactions)} complete transaction records displayed above")
            print("="*100 + "\n")

        return detailed_transactions


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

            # Get the last transaction date from database to know where to start fetching
            print("\n=== Checking last transaction in database ===")
            last_txn_result = db.client.execute("SELECT MAX(created_at) FROM test_payment_transactions")
            last_created_at = last_txn_result[0][0] if last_txn_result[0][0] else None

            if last_created_at:
                # Fetch from 7 days ago to ensure we catch everything (including out-of-order transactions)
                from datetime import datetime as dt, timedelta
                start_date_obj = dt.now() - timedelta(days=7)
                start_date = start_date_obj.strftime("%d-%m-%Y")
                print(f"Last sync in DB: {last_created_at}")
                print(f"Will fetch from: {start_date} (last 7 days to catch any missed transactions)")
            else:
                # No data in DB, start from 30 days ago to get all historical data
                from datetime import datetime as dt, timedelta
                start_date_obj = dt.now() - timedelta(days=30)
                start_date = start_date_obj.strftime("%d-%m-%Y")
                print(f"No transactions in DB yet. Starting from: {start_date} (last 30 days)")

            # Always use today as end date to get latest data
            end_date = datetime.now().strftime("%d-%m-%Y")
            print(f"Fetching up to: {end_date} (current date)")

            # OPTION 1: Fetch transaction details dynamically from date API
            print("\n=== Fetching all available transactions with auto token refresh ===")
            detailed_transactions = easebuzz.get_and_retrieve_transaction_details(
                start_date=start_date,
                end_date=end_date,
                hash_value=hash_value,
                limit=None,  # Fetch all transactions
                db_handler=db  # Pass database handler for batch insertion and duplicate checking
            )

            print(f"\n{'#'*100}")
            print(f"{'SUCCESS':^100}")
            print(f"{'#'*100}")
            print(f"[OK] Completed processing transactions from {start_date} to {end_date}")
            print(f"[OK] All transactions inserted in batches directly to database")

            # Get updated total count from database
            total_in_db = db.get_transaction_count()
            print(f"[OK] Total transactions in database: {total_in_db}")

            # Display recent transactions with addedon and error_message
            print(f"\n=== Verifying Saved Data (Last 20 transactions) ===")
            db.get_transactions_with_details(limit=20)

            print(f"\nData successfully saved to:")
            print(f"  1. ClickHouse database table: test_payment_transactions")
            print(f"     Fields saved: addedon, error_message (along with all other fields)")
            print(f"  2. Verification table above showing addedon & error_message values")
            print(f"{'#'*100}\n")

            # print("\n" + "="*80)

            # # OPTION 2: Original functionality - Fetch ALL transactions with pagination
            # # Comment this out for now to focus on detailed transaction fetch
            # print("\n=== Fetching ALL transactions with pagination ===")
            # all_transactions = easebuzz.get_all_transactions(
            #     start_date="09-09-2025",
            #     end_date="11-12-2025",
            #     hash_value=hash_value,
            #     db_handler=db  # Pass database handler for immediate insertion
            # )

            if False:  # Disabled for now
                all_transactions = []
                print(f"\n[OK] Successfully fetched {len(all_transactions)} total transactions!")

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
                print("\n[OK] All transactions saved to 'transactions.json'")
            else:
                print("\n[INFO] Failed to retrieve transactions")
        else:
            print("\n[ERROR] Authentication failed")

    except Exception as e:
        print(f"\n[ERROR] Error in main execution: {e}")

    finally:
        # Always disconnect from database
        print("\n=== Closing connections ===")
        db.disconnect()


def update_intermediate_statuses(hours_lookback=48):
    """
    Periodic job to update transactions stuck in intermediate status
    This should be run separately every 1-2 hours

    Args:
        hours_lookback: How many hours back to check (default: 48)
    """
    print(f"\n{'='*100}")
    print(f"PERIODIC STATUS UPDATE JOB - Checking last {hours_lookback} hours")
    print(f"{'='*100}\n")

    # Initialize API and database
    easebuzz = EasebuzzAPI()
    db = ClickHouseDB()

    try:
        # Connect to database
        print("=== Connecting to ClickHouse ===")
        if not db.connect():
            print("Failed to connect to ClickHouse. Exiting...")
            return

        # Authenticate with Easebuzz
        print("\n=== Authenticating with Easebuzz ===")
        if not easebuzz.get_auth_token():
            print("Failed to authenticate. Exiting...")
            return

        hash_value = "b80cdee1da064dc20f50d4fd87b70a2d81bf4cb3fc6945fa50072498d77dae75e7158bcdbad619e03fa8f524fa4ddcf742a54b61a6798fb9fa3dc43fd99bcf94"

        # Get transactions with intermediate statuses
        print(f"\n=== Finding transactions with intermediate statuses (last {hours_lookback}h) ===")
        intermediate_txns = db.get_intermediate_status_transactions(hours_lookback)

        if not intermediate_txns or len(intermediate_txns) == 0:
            print(f"[OK] No intermediate status transactions found in last {hours_lookback} hours")
            print("All transactions are up to date!")
            return

        print(f"Found {len(intermediate_txns)} transactions to check\n")

        # Update each transaction
        updated_count = 0
        no_change_count = 0
        error_count = 0

        for idx, (txnid, current_status, addedon, current_amount) in enumerate(intermediate_txns, 1):
            if idx % 50 == 0:
                print(f"\n[Progress] Processed {idx}/{len(intermediate_txns)} transactions...")

            # Fetch latest details from API
            details = easebuzz.retrieve_transaction_details(txnid, hash_value)

            if details:
                # Extract actual status and amount from msg
                if isinstance(details, dict) and details.get('status') in [1, True, 'true']:
                    txn = details.get('data') or details.get('msg')
                    if txn:
                        actual_status = txn.get('status', '')
                        actual_amount = float(txn.get('amount', txn.get('total_debit_amount', 0)))

                        # Check if status or amount changed
                        status_changed = actual_status != current_status
                        amount_changed = abs(actual_amount - float(current_amount)) > 0.01

                        if status_changed or amount_changed:
                            if db.update_transaction(txnid, details):
                                changes = []
                                if status_changed:
                                    changes.append(f"{current_status} -> {actual_status}")
                                if amount_changed:
                                    changes.append(f"Rs.{current_amount} -> Rs.{actual_amount}")

                                print(f"[{idx}/{len(intermediate_txns)}] Updated {txnid[:35]:<35} | {' | '.join(changes)}")
                                updated_count += 1
                            else:
                                print(f"[{idx}/{len(intermediate_txns)}] [ERROR] Update failed: {txnid}")
                                error_count += 1
                        else:
                            no_change_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
            else:
                error_count += 1

            # Refresh token every 100 transactions
            if idx % 100 == 0:
                print(f"\n[Token Refresh] Refreshing authentication...")
                easebuzz.get_auth_token(force_refresh=True)

        # Print summary
        print(f"\n{'='*100}")
        print("UPDATE SUMMARY")
        print(f"{'='*100}")
        print(f"Total transactions checked: {len(intermediate_txns)}")
        print(f"Successfully updated: {updated_count}")
        print(f"No change needed: {no_change_count}")
        print(f"Errors: {error_count}")
        print(f"{'='*100}\n")

        if updated_count > 0:
            print(f"[SUCCESS] Updated {updated_count} transactions with latest status/amounts")
        else:
            print("[OK] All checked transactions are already up to date")

    except Exception as e:
        print(f"\n[ERROR] Error in update job: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.disconnect()


def run_continuous_sync(poll_interval=300, status_update_interval=7200):
    """
    Run continuous polling mode - syncs new transactions at regular intervals

    Args:
        poll_interval: Seconds between transaction syncs (default: 300 = 5 minutes)
        status_update_interval: Seconds between status updates (default: 7200 = 2 hours)
    """
    import time

    print("\n" + "="*100)
    print("EASEBUZZ CLICKHOUSE CONTINUOUS SYNC SERVICE")
    print("="*100)
    print(f"Transaction Sync Interval: Every {poll_interval//60} minutes")
    print(f"Status Update Interval: Every {status_update_interval//60} minutes")
    print("Press Ctrl+C to stop")
    print("="*100 + "\n")

    last_status_update = 0
    sync_count = 0

    try:
        while True:
            sync_count += 1
            current_time = time.time()

            print(f"\n{'='*100}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SYNC #{sync_count} - Starting transaction sync...")
            print(f"{'='*100}\n")

            try:
                # Run main sync
                main()

                # Check if it's time for status update
                if current_time - last_status_update >= status_update_interval:
                    print(f"\n{'='*100}")
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running periodic status update...")
                    print(f"{'='*100}\n")
                    update_intermediate_statuses(hours_lookback=48)
                    last_status_update = current_time

                print(f"\n{'='*100}")
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sync completed successfully!")
                print(f"Next sync in {poll_interval//60} minutes...")
                print(f"{'='*100}\n")

            except Exception as e:
                print(f"\n[ERROR] Sync failed: {e}")
                import traceback
                traceback.print_exc()
                print(f"Will retry in {poll_interval//60} minutes...\n")

            # Wait before next sync
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n\n" + "="*100)
        print("SYNC SERVICE STOPPED BY USER")
        print(f"Total syncs completed: {sync_count}")
        print("="*100 + "\n")


if __name__ == "__main__":
    import sys

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--continuous' or sys.argv[1] == '--live':
            # Continuous polling mode
            poll_interval = 300  # 5 minutes default
            status_interval = 7200  # 2 hours default

            # Allow custom intervals
            if len(sys.argv) > 2:
                try:
                    poll_interval = int(sys.argv[2]) * 60  # Convert minutes to seconds
                except:
                    pass

            if len(sys.argv) > 3:
                try:
                    status_interval = int(sys.argv[3]) * 60  # Convert minutes to seconds
                except:
                    pass

            run_continuous_sync(poll_interval, status_interval)

        elif sys.argv[1] == '--update-status':
            # Run periodic status update
            hours = 48
            if len(sys.argv) > 2:
                try:
                    hours = int(sys.argv[2])
                except:
                    pass
            update_intermediate_statuses(hours_lookback=hours)
        else:
            # Run normal sync
            main()
    else:
        # Run normal sync (single run)
        main()

from sshtunnel import SSHTunnelForwarder
from clickhouse_driver import Client
from tabulate import tabulate

# SSH Configuration
ssh_host = '3.7.169.181'
ssh_port = 22
ssh_username = 'ubuntu'
ssh_key_path = r'D:\ClickHouse\SML_Castlecraft.pem'

# ClickHouse Configuration
ch_host = '127.0.0.1'
ch_port = 9000
ch_user = 'default'
ch_password = 'aSh49aVjfy8P'
ch_database = 'default'

try:
    # Create SSH tunnel
    print("Establishing SSH tunnel...")
    tunnel = SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_username,
        ssh_pkey=ssh_key_path,
        remote_bind_address=(ch_host, ch_port),
        local_bind_address=(ch_host, ch_port)
    )
    tunnel.start()
    print(f"SSH tunnel established on {tunnel.local_bind_port}")

    # Connect to ClickHouse
    print("Connecting to ClickHouse...")
    client = Client(
        host=ch_host,
        port=tunnel.local_bind_port,
        user=ch_user,
        password=ch_password,
        database=ch_database
    )
    print("Connected to ClickHouse successfully!\n")

    # Check table structure
    print("="*80)
    print("CURRENT TABLE STRUCTURE")
    print("="*80)

    query = """
    SELECT name, type
    FROM system.columns
    WHERE table = 'test_payment_transactions'
    AND database = 'default'
    ORDER BY position
    """

    columns = client.execute(query)

    table_data = []
    for idx, (name, col_type) in enumerate(columns, 1):
        table_data.append([idx, name, col_type])

    print(tabulate(table_data, headers=['#', 'Column Name', 'Type'], tablefmt='grid'))

    # Check if addedon and error_message exist
    column_names = [col[0] for col in columns]

    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)

    if 'addedon' in column_names:
        print("✓ Column 'addedon' EXISTS")
    else:
        print("✗ Column 'addedon' MISSING - Adding it now...")
        client.execute("ALTER TABLE test_payment_transactions ADD COLUMN addedon String")
        print("✓ Column 'addedon' added successfully")

    if 'error_message' in column_names:
        print("✓ Column 'error_message' EXISTS")
    else:
        print("✗ Column 'error_message' MISSING - Adding it now...")
        client.execute("ALTER TABLE test_payment_transactions ADD COLUMN error_message String")
        print("✓ Column 'error_message' added successfully")

    print("\n" + "="*80)
    print("SOLUTION FOR IDE")
    print("="*80)
    print("The columns exist in the database.")
    print("Your IDE is showing a cached schema.")
    print("\nTo fix in your IDE:")
    print("1. Right-click on 'test_payment_transactions' table")
    print("2. Select 'Refresh' or 'Synchronize'")
    print("3. Or disconnect and reconnect to the database")
    print("="*80)

    # Disconnect
    client.disconnect()
    tunnel.stop()
    print("\nConnections closed")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

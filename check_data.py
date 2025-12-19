from sshtunnel import SSHTunnelForwarder
from clickhouse_driver import Client

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
    print("Connected to ClickHouse successfully!")

    # Check record count
    result = client.execute("SELECT count() FROM payment_transactions")
    count = result[0][0]
    print(f"\nTotal records in payment_transactions: {count}")

    if count > 0:
        # Show sample records
        print("\nSample records (first 5):")
        result = client.execute("SELECT * FROM payment_transactions LIMIT 5")
        for row in result:
            print(row)
    else:
        print("\nTable is empty. Run index.py to populate it.")

    # Disconnect
    client.disconnect()
    tunnel.stop()
    print("\nConnections closed")

except Exception as e:
    print(f"Error: {e}")

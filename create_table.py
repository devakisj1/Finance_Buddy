import sqlite3

connection =sqlite3.connect("database.db")
cursor =  connection.cursor()
print("connected to DB")


# Create the users table
cursor.execute('CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT,last_name TEXT, password TEXT, email TEXT, budget INTEGER)')

# Create the transactions table with a proper foreign key
cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
    trans_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    category TEXT NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    payment_method TEXT NOT NULL, 
    notes TEXT,
    bill BLOB,
    FOREIGN KEY (user_id) REFERENCES users (user_id))''')

print("tables created")
cursor.close()
connection.close()




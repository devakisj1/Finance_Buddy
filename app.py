from flask import Flask, render_template, request, flash, redirect, url_for, session,jsonify
import sqlite3
import secrets
from werkzeug.security import generate_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import os
import re
from PIL import Image
import pytesseract
from datetime import datetime

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
app.secret_key = "super secret key"

#login
@app.route('/', methods =['GET','POST'])
def login():
        if request.method == "POST":
                
                # Connect to SQLite3 database 
                connection = sqlite3.connect('database.db')
                cursor = connection.cursor()

                email=request.form['email']
                password=request.form['password']

                query = "SELECT user_id, first_name FROM users WHERE email=? AND password=?"
                cursor.execute(query, (email, password))
                results = cursor.fetchone()
                
                if results is None:
                    # Redrect to login if error occurs
                    flash('Invalid email or password. Please try again.', 'danger')
                    return redirect(url_for('login'))

                else:
                    # Redirect to dashboard on login
                    session['user_id'] = results[0]  
                    session['username'] = results[1]  
                    return redirect(url_for('dashboard'))

        return render_template("index.html")

#logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))



SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
# Function to send a reset password email
def send_reset_email(email, token):
    reset_url = url_for('reset_password', token=token, _external=True)
    message = MIMEMultipart()
    message['From'] = SMTP_USERNAME
    message['To'] = email
    message['Subject'] = 'Password Reset Request'
    body = f"Click the link below to reset your password:\n\n{reset_url}"
    message.attach(MIMEText(body, 'plain'))
    print(message)
    print(SMTP_PASSWORD)
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
        print('Email sent successfully.')
    except Exception as e:
        print(f'Failed to send email: {e}')

@app.route('/password_reset_request', methods=['GET', 'POST'])
def password_reset_request():
    if request.method == 'POST':
        email = request.form['email']
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        connection.close()
        print(user)
        if user:
            token = secrets.token_urlsafe(32)
            send_reset_email(email, token)
            flash('A password reset link has been sent to your email.', 'success')
        else:
            flash('No account found with that email address.', 'danger')
        return redirect(url_for('login'))
    return render_template('password_reset_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(request.url)
        hashed_password = generate_password_hash(new_password)
        # Simulate token verification for demonstration; replace this logic with real token verification
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, "user_email@example.com"))
        connection.commit()
        connection.close()
        flash('Your password has been reset successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html')



#signup
@app.route("/signup", methods = ['POST', 'GET'])
def signup():
    if request.method == 'POST':
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            password = request.form['password']

            # Connect to SQLite3 database 
            with sqlite3.connect('database.db') as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                user_exists = cursor.fetchone()
                if user_exists:
                    flash('Email is already in use. Please use a different one', 'danger')
                else:
                    cursor.execute("INSERT INTO users (first_name, last_name, password, email, budget) VALUES (?,?,?,?,?)",(first_name, last_name, password, email,0))
                    connection.commit()
                    #flash message on success
                    flash('You have successfully signed up! Proceed to Login', 'success')
                    return redirect(url_for('login'))
    return render_template('signup.html')

# scan bill
@app.route('/process_bill', methods=['POST'])
def process_bill():
    if 'bill' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"}), 400

    bill = request.files['bill']
    if bill.filename == '':
        return jsonify({"success": False, "message": "Empty file name"}), 400

    try:
        # Read the uploaded file into a PIL Image object
        image = Image.open(bill)

        # Use pytesseract to perform OCR
        text = pytesseract.image_to_string(image, lang='eng')

        # Normalize the text to handle OCR formatting issues
        normalized_text = ' '.join(text.split())

        # Extract date using regex (handles "date: mm/dd/yyyy" or "Date: mm/dd/yyyy")
        date_match = re.search(r'\bDATE:\s*(\d{2}/\d{2}/\d{4})\b', normalized_text, re.IGNORECASE)
        date = date_match.group(1) if date_match else None

        # Extract amount using regex 
        amount_match = re.search(r'\bTOTAL[:\-]?\s*\$+\s*(\d+(\.\d{1,2})?)\b', normalized_text, re.IGNORECASE)
        amount = amount_match.group(1) if amount_match else None

        # Parse the date string into a datetime object
        date_obj = datetime.strptime(date, "%m/%d/%Y")
        formatted_date = date_obj.strftime("%d/%m/%Y")

        print(formatted_date)

        return jsonify({"success": True, "date": formatted_date, "amount": amount})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500




#add transaction            
@app.route('/add_transaction', methods=['POST', 'GET'])
def add_transaction():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        date = request.form['date']
        category = request.form['category']
        transaction_type = request.form['type']
        amount = request.form['amount']
        payment_method = request.form['payment_method']
        notes = request.form['notes']
        bill_obj = request.files['bill']

        # Save bill file if it exists
        destination_path = ""
        if bill_obj:
            destination_path = f"static/uploads/{bill_obj.filename}"
            bill_obj.save(destination_path)

        try:
            # Connect to SQLite3 database 
            connection = sqlite3.connect("database.db")
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO transactions (user_id, date, category, type, amount, payment_method, notes, bill) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, date, category, transaction_type, amount, payment_method, notes, destination_path))
            connection.commit()

            # Flash success message
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('add_transaction'))

        except sqlite3.Error as e:
            # Roll back if error
            connection.rollback()
            flash(f'An error occurred: {e}', 'danger')

        finally:
            # Close the database connection
            connection.close()
    return render_template('add_transaction.html')


#view monthly transaction
@app.route('/view_monthly_transaction', methods=['POST','GET'])
def view_monthly_transaction():
    show_results = False
    user_id = session['user_id']
    # Get current month and year
    selected_month = int(datetime.datetime.now().strftime('%m'))
    selected_year = int(datetime.datetime.now().strftime('%Y'))
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT strftime('%Y', date) FROM transactions WHERE user_id = ? ORDER BY date DESC", (user_id,)) 
    years =[int(row[0]) for row in cursor.fetchall()]
    connection.close() 

    if request.method =='POST':
        year = request.form.get('year')
        month = request.form.get('month')
        selected_year=int(year)
        selected_month=int(month)
        transactions = []

        if year and month:
            start_date = f"{year}-{month}-01"
            end_date = f"{year}-{month}-31" 
            connection = sqlite3.connect('database.db')
            cursor = connection.cursor()

            # Query to filter transactions by selected year and month
            query = """
                SELECT * FROM transactions
                WHERE user_id = ? AND date BETWEEN ? AND ? ORDER BY date DESC
            """
            cursor.execute(query, (user_id, start_date, end_date))
            transactions = cursor.fetchall()
            connection.close()
            show_results = True
            return render_template('view_monthly_transaction.html', transactions=transactions, show_results=show_results, selected_month=selected_month, selected_year=selected_year,years=years)
        
    return render_template('view_monthly_transaction.html', show_results=show_results, selected_month=selected_month, selected_year=selected_year, years=years)


@app.route('/transaction_menu')
def transaction_menu():
    if 'username' not in session:
        return redirect(url_for('login'))
    # Renders the HTML template with the two card options
    return render_template('transaction_menu.html')

@app.route('/statistics_menu')
def statistics_menu():
    if 'username' not in session:
        return redirect(url_for('login'))
    # Renders the HTML template with the two card options
    return render_template('statistics_menu.html')


from flask import request, session, redirect, url_for, render_template
import sqlite3

@app.route('/view_all_transactions')
def view_all_transactions():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    filter_flag =False

    # Connect to the database
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    # Query to select all transactions for the user
    query = "SELECT date, type, category, amount, payment_method, notes, bill FROM transactions WHERE user_id = ? ORDER BY date DESC"
    cursor.execute(query, (user_id,))
    transactions = cursor.fetchall()

    # Fetch min and max amounts for the slider
    cursor.execute("SELECT MIN(amount), MAX(amount) FROM transactions WHERE user_id = ?", (user_id,))
    min_max_amounts = cursor.fetchone()
    min_amount = min_max_amounts[0] if min_max_amounts[0] is not None else 0
    max_amount = min_max_amounts[1] if min_max_amounts[1] is not None else 0

    # Fetch unique values for filters
    cursor.execute("SELECT DISTINCT strftime('%Y', date) FROM transactions WHERE user_id = ?", (user_id,))
    years = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT category FROM transactions WHERE user_id = ?", (user_id,))
    categories = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT payment_method FROM transactions WHERE user_id = ?", (user_id,))
    payment_methods = [row[0] for row in cursor.fetchall()]

    connection.close()

    # Render template with all transactions and filter defaults
    return render_template(
        'view_transaction_history.html',
        transactions=transactions,
        years=years,
        categories=categories,
        payment_methods=payment_methods,
        selected_year="",
        selected_type="",
        selected_category="",
        selected_payment_method="",
        min_amount=min_amount,
        max_amount=max_amount,
        selected_min_amount=min_amount,
        selected_max_amount=max_amount,
        filter_flag=filter_flag
    )

@app.route('/filter_transaction_history', methods=['POST'])
def filter_transaction_history():
    if 'username' not in session:
        return redirect(url_for('login'))

    filter_flag=True
    # Get filter values from the request args
    selected_year = request.form.get('year', default="")
    selected_type = request.form.get('type', default="All")
    selected_category = request.form.get('category', default="")
    selected_payment_method = request.form.get('payment_method', default="")
    selected_min_amount = request.form.get('min_amount', type=float)
    selected_max_amount = request.form.get('max_amount', type=float)

    user_id = session['user_id']
    filters = [user_id]
    query = "SELECT date, type, category, amount, payment_method, notes, bill FROM transactions WHERE user_id = ?"

    # Apply filters to the SQL query
    if selected_year:
        query += " AND strftime('%Y', date) = ?"
        filters.append(str(selected_year))
    
    if selected_type and selected_type != "All":
        query += " AND type = ?"
        filters.append(selected_type)
    
    if selected_category:
        query += " AND category = ?"
        filters.append(selected_category)
    
    if selected_payment_method:
        query += " AND payment_method = ?"
        filters.append(selected_payment_method)

    # Connect to the database
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    # Fetch min and max amounts for the slider
    cursor.execute("SELECT MIN(amount), MAX(amount) FROM transactions WHERE user_id = ?", (user_id,))
    min_max_amounts = cursor.fetchone()
    min_amount = min_max_amounts[0] if min_max_amounts[0] is not None else 0
    max_amount = min_max_amounts[1] if min_max_amounts[1] is not None else 0

    # Apply amount range filter to the SQL query if selected
    if selected_min_amount is not None:
        query += " AND amount >= ?"
        filters.append(selected_min_amount)

    if selected_max_amount is not None:
        query += " AND amount <= ?"
        filters.append(selected_max_amount)

    # Order transactions by date in descending order
    query += " ORDER BY date DESC"

    # Fetch filtered transactions
    cursor.execute(query, tuple(filters))
    transactions = cursor.fetchall()

    # Fetch unique values for filters
    cursor.execute("SELECT DISTINCT strftime('%Y', date) FROM transactions WHERE user_id = ?", (user_id,))
    years = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT category FROM transactions WHERE user_id = ?", (user_id,))
    categories = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT payment_method FROM transactions WHERE user_id = ?", (user_id,))
    payment_methods = [row[0] for row in cursor.fetchall()]

    connection.close()

    # Render template with filtered transactions
    return render_template(
        'view_transaction_history.html',
        transactions=transactions,
        years=years,
        categories=categories,
        payment_methods=payment_methods,
        selected_year=selected_year,
        selected_type=selected_type,
        selected_category=selected_category,
        selected_payment_method=selected_payment_method,
        min_amount=min_amount,
        max_amount=max_amount,
        selected_min_amount=selected_min_amount,
        selected_max_amount=selected_max_amount,
        filter_flag=filter_flag
    )


#edit transaction
@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        destination_path=""
        date = request.form['date']
        category = request.form['category']
        transaction_type = request.form['type']
        amount = request.form['amount']
        payment_method = request.form['payment_method']
        notes = request.form['notes']
        bill_obj = request.files['bill']

        if bill_obj:
                destination_path= f"static/uploads/{bill_obj.filename}"
                bill_obj.save(destination_path)

        try:
            # Update the transaction in the database
            connection = sqlite3.connect("database.db")
            cursor = connection.cursor()
            if destination_path:
                query = """
                    UPDATE transactions 
                    SET date = ?, category = ?, type = ?, amount = ?, payment_method = ?, notes = ?, bill = ?
                    WHERE trans_id = ?
                """
                cursor.execute(query, (date, category, transaction_type, amount, payment_method, notes, destination_path, transaction_id))
            else:
                query = """
                    UPDATE transactions 
                    SET date = ?, category = ?, type = ?, amount = ?, payment_method = ?, notes = ?
                    WHERE trans_id = ?
                """
                cursor.execute(query, (date, category, transaction_type, amount, payment_method, notes, transaction_id))
            
            connection.commit()
            

        except sqlite3.Error as e:
            connection.rollback()
            flash(f'An error occurred: {e}', 'danger')
        
        finally:
            connection.close()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('edit_transaction', transaction_id=transaction_id))
    
    # For GET request, fetch the existing data
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    cursor.execute("SELECT date, category, type, amount, payment_method, notes FROM transactions WHERE trans_id = ?", (transaction_id,))
    transaction = cursor.fetchone()
    connection.close()
    
    return render_template('edit_transaction.html', transaction=transaction, transaction_id=transaction_id)


# Delete transaction
@app.route('/delete_transaction/<int:transaction_id>', methods=['GET'])
def delete_transaction(transaction_id):
    # connect to DB
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM transactions WHERE trans_id = ?", (transaction_id,))
    connection.commit()
    connection.close()
    return redirect(url_for('view_monthly_transaction'))


@app.route('/edit_account', methods=['GET', 'POST'])
def edit_account():
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        budget = request.form['budget']


        try:
            # Update the transaction in the database
            connection = sqlite3.connect("database.db")
            cursor = connection.cursor()
            query = """
                UPDATE users 
                SET first_name = ?, last_name = ?, email = ?, password = ?, budget = ?
                WHERE user_id = ?
            """
            cursor.execute(query,(first_name, last_name, email, password, budget, user_id))
            connection.commit()
            flash('Account details updated successfully!', 'success')
            

        except sqlite3.Error as e:
            connection.rollback()
            flash(f'An error occurred: {e}', 'danger')
        
        finally:
            connection.close()
        
        return redirect(url_for('edit_account'))

    user_id = session['user_id']
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("SELECT first_name, last_name, email, password, budget FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    connection.close()
    return render_template('account.html', user=user)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_name = session['username']

    # Get current month and year
    current_month = int(datetime.now().strftime('%m'))
    current_year = int(datetime.now().strftime('%Y'))

    # Handle POST request (when month/year is changed)
    if request.method == 'POST':
        selected_month = int(request.form['month']) 
        selected_year = int(request.form['year'])
    else:
        selected_month = current_month
        selected_year = current_year
    
    selected_year = str(selected_year)
    selected_month = str(selected_month).zfill(2)

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

        # Get valid years
    cursor.execute("SELECT DISTINCT strftime('%Y', date) FROM transactions WHERE user_id = ?", (user_id,))
    years = [int(row[0]) for row in cursor.fetchall()]

    # Fetch budget from users table
    cursor.execute("SELECT budget FROM users WHERE user_id = ?", (user_id,))
    budget_result = cursor.fetchone()
    budget = budget_result[0] if budget_result else 0

    cursor.execute("""
        SELECT SUM(amount) 
        FROM transactions 
        WHERE user_id = ? 
        AND type = 'Expense'
        AND strftime('%m', date) = ? 
        AND strftime('%Y', date) = ?
    """, (user_id, selected_month, selected_year))
    expense_result = cursor.fetchone()
    total_expenses = expense_result[0] if expense_result[0] else 0

    cursor.execute("""
        SELECT SUM(amount) 
        FROM transactions 
        WHERE user_id = ? 
        AND type = 'Income'
        AND strftime('%m', date) = ? 
        AND strftime('%Y', date) = ?
    """, (user_id, selected_month, selected_year))
    income_result = cursor.fetchone()
    total_income = income_result[0] if income_result[0] else 0

    connection.close()


    selected_year = int(selected_year)
    selected_month = int(selected_month)

    return render_template('dashboard.html', budget=budget, total_expenses=total_expenses, total_income =total_income, user_name=user_name, selected_year=selected_year, selected_month=selected_month, years=years)

@app.route('/daily_spending_data', methods=['GET', 'POST'])
def daily_spending_data():
    if 'username' in session:
        user_id = session['user_id']

        data = request.get_json()
        selected_month_str = str(data.get('month')).zfill(2) 
        selected_year_str = str(data.get('year'))
        
        # Fetch daily spending data from the database
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""
            SELECT strftime('%Y-%m-%d', date) AS day, SUM(amount) 
            FROM transactions 
            WHERE user_id = ? 
              AND strftime('%Y', date) = ? 
              AND strftime('%m', date) = ? 
            GROUP BY day 
            ORDER BY day ASC
        """, (user_id, selected_year_str, selected_month_str))
        
        data = c.fetchall()
        conn.close()

        # Format data for Chart.js
        labels = [row[0] for row in data]  # Dates in "YYYY-MM-DD" format
        amounts = [row[1] for row in data] # Corresponding amounts
        return jsonify({'labels': labels, 'amounts': amounts})
    else:
        return redirect(url_for('login'))
    

@app.route('/monthly_statistics', methods=['GET', 'POST'])
def monthly_statistics():
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))

    # Get current month and year
    selected_month = int(datetime.datetime.now().strftime('%m'))
    selected_year = int(datetime.datetime.now().strftime('%Y'))

    if request.method == 'POST':
        selected_month = int(request.form['month']) 
        selected_year = int(request.form['year'])

    selected_month = str(selected_month).zfill(2)

    # Define all possible income and expense categories
    income_categories = ["Salary", "Investments", "Freelancing", "Other Income"]
    expense_categories = ["Rent", "Groceries", "Utilities", "Education", "Travel", "Entertainment", "Other Expense"]

    # Initialize category dictionaries with 0
    income_by_category = {category: 0 for category in income_categories}
    expense_by_category = {category: 0 for category in expense_categories}

    # Connect to the database and fetch filtered data
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Get valid years
    cursor.execute("SELECT DISTINCT strftime('%Y', date) FROM transactions WHERE user_id = ?", (user_id,))
    years = [int(row[0]) for row in cursor.fetchall()]

    # Fetch total expenses for the selected month and year
    cursor.execute("""
        SELECT category, SUM(amount) 
        FROM transactions 
        WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ? AND type = 'Expense'
        GROUP BY category
    """, (user_id, selected_month, str(selected_year)))
    expense_data = cursor.fetchall()

    # Update expense_by_category with actual data
    for category, amount in expense_data:
        if category in expense_by_category:
            expense_by_category[category] = amount

    # Fetch total income for the selected month and year
    cursor.execute("""
        SELECT category, SUM(amount) 
        FROM transactions 
        WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ? AND type = 'Income'
        GROUP BY category
    """, (user_id, selected_month, str(selected_year)))
    income_data = cursor.fetchall()

    # Update income_by_category with actual data
    for category, amount in income_data:
        if category in income_by_category:
            income_by_category[category] = amount

    cursor.close()
    connection.close()

    # Sort the categories in descending order by amount
    sorted_expense_by_category = dict(sorted(expense_by_category.items(), key=lambda item: item[1], reverse=True))
    sorted_income_by_category = dict(sorted(income_by_category.items(), key=lambda item: item[1], reverse=True))
    

    return render_template(
        'monthly_statistics.html',
        total_expenses=sum(expense_by_category.values()),
        total_income=sum(income_by_category.values()),
        expense_by_category=sorted_expense_by_category,
        income_by_category=sorted_income_by_category,
        years=years,
        selected_month=int(selected_month),
        selected_year=selected_year
    )



@app.route('/yearly_statistics', methods=['GET', 'POST'])
def yearly_statistics():
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))

    selected_year = int(datetime.datetime.now().strftime('%Y'))

    if request.method == 'POST':
        selected_year = int(request.form['year'])


    # Define all possible income and expense categories
    income_categories = ["Salary", "Investments", "Freelancing", "Other Income"]
    expense_categories = ["Rent", "Groceries", "Utilities", "Education", "Travel", "Entertainment", "Other Expense"]

    # Initialize category dictionaries with 0
    income_by_category = {category: 0 for category in income_categories}
    expense_by_category = {category: 0 for category in expense_categories}

    # Connect to the database and fetch filtered data
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Get valid years
    cursor.execute("SELECT DISTINCT strftime('%Y', date) FROM transactions WHERE user_id = ?", (user_id,))
    years = [int(row[0]) for row in cursor.fetchall()]

    # Fetch total expenses for the selected month and year
    cursor.execute("""
        SELECT category, SUM(amount) 
        FROM transactions 
        WHERE user_id = ?  AND strftime('%Y', date) = ? AND type = 'Expense'
        GROUP BY category
    """, (user_id, str(selected_year)))
    expense_data = cursor.fetchall()

    # Update expense_by_category with actual data
    for category, amount in expense_data:
        if category in expense_by_category:
            expense_by_category[category] = amount

    # Fetch total income for the selected month and year
    cursor.execute("""
        SELECT category, SUM(amount) 
        FROM transactions 
        WHERE user_id = ? AND strftime('%Y', date) = ? AND type = 'Income'
        GROUP BY category
    """, (user_id, str(selected_year)))
    income_data = cursor.fetchall()

    # Update income_by_category with actual data
    for category, amount in income_data:
        if category in income_by_category:
            income_by_category[category] = amount

    cursor.close()
    connection.close()

    # Sort the categories in descending order by amount
    sorted_expense_by_category = dict(sorted(expense_by_category.items(), key=lambda item: item[1], reverse=True))
    sorted_income_by_category = dict(sorted(income_by_category.items(), key=lambda item: item[1], reverse=True))
    

    return render_template(
        'yearly_statistics.html',
        total_expenses=sum(expense_by_category.values()),
        total_income=sum(income_by_category.values()),
        expense_by_category=sorted_expense_by_category,
        income_by_category=sorted_income_by_category,
        years=years,
        selected_year=selected_year
    )


if __name__ == '__main__':
    app.run(debug=True)





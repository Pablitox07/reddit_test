from flask import Flask, render_template, request, jsonify
import pyodbc
import bcrypt

connection_string = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=Reddit_db;"
    "Trusted_Connection=Yes;"
)




try:
    conn = pyodbc.connect(connection_string)
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/createPost')
def createPost():
    return render_template('createPost.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/posts/<post_id>')
def view_posts(post_id):
    return render_template('view_posts.html')

@app.route("/profile/<user_id>")
def profile(user_id):
    return render_template("profile.html")

@app.route('/registerUser', methods=['POST'])
def registerUser():
    received_username = request.form.get('username')
    received_email = request.form.get('email')
    received_password = request.form.get('password_1')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # check email 
        check_unique_email = """
        SELECT COUNT(*)
        FROM Users 
        WHERE LOWER(email) = LOWER(?);
        """

        cursor.execute(check_unique_email, (received_email,))
        is_email_unique = cursor.fetchone()

        # check username
        check_unique_username = """
        SELECT COUNT(*) FROM Users
        WHERE LOWER(username) = LOWER(?);
        """ 
        cursor.execute(check_unique_username, (received_username,))
        is_username_unique = cursor.fetchone()

        # work with the password here 
        hashed_password = bcrypt.hashpw(received_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # check that the email is unique
        if is_email_unique[0] > 0:
            return "The email you entered is already in used."
        elif is_username_unique[0] > 0:
            return "The username you entered is already in used. "
        else:
            query_create_new_user = """
            INSERT INTO Users (email, password, username)
            VALUES (?, ?, ?)
            """
            cursor.execute(query_create_new_user,  (received_email, hashed_password, received_username))
            conn.commit()
            return "The user was registered correctly."
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/loguser', methods=['POST'])
def loguser():
    received_user = request.form.get('username')
    received_password = request.form.get('password')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # get username
        check_username = """
        SELECT * FROM Users
        WHERE LOWER(username) = LOWER(?);
        """ 
        cursor.execute(check_username, (received_user))
        username_unique = cursor.fetchone()

        if username_unique == None:
            return "The user or the password were incorrect."
        else:
            DB_password = username_unique[2]
            is_match = bcrypt.checkpw(received_password.encode('utf-8'), DB_password.encode('utf-8'))
            if is_match:
                return "user logged"
            else:
                return "The user or the password were incorrect."
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()



# ------------------- Functions below here ----------------------------

def get_db_connection():
    connection_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost;"
        "Database=Reddit_db;"
        "Trusted_Connection=Yes;"
    )
    return pyodbc.connect(connection_string)



if __name__ == '__main__':
    app.run(debug=True)

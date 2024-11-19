from flask import Flask, render_template, request, jsonify
from datetime import datetime, timezone, timedelta
import pyodbc
import bcrypt
import jwt
import pytz

connection_string = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=Reddit_db;"
    "Trusted_Connection=Yes;"
)

SECRET_KEY = "vcwwue32jidnsv5ncdu1223349dbucwutang"


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
    received_username = request.json.get('username')
    received_email = request.json.get('email')
    received_password = request.json.get('password_1')

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
            return {"message" : "The email you entered is already in used.", "status": 400}
        elif is_username_unique[0] > 0:
            return {"message" :"The username you entered is already in used. ", "status": 400}
        else:
            query_create_new_user = """
            INSERT INTO Users (email, password, username)
            VALUES (?, ?, ?)
            """
            cursor.execute(query_create_new_user,  (received_email, hashed_password, received_username))
            conn.commit()

            # get the user current info
            user_info = get_user_info(received_username)

            # creates a new token with the user current info
            token = create_token (user_info)
            print(token)

            return {
                "message" :"The user was registered correctly.", 
                "status": 200, 
                "user_info": { 
                "username": received_username, 
                "profile_pic": user_info[3], 
                "email":received_email, 
                "user_id" : user_info[0]
                },
                "token": token
            }
    except Exception as e:
        return {"message": str(e), "status": 500}
    finally:
        conn.close()

@app.route('/loguser', methods=['POST'])
def loguser():
    received_user = request.json.get('username_email')
    received_password = request.json.get('password')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # get username
        check_username = """
        SELECT * FROM Users
        WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?);
        """ 
        cursor.execute(check_username, (received_user, received_user))
        user_info = cursor.fetchone()

        if user_info == None:
            return {"message" :"The username and password are not correct.", "status": 400}
        else:
            DB_password = user_info[2]
            is_match = bcrypt.checkpw(received_password.encode('utf-8'), DB_password.encode('utf-8'))
            if is_match:
                # get the user current info            
                user_info = get_user_info(received_user)

                # creates a new token with the user current info
                token = create_token (user_info)
                print(token)

                    
                return {
                    "message" :"The user was logged in correctly.", 
                    "status": 200, 
                    "user_info": { 
                    "username": user_info[6], 
                    "profile_pic": user_info[3], 
                    "email":user_info[1], 
                    "user_id" : user_info[0]
                    },
                    "token": token
                }
            else:
                return {"message" :"The username and password are not correct.", "status": 400}
    except Exception as e:
        print(f"Error during login: {e}")
        return {"message": "An unexpected error occurred. Please try again later.", "status": 500}, 500

    finally:
        conn.close()

@app.route("/publishPost", methods=['POST'])
def publishPost():
    #get needed info from request 
    received_userid = request.json.get('userid')
    received_title = request.json.get("title")
    received_posts_text = request.json.get("text")
    received_category = request.json.get("category")
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith("Bearer "):
        return {"message": "Missing or invalid token.", "status": 401}, 401
    
    token = auth_header.split(" ")[1]
    
    try:
        # Decode and validate the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO Posts (user_id, content, title, category)
        VALUES 
            (?, ?, ?, ?)
        """
        cursor.execute(query, (received_userid, received_posts_text, received_title, received_category))
        conn.commit()

        query_get_post_id = """
        SELECT * FROM Posts
        WHERE content = ? AND title = ? AND user_id = ?;
        """
        cursor.execute(query_get_post_id, (received_posts_text, received_title, received_userid))
        new_post_row = cursor.fetchone()

        return {"message": "Success", "post_id": new_post_row[0]}
    


    except jwt.ExpiredSignatureError as e:
        print(e)
        return {"message": "Token has expired.", "status": 401}, 401
    except jwt.InvalidTokenError as e:
        print(e)
        return {"message": "Invalid token.", "status": 401}, 401
    except Exception as e:
        print(f"Error: {e}")
        return {"message": "An unexpected error occurred. Please try again later.", "status": 500}, 500



# ------------------- Functions below here ----------------------------

def get_db_connection():
    connection_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost;"
        "Database=Reddit_db;"
        "Trusted_Connection=Yes;"
    )
    return pyodbc.connect(connection_string)

def get_user_info(username):
    conn = get_db_connection()
    cursor = conn.cursor() 
    query = """
    SELECT * FROM Users
    WHERE LOWER(username) = LOWER(?);
    """
    cursor.execute(query, (username,))
    username_current_info = cursor.fetchone()
    conn.commit()
    conn.close()
    return username_current_info

def create_token (user_latest_info):
    # below is an example of the info order
    # 16, 'mf@ddom.com', '$2b$12$xafQ4jR6I8bwqGJZJbkMJeKt8pWtaaTRSCLFKv9mhclUbLbE46G.u', 'default_profile_img.png', 0, datetime.datetime(2024, 11, 16, 16, 43), 'mfdoom'
    token = jwt.encode({
    "user_id": user_latest_info[0],
    "email": user_latest_info[1],
    "password": user_latest_info[2],
    "profile_likes": user_latest_info[4],
    "exp": datetime.now(pytz.utc) + timedelta(hours=5), 
    "username": user_latest_info[6],
}, SECRET_KEY, algorithm="HS256")
    return token

if __name__ == '__main__':
    app.run(debug=True)

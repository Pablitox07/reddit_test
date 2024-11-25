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
    post_id = request.base_url.split(('/'))[-1]
    return render_template('view_posts.html', post_id=post_id)

@app.route("/load_comments", methods=["GET"])
def load_comments():
    received_post_id = request.args.get('post_id')
    received_current_user_id = request.args.get('current_user_id')

    return get_comments_from_post(received_post_id, received_current_user_id)

@app.route("/post_comment", methods=["POST"])
def post_comment():
    received_post_id = request.json.get('post_id')
    received_comment_author = request.json.get('comment_author')
    received_comment_text = request.json.get('comment_text')
    auth_header = request.headers.get('Authorization')

    try:
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"message": "Missing or invalid token.", "status": 401}, 401
    
        token = auth_header.split(" ")[1]
        query = """
        INSERT INTO Comments (post_id, comment_author, comment_text)
        VALUES (?, ?, ?);"""

        query_update_comments = """
        UPDATE Posts
        SET number_comments = number_comments + 1
        WHERE post_id = ?;
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(query, (received_post_id, received_comment_author, received_comment_text))
        conn.commit()
        cursor.execute(query_update_comments, (received_post_id))
        conn.commit()

        return {"status": 200}
    except jwt.ExpiredSignatureError as e:
        print(e)
        return {"message": "Token has expired.", "status": 401}
    except jwt.InvalidTokenError as e:
        print(e)
        return {"message": "Invalid token.", "status": 401}
    except Exception as e:
        print(f"Error: {e}")
        return {"message": "An unexpected error occurred. Please try again later.", "status": 500}
    finally:
        conn.close()

@app.route("/get_post_info", methods=["GET"])
def get_post_info():
    received_post_id = request.args.get('post_id')
    received_user_id = request.args.get('user_id')
    post_like_status = ""

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT Posts.*, Users.*
    FROM Posts
    JOIN Users ON Posts.user_id = Users.user_id
    WHERE Posts.post_id = ?;
    """
    cursor.execute(query, (received_post_id))
    post_info = cursor.fetchone()
    if str(received_user_id) != "nouser":
        like_post_info = check_user_likes_post(received_post_id, received_user_id)
        post_like_status = like_post_info['message']
    else:
        post_like_status = "annon user"

    if post_info == None:
        return {"message": "No post was not found", "status": 404}
    else:
        number_likes = calculate_like_dislike_ratio("Posts_likes", "post_id", received_post_id)
    # (10, 21, 0, 0, 'LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOLLLLLLLLLLLLLLLLLLLLLLLLLLLL66666666666', 'This is the tittle', 'Hobbies and Crafts', datetime.datetime(2024, 11, 18, 21, 5, 41, 80000), 21, 'gg@gm.com', '$2b$12$7WP8JhR83Vv4.cA5NQTNWOJ9wgGqvxDzWQRdbUNNygdM7dFrrJpXO', 'default_profile_img.png', 0, datetime.datetime(2024, 11, 17, 11, 5, 43, 397000), 'PABLITOX777')
        post_info_json = {
        "post_id": post_info[0],
        "user_id": post_info[1],
        "number_comments": post_info[2],
        "number_likes": number_likes,
        "content": post_info[4], 
        "title": post_info[5], 
        "category": post_info[6], 
        "created_at": post_info[7],
        "author_profile_picture": post_info[11],
        "username": post_info[14],
        "post_like_status": post_like_status,
        "status": 200
        }
        return post_info_json

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
                token = create_token(user_info)
                    
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
        return {"message": "An unexpected error occurred. Please try again later.", "status": 500}

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


@app.route("/post_like_dislike", methods=["POST"])
def post_like_dislike():
    received_comment_or_post_id = request.json.get('comment_or_post_id')
    # this holds the action that the user wants to do. so, it would be a sting with like or dislike
    received_like_or_dislike = request.json.get("like_or_dislike")
    # the user id
    received_user_id = request.json.get("user_id")
    # this is the token
    auth_header = request.headers.get('Authorization')
    query = ""
    like_dislike_db = ""
    # [0] = Comments or Posts, [1] = comment_id or post_id and [2] = Comments_likes or Posts_likes
    comment_or_post_variables = []
    query_update_comments_like = ""
    post_or_comment = request.json.get("post_or_comment")
    
    try:
        # check if user is logged in and if the seasion is still valid 
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"message": "Missing or invalid token.", "status": 401}, 401
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])


            
        if post_or_comment == "comment":
            comment_or_post_variables = ["Comments", "comment_id", "Comments_likes"]
        else: 
            comment_or_post_variables = ["Posts", "post_id", "Posts_likes"]

        print(comment_or_post_variables)
            
        # if the receive action is a like
        if received_like_or_dislike == "like":
            # query to sum one more like to the number_likes column 
            query = f"""
            UPDATE {comment_or_post_variables[0]}
            SET number_likes = number_likes + 1
            WHERE {comment_or_post_variables[1]} = ?;
            """
            # query to update the like_dislike status of the current user.
            query_update_comments_like = f"""
            UPDATE {comment_or_post_variables[2]}
            SET like_dislike = 'l'
            WHERE {comment_or_post_variables[1]} = ? AND user_id = ?;
            """
            like_dislike_db = "l"
        # if the received action is a dislike 
        else:
            # query to reduce by one the number_likes column 
            query = f"""
            UPDATE {comment_or_post_variables[0]}
            SET number_likes = number_likes - 1
            WHERE {comment_or_post_variables[1]} = ?;
            """
            # query to update the like_dislike status of the current user.
            query_update_comments_like = f"""
            UPDATE {comment_or_post_variables[2]}
            SET like_dislike = 'd'
            WHERE {comment_or_post_variables[1]} = ? AND user_id = ?;
            """
            like_dislike_db = "d"

        conn = get_db_connection()
        cursor = conn.cursor()
        
        query_check_user_already_like = f"""
        SELECT * FROM {comment_or_post_variables[2]}
        WHERE {comment_or_post_variables[1]} = ? AND user_id = ?;
        """

        cursor.execute(query_check_user_already_like, (received_comment_or_post_id, received_user_id))
        new_like_dislike = cursor.fetchone()

        
        # if no combination of comment_id and user_id is found then it should insert a new entry
        if new_like_dislike == None:
            query_post_like = f"""
            INSERT INTO {comment_or_post_variables[2]} ({comment_or_post_variables[1]}, user_id, like_dislike)
            VALUES 
                (?, ?, ?)
            """
            cursor.execute(query_post_like, (received_comment_or_post_id, received_user_id, like_dislike_db))
            conn.commit()

            number_likes = calculate_like_dislike_ratio(comment_or_post_variables[2], comment_or_post_variables[1], received_comment_or_post_id)

            return {
                "status": 200, 
                "change_status" : True,
                "number_likes": number_likes
            }


        # if the combination exists it means that the user already liked or disliked the comment
        else:
            # if the user's action is different as the status of the table then it sum or reduce the table and update the table  
            if str(new_like_dislike[3]) != like_dislike_db:
                cursor.execute(query_update_comments_like, (received_comment_or_post_id, received_user_id))
                conn.commit()
                number_likes = calculate_like_dislike_ratio(comment_or_post_variables[2], comment_or_post_variables[1], received_comment_or_post_id)
                return {
                    "status": 200, 
                    "change_status" : True,
                    "number_likes": number_likes
                }
            else:
                number_likes = calculate_like_dislike_ratio(comment_or_post_variables[2], comment_or_post_variables[1], received_comment_or_post_id)
                return {
                    "status": 200, 
                    "change_status" : False,
                    "number_likes": number_likes
                }
        
        



    except jwt.ExpiredSignatureError as e:
        print(f"Error: {e}")
        return {"message": "Token has expired.", "status": 401}
    except jwt.InvalidTokenError as e:
        print(e)
        return {"message": "Invalid token.", "status": 401}

@app.route('/check_user_likes_post', methods=["GET"])
def check_user_likes_post():
    received_post_id = request.args.get('post_id')
    received_user_id = request.args.get('user_id')
    return check_user_likes_post (received_post_id, received_user_id)


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

def get_comments_from_post(post_id, current_user_id):
    response = {}
    conn = get_db_connection()
    cursor = conn.cursor() 
    # query to get all comments from a specific post
    query = """
    SELECT Comments.*, Users.username, Users.profile_picture, Users.user_id
    FROM Comments
    JOIN Users ON Comments.comment_author = Users.user_id
    WHERE Comments.post_id = ?;
    """
    cursor.execute(query, (post_id))
    list_comments =  cursor.fetchall()

    # query to check if current user like or disliked a comment from the post 
    if current_user_id == "not_logged":
        current_user_id = -666
    query_check_current_user_like_comment = """
    SELECT like_dislike FROM Comments_likes
    WHERE comment_id = ? AND user_id = ?;
    """
    # for to format the response that will be sent to JS
    for x in range (len(list_comments)):
    # (5, 11, 2, 'comment_text', datetime, 0, 'aaaaaaaaaaaab1', 'default_profile_img.png')
        cursor.execute(query_check_current_user_like_comment, (str(list_comments[x][0]), current_user_id))
        l_d = cursor.fetchone()

        # calculate the likes a dislikes ratio
        query_calculate_likes_avg = """
        SELECT like_dislike FROM Comments_likes
        WHERE comment_id = ?;
        """
        cursor.execute(query_calculate_likes_avg, (str(list_comments[x][0])))
        list_likes = cursor.fetchall()
        # the likes starts on 0 
        likes_per_comments = 0

        # goes to all likes and if like it sums by 1 if not it reduces by 1 
        for item in list_likes:
            if item[0] == 'd':
                likes_per_comments -= 1
            elif item[0] == 'l':
                likes_per_comments += 1
        
        # already_liked_or_disliked will tell JS if the current user already liked or disliked the comment. 'l' = liked, 'd' = disliked and 'n' = not liked nor disliked 
        already_liked_or_disliked = ""
        if l_d == None: 
            already_liked_or_disliked = 'n'
        elif str(l_d[0]) == 'l' or str(l_d[0]) == 'd':
            already_liked_or_disliked = str(l_d[0])
    
        response[str(x)] = {
            "comment_id": list_comments[x][0], 
            "post_id": list_comments[x][1],
            "comment_author": list_comments[x][2],
            "comment_text":list_comments[x][3],
            "created_at": list_comments[x][4],
            "number_likes": likes_per_comments,
            "username": list_comments[x][6],
            "profile_picture": list_comments[x][7],
            "user_id": list_comments[x][8],
            "liked_dislike_status": already_liked_or_disliked
        }
    return {
        "status": 200, 
        "list_comments_posts": response
    }

def check_user_likes_post (post_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query_to_check_user_liked_post = """
    SELECT * FROM Posts_likes
    WHERE user_id = ? AND post_id = ?; 
    """
    cursor.execute(query_to_check_user_liked_post, (user_id, post_id))
    result_user_liked_post = cursor.fetchone()

    if result_user_liked_post == None:
        return {
            "status": 200,
            "message": "no like"
        }
    else: 
        return {
            "status": 200,
            "message": str(result_user_liked_post[3]),

        }

def calculate_like_dislike_ratio(table_name, post_comment_id, actual_post_comment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # calculate the likes a dislikes ratio
    query_calculate_likes_avg = f"""
    SELECT like_dislike FROM {table_name}
    WHERE {post_comment_id} = ?;
    """

    cursor.execute(query_calculate_likes_avg, (actual_post_comment_id))
    list_likes = cursor.fetchall()
    # the likes starts on 0 
    likes_per_comments = 0

    # goes to all likes and if like it sums by 1 if not it reduces by 1 
    for item in list_likes:
        if item[0] == 'd':
            likes_per_comments -= 1
        elif item[0] == 'l':
            likes_per_comments += 1

    return likes_per_comments

if __name__ == '__main__':
    app.run(debug=True)

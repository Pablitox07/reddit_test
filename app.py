from flask import Flask, render_template, request, jsonify
from datetime import datetime, timezone, timedelta
import pyodbc
import bcrypt
import jwt
import pytz
import os
from dotenv import load_dotenv
import traceback
import shutil
import re
import base64
load_dotenv()

db_password = os.environ.get('DB_PASSWORD')

connection_string = ()

SECRET_KEY = "vcwwue32jidnsv5ncdu1223349dbucwutang"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join("static","images")
app.config['UPLOAD_POST_IMAGES'] = os.path.join("static","post_images")
running_on = ""


if os.environ.get("WEBSITE_SITE_NAME"):
    print("Running in Azure App Service")
    running_on = "app service"
    connection_string = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=tcp:mysqltestpablitox.database.windows.net;"
        "Database=Reddit_db;"
        "Authentication=ActiveDirectoryMsi;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    app.config['UPLOAD_FOLDER'] = "/home/site/wwwroot/images"
    app.config['UPLOAD_POST_IMAGES'] = "/home/site/wwwroot/post_images"
    source = "/home/site/wwwroot/images"
    source_post_images = "/home/site/wwwroot/post_images"
    link_name = os.path.join("static", "images")
    link_name_post_images = os.path.join("static", "post_images")
    # If it's a real folder, delete it
    if os.path.isdir(link_name) and not os.path.islink(link_name):
        print(f"Removing existing folder at {link_name}")
        shutil.rmtree(link_name)
    
    if os.path.isdir(link_name_post_images) and not os.path.islink(link_name_post_images):
        print(f"Removing existing folder at {link_name_post_images}")
        shutil.rmtree(link_name_post_images)


    # Create the symlink if it doesn't exist
    if not os.path.islink(link_name):
        try:
            os.symlink(source, link_name)
            print(f"Symlink created: {link_name} → {source}")
        except Exception as e:
            print(f"Failed to create symlink: {e}")
    if not os.path.islink(link_name_post_images):
        try:
            os.symlink(source_post_images, link_name_post_images)
            print(f"Symlink created: {link_name_post_images} → {source_post_images}")
        except Exception as e:
            print(f"Failed to create symlink: {e}")

elif os.environ.get("COMPUTERNAME"):
    print(f"Running on a {os.environ.get("COMPUTERNAME")}")
    running_on = "vm"
    connection_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=mysqltestpablitox.database.windows.net;"
        "Database=Reddit_db;"
        "Uid=pablitox;"
        f"Pwd={db_password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
else:
    print("Running locally or unknown")
    running_on = "vm"
    connection_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=mysqltestpablitox.database.windows.net;"
        "Database=Reddit_db;"
        "Uid=pablitox;"
        f"Pwd={db_password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

try:
    conn = pyodbc.connect(connection_string)
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/load_home_posts')
def load_home_posts():
    response = {}
    conn = get_db_connection()
    cursor = conn.cursor()

    query_get_latest_10_posts = """
    SELECT TOP 10 Posts.*, Users.user_id, Users.profile_picture, Users.username
    FROM Posts
    JOIN Users ON Posts.user_id = Users.user_id
    ORDER BY Posts.created_at DESC;
    """

    cursor.execute(query_get_latest_10_posts)
    latest_posts = cursor.fetchall()
    for post_number in range(len(latest_posts)):
        current_post_id = latest_posts[post_number][0]
        query_calculate_number_comments = """
        SELECT COUNT(*) FROM Comments
        WHERE post_id = ?;
        """
        cursor.execute(query_calculate_number_comments, (current_post_id))
        post_number_comments = cursor.fetchone()

        post_number_likes = calculate_like_dislike_ratio("Posts_likes", "post_id", current_post_id)
        # 0 post_id, 1 user_id, 2 comments DO NOT USE THIS ONE, 3 Likes DO NOT USE, 4 post_text, 5 tittle, 6 category, 7 created_at, 8 profile_pic, 9 username
        response[str(post_number)] = {
            "post_id": latest_posts[post_number][0],
            "user_id": latest_posts[post_number][1],
            "post_text": latest_posts[post_number][4],
            "tittle": latest_posts[post_number][5],
            "category": latest_posts[post_number][6],
            "created_at": latest_posts[post_number][7],
            "profile_pic": latest_posts[post_number][9],
            "username": latest_posts[post_number][10],
            "number_comments": post_number_comments[0],
            "number_likes": post_number_likes
        }
    return response

@app.route('/load_top_post')
def load_top_post():
    response = {}
    response["top_posters"] = {}
    response["top_posts"] = {}

    conn = get_db_connection()
    cursor = conn.cursor()

    query_top_posters = """
    SELECT TOP 5 user_id, COUNT(*) AS total_posts
    FROM Posts
    GROUP BY user_id
    ORDER BY total_posts desc;
    """

    query_top_posts = """
    SELECT TOP 5
        Posts_likes.post_id,
        SUM(CASE WHEN Posts_likes.like_dislike = 'l' THEN 1 ELSE 0 END) -
        SUM(CASE WHEN Posts_likes.like_dislike = 'd' THEN 1 ELSE 0 END) AS net_likes,
        Posts.title,
        Posts.user_id,
	    Users.profile_picture
    FROM Posts_likes
    JOIN Posts ON Posts.post_id = Posts_likes.post_id
    JOIN Users ON Users.user_id = Posts.user_id
    GROUP BY Posts_likes.post_id, Posts.title, Posts.user_id, Users.profile_picture
    ORDER BY net_likes DESC;
    """

    cursor.execute(query_top_posters)
    top_posters = cursor.fetchall()

    cursor.execute(query_top_posts)
    top_posts = cursor.fetchall()


    for number_user in range(len(top_posters)):
        user_id = top_posters[number_user][0]
        total_posts = top_posters[number_user][1]
        query_get_top_poster_info = """
        SELECT username, profile_picture FROM Users
        WHERE user_id = ?;
        """

        cursor.execute(query_get_top_poster_info, (user_id))
        user_info = cursor.fetchone()
        response["top_posters"][number_user] = {
            "user_id" : user_id,
            "username": user_info[0], 
            "user_score": total_posts,
            "profile_pic": user_info[1]
        }

        response["top_posts"][number_user] = {
            "post_id" : top_posts[number_user][0], 
            "number_likes" : top_posts[number_user][1],
            "tittle":  top_posts[number_user][2],
            "user_id": top_posts[number_user][3],
            "profile_pic": top_posts[number_user][4]
        }

    return response
    
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
    user_id = request.base_url.split(('/'))[-1]
    return render_template("profile.html", user_id=user_id)


@app.route('/get_user_info', methods=["GET"])
def get_user_info():
    received_user_id = request.args.get('user')
    response = {}
    most_liked_list = []
    conn = get_db_connection()
    cursor = conn.cursor()
    query_user_info = """
    SELECT profile_picture, created_at, user_id, username FROM Users
    WHERE user_id = ?;
    """
    cursor.execute(query_user_info, (received_user_id))
    # ('the_beatles.png', datetime.datetime(2024, 11, 28, 17, 35, 35, 743000), 31)
    user_info = cursor.fetchone()
    
    query_get_first_post = """
    SELECT post_id, title FROM Posts
    WHERE user_id = ?
    ORDER BY created_at ASC;
    """
    cursor.execute(query_get_first_post, (received_user_id))
    posts_info = cursor.fetchall()
    # [(19, 'The Beatles: A Timeless Legacy')] [0] is the first post
    if posts_info == []:
        return {
            "username": user_info[3],
            "profile_pic": user_info[0],
            "joined_on": user_info[1],
            "first_post_title": "no posts yet",
            "first_post_id": "no posts yet",
            "latest_post_title":"no posts yet",
            "latest_post_id":"no posts yet",
            "popular_post_title": "no posts yet",
            "popular_post_id": "no posts yet",
        }
    else:
        for post in posts_info:
            query_get_likes = """
            SELECT     
                SUM(CASE WHEN Posts_likes.like_dislike = 'l' THEN 1 ELSE 0 END) -
                SUM(CASE WHEN Posts_likes.like_dislike = 'd' THEN 1 ELSE 0 END) AS net_likes 
            FROM Posts_likes
            WHERE post_id = ?;
            """
            cursor.execute(query_get_likes, (post[0]))
            current_post_likes = cursor.fetchone()
            if current_post_likes[0] == None:
                most_liked_list.append(0)
            else:
                most_liked_list.append(current_post_likes[0])


    if max(most_liked_list) == 0:
        return {
            "username": user_info[3],
            "profile_pic": user_info[0],
            "joined_on": user_info[1],
            "first_post_title": posts_info[0][1],
            "first_post_id": posts_info[0][0],
            "latest_post_title":posts_info[-1][1],
            "latest_post_id":posts_info[-1][0],
            "popular_post_title": "no likes yet",
            "popular_post_id": "no likes yet",
        }

    else:
        popular_post_index = most_liked_list.index(max(most_liked_list))
        return {
            "username": user_info[3],
            "profile_pic": user_info[0],
            "joined_on": user_info[1],
            "first_post_title": posts_info[0][1],
            "first_post_id": posts_info[0][0],
            "latest_post_title":posts_info[-1][1],
            "latest_post_id":posts_info[-1][0],
            "popular_post_title": posts_info[popular_post_index][1],
            "popular_post_id": posts_info[popular_post_index][0],
        }

@app.route('/change_profile_pic', methods=["POST"])
def change_profile_pic():
    user_to_be_change = request.args.get('user')
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith("Bearer "):
        return {"message": "Missing or invalid token.", "status": 401}, 401
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        if 'file' not in request.files:
            return "No file part in the request", 400

        file = request.files['file']
        if file.filename == '':
            return "No file selected", 400

        file_format = file.filename.split(".")[-1]
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"user_{user_to_be_change}.{file_format}"))
        query_modify_profile_pic = """
        UPDATE Users
        SET profile_picture = ?
        WHERE user_id = ?;
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(query_modify_profile_pic, (f"user_{user_to_be_change}.{file_format}", user_to_be_change))
        conn.commit()
        conn.close()

        return {"message": f"user_{user_to_be_change}.{file_format}", "status": 200}, 200
    except jwt.ExpiredSignatureError as e:
        print(e)
        return {"message": "Token has expired.", "status": 401}, 401
    except jwt.InvalidTokenError as e:
        print(e)
        return {"message": "Invalid token.", "status": 401}, 401
    except Exception as e:
        print(f"Error: {e}")
        return {"message": "An unexpected error occurred. Please try again later.", "status": 500}, 500


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
    # Get needed info from request JSON payload
    received_userid = request.json.get('userid')
    received_title = request.json.get("title")
    received_posts_text = request.json.get("text")
    received_category = request.json.get("category")
    
    # Get the Authorization header from the request
    auth_header = request.headers.get('Authorization')

    # Check if the Authorization header is missing or improperly formatted
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"message": "Missing or invalid token.", "status": 401}, 401
    
    # Extract the token from the Authorization header
    token = auth_header.split(" ")[1]
        
    try:
        # Decode and validate the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find all base64-encoded images in the post content
        img_tags = re.findall(r'<img[^>]+src="(data:image/[^"]+)"', received_posts_text)

        # If there are embedded images in the post content
        if img_tags != []:
            # Insert a temporary post with placeholder content ("template")
            query = """
            INSERT INTO Posts (user_id, content, title, category)
            VALUES 
                (?, ?, ?, ?)
            """
            cursor.execute(query, (received_userid, "template", received_title, received_category))
            conn.commit()

            # Retrieve the newly inserted post to get its ID
            query_get_post_id = """
            SELECT * FROM Posts
            WHERE content = ? AND title = ? AND user_id = ?;
            """
            cursor.execute(query_get_post_id, ("template", received_title, received_userid))
            new_post_row = cursor.fetchone()
            post_id = new_post_row[0]

            NUM = 0  # Image counter to create unique filenames
            for base64_image in img_tags:
                # Split base64 image data into header and actual image data
                header, encoded = base64_image.split(',', 1)  
                # Get file extension from the header
                file_ext = header.split('/')[1].split(';')[0]
                # Decode the base64-encoded image
                binary_data = base64.b64decode(encoded)
                # Generate a unique filename and define the file path
                filename = f'post_{post_id}_{NUM}.{file_ext}'
                filepath = os.path.join(app.config['UPLOAD_POST_IMAGES'], filename)

                # Save the image to the file system
                with open(filepath, 'wb') as f:
                    f.write(binary_data)

                # Replace base64 string in content with URL to saved image
                image_url = f'/static/post_images/{filename}'
                received_posts_text = received_posts_text.replace(base64_image, image_url)
                NUM += 1

            # Update the post with the actual content including image URLs
            update_content = """
            UPDATE Posts
            SET content = ?
            WHERE post_id = ?;
            """
            cursor.execute(update_content, (received_posts_text, post_id))
            conn.commit()

            # Return success message and new post ID
            return {"message": "Success", "post_id": new_post_row[0]}
        
        else: 
            # If there are no images, insert the post directly
            query = """
            INSERT INTO Posts (user_id, content, title, category)
            VALUES 
                (?, ?, ?, ?)
            """
            cursor.execute(query, (received_userid, received_posts_text, received_title, received_category))
            conn.commit()

            # Retrieve the inserted post to get its ID
            query_get_post_id = """
            SELECT * FROM Posts
            WHERE content = ? AND title = ? AND user_id = ?;
            """
            cursor.execute(query_get_post_id, (received_posts_text, received_title, received_userid))
            new_post_row = cursor.fetchone()

            # Return success message and new post ID
            return {"message": "Success", "post_id": new_post_row[0]}
    
    # Handle expired token error
    except jwt.ExpiredSignatureError as e:
        print(e)
        return {"message": "Token has expired.", "status": 401}, 401

    # Handle invalid token error
    except jwt.InvalidTokenError as e:
        print(e)
        return {"message": "Invalid token.", "status": 401}, 401

    # Handle any other unexpected errors
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

@app.route('/categories/<category>', methods=['GET'])
def categories(category):
    return render_template("category.html", category=category.replace("_", " "))

@app.route('/category_posts', methods=['GET'])
def category_posts():
    received_category_name = request.args.get('category_name')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT TOP 10 post_id, Posts.user_id, content, title, Posts.created_at, Users.username, Users.profile_picture FROM Posts
    JOIN Users ON Posts.user_id = Users.user_id
    WHERE category = ?
    ORDER BY created_at asc;
    """
    cursor.execute(query, (received_category_name))
    list_posts_per_category =  cursor.fetchall()
    if list_posts_per_category == []:
        return {"message": "No posts yet!", "status": 200}
    else:
        result = {
            "message": "posts found", 
            "status": 200,
            "posts": []
        }
        for number_post in range(len(list_posts_per_category)):
            post_likes = calculate_like_dislike_ratio("Posts_likes", "post_id", list_posts_per_category[number_post][0])
            query_number_comments = """
            SELECT COUNT(*) FROM Comments
            Where post_id = ?;
            """
            cursor.execute(query_number_comments, (list_posts_per_category[number_post][0]))
            number_comments =  cursor.fetchone()
            result["posts"].append({
                "post_id": list_posts_per_category[number_post][0],
                "user_id": list_posts_per_category[number_post][1],
                "content": list_posts_per_category[number_post][2],
                "title": list_posts_per_category[number_post][3],
                "created_at": list_posts_per_category[number_post][4],
                "user_name" : list_posts_per_category[number_post][5],
                "profile_pic": list_posts_per_category[number_post][6],
                "number_likes": post_likes,
                "number_comments": number_comments[0]
            })
        return result




# ------------------- Functions below here ----------------------------

def get_db_connection():
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

def check_user_authentication(token):
    try:
        # Decode the JWT and return the payload
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True

    except jwt.ExpiredSignatureError:
        return {"message": "Token has expired.", "status": 401}, 401

    except jwt.InvalidTokenError:
        return {"message": "Invalid token.", "status": 401}, 401

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"message": "Authentication failed due to server error.", "status": 500}, 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)

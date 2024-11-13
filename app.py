from flask import Flask, render_template

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
if __name__ == '__main__':
    app.run(debug=True)

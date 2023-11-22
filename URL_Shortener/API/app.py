import sqlite3  # for database operations, a database engine, a relational database management system
import random
import string  # provides a collection of string constants(ASCII characters, digits, lowercase and uppercase letters,
# and various string-related constants)

import segno  # a python library for generating qr codes

from flask import Flask, request, redirect, render_template, url_for, flash, session

# Flask: This is the main class of the Flask framework, represents a Flask web application, creating an instance of
# this class to define and run web application

# request: an object that allows you to access data submitted in forms.

# redirect: a function used to redirect the user's browser to a different URL, used for handling a certain route.

# render_template: a function used to render HTML templates, allowing you to insert data into the HTML.

# url_for: a function that generates a URL for a given endpoint, used to redirect to a specific route.

# flash: a mechanism for storing a message in one view, used to display messages to the user after a certain action.

# session: a dictionary-like object that allows you to keep user-specific information.


from werkzeug.security import check_password_hash, generate_password_hash
# Werkzeug is utility library for WSGI that provides security related functions


from flask_login import LoginManager, UserMixin, login_user, login_required
# Flask-Login is an extension for Flask

# LoginManager: This class is part of Flask-Login, handles user authentication, responsible for
# managing the user session, handles the session management, and provides a way to load users from an ID.

# UserMixin: This class is provided by Flask-Login and helps simplify the integration of user class with Flask-Login.

# login_user: a function used to log a user in. It takes a user object as an argument and records the user's ID in the
# session, making the user accessible in subsequent requests.

# login_required: a decorator provided by Flask-Login. When applied to a view function, it ensures that the user must
# be logged in to access that particular view, if a user is not logged in, they are redirected to the login page.

# ----These components collectively contribute to the implementation of user authentication and session management in a
# Flask application using Flask-Login.------

# -------------------------------------------------------------------


app = Flask(__name__)  # initializing flask project, creating a Flask application instance named 'app'
# Flask(__name__) tells Flask to look for resources (templates, static files, etc.) relative to the current module.

app.secret_key = 'your_secret_key'  # a secret key for the Flask application to ensure the integrity of session data

login_manager = LoginManager(app)  # creating a LoginManager object, the LoginManager is used to manage user
# authentication and session management.

login_manager.login_view = 'signin'  # specifying the route where Flask-Login should redirect users if they are
# not authenticated. Here, I have set it to 'signin', meaning users will be redirected to the 'signin' route.


class User(UserMixin):  # creating User class that inherits from UserMixin of Flask-Login
    def __init__(self, user_id):  # a constructor (__init__ method) that takes a user_id as a parameter.
        self.id = user_id  # initializing an attribute self.id with the provided user_id.

    def get_id(self):  # User class defines a method named get_id.
        return str(self.id)   # returns the string representation of the user_id
    # Flask-Login requires this method to return a unique identifier for the user.


@login_manager.user_loader  # tells Flask-Login how to load a user from the user ID stored in the session.
def load_user(user_id):
    # a function that creates and returns a User instance based on a given user_id
    # This function is a callback required by Flask-Login to load a user from the user ID stored in the session.
    # It takes a user_id as a parameter and returns an instance of the User class with the provided user_id.
    return User(user_id)

# the above code sets up a Flask application, configures it for user authentication using Flask-Login,
# defines a User class for managing user objects, and specifies how to load a user when needed.
# The secret key is used for session security, and the login manager helps in handling user authentication.


@app.route('/')  # a decorator to specify that the associated function (home()) should be called when the user visits
# the root URL of the application.
def home():  # function is executed when a user accesses the root URL
    return render_template("main.html")  # Renders the main.html template for the home page.


@app.route('/signup', methods=["GET", "POST"])  # a route for user signup with support for both GET and POST methods
def signup():
    conn = sqlite3.connect("url_shortener.db")  # connecting to the SQLite database
    # Establishing a connection to the SQLite database named "url_shortener.db"
    c = conn.cursor()

    # creating users and url_mappings tables if they don't exist
    c.execute(
        'CREATE TABLE IF NOT EXISTS users '
        '(ID INTEGER PRIMARY KEY AUTOINCREMENT, NAME TEXT, EMAIL TEXT UNIQUE, PASSWORD TEXT)'
    )
    c.execute(
        'CREATE TABLE IF NOT EXISTS url_mappings '
        '(URL_ID INTEGER PRIMARY KEY AUTOINCREMENT,  USER_ID INTEGER, LONG_URL TEXT, SHORT_URL TEXT, '
        'FOREIGN KEY (USER_ID) REFERENCES users(ID))'
    )
    # committing the changes to the database and close the connection
    conn.commit()
    conn.close()

    if request.method == "POST":  # check if the request method is POST

        # retrieve user input from the signup html form
        name = request.form.get('NAME')
        email = request.form.get('EMAIL')
        password = request.form.get('PASSWORD')
        hashed_password = generate_password_hash(password)
        # generate_password_hash: This function is used to hash a password

        try:
            conn = sqlite3.connect('url_shortener.db')  # connect to the database again
            cursor = conn.cursor()
            # Checks if a user with the provided email already exists in the database.
            cursor.execute("SELECT * FROM users WHERE EMAIL = ?", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                # If the email is already in use, shows an error message and redirects to the signup page.
                flash("Email already in use. Please use a different email.")
                return redirect(url_for('signup'))
            else:
                # Inserts a new user into the users table if the email is unique.
                cursor.execute("INSERT INTO users (NAME, EMAIL, PASSWORD) VALUES (?, ?, ?)",
                               (name, email, hashed_password))
                conn.commit()
                cursor.close()   # close the cursor and connection
                conn.close()

                # Sets a session flag indicating successful signup and redirects to the signup success page.
                session['signed_up'] = True

                # Redirect to the signup success page
                return redirect(url_for('signup_success'))

        except Exception as e:
            flash("An error occurred during signup. Please try again.")  # Flash an error message
            print("Error during signup:", str(e))  # Print the error for debugging

    return render_template("signup.html")


@app.route('/signin', methods=["GET", "POST"])  # Sign-in route supporting both GET and POST methods
def signin():
    if request.method == "POST":  # handling form submission (if method is POST)

        # retrieving user input (email and password) from the signin form.
        email = request.form.get('EMAIL')
        password = request.form.get('PASSWORD')

        # connecting to the db, creating cursor object
        conn = sqlite3.connect('url_shortener.db')
        cursor = conn.cursor()

        cursor.execute("SELECT ID, PASSWORD FROM users WHERE EMAIL = ?", (email,))
        user_data = cursor.fetchone()   # Fetch user data based on the provided email

        cursor.close()
        conn.close()

        if user_data:  # checks if user data was successfully retrieved from the database. If a user with the provided
            # email exists, the code proceeds

            stored_hash = user_data[1]  # Retrieve the hashed password from the database

            # Checks if the entered password matches the stored hashed password in the database.
            if stored_hash and check_password_hash(stored_hash, password):

                # If the password is correct, creates a user object and logs in the user using Flask-Login.
                user = User(user_data[0])  # Create an instance of the User class
                login_user(user)  # Log in the user

                session['user_id'] = user_data[0]  # Stores the user's ID in the session and redirects to the URL
                # shortener page.
                return redirect(url_for('urlshortner'))
            else:
                flash("Invalid username or password")  # Flash an error message if the password is incorrect and
                # redirect to the signin page
                return redirect(url_for("signin"))
        else:
            # If the user is not found, shows an error message and redirects to the signin page.
            flash("Invalid username or password")  # Flash an error message if the user is not found
            return redirect(url_for("signin"))

    return render_template("signin.html")  # Render the signin.html template for GET requests


@app.route('/signup-success')
def signup_success():  # a route that displays success message and asks user if they want to sign in or go to home page
    return render_template('signup_success.html')


@app.route('/logout', methods=["GET", "POST"])  # a route to log out the user & redirect them to home page
@login_required
def logout():
    session.clear()  # resetting the information stored about a user during their visit to website
    return redirect(url_for('home'))  # Redirects the user to the home page after logging out.


def generate_random_short_code():  # Function to generate a random string of 6 uppercase letters
    characters = string.ascii_uppercase  # generating a string containing all uppercase letters
    return ''.join(random.choice(characters) for _ in range(6))
    # Generates a random string of 6 uppercase letters by choosing characters randomly from the string.


@app.route('/urlshortener', methods=["GET", "POST"])  # a route to go to the url shortener page
# @login_required
def urlshortner():
    return render_template('index.html')  # Renders the index.html template, displaying the URL shortener page.


@app.route('/shorten-url', methods=['POST'])  # Shorten url endpoint route
@login_required
def shorten_url_endpoint():
    if request.method == "POST":  # Handling form submission if method is POST

        # Retrieving user input (original URL and custom short code) from the form.
        original_url = request.form.get('original_url')
        custom_short_code = request.form.get('custom_short_code')

        user_id = session.get('user_id')  # Retrieves the user's ID from the session.

        if not user_id:
            flash("User not logged in.")
            # Shows an error message and redirects to the signin page if the user is not logged in.
            return redirect(url_for('signin'))

        conn = sqlite3.connect('url_shortener.db')
        cursor = conn.cursor()

        try:
            if custom_short_code:  # checks if a custom short code was provided by the user

                # database query to check if a mapping with the given custom_short_code already exists for the
                # specific user
                check_existing_mapping_query = "SELECT * FROM url_mappings WHERE USER_ID = ? AND SHORT_URL = ?"
                existing_mapping = cursor.execute(check_existing_mapping_query,
                                                  (user_id, f'https://short-url/{custom_short_code}')).fetchone()
                if existing_mapping:
                    flash(f"Short code '{custom_short_code}' is already in use for your account. "
                          f"Please choose another.")
                    return redirect(request.referrer)  # Redirect back to the same page to try again

            # If a random short code or custom code not valid, generate a new one
            valid_short_code_found = False
            short_code = custom_short_code or generate_random_short_code()

            while not valid_short_code_found:
                # Generates a new short code if using a random short code or the custom code is not valid
                existing_mapping = cursor.execute("SELECT * FROM url_mappings WHERE USER_ID = ? AND SHORT_URL = ?",
                                                  (user_id, f'https://short-url/{short_code}')).fetchone()

                if not existing_mapping:
                    valid_short_code_found = True
                else:
                    short_code = generate_random_short_code()

            short_url = f'https://short-url/{short_code}'  # Creates the short URL using the generated short code.

            insert_mapping_query = "INSERT INTO url_mappings (USER_ID, LONG_URL, SHORT_URL) VALUES (?, ?, ?)"
            cursor.execute(insert_mapping_query, (user_id, original_url, short_url))
            conn.commit()

            flash("URL shortened successfully!")
            # Shows a success message, renders the URL shortener page with the shortened URL.
            return render_template('index.html', short_url=short_url)

        except sqlite3.Error as e:
            flash("An error occurred while processing your request.")
            print("SQLite error:", e)

        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('signin'))


@app.route('/test-url', methods=['GET', 'POST'])  # a route to test if a short url exists in db
@login_required  # Ensures that the user must be logged in to access this route.
def test_url():
    if request.method == 'POST':  # Checks if the form was submitted (POST request).
        test_url1 = request.form.get('test-url')  # Retrieve the short URL to be tested from the form data

        conn = sqlite3.connect('url_shortener.db')  # Connect to the SQLite database
        cursor = conn.cursor()

        user_id = session.get('user_id')  # Retrieve the user ID from the session

        print(f"User ID from session: {user_id}")

        if user_id:
            # Checks if the user is logged in.
            user_id = int(user_id)  # Convert user_id to an integer if it's stored as a string

            # Executes a SQL query to check if the provided short URL exists in the database for the specific user.
            cursor.execute("SELECT SHORT_URL FROM url_mappings WHERE USER_ID = ? AND SHORT_URL = ?",
                           (user_id, test_url1))

            short_url = cursor.fetchone()  # Fetch the result (short URL) from the database

            print(f"Short URL from database: {short_url}")

            # Close the cursor and database connection
            cursor.close()
            conn.close()

            if short_url:
                # If the short URL exists, render the success.html template
                print("Rendering success.html")
                return render_template('success.html')
            else:
                # If the short URL doesn't exist, render the failure.html template
                print("Rendering failure.html")
                return render_template('failure.html')
        else:
            # If the user is not logged in, redirect to the signin route
            flash("User not logged in.")
            return redirect(url_for('signin'))
    # Render the test_url.html template for GET requests
    return render_template('test_url.html')


def list_urls_for_user(user_id):
    conn = sqlite3.connect('url_shortener.db')  # Connect to the SQLite database
    cursor = conn.cursor()

    # Retrieve all short URLs for the specified user from the database
    cursor.execute("SELECT SHORT_URL FROM url_mappings WHERE USER_ID = ?", (user_id,))

    # Extract short URLs from the fetched data
    short_urls = [url[0] for url in cursor.fetchall()]

    # Close the cursor and database connection
    cursor.close()
    conn.close()

    # Return the list of short URLs for the user
    return short_urls


@app.route('/list-urls', methods=['GET'])  # a route to view lists of a particular user
@login_required
def list_urls():
    user_id = session['user_id']  # Retrieve the user ID from the session

    if user_id:  # Checks if the user is logged in.
        short_urls = list_urls_for_user(user_id)   # Get the list of short URLs for the user
        # Calls the list_urls_for_user function to retrieve the list of short URLs for the user.

        # Renders the list_urls.html template, passing the list of short URLs.
        return render_template('lists_urls.html', short_urls=short_urls)
    else:
        # Redirects to the signin page with a flash message if the user is not logged in.
        flash("User not logged in.")
        return redirect(url_for('signin'))


def get_original_url(full_shortened_link, user_id):
    # a function to retrieve the original URL from the database based on the short URL and user ID.
    conn = sqlite3.connect('url_shortener.db')
    cursor = conn.cursor()

    # Executes a SQL query to retrieve the original URL based on the short URL and user ID.
    cursor.execute("SELECT LONG_URL FROM url_mappings WHERE SHORT_URL = ? AND USER_ID = ?", (full_shortened_link,
                                                                                             user_id))
    result = cursor.fetchone()

    # Check if a result is found, and extract the original URL
    if result:
        original_url = result[0]
    else:
        original_url = None

    conn.close()
    return original_url


@app.route('/redirect', methods=['GET', 'POST'])  # a route to redirect user to their original url using short url
@login_required  # Ensures that the user must be logged in to access this route.
def redirect_to_original_page():
    user_id = session['user_id']  # Retrieve the user ID from the session

    if request.method == 'POST':
        if user_id:

            # Get the short URL from the form submission
            short_url = request.form['shortURL']

            # Retrieve the original URL based on the short URL and user ID
            original_url = get_original_url(short_url, user_id)

            if original_url:
                print("Original URL Retrieved:", original_url)
                return redirect(original_url)  # Redirects the user to their original URL.
            else:
                return render_template('redirect.html',
                                       error="The provided short URL does not correspond to a valid link.")
        else:
            flash("User not logged in")
            return redirect(url_for('signin'))
    else:
        return render_template('redirect.html')  # Renders the redirect.html template for GET requests.


def get_long_url(short_url, user_id):
    # Defines a function to retrieve the original (long) URL from the database based on the short URL and user ID.
    conn = sqlite3.connect('url_shortener.db')
    cursor = conn.cursor()

    # Retrieve the original URL from the database based on the short URL and user ID
    cursor.execute("SELECT LONG_URL FROM url_mappings WHERE USER_ID = ? AND SHORT_URL = ?", (user_id, short_url))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:  # Check if a result is found and extract the original URL
        return result[0]
    else:
        return None


@app.route('/generate-qr-code', methods=['POST'])
@login_required
def generate_qr_code():  # Defines a route for generating a QR code based on a short URL.
    user_id = session['user_id']  # Retrieve the user ID from the session

    if user_id:  # Get the full short URL from the form submission
        short_url = request.form.get('full_short_url')

        long_url = get_long_url(short_url, user_id)  # Retrieve the long URL based on the short URL and user ID

        if long_url:  # Generate a QR code for the long URL
            qr = segno.make(long_url)
            image_path = f"./static/qr_codes/{user_id}_qr_code.png"  # a unique filename for each user

            qr.save(image_path)  # Save the QR code image

            # Render the redirect.html template with the QR code image
            return render_template('redirect.html', qr_image=image_path)
        else:
            return render_template('redirect.html', error="Short URL not valid.")
    else:
        return render_template('redirect.html', error="User not logged in.")


@app.route('/delete-url', methods=['GET', 'POST'])  # a route to delete a particular short url stored in db
@login_required
def delete_url_mapping():
    user_id = session['user_id']  # Retrieve the user ID from the session

    if request.method == 'GET':
        return render_template('delete_url.html')
    elif request.method == 'POST':
        if user_id:

            # Get the short URL to delete from the form submission
            short_url_to_delete = request.form['short-url-to-delete']

            # if the URL to delete belongs to the signed-in user
            conn = sqlite3.connect('url_shortener.db')
            cursor = conn.cursor()
            cursor.execute("SELECT SHORT_URL FROM url_mappings WHERE USER_ID = ? AND SHORT_URL = ?",
                           (user_id, short_url_to_delete))
            url = cursor.fetchone()

            if url:
                # Delete the URL mapping
                cursor.execute("DELETE FROM url_mappings WHERE USER_ID = ? AND SHORT_URL = ?",
                               (user_id, short_url_to_delete))
                conn.commit()
                conn.close()
                return "Short URL deleted successfully"
            else:
                conn.close()
                return "Unauthorized deletion: URL doesn't belong to the user", 401
        return "Unauthorized deletion", 401  # Returns an unauthorized status if the user is not signed in.


if __name__ == '__main__':  # ensuring that the development server is only started when the script is executed directly,
    # not when it's imported as a module.
    app.run(debug=True)

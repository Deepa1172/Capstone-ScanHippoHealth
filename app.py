from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import numpy as np
import os
import tensorflow as tf
import bcrypt
from dotenv import load_dotenv
from helper import convert_image_to_numpy, save_image, save_mask, get_pred

app = Flask(__name__)

load_dotenv()

app.secret_key = os.getenv('APP_SECRET_KEY')

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)

current_username = ''


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            hashed_password_from_db = account['password']
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password_from_db.encode('utf-8')):
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                msg = 'Logged in successfully !'
                global current_username
                current_username = username
                return render_template('index.html', username=username)
            else:
                msg = 'Incorrect Password!'
        else:
            msg = 'Incorrect Username!'
    return render_template('login.html', message=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        plain_password = request.form['password']
        email = request.form['email']
        hashed_password = bcrypt.hashpw(
            plain_password.encode('utf-8'), bcrypt.gensalt())
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'^[A-Za-z0-9_]+$', username):
            msg = 'Username must contain only characters, numbers, and underscores!'
        elif not username or not plain_password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute(
                'INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, hashed_password, email, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', message=msg)


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if 'mri_scan' not in request.files:
        return jsonify({'error': 'No test image provided'})

    f = request.files['mri_scan']
    print("current path")
    path_exists = False
    basepath = os.path.dirname(__file__)
    print("current path", basepath)
    filepath = os.path.join(basepath, 'uploads', f.filename)
    print("upload folder is ", filepath)
    f.save(filepath)
    if path_exists:
        test_img = convert_image_to_numpy(filepath)
        test_img_input = np.expand_dims(test_img, axis=0)
        my_model = tf.keras.saving.load_model('3d_unet_v2.hdf5')
        test_prediction = my_model.predict(test_img_input)
        test_prediction_argmax = np.argmax(test_prediction, axis=4)[0, :, :, :]
        save_mask(test_prediction_argmax)
        save_image(test_img)
    num = get_pred(f.filename)
    output_image_path = 'static/assets/images/image_' + str(num) + '.png'
    output_mask_path = 'static/assets/predictions/image_' + str(num) + '.png'
    print(output_image_path)
    return render_template('index.html', image_path=output_image_path, mask_path=output_mask_path, username=current_username)


if __name__ == "__main__":
    app.run()

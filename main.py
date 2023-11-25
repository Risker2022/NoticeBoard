from flask import Flask, render_template, url_for, request, redirect

from hashlib import sha256
import logging
import json

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
json_file = "database.json"


def read_file(file="database.json"):
    with open(file, 'r') as file:
        return json.load(file)


def update_file(new_data, file='database.json'):
    with open(file, 'w') as file:
        json.dump(new_data, file, indent=2)


def hash_obj(obj):
    hash_object = sha256()
    hash_object.update(obj.encode("utf-8"))
    return hash_object.hexdigest()


data = read_file()
notices = data["announcements"]
groups = data["groups"]
accounts = data["accounts"]
my_notices = {}

user = None
failed = False


@app.route("/")
def starter():
    return redirect(url_for('home'))


@app.route("/home")
def home():
    important = {title: specifications for title, specifications in notices.items()
                 if specifications[-1] == "True"}
    unimportant = {title: specifications for title, specifications in notices.items()
                   if specifications[-1] == "False"}
    reformatted = important
    reformatted.update(unimportant)
    return render_template('home.html', notices=reformatted, groups=groups, logined=user)


@app.route("/all")
def announcements():
    important = {title: specifications for title, specifications in notices.items()
                 if specifications[-1] == "True"}
    unimportant = {title: specifications for title, specifications in notices.items()
                   if specifications[-1] == "False"}
    reformatted = important
    reformatted.update(unimportant)
    return render_template("all.html", notices=reformatted, logined=user)


@app.route("/search", methods=["POST"])
def search():
    searched_word = request.form['search']
    searched_notice = {title: notices[title] for title in notices
                       if searched_word in title}
    return render_template("search.html", notices=searched_notice, logined=user)


@app.route("/login", methods=['GET', 'POST'])
def login():
    global failed, user, my_notices

    if request.method == 'POST':

        username = request.form['username']
        password = hash_obj(request.form['password'])

        if username in accounts:
            if accounts[username] == password:
                user = username
                my_notices = {title: specifications for title, specifications in notices.items()
                              if specifications[1] == user}
                return redirect(url_for('home'))
        failed = True

    return render_template('login.html', failed=failed)


@app.route("/signup", methods=['GET', 'POST'])
def sign_up():
    global data, accounts, failed, user

    if request.method == 'POST':

        new_username = request.form['username']
        new_password = hash_obj(request.form['password'])
        confirm_pass = hash_obj(request.form['com_password'])

        if new_username not in accounts and confirm_pass == new_password:
            accounts[new_username] = new_password
            data["accounts"] = accounts
            update_file(data)

            user = new_username

            return redirect(url_for('home'))

    return render_template("signup.html")


@app.route("/my_account")
def my_account():
    if user:
        important = {title: specifications for title, specifications in my_notices.items()
                     if specifications[-1] == "True"}
        unimportant = {title: specifications for title, specifications in my_notices.items()
                       if specifications[-1] == "False"}
        reformatted = important
        reformatted.update(unimportant)
        return render_template('my_account.html', notices=reformatted, logined=user)
    return redirect(url_for('login'))


@app.route('/my_account/edit/<title>', methods=["GET", "POST"])
def edit(title):
    global data, notices, my_notices
    if user:
        if request.method == "POST":
            selected = request.form["announcement"]
            title = request.form["title"]
            descrip = request.form["descrip"]
            importance = request.form["importance"]
            if title not in notices:
                temp = [selected, notices[selected]]
                del my_notices[selected]
                del notices[selected]
                if title:
                    temp[0] = title
                if descrip:
                    temp[1][0] = descrip
                if importance.lower() == "important":
                    temp[1][2] = 'True'
                elif importance.lower() == "unimportant":
                    temp[1][2] = 'False'
                notices.update({temp[0]: temp[1]})
                my_notices.update({temp[0]: temp[1]})
                data["announcements"] = notices
                update_file(data)
                return redirect(url_for('my_account'))
        return render_template('edit.html', notices=my_notices, target=title, logined=user)
    return redirect(url_for('login'))


@app.route('/my_account/delete/<title>')
def delete(title):
    global data, notices, my_notices
    if user:
        if title in my_notices:
            del notices[title]
            del my_notices[title]
            data["announcements"] = notices
            update_file(data)
        return redirect(url_for('my_account'))
    return redirect(url_for('login'))


@app.route('/my_account/add', methods=["GET", "POST"])
def add():
    global data, notices, my_notices
    if user:
        if request.method == "POST":
            title = request.form['title']
            descrip = request.form['descrip']
            importance = request.form['importance']
            if title not in notices:
                if importance == 'Important':
                    importance = 'True'
                else:
                    importance = 'False'
                notices.update({title: [descrip, user, importance]})
                my_notices.update({title: [descrip, user, importance]})
                data["announcements"] = notices
                update_file(data)
                return redirect(url_for('my_account'))
        return render_template('add.html', logined=user)
    return redirect(url_for('login'))


@app.route('/my_account/change_pass', methods=["GET", "POST"])
def change_password():
    global data, accounts
    if user:
        if request.method == 'POST':
            curr_username = request.form["curr_user"]
            curr_pass = hash_obj(request.form["curr_pass"])
            new_pass = hash_obj(request.form["new_pass"])
            com_new_pass = hash_obj(request.form["com_new_pass"])

            if curr_username == user and curr_pass == accounts[user] and new_pass == com_new_pass:
                accounts[curr_username] = new_pass
                data["accounts"] = accounts
                update_file(data)
                return redirect(url_for("my_account"))

        return render_template('change_pass.html', logined=user)

    return redirect(url_for('login'))


@app.route('/my_account/change_user', methods=['GET', 'POST'])
def change_user():
    global user, data, accounts, notices, my_notices
    if user:
        if request.method == "POST":
            old_username = request.form["curr_user"]
            new_username = request.form["new_user"]
            com_new_user = request.form["com_new_user"]
            if old_username == user and new_username == com_new_user:
                accounts.update({new_username: accounts[user]})
                del accounts[user]
                user = new_username

                for title, specifications in notices.items():
                    if specifications[1] == old_username:
                        notices[title] = [specifications[0], user, specifications[2]]

                my_notices = {title: specifications for title, specifications in notices.items()
                              if specifications[1] == user}

                data["announcements"], data["accounts"] = notices, accounts
                update_file(data)
                return redirect(url_for("my_account"))
        return render_template('change_user.html', logined=user)
    return redirect(url_for('login'))


@app.route("/my_account/del_acc")
def delete_account():
    global data, accounts, notices, my_notices, user
    if user:
        for title in my_notices:
            del notices[title]
        my_notices = {}

        del accounts[user]
        user = None
        data["announcements"], data["accounts"] = notices, accounts
        update_file(data)
        return redirect(url_for("home"))

    return redirect(url_for('login'))


@app.route("/logout")
def logout():
    global user, my_notices
    if user:
        user = None
        my_notices = {}
        return redirect(url_for("home"))
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

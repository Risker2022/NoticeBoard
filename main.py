from flask import Flask, render_template, url_for, request, redirect, session

from functools import wraps
from hashlib import sha256
import logging
import json

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
app.secret_key = b'vrfjhbvwbuvg83'
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
my_groups ={}

failed = False

def loginCheck(func):
    @wraps(func)
    def check(*args, **kwargs):
        if session.get('name'):
            return func(*args, **kwargs)
        return redirect(url_for("login"))
        
    return check


@app.route("/")
def starter():
    return redirect(url_for('home'))


@app.route("/home")
def home():
    updated_notices = {
        title: specifications
        for title, specifications in notices.items()
        if (
            specifications[-1] == "False"
            and not specifications[2]
            )
        }
    important = {
        title: specifications
        for title, specifications in notices.items()
        if specifications[-1] == "True"
        }
    return render_template('home.html', important=important, notices=updated_notices, groups=groups, logined=session.get('name'))


@app.route("/all")
def announcements():
    important = {title: specifications for title, specifications in notices.items()
                 if specifications[-1] == "True"}
    unimportant = {title: specifications for title, specifications in notices.items()
                   if specifications[-1] == "False"}
    reformatted = important
    reformatted.update(unimportant)
    return render_template("all.html", notices=reformatted, logined=session.get('name'))


@app.route("/groups")
def group_page():
    return render_template("groups.html", groups=groups, logined=session.get('name'))


@app.route("/groups/<title>")
def group_content(title):
    group_notices = {
        notice: details 
        for notice, details in notices.items()
        if (
            details[2] == title
        )
    }
    if title == "Important":
        group_notices = {notice: details for notice, details in notices.items()
                         if details[-1] == "True"}
    return render_template("group_items.html", notices=group_notices, group_name=title, logined=session.get('name'))


@app.route("/search", methods=["POST"])
def search():
    searched_word = request.form['search']
    searched_group = {title: groups[title] for title in groups if searched_word in title}
    searched_notice = {title: notices[title] for title in notices
                       if searched_word in title}
    return render_template("search.html", groups=searched_group, notices=searched_notice, logined=session.get('name'))


@app.route("/login", methods=['GET', 'POST'])
def login():
    global failed, my_notices, my_groups

    if request.method == 'POST':

        username = request.form['username']
        password = hash_obj(request.form['password'])

        if username in accounts:
            if accounts[username] == password:
                session['name'] = username
                my_notices = {title: specifications for title, specifications in notices.items()
                              if specifications[1] == session.get('name')}
                my_groups = {title: specifications for title, specifications in groups.items()
                             if specifications["creator"] == session.get('name')}
                return redirect(url_for('home'))
        failed = True

    return render_template('login.html', failed=failed)


@app.route("/signup", methods=['GET', 'POST'])
def sign_up():
    global data, accounts, failed

    if request.method == 'POST':

        new_username = request.form['username']
        new_password = hash_obj(request.form['password'])
        confirm_pass = hash_obj(request.form['com_password'])

        if new_username not in accounts and confirm_pass == new_password:
            accounts[new_username] = new_password
            data["accounts"] = accounts
            update_file(data)

            session['name'] = new_username

            return redirect(url_for('home'))

    return render_template("signup.html")


@app.route("/my_account", endpoint="my_account")
@loginCheck
def my_account():
    important = {title: specifications for title, specifications in my_notices.items()
                    if specifications[-1] == "True" and not specifications[2]}
    unimportant = {title: specifications for title, specifications in my_notices.items()
                    if specifications[-1] == "False" and not specifications[2]}
    reformatted = important
    reformatted.update(unimportant)
    return render_template('my_account.html', notices=reformatted, groups=my_groups, logined=session.get('name'))


@app.route("/my_account/groups/<group>", endpoint="my_groups_page")
@loginCheck
def my_groups_page(group):
    grouped_notices = {title: specifications for title, specifications in notices.items()
                       if specifications[2] == group}
    return render_template('my_groups_page.html', notices=grouped_notices, logined=session.get('name'))


@app.route('/my_account/edit/<title>', methods=["GET", "POST"], endpoint="edit")
@loginCheck
def edit(title):
    global data, notices, my_notices
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
    return render_template('edit.html', notices=my_notices, target=title, logined=session.get('name'))


@app.route('/my_account/delete/<title>', endpoint="delete")
@loginCheck
def delete(title):
    global data, notices, my_notices
    if title in my_notices:
        del notices[title]
        del my_notices[title]
        data["announcements"] = notices
        update_file(data)
    return redirect(url_for('my_account'))


@app.route('/my_account/add', methods=["GET", "POST"], endpoint="add")
@loginCheck
def add():
    global data, notices, my_notices
    if request.method == "POST":
        title = request.form['title']
        descrip = request.form['descrip']
        importance = request.form['importance']
        if title not in notices:
            if importance == 'Important':
                importance = 'True'
            else:
                importance = 'False'
            notices.update({title: [descrip, session.get('name'), importance]})
            my_notices.update({title: [descrip, session.get('name'), importance]})
            data["announcements"] = notices
            update_file(data)
            return redirect(url_for('my_account'))
    return render_template('add.html', logined=session.get('name'))


@app.route('/my_account/change_pass', methods=["GET", "POST"], endpoint="change_password")
@loginCheck
def change_password():
    global data, accounts
    if request.method == 'POST':
        curr_username = request.form["curr_user"]
        curr_pass = hash_obj(request.form["curr_pass"])
        new_pass = hash_obj(request.form["new_pass"])
        com_new_pass = hash_obj(request.form["com_new_pass"])

        if curr_username == session.get('name') and curr_pass == accounts[session.get('name')] and new_pass == com_new_pass:
            accounts[curr_username] = new_pass
            data["accounts"] = accounts
            update_file(data)
            return redirect(url_for("my_account"))

    return render_template('change_pass.html', logined=session.get('name'))


@app.route('/my_account/change_user', methods=['GET', 'POST'], endpoint="change_user")
@loginCheck
def change_user():
    global data, accounts, notices, my_notices, my_groups, groups
    if request.method == "POST":
        old_username = request.form["curr_user"]
        new_username = request.form["new_user"]
        com_new_user = request.form["com_new_user"]
        if old_username == session.get('name') and new_username == com_new_user:
            accounts.update({new_username: accounts[old_username]})
            del accounts[session.get('name')]
            session['name'] = new_username

            for title, specifications in notices.items():
                if specifications[1] == old_username:
                    notices[title] = [specifications[0], session.get('name'), specifications[-1]]

            for title, specifications in groups.items():
                if specifications["creator"] == old_username:
                    groups[title]["creator"] = session.get("name")

            my_notices = {title: specifications for title, specifications in notices.items()
                            if specifications[1] == session.get('name')}
            my_groups = {title: specifications for title, specifications in groups.items()
                         if specifications["creator"] == session.get("name")}

            data["announcements"], data["groups"], data["accounts"] = notices, groups, accounts
            update_file(data)
            return redirect(url_for("my_account"))
    return render_template('change_user.html', logined=session.get('name'))


@app.route("/my_account/del_acc", endpoint="delete_account")
@loginCheck
def delete_account():
    global data, accounts, notices, my_notices, groups, my_groups
    for title in my_notices:
        del notices[title]
    my_notices = {}
    for title in my_groups:
        del groups[title]
    my_groups = {}

    del accounts[session.get('name')]
    session['name'] = None
    data["announcements"], data["groups"], data["accounts"] = notices, groups, accounts
    update_file(data)
    return redirect(url_for("home"))


@app.route("/logout", endpoint="logout")
@loginCheck
def logout():
    global my_notices
    session['name'] = None
    my_notices = {}
    my_groups = {}
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

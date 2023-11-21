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
        json.dump(new_data, file)


def hash_obj(obj):
    hash_object = sha256()
    hash_object.update(obj.encode("utf-8"))
    return hash_object.hexdigest()


data = read_file()

user = None
logined = False
failed = False


@app.route("/")
def starter():
    return redirect(url_for('home'))


@app.route("/home")
def home():
    global data
    important = {title: specifications for title, specifications in data["announcements"].items()
                 if specifications[-1] is True}
    return render_template('home.html', notices=important, logined=logined)


@app.route("/all")
def announcements():
    global lines
    all_notices = {line.split(":")[0]: [line.split(":")[1], line.split(":")[2], line.split(":")[3]]
                   for line in lines[:-1]}
    return render_template("all.html", notices=all_notices, logined=logined)


@app.route("/search", methods=["POST"])
def search():
    global lines
    searched_word = request.form['search']
    searched_notice = {line.split(":")[0]: [line.split(":")[1], line.split(":")[2]] for line in lines[:-1]
                       if searched_word in line.split(":")[0]}
    return render_template("search.html", notices=searched_notice, logined=logined)


@app.route("/login", methods=['GET', 'POST'])
def login():
    global logined, accounts, failed, user

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username in accounts:
            if accounts[username] == password:
                logined = True
                user = username
                return redirect(url_for('home'))
        failed = True

    return render_template('login.html', failed=failed)


@app.route("/signup", methods=['GET', 'POST'])
def sign_up():
    global logined, lines, accounts, failed, user

    if request.method == 'POST':

        new_username = request.form['username']
        new_password = request.form['password']
        confirm_pass = request.form['com_password']

        if new_username not in accounts and confirm_pass == new_password:

            accounts[new_username] = new_password
            rewritten = '\n'.join(lines[:-1])
            rewritten += "\n" + str(accounts)[1:-1].replace("'", "").replace(" ", "")

            with open('database.txt', 'w') as file:
                file.write(rewritten)

            logined = True
            user = new_username

            return redirect(url_for('home'))

    return render_template("signup.html")


@app.route("/my_account")
def my_account():
    global lines, user, logined
    if logined is True:
        my_notices = {line.split(":")[0]: [line.split(":")[1], line.split(":")[2], line.split(":")[3]]
                      for line in lines[:-1] if line.split(":")[2] == user}
        return render_template('my_account.html', notices=my_notices, logined=logined)
    return redirect(url_for('login'))


@app.route('/my_account/edit/<title>')
def edit(title):
    global user, lines, logined
    if logined:
        my_notices = {line.split(":")[0]: [line.split(":")[1], line.split(":")[2], line.split(":")[3]]
                      for line in lines[:-1] if line.split(":")[2] == user}
        return render_template('edit.html', notices=my_notices, target=title)
    return redirect(url_for('login'))


@app.route('/my_account/delete/<title>')
def delete(title):
    global user, lines, logined
    if logined:
        for index, line in enumerate(lines[:-1]):
            new = line.split(":")
            if title == new[0] and user == new[2]:
                lines.pop(index)
                with open('database.txt', 'w') as file:
                    file.write('\n'.join(lines))
                break
        return redirect(url_for('my_account'))
    return redirect(url_for('login'))


@app.route('/my_account/add', methods=["GET"])
def add():
    global logined
    if logined:
        return render_template('add.html')
    return redirect(url_for('login'))


@app.route('/my_account/change_pass', methods=["GET", "POST"])
def change_password():
    global logined
    if logined:
        if request.method == 'POST':
            pass
        return render_template('change_pass.html')
    return redirect(url_for('login'))


@app.route('/my_account/change_user', methods=['GET', 'POST'])
def change_user():
    global logined
    if logined:
        return render_template('change_user.html')
    return redirect(url_for('login'))


@app.route("/my_account/process_input", methods=['POST'])
def edit_logic():
    global lines, logined
    if logined:
        selected = request.form["announcement"]
        title = request.form["title"]
        descrip = request.form["descrip"]
        importance = request.form["importance"]
        if title not in (line.split(":")[0] for line in lines):
            for index, line in enumerate(lines[:-1]):
                new = line.split(":")
                if new[0] == selected:
                    if title:
                        new[0] = title
                    if descrip:
                        new[1] = descrip
                    if importance.lower() == "important":
                        new[3] = 'True'
                    elif importance.lower() == "unimportant":
                        new[3] = 'False'
                    lines[index] = ":".join(new)
            with open('database.txt', 'w') as file:
                file.write("\n".join(lines))
            return redirect(url_for('my_account'))
        else:
            my_notices = {line.split(":")[0]: [line.split(":")[1], line.split(":")[2], line.split(":")[3]]
                          for line in lines[:-1] if line.split(":")[2] == user}
            return render_template('edit.html', notices=my_notices, target=selected)
    return redirect(url_for('login'))


@app.route('/my_account/add/add_logic', methods=['POST'])
def add_logic():
    global lines, user
    if user:
        title = request.form['title']
        if title not in (line.split(":")[0] for line in lines):
            descrip = request.form['descrip']
            importance = request.form['importance']
            if importance == 'Important':
                importance = 'True'
            else:
                importance = 'False'
            new_notice = ':'.join([title, descrip, user, importance])
            lines.insert(-1, new_notice)
            with open("database.txt", "w") as file:
                file.write("\n".join(lines))
            return redirect(url_for('my_account'))
        return redirect(url_for('add'))
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

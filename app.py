from flask import Flask, render_template, request, redirect, flash, abort, url_for
import database
import os 

app = Flask(__name__)
database.connect()
app.secret_key = os.urandom(24)

def RenderBookPage(title):
    bookInfo=database.get_book(title)
    if bookInfo is None:
        abort(404, description="Book Not Found")
    return render_template('book_page.j2', 
                        title = title,
                        author=bookInfo['author'],
                        series = bookInfo['series'],
                        series_number = bookInfo['series_number'],
                        genre = bookInfo['genre'],
                        location=bookInfo['location'],
                        copies = bookInfo['copies'],
                        available = bookInfo['available'],
                        borrowers=bookInfo['borrowers'])

@app.route("/")
def HomePage():
    return render_template('home.j2')

@app.route("/catalog/<title>", methods=["GET"] )
def bookPage_get(title):
    return RenderBookPage(title)

@app.route("/catalog/<title>", methods=["POST"])
def bookPage_post(title):
    if request.method == 'POST':
        if database.get_book(title) is None:
            abort(404, description="Book Not Found")
        fields=['action','borrower']
        for field in fields:
            if field not in request.form:
                flash("ERROR: Both action and borrower are required") 
                return redirect(url_for('bookPage_get', title=title))
            if len(str(request.form.get(field)).strip()) == 0:
                flash('ERROR: all fields must have value')
                return(redirect(url_for('bookPage_get', title=title)))
        if request.form.get('action') not in ['borrow','return']:
            flash('ERROR: Unkown action')
            return(redirect(url_for('bookPage_get',title=title)))
        
        action = request.form.get('action')
        borrower = request.form.get('borrower')

        if action == 'borrow':
            borrowing_success = database.checkout(title,borrower)
            if borrowing_success == True:
                flash(f'{title} successfully checked out to {borrower}!')
                return(redirect(url_for('bookPage_get',title=title)))
            if borrowing_success == False:
                flash(f'ERROR: No copies available for checkout')
                return(redirect(url_for('bookPage_get',title=title)))
        if action == 'return':
            return_success = database.return_book(title,borrower)
            if return_success == True:
                flash(f'{title} from {borrower} successfully returned!')
                return (redirect(url_for('bookPage_get',title=title)))
            if return_success == False:
                flash(f'ERROR: No copy of {title} is checked out out to {borrower}')
                return (redirect(url_for('bookPage_get',title=title)))
            return

@app.route("/register", methods=["GET"])
def register():
    return(render_template("register_book.j2"))

@app.route("/register", methods=["POST"])
def registerPage_post():
    title = request.form.get('title')
    author = request.form.get('author')
    series = request.form.get('series')
    series_number = request.form.get('series_number')
    if series_number == "":
        series_number == "N/A"
    else: 
        series_number = int(series_number)
    genre = request.form.get('genre')
    location = request.form.get('location')
    copies = int(request.form.get('copies'))
    print(title, author, series, series_number, genre, location, copies)
    register_success = database.register_book(title,author, series, series_number, genre, location, copies)
    if register_success == True:
        flash(f'{title} successfully registered!')

    if register_success == False:
        flash(f'Error registering {title}, please try again')
    return redirect(url_for('register'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    results = []
    if query:
        results = database.search_title(query, limit=5)
    return render_template('search.j2', query=query, results=results)

app.run(port=8080, debug=True)
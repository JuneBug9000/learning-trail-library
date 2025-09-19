import sqlite3
from thefuzz import fuzz

__db = None

def connect():
    global __db
    __db = sqlite3.connect('library.db')

    table_catalog =  "CREATE TABLE IF NOT EXISTS catalog(id INTEGER PRIMARY KEY, title TEXT NOT NULL, author TEXT, series TEXT, series_number INTEGER, genre TEXT, location TEXT);"
    table_copies="CREATE TABLE IF NOT EXISTS books(copy_id INTEGER PRIMARY KEY, book_id INTEGER NOT NULL, status TEXT DEFAULT 'available', borrower , FOREIGN KEY(book_id) REFERENCES catalog(id));"

    __db.execute(table_catalog)
    __db.execute(table_copies)
    __db.commit()
    __db.close()

def get_book(title):
    __db = sqlite3.connect('library.db')
    cursor = __db.cursor()

    cursor.execute("SELECT id, title, author, series, series_number, genre, location FROM catalog WHERE title=?", (title,))
    row = cursor.fetchone()
    if row == None:
        return None
    book_id = row[0]
    cursor.execute('SELECT status FROM books WHERE book_id=?',(book_id,))
    copies = cursor.fetchall()
    total=0
    available=0
    for copy in copies:
        total+=1
        if copy[0]=='available':
            available+=1
    cursor.execute('SELECT borrower FROM books WHERE book_id=? AND status=?',(book_id, 'checked out'))
    borrowers_list = cursor.fetchall()
    '''
    for borrower in borrowers_list:
        borrower = str(borrower)
        borrower = borrower.replace("(","")
        borrower = borrower.replace(".","")
        borrower = borrower.replace("'","")
    '''
    borrowers = ", ".join(str(borrower).replace("(","").replace(",","").replace("'","").replace(")","") for borrower in borrowers_list)
    __db.close()

    return{
        "author" : row[2],
        "series" : row[3],
        "series_number":row[4],
        "genre":row[5],
        "location":row[6],
        "copies" : total,
        "available" : available,
        "borrowers":borrowers


        
    }

def checkout(title, borrower):
    try: 
        __db = sqlite3.connect('library.db')
        cursor=__db.cursor()

        cursor.execute('SELECT id FROM catalog WHERE title=?',(title,))
        row = cursor.fetchone()
        if row == None:
            print('Error: Book does not exist')
        
        cursor.execute('SELECT copy_id, status FROM books WHERE book_id=? AND status="available"',(row[0],))
        copies = cursor.fetchone()
        if copies == None:
            #print('Error: No copies available for checkout')
            return(False)
            
        copy_id = copies[0]
        cursor.execute('UPDATE books SET status=?, borrower=? WHERE copy_id=?', ("checked out", borrower, copy_id))
        #print(f'{title} successfully checked out to {borrower}!')
        
        __db.commit()
        __db.close()
        return(True)

    except sqlite3.Error as e:
        __db.rollback()
        print('An error has occurred: ', e)
        return

def return_book(title, borrower):
    try:
        __db = sqlite3.connect('library.db')
        cursor=__db.cursor()
        print('1')
        cursor.execute('SELECT id FROM catalog WHERE title=?', (title,))
        row = cursor.fetchone()
        if row is None:
            __db.rollback()
            return(False)
        print('2')
        book_id = row[0]
        cursor.execute('SELECT copy_id FROM books WHERE book_id=? AND status=? AND borrower=?',(book_id,'checked out', borrower))
        copy = cursor.fetchone()
        if copy is None:
            __db.rollback()
            return(False)
        print('3')
        copy_id=copy[0]
        cursor.execute('UPDATE books SET status="available", borrower= NULL WHERE copy_id=?', (copy_id,))
        print('4')
        return(True)
    except sqlite3.Error as e:
        __db.rollback()
        print('An error has occured: ', e)
        return(False)
    finally:
        __db.commit()
        __db.close()

def register_book(title, author, series, series_number, genre, location, copies):
    try:
        __db = sqlite3.connect('library.db')
        cursor = __db.cursor()

        cursor.execute('SELECT id FROM catalog WHERE title=?',(title,))
        book_id = cursor.fetchone()
        if book_id == None:
            cursor.execute('INSERT INTO catalog(title, author, series, series_number, genre, location) VALUES (?,?,?,?,?,?)', (title, author, series, series_number, genre, location))
            book_id = cursor.lastrowid
        else:
            book_id = book_id[0]
        for i in range(copies):
            cursor.execute('INSERT INTO books(book_id) VALUES(?)', (book_id,))
    
        __db.commit()
        return True
    except sqlite3.Error as e:
        __db.rollback()
        print('An error has occurred:', e)
        return False
    finally:
        __db.close()


def print_db(): #FOR TESTING ONLY
    __db = sqlite3.connect('library.db')
    cursor = __db.cursor()

    cursor.execute('SELECT * FROM catalog')
    catalog = cursor.fetchall()

    cursor.execute('SELECT * FROM books')
    books =cursor.fetchall()
    __db.commit()
    __db.close()

    return(f'catalog: {catalog}, books: {books}')

def get_series(series):
    try:
        __db = sqlite3.connect('library.db')
        cursor = __db.cursor()

        cursor.execute('SELECT book_id FROM catalog WHERE series=?', (series,))
        book_id = cursor.fetchone
        if book_id == None:
            return('Series not found')
        
    except sqlite3.Error as e:
        __db.rollback()
        print('An error has occurred: ', e)
    finally:
        __db.close()

def fuzzy_search(query, data, threshold=50):
    q = query.lower().strip()
    results = []
    for item in data:
        score = fuzz.ratio(q, item.lower())
        if score >= threshold:
            results.append((item, score))
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def search_title(query, limit=5):
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT title, author, series FROM catalog")
    rows = cur.fetchall()
    conn.close()

    titles = [r['title'] for r in rows]
    matches = fuzzy_search(query, titles)[:limit]

    results = []
    seen_titles=set()
    for title, score in matches:
        matching_rows = [r for r in rows if r['title'] == title]
        for row in matching_rows: 
            if row['title'] not in seen_titles:
                results.append({
                    'title':  row['title'],
                    'author': row['author'],
                    'series': row['series'] or '',
                    'score':  score
                })
            seen_titles.add(row['title'])
    return results

def search_author(query, limit=5):
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT title, author, series FROM catalog")
    rows = cur.fetchall()
    conn.close()

    authors = [r['author'] for r in rows]
    matches = fuzzy_search(query, authors)[:limit]

    results = []
    seen_titles=set()
    for author, score in matches:
        matching_rows = [r for r in rows if r['author'] == author]
        for row in matching_rows:
            if row['title'] not in seen_titles:
                results.append({
                    'title':  row['title'],
                    'author': row['author'],
                    'series': row['series'] or '',
                    'score':  score
                })
            seen_titles.add(row['title'])
    return results

def search_series(query, limit=5):
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT title, author, series FROM catalog")
    rows = cur.fetchall()
    conn.close()

    series = [r['series'] for r in rows]
    matches = fuzzy_search(query, series)[:limit]
    results = []
    seen_titles = set()
    for serie, score in matches:
        matching_rows = [r for r in rows if r['series'] == serie]
        for row in matching_rows:
            if row['title'] not in seen_titles:
                results.append({
                    'title':  row['title'],
                    'author': row['author'],
                    'series': row['series'] or '',
                    'score':  score
                })
                seen_titles.add(row['title'])
    return results
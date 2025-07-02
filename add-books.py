import database
import os


#if os.path.exists('library.db'):
#    os.remove('library.db')

database.connect()
'''
df = pd.read_csv("Library Inventory - All.csv", usecols=["Title","Author","Series","Series_Number","Topic/Genre","Location","Coppies"])
print(df.head())
for row in df:
    title = row[0]
    print(title)
    author = row[1]
    print(author)
    series = row[2]
    series_number = row[3]
    genre= row[4]    
    #database.register_book(title,author,series,series_number,genre,location,copies)
'''

import csv

def safe_int(val, default=None):
    """
    Try to convert val to int; return default on failure or empty.
    """
    try:
        val = str(val).strip()
        return int(val) if val else default
    except ValueError:
        return default

def bulk_register_from_csv(csv_path):
    """
    Reads a CSV with columns:
      Title, Author, Series, Series_Number, Topic/Genre, Location, Coppies
    and calls database.register_book(...) for each row.
    """
    failures = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # pull & normalize fields
            title         = row.get('Title', '').strip()
            author        = row.get('Author', '').strip()
            series        = row.get('Series', '').strip() or None
            series_number = safe_int(row.get('Series_Number', ''), default=None)
            genre         = row.get('Topic/Genre', '').strip() or None
            location      = row.get('Location', '').strip()
            copies        = safe_int(row.get('Coppies', ''), default=0) or 0

            # sanity check required fields
            if not (title and author and location and copies > 0):
                print(f"Skipping invalid row: {row}")
                failures.append(title or "(no title)")
                continue

            # call your existing function
            success = database.register_book(
                title, author,
                series, series_number,
                genre, location, copies
            )
            if not success:
                failures.append(title)

    if failures:
        print("Failed to register these titles:")
        for t in failures:
            print(" •", t)
    else:
        print("All books registered successfully!")

#bulk_register_from_csv("Library Inventory - All.csv")
#print(database.print_db())




from pathlib import Path
import urllib.request

data_folder = Path("data")
data_folder.mkdir(exist_ok=True)

files = {
    "title.basics.tsv.gz": "https://datasets.imdbws.com/title.basics.tsv.gz",
    "title.ratings.tsv.gz": "https://datasets.imdbws.com/title.ratings.tsv.gz",
    "title.principals.tsv.gz": "https://datasets.imdbws.com/title.principals.tsv.gz",
    "name.basics.tsv.gz": "https://datasets.imdbws.com/name.basics.tsv.gz",
    "title.crew.tsv.gz": "https://datasets.imdbws.com/title.crew.tsv.gz",
}

for filename, url in files.items():
    destination = data_folder / filename

    if destination.exists():
        print(f"Υπάρχει ήδη: {filename}")
        continue

    print(f"Κατεβάζω: {filename}")
    urllib.request.urlretrieve(url, destination)
    print(f"Ολοκληρώθηκε: {filename}")

print("Τα IMDb αρχεία κατέβηκαν επιτυχώς!")
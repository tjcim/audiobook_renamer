"""
I want to update this script so that it sorts books by series if there is one listed in the
Album field sorted by the CD field.

***
Update 2/15/21 - I want to be notified if the script encounters a new file and then verifies that
all the data is set before copying it over to the destination directory.
I created a create_book_list.py which creates an initial json file object.

Steps:
1. Read in json object to python dictionary
2. Check if book is in dictionary
  A. If book is in dictionary, continue on as normal
  B. If book is not in dictionary, print out the information and check if it is valid
***

***
TODO:
A. Implement an ignore list. For example I don't want to copy over "Your First Listen"
B. Check if an existing file has updated data (possibly rename file/folder).
C. Re-implement the fixes.yaml file.
***

"""
import os
import sys
import json
import shutil
import string
import logging
import unicodedata

import eyed3
import click


SAFE_CHARS = f"-_.() {string.ascii_letters}{string.digits}"


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="{asctime} [{threadName}][{levelname}][{name}] {message}",
    style="{", datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def create_books_data(source):
    json_file = os.path.join(source, "books.json")
    books_data = ""
    with open(json_file, "r") as f:
        books_data = json.load(f)
    return books_data


def clean_name(name):
    """
    Quick pass to sanitize folder and file names
    """
    cleaned_name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode()
    return "".join(c for c in cleaned_name if c in SAFE_CHARS)


def get_file_list(folder, extension):
    """
    Returns a list of all files in folder with extension.
    """
    return [f"{folder}/{filename}" for filename in os.listdir(folder) if filename.endswith(f".{extension}")]


def get_book_info(file_path, destination):
    """
    Read author (artist) and title information from the ID3 tags on the MP3 file. Return as a dictionary.
    """
    book = eyed3.load(file_path)
    author = clean_name(book.tag.artist or "Unknown")
    title = clean_name(book.tag.title)
    series = book.tag.album or "None"
    series_num = book.tag.disc_num[0] or 0
    data = {
        "source_path": file_path,
        "author": clean_name(author),
        "title": clean_name(title),
        "series": series,
        "series_num": series_num,
    }
    data = book_dest_info(data, destination)
    return data


def book_dest_info(data, destination):
    series = data["series"]
    series_num = data["series_num"]
    # If series is not defined, set it to the main audiobook folder
    if series is None or series == "None":
        series_dest_path = destination
    else:
        series_dest_path = os.path.join(destination, series)
    # Add series number if book is part of a series
    if series != "None" and series_num != 0:
        book_path = os.path.join(series_dest_path, data["title"] + f"-{series_num}")
    else:
        book_path = os.path.join(series_dest_path, data["title"])
    file_name = f"{data['title']}.mp3"
    audio_path = os.path.join(book_path, file_name)
    data["series_dest_path"] = series_dest_path
    data["book_path"] = book_path
    data["audio_path"] = audio_path
    return data


def write_tag_info(data):
    book = eyed3.load(data['source_path'])
    book.tag.album = data["series"]
    book.tag.disc_num = data["series_num"]
    book.tag.save()


def is_new(books_data, data):
    """
    Checks if the book is new. If new, validate the data.
    """
    if data["title"] not in books_data:
        log.info("Book is new")
        return True
    return False


def json_record_exists(books_data, data):
    """
    Checks if the book data is already in the books_data json file.

    Returns True if exists otherwise False
    """
    if books_data[data["title"]]:
        log.debug("Book exists in json file.")
        return True
    return False


def new_book_update(books_data, data, destination):
    log.info(f"Current book data:"
             f"\n\tTitle: {data['title']}"
             f"\n\tSeries: {data['series']}"
             f"\n\tSeries Number: {data['series_num']}")
    series_correct = input("Is the series info correct? ")
    if series_correct in ["Y", "y", "Yes", "yes", "YES"]:
        log.info("Series data is correct")
    else:
        data["series"] = input("Enter in the series name: ")
        series_num = input("Enter in the series number: ")
        if series_num is None:
            series_num = 0
        data["series_num"] = series_num
    data = book_dest_info(data, destination)
    books_data[data['title']] = data
    print(data)
    if input("Does that all look correct? [Y]: ") not in ["", "Y", "y", "Yes", "yes", "YES"]:
        log.info("Sorry, I cannot help anymore.")
        sys.exit()
    else:
        write_tag_info(data)


def make_series_dir(data):
    """
    Create a series directory if it does not already exist
    """
    if os.path.isdir(data["series_dest_path"]):
        log.debug(f"Directory {data['series_dest_path']} already exists")
    else:
        log.info(f"Creating Series Directory: {data['series_dest_path']}")
        os.mkdir(data["series_dest_path"])


def make_book_dir(data):
    """
    Create book directory if it does not already exist
    """
    if os.path.isdir(data["book_path"]):
        log.debug(f"Directory {data['book_path']} already exists")
    else:
        log.info(f"Creating Book Directory: {data['book_path']}")
        os.mkdir(data["book_path"])


def get_file_size(file_path):
    """
    Returns the file size.
    """
    return os.stat(file_path).st_size


def copy_book(data):
    """
    Copy file to destination with the new path information. Check if the src file is larger than the
    destination. If so, overwrite the existing file.
    """
    copy = False
    if os.path.isfile(data["audio_path"]):
        # I need to check file size
        src_file_size = os.stat(data["source_path"]).st_size
        dst_file_size = os.stat(data["audio_path"]).st_size
        if src_file_size > dst_file_size:
            copy = True
    else:
        copy = True
    if copy:
        log.info(f"Copying book to directory {data['audio_path']}")
        shutil.copyfile(data['source_path'], data['audio_path'])
    else:
        log.debug(f"Book {data['audio_path']} already exists")


def write_json_file(source, books_data):
    """
    Writes the books_data to a json file.
    """
    json_object = json.dumps(books_data, indent=4)
    books_json_path = os.path.join(source, "books.json")
    with open(books_json_path, "w") as f:
        f.write(json_object)


def main(source, destination):
    if source.endswith("/"):
        source = source[:-1]
    books_data = create_books_data(source)
    books_list = get_file_list(source, "mp3")
    book_count = len(books_list)
    log.info(f"Processing {book_count} books")
    index = 0
    for book in books_list:
        index += 1
        data = get_book_info(book, destination)
        if is_new(books_data, data):
            new_book_update(books_data, data, destination)
        # Prioritize info from books.json.
        if json_record_exists(books_data, data):
            desired_data = books_data[data["title"]]
        else:
            desired_data = data
        make_series_dir(desired_data)
        make_book_dir(desired_data)
        copy_book(desired_data)
        if index % 10 == 0:
            log.info(f"Processed {index} of {book_count}")
    write_json_file(source, books_data)


@click.command()
@click.option("-s", "--source", help="Source path", default="/mnt/nas/media/OpenAudible/mp3/")
@click.option("-d", "--destination", help="Destination path",
              default="/mnt/nas/media/Audiobooks/")
def cli(source, destination):
    main(source, destination)


if __name__ == "__main__":
    cli()

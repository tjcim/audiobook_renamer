"""
This is a script for an initial pass to establish when we see a new file.

1. Get a list of books
2. Get book data
3. Collect book data into json object
4. Write book data to json file
"""
import os
import sys
import json
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

    # If series is not defined, set it to the main audiobook folder
    if series is None or series == "None":
        series_dest_path = destination
    else:
        series_dest_path = os.path.join(destination, series)

    # Add series number if book is part of a series
    if series != "None" and series_num != 0:
        book_path = os.path.join(series_dest_path, title + f"-{series_num}")
    else:
        book_path = os.path.join(series_dest_path, title)
    file_name = f"{title}.mp3"
    audio_path = os.path.join(book_path, file_name)
    data = {
        "source_path": file_path,
        "author": clean_name(author),
        "title": clean_name(title),
        "series": series,
        "series_num": series_num,
        "series_dest_path": series_dest_path,
        "book_path": book_path,
        "audio_path": audio_path,
    }
    return data


def add_to_books_data(books_data, data):
    """
    Adds the book data to the existing books_data
    """
    if data["title"] in books_data:
        log.info("Book is already in books_data")
    else:
        # Add the book info
        books_data[data["title"]] = data


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
    books_list = get_file_list(source, "mp3")
    book_count = len(books_list)
    log.info(f"Processing {book_count} books")
    books_data = {}
    index = 0
    for book in books_list:
        index += 1
        data = get_book_info(book, destination)
        add_to_books_data(books_data, data)
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

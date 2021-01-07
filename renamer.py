import os
import sys
import shutil
import string
import logging
import unicodedata

import eyed3
import click
import yaml


SAFE_CHARS = f"-_.() {string.ascii_letters}{string.digits}"
YAML_TEST = {
    "authors": {
        "B.V. Larson": "B. V. Larson",
    },
    "titles": {},
}


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="{asctime} [{threadName}][{levelname}][{name}] {message}",
    style="{", datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def read_fixes():
    """
    Load yaml file with fixes for author and titles
    """
    with open("fixes.yaml") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


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


def get_book_info(file_path, fixes):
    """
    Read author (artist) and title information from the ID3 tags on the MP3 file. Return as a dictionary.
    """
    book = eyed3.load(file_path)
    author = book.tag.artist
    title = book.tag.title
    if fixes["authors"] and author in fixes["authors"]:
        author = fixes["authors"][author]
    if fixes["titles"] and title in fixes["titles"]:
        title = fixes["titles"][title]
    data = {
        "author": clean_name(author),
        "title": clean_name(title),
    }
    return data


def make_author_dir(output_path, data):
    """
    Create author directory if it does not already exist
    """
    author_path = os.path.join(output_path, data["author"])
    if os.path.isdir(author_path):
        log.debug(f"Directory {author_path} already exists")
    else:
        log.info(f"Creating Author Directory: {author_path}")
        os.mkdir(author_path)
    return author_path


def make_book_dir(author_path, data):
    """
    Create book directory if it does not already exist
    """
    book_path = os.path.join(author_path, data["title"])
    if os.path.isdir(book_path):
        log.debug(f"Directory {book_path} already exists")
    else:
        log.info(f"Creating Book Directory: {book_path}")
        os.mkdir(book_path)
    return book_path


def get_file_size(file_path):
    """
    Returns the file size.
    """
    return os.stat(file_path).st_size


def copy_book(src, book_path, data):
    """
    Copy file to destination with the new path information. Check if the src file is larger than the
    destination. If so, overwrite the existing file.
    """
    copy = False
    book_file_path = os.path.join(book_path, f"{data['title']}.mp3")
    if os.path.isfile(book_file_path):
        # I need to check file size
        src_file_size = os.stat(src).st_size
        dst_file_size = os.stat(book_file_path).st_size
        if src_file_size > dst_file_size:
            copy = True
    else:
        copy = True
    if copy:
        log.info(f"Copying book to directory {book_file_path}")
        shutil.copyfile(src, book_file_path)
    else:
        log.debug(f"Book {book_file_path} already exists")


def main(input_path, output_path):
    fixes = read_fixes()
    if input_path.endswith("/"):
        input_path = input_path[:-1]
    books = get_file_list(input_path, "mp3")
    book_count = len(books)
    log.info(f"Processing {book_count} books")
    index = 0
    for book in books:
        index += 1
        data = get_book_info(book, fixes)
        if output_path.endswith("/"):
            output_path = output_path[:-1]
        author_path = make_author_dir(output_path, data)
        book_path = make_book_dir(author_path, data)
        copy_book(book, book_path, data)
        if index % 10 == 0:
            log.info(f"Processed {index} of {book_count}")


@click.command()
@click.option("-s", "--source", help="Source path", default="/mnt/nas/media/OpenAudible/mp3/")
@click.option("-d", "--destination", help="Destination path",
              default="/mnt/nas/media/Audiobooks/")
def cli(source, destination):
    main(source, destination)


if __name__ == "__main__":
    cli()

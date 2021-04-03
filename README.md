# Audiobook Renamer

A quick utility to rename and sort my audiobooks by series.

I built this so that I could listen to the audiobooks purchased through audible using a different application. I am currently using Smart Audiobook Player. I create a backup copy of my books using OpenAudible and then rename them with this script. One of the main advantages to this "system" is that Smart Audiobook Player has a queue function, which is great, but if I want to listen to a series of books it becomes difficult to know which books. This way I can just download a series folder to my phone and grab all the books at once. I can then add them to the queue in order by the series number which should now be in the book title.

This script uses a books.json file which is the source of truth for book data. It will scan through existing mp3 files from the source and check if it exists in the `books.json` file. If it does not exist it will show you the current title, series and series number (read from the ID3 tags) and ask you if the info is correct. This is your opportunity to give the book series information if desired along with a number to indicate the books order in the series.

The script will use the information in the `books.json` file when copying the file to the `destination`.

Updates 4/3/21: I did not want the files to end with something like `Book 6-6`, so I added a check that will not add the book series number to the file path if the title ends with the series number. So, `Book 6` will match a series number with `6` thus the series number will **not** be added.

Updates 3/29/21: I fixed a bug where the series number was not carried over to the `books.json` file. I also made it so if data is in the `books.json` file that data is used first and will fall back to the ID3 tags on the source mp3 file.

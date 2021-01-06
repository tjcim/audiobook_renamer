# Audiobook Renamer

A quick utility to rename and sort my audiobooks by author/title.

I built this so that I could listen to the audiobooks purchased through audible using a different app. I am currently using Smart Audiobook Player. I create a backup copy of my books using OpenAudible and then rename them with this script.

It is easy to run. Install the requirements and then do:

```
python renamer.py -s <source directory> -d <destination directory>
```

If there are any authors or titles that you want to change (e.g. B.V. Larson to B. V. Larson). Just create entries in the `fixes.yaml` file.

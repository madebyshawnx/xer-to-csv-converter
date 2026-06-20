# xer2csv

xer2csv converts Primavera P6 XER files into CSV files. Each table inside an XER file is saved as its own CSV file.

## Desktop App (no command line needed)

Use this option if you just want to convert a file without installing Python or using a terminal. This app runs on Windows.

1. Go to [release/XER-to-CSV-Converter.zip](release/XER-to-CSV-Converter.zip) and click the download button.
2. Find the downloaded ZIP file, right-click it, and choose "Extract All".
3. Open the extracted folder and double-click `XER-to-CSV-Converter.exe`.
4. In the window, click "Add files" to select your XER file or files. Click "Browse" to choose where the CSV files should be saved. Then click "Convert".

When the conversion finishes, you will find one folder per XER file. Inside each folder there is one CSV file for every table in that XER file. By default, the app also creates one master Excel file (`.xlsx`) in the same folder, with every table on its own tab. You can turn the master Excel file off with the checkbox if you only want the CSV files.

### Why the app is shared as a ZIP file

Web browsers and Microsoft Defender often block a program file (`.exe`) that is downloaded directly, because the file is new and is not signed with a paid certificate. Putting the program inside a ZIP file lets the download complete normally. The file is safe. It is simply too new for Windows to recognize yet.

The first time you run the program, Windows may still show a screen that says "Windows protected your PC". This is expected for a new app. Click "More info" and then "Run anyway" to start it. This prompt usually stops appearing after the app has been used for a while.

## Install From Source (Python users)

Install the package with [pip](https://pip.pypa.io/en/stable/):

```
pip install xer2csv
```

You can then use the converter in your own Python code:

```python
from xer2csv import XerToCsvConverter

converter = XerToCsvConverter()
converter.read_xer("schedule.xer")
converter.convert_to_csv("output_folder")
```

By default, each CSV includes a leading row-number column. Pass `include_index=False` to leave it out:

```python
converter.convert_to_csv("output_folder", include_index=False)
```

To create one Excel workbook that holds every table on its own sheet, use `convert_to_excel`:

```python
converter.convert_to_excel("output_folder", "schedule.xlsx", include_index=False)
```

## Run the Desktop App From Source

If you have Python installed, you can run the app directly without the executable. This also lets Mac and Linux users run it.

```
python xer2csv_gui.py
```

## Run the Batch Script

The `tests/test.py` script converts every XER file in an input folder. Run it from the project root so Python can find the package:

```
python tests/test.py input_folder output_folder
```

For each XER file, the script creates a subfolder named after the file and writes one CSV per table into it.

## License

[MIT](https://choosealicense.com/licenses/mit/)

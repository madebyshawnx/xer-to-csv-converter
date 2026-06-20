# xer2csv

xer2csv converts Primavera P6 XER files into CSV files. Each table inside an XER file is saved as its own CSV file.

## Desktop App (no command line needed)

Use this option if you just want to convert a file without installing Python or using a terminal.

1. Go to [release/XER-to-CSV-Converter.exe](release/XER-to-CSV-Converter.exe) and click the download button. This app runs on Windows.
2. Double-click the file you downloaded.
3. In the window, click "Add files" to select your XER file or files. Click "Browse" to choose where the CSV files should be saved. Then click "Convert".

When the conversion finishes, you will find one folder per XER file. Inside each folder there is one CSV file for every table in that XER file.

### About the Windows download warning

The first time you download or open the app, Windows may show a warning from Microsoft Defender SmartScreen that says the file is not commonly downloaded. This is expected. It happens because the app is new and is not signed with a paid code-signing certificate. It does not mean the file is unsafe.

To download the file, click the three dots or the down arrow next to the warning and choose "Keep". To open the file, double-click it, then click "More info" followed by "Run anyway". The warning normally stops appearing once the file has been downloaded by enough people over time.

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

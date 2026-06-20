# xer2csv
This package provides tools to convert XER files to CSV files.

## Desktop App (no command line needed)
Just want to convert a file without installing Python or touching a terminal?

1. Download **[release/XER-to-CSV-Converter.exe](release/XER-to-CSV-Converter.exe)** (Windows).
   On the file page, click the **Download** button (or the download icon).
2. Double-click the downloaded `XER-to-CSV-Converter.exe`.
   - Windows may show a "Windows protected your PC" warning the first time
     (because the app isn't code-signed). Click **More info -> Run anyway**.
3. In the window: click **Add files...** to pick your `.xer` file(s), click
   **Browse...** to choose where the CSVs should be saved, then click **Convert**.

For each XER file, a subfolder is created containing one CSV per table.

> The `.exe` is a standalone Windows build — it bundles Python and pandas, so the
> end user needs nothing installed. It runs on Windows only; Mac/Linux users can
> run the app from source (`python xer2csv_gui.py`).

## Installation
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install [xer2csv](https://pypi.org/project/xer2csv/).
```
pip install xer2csv
```

## Testing
test.py file will parse all the ".xer" files from the `input_dir` location and will parse them to the `output_dir` directory. For each table from XER file a separate CSV file will be created (within a subdirectory with the name of the original XER file).
usage: 
```
python test.py input_dir output_dir
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
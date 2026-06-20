import os
import pandas as pd


class XerToCsvConverter:
    def __init__(self):
        self.tables = []

    def read_xer(self, file_path):
        with open(file_path, encoding="utf8", errors='ignore') as f:
            content = f.read()
            tables = content.split('%T')
            self.tables = tables[1:]

    # auxiliary function (no call from user needed)
    def check_output_dir(self, output_location):
        if not os.path.exists(output_location):
            os.makedirs(output_location)

    # auxiliary function (no call from user needed)
    def check_missing_values(self, columns, rows_list):
        for row in rows_list:
            if len(columns) > len(row):
                row[len(columns):len(row)] = [None]*(len(columns) - len(row))
        return rows_list

    # auxiliary function (no call from user needed)
    def build_dataframe(self, table):
        """Parse one table chunk into (table_name, DataFrame).

        Returns None for empty or malformed chunks that have no field
        definition, so callers can simply skip them.
        """
        if '%F' not in table:
            return None

        table_name = table.split()[0]
        fields = table.split('%F')[1].split('\n')[0].split()
        rows = table.split('%R')[1:]
        # Keep only the first line of each row so the trailing end-of-file
        # marker ('%E') and any later content do not leak into the last cell.
        rows_list = [r.split('\n')[0].strip().split('\t') for r in rows]

        checked_rows_list = self.check_missing_values(fields, rows_list)
        df = pd.DataFrame(checked_rows_list, columns=fields, index=None)
        return table_name, df

    # auxiliary function (no call from user needed)
    def safe_sheet_name(self, name, used_names):
        """Return an Excel-safe, unique worksheet name.

        Excel sheet names must be 31 characters or fewer, cannot be blank, and
        cannot contain any of these characters: [ ] : * ? / \\
        """
        invalid = set('[]:*?/\\')
        cleaned = ''.join('_' if c in invalid else c for c in name).strip()
        cleaned = cleaned[:31] or 'Sheet'

        candidate = cleaned
        counter = 1
        while candidate.lower() in used_names:
            suffix = '_' + str(counter)
            candidate = cleaned[:31 - len(suffix)] + suffix
            counter += 1

        used_names.add(candidate.lower())
        return candidate

    def convert_to_csv(self, output_path, include_index=True):
        for table in self.tables:
            parsed = self.build_dataframe(table)
            if parsed is None:
                continue

            table_name, df = parsed
            self.check_output_dir(output_path)
            csv_file_path = os.path.join(output_path, table_name + '.csv')
            df.to_csv(csv_file_path, index=include_index)

    def convert_to_excel(self, output_path, filename, include_index=True):
        """Write every table into a single Excel workbook, one sheet per table.

        Requires the 'openpyxl' package (installed automatically with pandas
        when you install this package).
        """
        self.check_output_dir(output_path)
        excel_path = os.path.join(output_path, filename)

        used_names = set()
        wrote_any = False
        with pd.ExcelWriter(excel_path) as writer:
            for table in self.tables:
                parsed = self.build_dataframe(table)
                if parsed is None:
                    continue

                table_name, df = parsed
                sheet_name = self.safe_sheet_name(table_name, used_names)
                df.to_excel(writer, sheet_name=sheet_name, index=include_index)
                wrote_any = True

            # A workbook must contain at least one visible sheet.
            if not wrote_any:
                pd.DataFrame().to_excel(writer, sheet_name='No tables found')

        return excel_path

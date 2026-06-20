import os
import pandas as pd


class XerToCsvConverter:
    def __init__(self):
        self.tables = []

    def read_xer(self, file_path):
        with open(file_path, 'rb') as f:
            raw = f.read()

        # XER files are usually Windows-1252 (Primavera default) but newer
        # exports can be UTF-8. Try the most accurate encodings first and fall
        # back to latin-1, which maps every byte and never fails, so no
        # characters are ever silently dropped.
        content = None
        for encoding in ('utf-8-sig', 'cp1252', 'latin-1'):
            try:
                content = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if content is None:
            content = raw.decode('utf-8', errors='replace')

        self.tables = self.split_tables(content)

    # auxiliary function (no call from user needed)
    def split_tables(self, content):
        """Split file text into one chunk per table.

        Splitting is done on lines that begin with the '%T' marker so that the
        markers ('%T', '%F', '%R', '%E') appearing inside a field value cannot
        break the parsing.
        """
        tables = []
        current = None
        for raw_line in content.split('\n'):
            line = raw_line.rstrip('\r')
            if line.startswith('%T'):
                if current is not None:
                    tables.append('\n'.join(current))
                # Start a new table chunk with its name line (without '%T').
                current = [line[2:].lstrip('\t')]
            elif current is not None:
                current.append(line)
            # Lines before the first '%T' (the ERMHDR header) are ignored.
        if current is not None:
            tables.append('\n'.join(current))
        return tables

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
        definition, so callers can simply skip them. The parser works line by
        line so that it keeps multi-line text values intact, ignores the
        end-of-file marker ('%E'), and never loses data.
        """
        if '%F' not in table:
            return None

        table_name = None
        fields = None
        rows = []
        for raw_line in table.split('\n'):
            line = raw_line.rstrip('\r')

            if table_name is None:
                # The first non-empty line is the table name.
                if line.strip():
                    table_name = line.strip().split('\t')[0].strip()
                continue

            if line.startswith('%F'):
                fields = [c.strip() for c in line.split('\t')[1:]]
                while fields and fields[-1] == '':
                    fields.pop()
            elif line.startswith('%R'):
                rows.append(line.split('\t')[1:])
            elif line.startswith('%E') or line.startswith('%T'):
                break
            elif rows:
                # A line that is not a marker continues the previous row's last
                # value (a text field that contains line breaks).
                rows[-1][-1] = rows[-1][-1] + '\n' + line

        if fields is None:
            return None

        width = len(fields)
        normalized = []
        for row in rows:
            if len(row) < width:
                row = row + [None] * (width - len(row))
            elif len(row) > width:
                # Keep every value rather than dropping the extras: merge the
                # overflow into the last column.
                row = row[:width - 1] + ['\t'.join(row[width - 1:])]
            normalized.append(row)

        df = pd.DataFrame(normalized, columns=fields, index=None)
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

import os


def get_csv_files(base_dir):
    """
    Scan the application folder for CSV files.
    Returns a list of CSV files found.
    """
    csv_files = []

    try:
        for filename in os.listdir(base_dir):
            if filename.lower().endswith(".csv"):
                csv_files.append(filename)

    except Exception as e:
        print(f"Error scanning for CSV files: {e}")

    return sorted(csv_files) if csv_files else ["No CSV files found"]

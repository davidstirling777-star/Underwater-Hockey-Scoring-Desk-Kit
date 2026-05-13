
    def open_csv_folder(self):
        """Open the folder containing CSV files in the system file manager."""
        # Open the current working directory (where CSV files are located)
        csv_folder = os.getcwd()
        open_folder_in_file_manager(csv_folder)

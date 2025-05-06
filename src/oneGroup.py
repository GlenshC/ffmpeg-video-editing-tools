import os
import shutil

# Paths (update these)


# Ensure the destination folder exists
def pullOut(source_parent_folder,destination_folder):
    os.makedirs(destination_folder, exist_ok=True)

    # Loop through all folders in the parent folder
    for folder_name in os.listdir(source_parent_folder):
        folder_path = os.path.join(source_parent_folder, folder_name)

        # Check if it's a folder
        if os.path.isdir(folder_path):
            # Loop through all files in the folder
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)

                # Ensure it's a file (not a folder inside the folder)
                if os.path.isfile(file_path):
                    # Rename file to include the folder name (e.g., "1_file.txt")
                    new_file_name = f"{folder_name}_{file_name}"
                    new_file_path = os.path.join(destination_folder, new_file_name)

                    # Move the file
                    shutil.move(file_path, new_file_path)

    print("All files have been moved successfully!")
   

pullOut("0322","finalClips")

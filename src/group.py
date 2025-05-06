import os
import shutil

# Specify the directory where the files are located
source_directory = "out"

# Loop through all files in the directory
for filename in os.listdir(source_directory):
    if filename.startswith("chunk_"):
        # Extract the group number from the filename
        parts = filename.split("_")
        group_number = int(parts[1])  # Convert '001' to 1, '002' to 2, etc.
        
        # Create the target folder based on the group number
        target_folder = os.path.join(source_directory, str(group_number))
        os.makedirs(target_folder, exist_ok=True)
        
        # Move the file to the respective folder
        source_path = os.path.join(source_directory, filename)
        target_path = os.path.join(target_folder, filename)
        shutil.move(source_path, target_path)

print("Files organized successfully!")

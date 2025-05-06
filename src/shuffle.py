import os
import random


# shuffles the folder

def shuffle_and_rename_files(folder_path):
    # Ensure the folder path exists
    if not os.path.isdir(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return
    
    # Get a list of all files in the folder
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    # Shuffle the files
    random.shuffle(files)
    
    # Step 1: Rename all files to temporary unique names to avoid collisions
    temp_names = []
    for index, file in enumerate(files):
        # Create a temporary name (e.g., "temp_<index>_<random>.ext")
        file_extension = os.path.splitext(file)[1]
        temp_name = f"temp_{index}_{random.randint(1000, 9999)}{file_extension}"
        temp_path = os.path.join(folder_path, temp_name)
        
        old_path = os.path.join(folder_path, file)
        os.rename(old_path, temp_path)
        temp_names.append(temp_name)
    
    # Step 2: Rename from temporary names to final sequential names
    for index, temp_name in enumerate(temp_names):
        file_extension = os.path.splitext(temp_name)[1]
        final_name = f"{index}{file_extension}"
        
        temp_path = os.path.join(folder_path, temp_name)
        final_path = os.path.join(folder_path, final_name)
        
        os.rename(temp_path, final_path)
    
    print(f"Successfully shuffled and renamed {len(files)} files in '{folder_path}'.")

# Example usage
for i in range(0,33):
    shuffle_and_rename_files("out/"+str(i))
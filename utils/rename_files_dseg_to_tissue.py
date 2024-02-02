import os

# Path to the root directory
root_directory = '/home/mroulet/Documents/PYTHON/fabian_utils/atlas/CHUV/'

# Walk through the directory
for dirpath, dirnames, filenames in os.walk(root_directory):
    for filename in filenames:
        # Check if the filename contains 'dseg'
        if 'dseg' in filename:
            # Construct the new filename by replacing 'dseg' with 'tissue'
            new_filename = filename.replace('dseg', 'tissue')

            # Construct the full paths for the old and new filenames
            old_filepath = os.path.join(dirpath, filename)
            new_filepath = os.path.join(dirpath, new_filename)

            # Rename the file
            os.rename(old_filepath, new_filepath)

print("Processing completed.")

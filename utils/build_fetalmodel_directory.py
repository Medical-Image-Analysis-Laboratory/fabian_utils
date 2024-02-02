import os
import shutil

# Path to the root directory containing sub folders
#root_directory = '/home/mroulet/Documents/Data/fidon_merged_chuv/'
root_directory = '/home/mroulet/Documents/Data/miccai_submission/merged_feta/'
# Create the 'fetalmodel' directory
#fetalmodel_directory = '/home/mroulet/Documents/PYTHON/fabian_utils/atlas/CHUV/'
fetalmodel_directory = '/home/mroulet/Documents/PYTHON/fabian_utils/atlas/FETA/'

os.makedirs(fetalmodel_directory, exist_ok=True)

# Iterate through sub folders
for sub_folder in sorted(os.listdir(root_directory)):
    sub_folder_path = os.path.join(root_directory, sub_folder)

    # Check if it's a directory and starts with 'sub-'
    if os.path.isdir(sub_folder_path) and sub_folder.startswith('sub-'):
        # Create a directory in 'fetalmodel' for each sub
        output_sub_folder_path = os.path.join(fetalmodel_directory, sub_folder)
        print(output_sub_folder_path)
        os.makedirs(output_sub_folder_path, exist_ok=True)

        # Iterate through files in the 'anat' directory
        input_anat_path = os.path.join(sub_folder_path, 'anat')
        for filename in os.listdir(input_anat_path):

            if filename.endswith('.nii.gz') and ('brainmask' not in filename):
                # Remove "rec-mial" from the filename
                new_filename = filename.replace("rec-mial_", "")
                new_filename = new_filename.replace("rec-irtk_", "")

                # Create the output path and copy the file to the new directory
                output_file_path = os.path.join(output_sub_folder_path, new_filename)
                shutil.copy2(os.path.join(input_anat_path, filename), output_file_path)

print("Processing completed.")

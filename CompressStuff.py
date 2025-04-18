import os
import json
import argparse
import pyzipper
from cryptography.fernet import Fernet

def zip_stuff(input_path, input_password):
    base_name = os.path.basename(os.path.normpath(input_path))
    zip_output = f"{base_name}.zip"
    keys_output = {}

    #gathers files
    files = os.listdir(input_path)
    files = [f for f in files if os.path.isfile(os.path.join(input_path, f))]

    if len(files) == 0:
        raise ValueError("No stuff found in that directory.")

    #encrypting stuff
    os.makedirs("temp_encrypt", exist_ok=True)
    encrypted_files = []

    for file in files:
        key = Fernet.generate_key()
        fernet = Fernet(key)
        with open(os.path.join(input_path, file), 'rb') as original_file:
            original_data = original_file.read()
        encrypted_data = fernet.encrypt(original_data)
        encrypted_filename = f"enc_{file}"
        with open(os.path.join("temp_encrypt", encrypted_filename), 'wb') as encrypted_file:
            encrypted_file.write(encrypted_data)

        encrypted_files.append(encrypted_filename)
        keys_output[file] = key.decode()

    #zip stuff using password
    with pyzipper.AESZipFile(zip_output, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zipper:
        zipper.setpassword(input_password.encode())

        for encrypted_file in encrypted_files:
            zipper.write(os.path.join("temp_encrypt", encrypted_file), arcname=encrypted_file)

        #add metadata to json for decode
        zipper.writestr("file_keys.json", json.dumps(keys_output, indent=2))

    print(f"The stuff has been zipped: {zip_output}")


if __name__ == "__main__":
    #stuff to run as CLI
    parser = argparse.ArgumentParser(description="Generate a password protected & encrypted zip from a folder of files.")
    parser.add_argument("input_dir", help="Path to the input directory containing files")
    args = parser.parse_args()

    #take user input instead
    if not args.input_dir:
        args.input_dir = input("Enter the path to the input directory: ").strip()

    #set the password
    password = input("Set a password for the zipped stuff: ").strip()

    #let the zipping commence
    zip_stuff(args.input_dir, password)

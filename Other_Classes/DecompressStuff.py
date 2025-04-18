import os
import json
import pyzipper
from cryptography.fernet import Fernet
import argparse

#decrypt the stuff
def unzip_stuff(zip_path, password):
    #output dir name generation
    output_dir = os.path.splitext(zip_path)[0]
    os.makedirs(output_dir, exist_ok=True)

    #extract stuff from zip using password
    with pyzipper.AESZipFile(zip_path, 'r') as unzipper:
        unzipper.setpassword(password.encode())

        #read the keys
        with unzipper.open("file_keys.json") as f:
            file_keys = json.load(f)

        #decrypt listed files from the json
        for file, key in file_keys.items():
            enc_file_path = f"enc_{file}"
            if enc_file_path not in unzipper.namelist():
                print(f"Encrypted file not found in archive: {enc_file_path}")
                continue

            #read the files
            encrypted_data = unzipper.read(enc_file_path)
            fernet = Fernet(key.encode())

            try:
                decrypted_data = fernet.decrypt(encrypted_data)
            except Exception as e:
                print(f"Decryption failed for {file}: {e}")
                continue

            #save the decrypted files to the output files
            output_file_path = os.path.join(output_dir, file)
            with open(output_file_path, "wb") as df:
                df.write(decrypted_data)

            print(f"{file} decrypted successfully.")

# Main function to handle user inputs
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Decrypt all the files & folders from the zip.")
    parser.add_argument("zip_path", help="Path to the zip")
    args = parser.parse_args()

    #get user input for the stuffs password
    password = input("Enter the password for the stuff: ").strip()

    #let the unzipping commence
    unzip_stuff(args.zip_path, password)
    print(f"The decrypted stuff has been saved to: {os.path.splitext(args.zip_path)[0]}")

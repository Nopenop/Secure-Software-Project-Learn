import os
import json
import pyzipper
from cryptography.fernet import Fernet
from pyzipper.zipfile import ZipInfo
import argparse


# decrypt the stuff
def unzip_stuff(zip_path: str, password: bytes, aes_key: bytes):
    # output dir name generation
    output_dir = os.path.splitext(zip_path)[0]
    os.makedirs(output_dir, exist_ok=True)

    # extract stuff from zip using password
    with pyzipper.AESZipFile(zip_path, "r") as unzipper:
        unzipper.setpassword(password)
        for file in unzipper.infolist():
            encrypted_data = unzipper.read(file)
            fernet = Fernet(aes_key)
            try:
                decrypted_data = fernet.decrypt(encrypted_data)
            except Exception as e:
                print(f"Decryption failed for {file}: {e}")
                continue

            # save the decrypted files to the output files
            output_file_path = os.path.join(output_dir, file.filename)
            with open(output_file_path, "wb") as df:
                df.write(decrypted_data)

            print(f"{file} decrypted successfully.")


# Main function to handle user inputs
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Decrypt all the files & folders from the zip."
    )
    parser.add_argument("zip_path", help="Path to the zip")
    args = parser.parse_args()

    # get user input for the stuffs password
    password = input("Enter the password for the stuff: ").strip().encode()

    aes_key = input("Enter the AES to unencrypt files: ").strip().encode()

    # let the unzipping commence
    unzip_stuff(args.zip_path, password, aes_key)
    print(
        f"The decrypted stuff has been saved to: {os.path.splitext(args.zip_path)[0]}"
    )

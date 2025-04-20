import os
import argparse
import pyzipper
from cryptography.fernet import Fernet
import shutil


def zip_stuff(input_path: str, input_password: bytes, aes_key: bytes) -> str:
    base_name = os.path.basename(os.path.normpath(input_path))
    zip_output = f"{base_name}.zip"

    # gathers files
    files = os.listdir(input_path)
    files = [f for f in files if os.path.isfile(os.path.join(input_path, f))]

    if len(files) == 0:
        raise ValueError("No stuff found in that directory.")

    # encrypting stuff
    os.makedirs("temp_encrypt", exist_ok=True)
    encrypted_files = []

    for file in files:
        fernet = Fernet(aes_key)
        with open(os.path.join(input_path, file), "rb") as original_file:
            original_data = original_file.read()
        encrypted_data = fernet.encrypt(original_data)
        encrypted_filename = f"enc_{file}"
        with open(
            os.path.join("temp_encrypt", encrypted_filename), "wb"
        ) as encrypted_file:
            encrypted_file.write(encrypted_data)

        encrypted_files.append(encrypted_filename)

    # zip stuff using password
    with pyzipper.AESZipFile(
        zip_output, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES
    ) as zipper:
        zipper.setpassword(input_password)

        for encrypted_file in encrypted_files:
            zipper.write(
                os.path.join("temp_encrypt", encrypted_file), arcname=encrypted_file
            )

    # Remove temporary directory
    shutil.rmtree("temp_encrypt")
    return zip_output


if __name__ == "__main__":
    # stuff to run as CLI
    parser = argparse.ArgumentParser(
        description="Generate a password protected & encrypted zip from a folder of files."
    )
    parser.add_argument(
        "input_dir", help="Path to the input directory containing files"
    )
    args = parser.parse_args()

    # take user input instead
    if not args.input_dir:
        args.input_dir = input("Enter the path to the input directory: ").strip()

    # set the password
    password = input("Set a password for the zipped stuff: ").strip().encode()

    # set the password
    aes_key = input("Set AES key to encrypt files: ").strip().encode()

    # let the zipping commence
    zip_stuff(args.input_dir, password, aes_key)

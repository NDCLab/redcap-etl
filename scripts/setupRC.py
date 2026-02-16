import subprocess
import sys
import argparse
import os
import pandas as pd
import platform
from cryptography.fernet import Fernet
from io import StringIO
import requests

""" Module for transforming basic CSV to REDCap ETL setup CSV format.
Performs: 
- encryption/decryption of API tokens
- ensuring correct file naming conventions
- ensuring column formats
- validating API tokens against expected survey names
Includes argument parsing for command-line execution.
Usage:
    python setupRC.py --input <input_csv> --key <encryption_key>
Arguments:
    --input : Path to a CSV file containing project metadata and encrypted API tokens.
    --key   : Base64-encoded 32-byte string used to encrypt API tokens.
"""

def parseArgs():
    parser = argparse.ArgumentParser(description="REDCap ETL Extractor")
    parser.add_argument('--input', type=str, help='Input file path')
    parser.add_argument('--key', type=str, help='Decryption key (base64-encoded 32-byte string)')
    if not sys.argv[1:]:
        parser.print_help()
        sys.exit(1)
    # Add more arguments as needed
    return parser.parse_args()


def encrypt_token(token, key):
    if token is None or token == "":
        raise ValueError("API token cannot be empty for encryption.")
    cipher = Fernet(key)
    encrypted_token = cipher.encrypt(token.encode()).decode()
    return encrypted_token

def decrypt_token(encrypted_token, key):
    cipher = Fernet(key)
    decrypted_token = cipher.decrypt(encrypted_token).decode()
    return decrypted_token
def checkColumns(df):
    required_columns = ["project_name", "project_type", "API_Token", "folder_path", "encrypted"]
    for col in df.columns:
        if col in required_columns:
            required_columns.remove(col)
        else:
            print(f"Warning: Unexpected column '{col}' found in the input.")
    if required_columns:
        raise ValueError(f"Missing required columns: {', '.join(required_columns)}")
    print("All required columns are present.")
def set_encryption_key(keyName: str = "REDCAP_ENCRYPTION_KEY", value: str = None):
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(
                ["setx", keyName, value],
                check=True,
                capture_output=True,
                text=True
            )

        elif system in ("Linux", "Darwin"):
            shell_rc = os.path.expanduser("~/.bashrc")

            with open(shell_rc, "a", encoding="utf-8") as f:
                f.write(f'\nexport {keyName}="{value}"\n')

        else:
            raise RuntimeError(f"Unsupported OS: {system}")

    except (subprocess.CalledProcessError, OSError) as e:
        raise RuntimeError(f"Failed to persist {keyName}") from e

def validateAPIToken(survey_name,API_token):
    url = "https://redcap.fiu.edu/api/"
    data = {
    "token": API_token,
    "content": "project",
    "format": "csv",
    }

    response = requests.post(url, data=data)
    metadataDF = pd.read_csv(StringIO(response.text))
    expected_survey_name =  metadataDF.iloc[0]["project_title"]
    if expected_survey_name != survey_name:
        raise ValueError(f"API token is invalid for survey {survey_name}. Expected survey name: {expected_survey_name}")

def create_encryptedKey():
    cipher_key = Fernet.generate_key()  # This is base64-encoded 32 bytes
    set_encryption_key(value=cipher_key.decode())
    print("Key saved to REDCAP_ENCRYPTION_KEY environment variable.")
    print("Generated encryption key (store this securely):")
    print(cipher_key.decode())
    return cipher_key
def main(args):
    print("REDCap ETL Setup")
    #print(f"Arguments received: {args}")
    key = None
    if args.key:
        key = args.key
        if len(key) != 44:
            raise ValueError("Decryption key must be a base64-encoded 32-byte string.")
    else:
        key = create_encryptedKey()
    input_df = pd.read_csv(args.input)
    checkColumns(input_df)
    for index, row in input_df.iterrows():
        if row["encrypted"] == False or pd.isna(row["encrypted"]):
            validateAPIToken(row["project_name"], row["API_Token"])
            print(f"Encrypting token for project: {row['project_name']}")
            encrypted_token = encrypt_token(row["API_Token"], key)
            #encrypted_token = decrypt_token(row["API_Token"], key)
            input_df.at[index, "API_Token"] = encrypted_token
            input_df.at[index, "encrypted"] = True
    input_df.to_csv(args.input, index=False)
    
if __name__ == "__main__":
    args = parseArgs()
    main(args)
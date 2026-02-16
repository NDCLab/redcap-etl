"""
extractRedcaps.py

Module for extracting, transforming, and saving data from REDCap projects using an ETL (Extract, Transform, Load) process.
This script is designed to be run from the command line and supports the following features:
- Securely decrypts REDCap API tokens using a provided encryption key.
- Connects to the REDCap API to extract project data in CSV format.
- Saves the cleaned data as CSV files in user-specified directories.
Usage:
    python extractRedcaps.py --input <input_csv> --key <decryption_key>
Arguments:
    --input : Path to a CSV file containing project metadata and encrypted API tokens.
    --key   : Base64-encoded 32-byte string used to decrypt API tokens.
"""
import re
import sys

import datetime
import os
import pandas as pd
import requests
from cryptography.fernet import Fernet
from io import StringIO
import time
import argparse
import getpass

REDCAP_API_URL = "https://redcap.fiu.edu/api/"

COLOR_MAP = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "reset": "\033[0m"
}
def getData(api_token):
    data = {
        "token": api_token,
        "content": "record",
        "format": "csv",
        "type": "flat",
        "exportSurveyFields": "true"
    }
    response = requests.post(REDCAP_API_URL, data=data)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code} - {response.text}")
    return response

def transformData(response):
    """ Transforms the raw CSV response from REDCap into a cleaned DataFrame. """
    created_df = pd.read_csv(StringIO(response))
    # if the columns are numbers, then set the first row as header
    if  all(isinstance(c, int) for c in created_df.columns):
        created_df.columns = created_df.iloc[0]
        created_df = created_df.iloc[1:].reset_index(drop=True)

    if "redcap_survey_identifier" in created_df.columns:
        # remove redcap_survey_identifer column
        created_df = created_df.drop(columns=["redcap_survey_identifier"])
    return created_df


def create_typing_effect(text, delay=0.01, color="blue"):
    """
    Displays text with a typing effect in the console.
    
    :param text: The text to display with typing effect
    :param delay: Delay between each character (in seconds)
    :param color: Color of the text
    """
    color_code = COLOR_MAP.get(color, COLOR_MAP["red"])
    for char in text:
        sys.stdout.write(f"{color_code}{char}{COLOR_MAP['reset']}")
        sys.stdout.flush()
        if delay > 0:
            time.sleep(delay)
    sys.stdout.write('\n')

def parseArgs():
    parser = argparse.ArgumentParser(description="REDCap ETL Extractor")
    parser.add_argument('--input', type=str, help='Input dataframe')
    parser.add_argument('--key', type=str, help='Decryption key (base64-encoded 32-byte string)')
    parser.add_argument('--no_clears', action='store_true', help='Do not clear existing files in target directories before extraction.')
    parser.add_argument('--isDirect', action='store_true', help='Uploads data directly without saving CSV files elsewhere.')
    # Add more arguments as needed
    if not sys.argv[1:]:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()

def format_fileName(date, df):
    """
    Formats the file name based on project details and date.
    
    :param date: Date string from the response headers
    :param df: DataFrame row containing project details
    :return: Formatted file name as a string
    """
    dt = datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %Z')
    date_str = dt.strftime('%Y-%m-%d_%H%M')
    if  pd.isna(df["project_name"]):
        raise ValueError("Project name cannot be empty for file naming.")
    project_name = df["project_name"]
    project_name = df.get("project_name", "UnknownProject")
    if df["custom_name"] != "":
        project_name = df["custom_name"]
    # format file name by removing any underscores in project name
    # check to see if the project ends with REMOTE_ONLY, replace it with just R
    project_name = re.sub(r'_REMOTE-ONLY$', '', project_name)
    project_name = re.sub(r'[_\s]+', '', project_name)
    project_name = project_name.capitalize()
    project_type = df.get("project_type", "DATA")
    return f"{project_name}_{project_type}_{date_str}.csv"


def decrypt_token(encrypted_token, key):
    """
    Decrypts the given encrypted API token using the provided key.
    
    :param encrypted_token: The encrypted API token to decrypt
    :param key: The decryption key (base64-encoded 32-byte string)
    :return: Decrypted API token as a string
    """
    if encrypted_token is None or encrypted_token == "":
        raise ValueError("API token cannot be empty for decryption.")
    cipher = Fernet(key.encode())
    decrypted_token = cipher.decrypt(encrypted_token).decode()
    return decrypted_token

def create_csv(df, file_name,folder_path,isDirect=False):
    """
    Creates a CSV file from the given DataFrame in the specified folder path.
    
    :param df: DataFrame to be saved as CSV
    :param file_name: Name of the CSV file
    :param folder_path: Folder path where the CSV file will be saved
    :return: Path to the created CSV file
    """

    if not os.path.exists(folder_path):
        if isDirect:
            raise FileNotFoundError(f"The folder path {folder_path} does not exist.")
        else:
            os.makedirs(folder_path)
    file_path = os.path.join(folder_path, file_name)
    # check if file already exists
    if os.path.exists(file_path):
        print(f"File {file_path} already exists. Overwriting.")
    df.to_csv(file_path, index=False)
    return file_path

def update_progress_bar(total=100, length=40,progress=0, color="green"):
    i =progress
    color_code = COLOR_MAP.get(color, COLOR_MAP["reset"])
    percent = int(100 * i / total)
    filled_length = int(length * i // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{color_code}|{bar}| {percent}%{COLOR_MAP["reset"]}')
    sys.stdout.flush()

def clear_files(folder_paths):
    """
    Clears all files in the specified folder path.
    
    :param folder_paths: List of folder paths to clear files from
    """
    for folder_path in folder_paths:
        if not os.path.exists(folder_path):
            return
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                else:
                    print(f"Skipping {file_path} as it is not a file.")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")


def main(args):
    create_typing_effect("Welcome to the REDCap ETL Extractor!\n", color="red")
    isDirect = args.isDirect
    #print(f"Arguments received: {args}")
    key = args.key
    if key is None:
        # check if key is provided as environment variable
        key = os.getenv("REDCAP_ENCRYPTION_KEY")
        if key is None:
            # ask user to input key
            key = getpass.getpass("Enter the decryption key (base64-encoded 32-byte string): ")
    if len(key) != 44:
        raise ValueError("Decryption key must be a base64-encoded 32-byte string.")
    api_df = pd.read_csv(args.input)
    # get number of rows in the dataframe
    total_rows = len(api_df)
    create_typing_effect(f"Starting extraction for {total_rows} projects...\n", color="yellow")
    if args.no_clears == False:
        if isDirect == True:
            raise ValueError("Cannot clear files in direct mode.")
        folder_paths = api_df["folder_path"].unique()
        # remove "all" from folder_paths
        folder_paths = [path for path in folder_paths if path != "all"]
        create_typing_effect("Clearing existing files in target directories...\n", color="yellow")
        clear_files(folder_paths)
        print("Existing files cleared.\n")
    for index, row in api_df.iterrows():
        update_progress_bar(total=total_rows, progress=index+1, color="white")
        if row["encrypted"] == False:
            raise ValueError(f"API token for project {row['project_name']} is not encrypted. Please encrypt it before proceeding.")
        decrypted_token = decrypt_token(row["API_Token"], key)
        response = getData(decrypted_token)
        # check if response is empty
        if not response.text.strip():
            raise ValueError(f"No data returned for project {row['project_name']}.")
        date = response.headers['Date']
        created_df = transformData(response.text)
        file_name = format_fileName(date, row)
        # check if the folder path is "all" for downloading to all folders 
        if row["folder_path"] == "all":
            uniquePaths = api_df["folder_path"].unique()
            # remove "all" from uniquePaths
            uniquePaths = [path for path in uniquePaths if path != "all"]
            for path in uniquePaths:
                create_csv(created_df, file_name, path, isDirect=isDirect)
        else:
            create_csv(created_df, file_name, row["folder_path"], isDirect=isDirect)
    create_typing_effect("\n\n\n RedCap Extraction Completed.", delay=0, color="green")


if __name__ == "__main__":
    args = parseArgs()
    main(args)

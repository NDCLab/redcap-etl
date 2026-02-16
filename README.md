# REDCap ETL Utilities

## Project Goal
This folder contains two Python scripts for managing REDCap data extraction and setup:

- **setupRC.py**: Prepares your project metadata CSV for secure REDCap API extraction by encrypting API tokens and ensuring correct formatting.
- **extractRedcaps.py**: Extracts, transforms, and saves REDCap project data using encrypted API tokens.


## Background & Design
Replace this text with a slightly longer (but still only max 250 words) description of the project background and its design. 


## Usage
## 1. Setting Up Your REDCap Metadata (setupRC.py)
This script encrypts API tokens in your metadata CSV and ensures all required columns are present.

**Usage:**
```bash
python setupRC.py --input <input_csv> --key <encryption_key>
```
- `--input`: Path to your metadata CSV file.
- `--key`: (Optional) Base64-encoded 32-byte string for encryption. If omitted, a new key is generated and saved to the `REDCAP_ENCRYPTION_KEY` environment variable.

**Example:**
```bash
python setupRC.py --input test_redcap_setup.csv --key <your_key>
```

## 2. Extracting Data from REDCap (extractRedcaps.py)
This script decrypts API tokens, connects to the REDCap API, and saves cleaned data as CSV files.

**Usage:**
```bash
python extractRedcaps.py --input <input_csv> --key <decryption_key> --no_clears --isDirect
```
- `--input`: Path to your encrypted metadata CSV file.
- `--key`: (Optional) Base64-encoded 32-byte string for decryption. If omitted, you will be prompted or the script will use the `REDCAP_ENCRYPTION_KEY` environment variable.
- `--no_clears`: (Optional) If set, existing files in target directories are not deleted before extraction.
- `--isDirect`: (Optional) If set, uploads data directly without saving CSV files elsewhere.

**Example:**
```bash
python extractRedcaps.py --input test_redcap_setup.csv --key <your_key>
```
## 3. Input CSV Format

The input_csv is a metadata file listing all REDCap projects to be processed. It must be a CSV file with the following columns:
| project_name                | project_type | API_Token | folder_path      | encrypted |
|-----------------------------|--------------|-----------|------------------|-----------|
| thrive_iqs_clinician_s1_r1  | DATA         | 123ABC345DEF  | data/s1/redcap   | False     |
| thrive_bbs_child_s1_r1      | DATA         | 123ABC345DEF   | data/s1/redcap   | False     |

- project_name: Name of the REDCap project.
- project_type: Type/category of the project (e.g., DATA).
- API_Token: The REDCap API token (will be encrypted by setupRC.py).
- folder_path: Directory where extracted data will be saved.
- encrypted: Boolean indicating if the token is encrypted (should be False initially).


## Work in Development
This `main` branch contains completed releases for this project. For all work-in-progress, please switch over to the `dev` branches.



## Contributors
| Role | Name |
| ---  | ---  |
| Lab Technician | Rohan Prasad |

Learn more about us [here](https://www.ndclab.com/people).

## Contributing
If you are interested in contributing, please read our [CONTRIBUTING.md](CONTRIBUTING.md) file.


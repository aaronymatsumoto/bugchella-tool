# Bugchella Tool

A Python command-line interface (CLI) tool that authenticates with the BuildOps public API, retrieves customer and property data, and saves it to CSV files.

## Features

- Authenticates with BuildOps API
- Fetches customers and properties
- Saves data to CSV for analysis or reporting
- Supports multi-threaded requests for speed

## Prerequisites

- Python 3.13+
- pip

## Setup

1. Go to the GitHub repository: https://github.com/aaronymatsumoto/bugchella-tool
2. Click the green "Code" button near the top right
3. Click "Download ZIP"
4. Unzip the folder to your computer
5. Open the unzipped folder in File Explorer
6. Click the top address bar — it should look something like:
   C:\Users\YourName\Downloads\ToolName-main
7. In the top address bar, type in "cmd" and press enter. The black "Command Prompt" box should appear.
8. The command prompt should show the same address as step 6.
9. Type in "pip install -r requirements.txt" and press Enter

## Usage
1. To list all customers that have no properties
   Type in "python main.py get_customers_no_properties" and press Enter
   A .csv file with the results will be saved in the folder that you are in

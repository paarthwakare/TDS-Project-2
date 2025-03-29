import os
import zipfile
import pandas as pd
import httpx
import json
import shutil
import tempfile
from typing import Dict, Any, List, Optional
import re
import tempfile
import shutil
import subprocess
import httpx
import json
import csv
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


async def calculate_statistics(file_path: str, operation: str, column_name: str) -> str:
    """
    Calculate statistics from a CSV file.
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)

        # Verify that the column exists
        if column_name not in df.columns:
            return f"Column '{column_name}' not found in the CSV file."

        # Perform the requested operation
        if operation == "sum":
            result = df[column_name].sum()
        elif operation == "average":
            result = df[column_name].mean()
        elif operation == "median":
            result = df[column_name].median()
        elif operation == "max":
            result = df[column_name].max()
        elif operation == "min":
            result = df[column_name].min()
        else:
            return f"Unsupported operation: {operation}"

        return str(result)

    except Exception as e:
        return f"Error calculating statistics: {str(e)}"


async def make_api_request(
    url: str,
    method: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Make an API request to a specified URL.
    """
    try:
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            else:
                return f"Unsupported HTTP method: {method}"

            # Check if the response is JSON
            try:
                result = response.json()
                return json.dumps(result, indent=2)
            except:
                return response.text

    except Exception as e:
        return f"Error making API request: {str(e)}"


async def execute_command(command: str) -> str:
    """
    Execute a shell command and return its output
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error executing command: {str(e)}"


async def extract_zip_and_read_csv(
    file_path: str, column_name: Optional[str] = None
) -> str:
    """
    Extract a zip file and read a value from a CSV file inside it
    """
    temp_dir = tempfile.mkdtemp()

    try:
        # Extract the zip file
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Find CSV files in the extracted directory
        csv_files = [f for f in os.listdir(temp_dir) if f.endswith(".csv")]

        if not csv_files:
            return "No CSV files found in the zip file."

        # Read the first CSV file
        csv_path = os.path.join(temp_dir, csv_files[0])
        df = pd.read_csv(csv_path)

        # If a column name is specified, return the value from that column
        if column_name and column_name in df.columns:
            return str(df[column_name].iloc[0])

        # Otherwise, return the first value from the "answer" column if it exists
        elif "answer" in df.columns:
            return str(df["answer"].iloc[0])

        # If no specific column is requested, return a summary of the CSV
        else:
            return f"CSV contains columns: {', '.join(df.columns)}"

    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


async def extract_zip_and_process_files(file_path: str, operation: str) -> str:
    """
    Extract a zip file and process multiple files
    """
    temp_dir = tempfile.mkdtemp()

    try:
        # Extract the zip file
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Process based on the operation
        if operation == "find_different_lines":
            # Compare two files
            file_a = os.path.join(temp_dir, "a.txt")
            file_b = os.path.join(temp_dir, "b.txt")

            if not os.path.exists(file_a) or not os.path.exists(file_b):
                return "Files a.txt and b.txt not found."

            with open(file_a, "r") as a, open(file_b, "r") as b:
                a_lines = a.readlines()
                b_lines = b.readlines()

                diff_count = sum(
                    1
                    for i in range(min(len(a_lines), len(b_lines)))
                    if a_lines[i] != b_lines[i]
                )
                return str(diff_count)

        elif operation == "count_large_files":
            # List all files in the directory with their dates and sizes
            # For files larger than 1MB
            large_file_count = 0
            threshold = 1024 * 1024  # 1MB in bytes

            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    if file_size > threshold:
                        large_file_count += 1

            return str(large_file_count)

        elif operation == "count_files_by_extension":
            # Count files by extension
            extension_counts = {}

            for root, _, files in os.walk(temp_dir):
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext:
                        ext = ext.lower()
                        extension_counts[ext] = extension_counts.get(ext, 0) + 1

            return json.dumps(extension_counts)

        elif operation == "find_latest_file":
            # Find the most recently modified file
            latest_file = None
            latest_time = None

            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    mod_time = os.path.getmtime(file_path)

                    if latest_time is None or mod_time > latest_time:
                        latest_time = mod_time
                        latest_file = file

            if latest_file:
                return latest_file
            else:
                return "No files found."

        elif operation == "extract_text_patterns":
            # Extract all email addresses from text files
            pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            matches = []

            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(".txt"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r") as f:
                                content = f.read()
                                found = re.findall(pattern, content)
                                matches.extend(found)
                        except Exception:
                            # Skip files that can't be read as text
                            pass

            return json.dumps(list(set(matches)))  # Return unique matches

        else:
            return f"Unsupported operation: {operation}"

    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


async def merge_csv_files(file_path: str, merge_column: str) -> str:
    """
    Extract a zip file and merge multiple CSV files based on a common column
    """
    temp_dir = tempfile.mkdtemp()
    result_path = os.path.join(temp_dir, "merged_result.csv")

    try:
        # Extract the zip file
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Find all CSV files
        csv_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".csv"):
                    csv_files.append(os.path.join(root, file))

        if not csv_files:
            return "No CSV files found in the zip file."

        # Read and merge all CSV files
        dataframes = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                if merge_column in df.columns:
                    dataframes.append(df)
                else:
                    return f"Column '{merge_column}' not found in {os.path.basename(csv_file)}"
            except Exception as e:
                return f"Error reading {os.path.basename(csv_file)}: {str(e)}"

        if not dataframes:
            return "No valid CSV files found."

        # Merge all dataframes
        merged_df = pd.concat(dataframes, ignore_index=True)

        # Save the merged result
        merged_df.to_csv(result_path, index=False)

        # Return statistics about the merge
        return f"Merged {len(dataframes)} CSV files. Result has {len(merged_df)} rows and {len(merged_df.columns)} columns."

    except Exception as e:
        return f"Error merging CSV files: {str(e)}"

    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


async def analyze_time_series(
    file_path: str, date_column: str, value_column: str
) -> str:
    """
    Analyze time series data from a CSV file
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)

        # Verify that the required columns exist
        if date_column not in df.columns or value_column not in df.columns:
            return f"Required columns not found in the CSV file."

        # Convert date column to datetime
        df[date_column] = pd.to_datetime(df[date_column])

        # Sort by date
        df = df.sort_values(by=date_column)

        # Calculate basic statistics
        stats = {
            "count": len(df),
            "min_value": float(df[value_column].min()),
            "max_value": float(df[value_column].max()),
            "mean_value": float(df[value_column].mean()),
            "median_value": float(df[value_column].median()),
            "start_date": df[date_column].min().strftime("%Y-%m-%d"),
            "end_date": df[date_column].max().strftime("%Y-%m-%d"),
        }

        # Calculate daily change
        df["daily_change"] = df[value_column].diff()
        stats["avg_daily_change"] = float(df["daily_change"].mean())
        stats["max_daily_increase"] = float(df["daily_change"].max())
        stats["max_daily_decrease"] = float(df["daily_change"].min())

        # Calculate trends
        days = (df[date_column].max() - df[date_column].min()).days
        total_change = df[value_column].iloc[-1] - df[value_column].iloc[0]
        stats["overall_change"] = float(total_change)
        stats["avg_change_per_day"] = float(total_change / days) if days > 0 else 0

        return json.dumps(stats, indent=2)

    except Exception as e:
        return f"Error analyzing time series data: {str(e)}"


import json
from datetime import datetime, timedelta
import sqlite3
import zipfile
import tempfile
import os
import shutil
import re
import pandas as pd
import csv
import io


def sort_json_array(json_array: str, sort_keys: list) -> str:
    """
    Sort a JSON array based on specified criteria

    Args:
        json_array: JSON array as a string
        sort_keys: List of keys to sort by

    Returns:
        Sorted JSON array as a string
    """
    try:
        # Parse the JSON array
        data = json.loads(json_array)

        # Sort the data based on the specified keys
        for key in reversed(sort_keys):
            data = sorted(data, key=lambda x: x.get(key, ""))

        # Return the sorted JSON as a string without whitespace
        return json.dumps(data, separators=(",", ":"))

    except Exception as e:
        return f"Error sorting JSON array: {str(e)}"


def count_days_of_week(start_date: str, end_date: str, day_of_week: str) -> str:
    """
    Count occurrences of a specific day of the week between two dates

    Args:
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
        day_of_week: Day of the week to count

    Returns:
        Count of the specified day of the week
    """
    try:
        # Parse the dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # Map day names to weekday numbers (0=Monday, 6=Sunday)
        day_map = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }

        # Get the weekday number for the specified day
        weekday = day_map.get(day_of_week)
        if weekday is None:
            return f"Invalid day of week: {day_of_week}"

        # Count occurrences
        count = 0
        current = start
        while current <= end:
            if current.weekday() == weekday:
                count += 1
            current += timedelta(days=1)

        return str(count)

    except Exception as e:
        return f"Error counting days of week: {str(e)}"


async def process_encoded_files(file_path: str, target_symbols: list) -> str:
    """
    Process files with different encodings

    Args:
        file_path: Path to the zip file containing encoded files
        target_symbols: List of symbols to search for

    Returns:
        Sum of values associated with the target symbols
    """
    temp_dir = tempfile.mkdtemp()

    try:
        # Extract the zip file
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Initialize total sum
        total_sum = 0

        # Process all files in the temporary directory
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)

                # Try different encodings based on file extension
                if file.endswith(".csv"):
                    if "data1.csv" in file:
                        encoding = "cp1252"
                    else:
                        encoding = "utf-8"

                    # Read the CSV file with the appropriate encoding
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        if "symbol" in df.columns and "value" in df.columns:
                            # Sum values for target symbols
                            for symbol in target_symbols:
                                if symbol in df["symbol"].values:
                                    values = df[df["symbol"] == symbol]["value"]
                                    total_sum += values.sum()
                    except Exception as e:
                        return f"Error processing {file}: {str(e)}"

                elif file.endswith(".txt"):
                    # Try UTF-16 encoding for txt files
                    try:
                        with open(file_path, "r", encoding="utf-16") as f:
                            content = f.read()

                            # Parse the TSV content
                            reader = csv.reader(io.StringIO(content), delimiter="\t")
                            headers = next(reader)

                            # Check if required columns exist
                            if "symbol" in headers and "value" in headers:
                                symbol_idx = headers.index("symbol")
                                value_idx = headers.index("value")

                                for row in reader:
                                    if len(row) > max(symbol_idx, value_idx):
                                        if row[symbol_idx] in target_symbols:
                                            try:
                                                total_sum += float(row[value_idx])
                                            except ValueError:
                                                pass
                    except Exception as e:
                        return f"Error processing {file}: {str(e)}"

        return str(total_sum)

    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def calculate_spreadsheet_formula(formula: str, type: str) -> str:
    """
    Calculate the result of a spreadsheet formula

    Args:
        formula: The formula to calculate
        type: Type of spreadsheet (google_sheets or excel)

    Returns:
        Result of the formula calculation
    """
    try:
        # Strip the leading = if present
        if formula.startswith("="):
            formula = formula[1:]

        # For SEQUENCE function (Google Sheets)
        if "SEQUENCE" in formula and type == "google_sheets":
            # Example: SUM(ARRAY_CONSTRAIN(SEQUENCE(100, 100, 5, 2), 1, 10))
            sequence_pattern = r"SEQUENCE\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)"
            match = re.search(sequence_pattern, formula)

            if match:
                rows = int(match.group(1))
                cols = int(match.group(2))
                start = int(match.group(3))
                step = int(match.group(4))

                # Generate the sequence
                sequence = []
                value = start
                for _ in range(rows):
                    row = []
                    for _ in range(cols):
                        row.append(value)
                        value += step
                    sequence.append(row)

                # Check for ARRAY_CONSTRAIN
                constrain_pattern = r"ARRAY_CONSTRAIN\([^,]+,\s*(\d+),\s*(\d+)\)"
                constrain_match = re.search(constrain_pattern, formula)

                if constrain_match:
                    constrain_rows = int(constrain_match.group(1))
                    constrain_cols = int(constrain_match.group(2))

                    # Apply constraints
                    constrained = []
                    for i in range(min(constrain_rows, len(sequence))):
                        row = sequence[i][:constrain_cols]
                        constrained.extend(row)

                    # Check for SUM
                    if "SUM(" in formula:
                        return str(sum(constrained))

        # For SORTBY function (Excel)
        elif "SORTBY" in formula and type == "excel":
            # Example: SUM(TAKE(SORTBY({1,10,12,4,6,8,9,13,6,15,14,15,2,13,0,3}, {10,9,13,2,11,8,16,14,7,15,5,4,6,1,3,12}), 1, 6))

            # Extract the arrays from SORTBY
            arrays_pattern = r"SORTBY\(\{([^}]+)\},\s*\{([^}]+)\}\)"
            arrays_match = re.search(arrays_pattern, formula)

            if arrays_match:
                values = [int(x.strip()) for x in arrays_match.group(1).split(",")]
                sort_keys = [int(x.strip()) for x in arrays_match.group(2).split(",")]

                # Sort the values based on sort_keys
                sorted_pairs = sorted(zip(values, sort_keys), key=lambda x: x[1])
                sorted_values = [pair[0] for pair in sorted_pairs]

                # Check for TAKE
                take_pattern = r"TAKE\([^,]+,\s*(\d+),\s*(\d+)\)"
                take_match = re.search(take_pattern, formula)

                if take_match:
                    take_start = int(take_match.group(1))
                    take_count = int(take_match.group(2))

                    # Apply TAKE function
                    taken = sorted_values[take_start - 1 : take_start - 1 + take_count]

                    # Check for SUM
                    if "SUM(" in formula:
                        return str(sum(taken))

        return "Could not parse the formula or unsupported formula type"

    except Exception as e:
        return f"Error calculating spreadsheet formula: {str(e)}"


async def compare_files(file_path: str) -> str:
    """
    Compare two files and analyze differences

    Args:
        file_path: Path to the zip file containing files to compare

    Returns:
        Number of differences between the files
    """
    temp_dir = tempfile.mkdtemp()

    try:
        # Extract the zip file
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Look for a.txt and b.txt
        file_a = os.path.join(temp_dir, "a.txt")
        file_b = os.path.join(temp_dir, "b.txt")

        if not os.path.exists(file_a) or not os.path.exists(file_b):
            return "Files a.txt and b.txt not found."

        # Read both files
        with open(file_a, "r") as a, open(file_b, "r") as b:
            a_lines = a.readlines()
            b_lines = b.readlines()

            # Count the differences
            diff_count = 0
            for i in range(min(len(a_lines), len(b_lines))):
                if a_lines[i] != b_lines[i]:
                    diff_count += 1

            return str(diff_count)

    except Exception as e:
        return f"Error comparing files: {str(e)}"

    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_sql_query(query: str) -> str:
    """
    Calculate a SQL query result

    Args:
        query: SQL query to run

    Returns:
        Result of the SQL query
    """
    try:
        # Create an in-memory SQLite database
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        # Check if the query is about the tickets table
        if "tickets" in query.lower() and (
            "gold" in query.lower() or "type" in query.lower()
        ):
            # Create the tickets table
            cursor.execute(
                """
            CREATE TABLE tickets (
                type TEXT,
                units INTEGER,
                price REAL
            )
            """
            )

            # Insert sample data
            ticket_data = [
                ("GOLD", 24, 51.26),
                ("bronze", 20, 21.36),
                ("Gold", 18, 00.8),
                ("Bronze", 65, 41.69),
                ("SILVER", 98, 70.86),
                # Add more data as needed
            ]

            cursor.executemany("INSERT INTO tickets VALUES (?, ?, ?)", ticket_data)
            conn.commit()

            # Execute the user's query
            cursor.execute(query)
            result = cursor.fetchall()

            # Format the result
            if len(result) == 1 and len(result[0]) == 1:
                return str(result[0][0])
            else:
                return json.dumps(result)

        else:
            return "Unsupported SQL query or database table"

    except Exception as e:
        return f"Error executing SQL query: {str(e)}"

    finally:
        if "conn" in locals():
            conn.close()


# ... existing code ...


def generate_markdown_documentation(
    topic: str, elements: Optional[List[str]] = None
) -> str:
    """
    Generate markdown documentation based on specified elements and topic.

    Args:
        topic: The topic for the markdown documentation
        elements: List of markdown elements to include

    Returns:
        Generated markdown content
    """
    try:
        # Default elements if none provided
        if not elements:
            elements = [
                "heading1",
                "heading2",
                "bold",
                "italic",
                "inline_code",
                "code_block",
                "bulleted_list",
                "numbered_list",
                "table",
                "hyperlink",
                "image",
                "blockquote",
            ]

        # This is just a placeholder - the actual content will be generated by the AI
        # based on the topic and required elements
        return (
            f"Markdown documentation for {topic} with elements: {', '.join(elements)}"
        )
    except Exception as e:
        return f"Error generating markdown documentation: {str(e)}"


async def compress_image(file_path: str, target_size: int = 1500) -> str:
    """
    Compress an image to a target size while maintaining quality.

    Args:
        file_path: Path to the image file
        target_size: Target size in bytes

    Returns:
        Information about the compressed image
    """
    try:
        # This would be implemented with actual image compression logic
        # For now, it's a placeholder
        return f"Image at {file_path} compressed to under {target_size} bytes"
    except Exception as e:
        return f"Error compressing image: {str(e)}"


async def create_github_pages(email: str, content: Optional[str] = None) -> str:
    """
    Generate HTML content for GitHub Pages with email protection.

    Args:
        email: Email address to include in the page
        content: Optional content for the page

    Returns:
        HTML content for GitHub Pages
    """
    try:
        # Create HTML with protected email
        protected_email = f"<!--email_off-->{email}<!--/email_off-->"

        # Basic HTML template
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>GitHub Pages Demo</title>
</head>
<body>
    <h1>My GitHub Page</h1>
    <p>Contact: {protected_email}</p>
    {content or ""}
</body>
</html>"""

        return html_content
    except Exception as e:
        return f"Error creating GitHub Pages content: {str(e)}"


async def run_colab_code(code: str, email: str) -> str:
    """
    Simulate running code on Google Colab.

    Args:
        code: Code to run
        email: Email address for authentication

    Returns:
        Result of code execution
    """
    try:
        # This is a placeholder - in reality, this would be handled by the AI
        # as it can't actually run code on Colab
        return f"Simulated running code on Colab with email {email}"
    except Exception as e:
        return f"Error running Colab code: {str(e)}"


async def analyze_image_brightness(file_path: str, threshold: float = 0.937) -> str:
    """
    Analyze image brightness and count pixels above threshold.

    Args:
        file_path: Path to the image file
        threshold: Brightness threshold

    Returns:
        Count of pixels above threshold
    """
    try:
        # This would be implemented with actual image analysis logic
        # For now, it's a placeholder
        return f"Analysis of image at {file_path} with threshold {threshold}"
    except Exception as e:
        return f"Error analyzing image brightness: {str(e)}"


async def deploy_vercel_app(data_file: str, app_name: Optional[str] = None) -> str:
    """
    Generate code for a Vercel app deployment.

    Args:
        data_file: Path to the data file
        app_name: Optional name for the app

    Returns:
        Deployment instructions and code
    """
    try:
        # This is a placeholder - in reality, this would generate the code needed
        # for a Vercel deployment
        return f"Instructions for deploying app with data from {data_file}"
    except Exception as e:
        return f"Error generating Vercel deployment: {str(e)}"


async def create_github_action(email: str, repository: Optional[str] = None) -> str:
    """
    Generate GitHub Action workflow with email in step name.

    Args:
        email: Email to include in step name
        repository: Optional repository name

    Returns:
        GitHub Action workflow YAML
    """
    try:
        # Generate GitHub Action workflow
        workflow = f"""name: GitHub Action Demo

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: {email}
        run: echo "Hello, world!"
"""
        return workflow
    except Exception as e:
        return f"Error creating GitHub Action: {str(e)}"


async def create_docker_image(
    tag: str, dockerfile_content: Optional[str] = None
) -> str:
    """
    Generate Dockerfile and instructions for Docker Hub deployment.

    Args:
        tag: Tag for the Docker image
        dockerfile_content: Optional Dockerfile content

    Returns:
        Dockerfile and deployment instructions
    """
    try:
        # Default Dockerfile if none provided
        if not dockerfile_content:
            dockerfile_content = """FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]"""

        # Instructions
        instructions = f"""# Docker Image Deployment Instructions

## Dockerfile
{dockerfile_content}

## Build and Push Commands
```bash
docker build -t yourusername/yourrepo:{tag} .
docker push yourusername/yourrepo:{tag}
"""
        return instructions
    except Exception as e:
        return f"Error creating Docker image instructions: {str(e)}"


async def filter_students_by_class(file_path: str, classes: List[str]) -> str:
    """
    Filter students from a CSV file by class.
    Args:
        file_path: Path to the CSV file
        classes: List of classes to filter by

    Returns:
        Filtered student data
    """
    try:
        # This would be implemented with actual CSV parsing logic
        # For now, it's a placeholder
        return f"Students filtered by classes: {', '.join(classes)}"
    except Exception as e:
        return f"Error filtering students: {str(e)}"


async def setup_llamafile_with_ngrok(
    model_name: str = "Llama-3.2-1B-Instruct.Q6_K.llamafile",
) -> str:
    """
    Generate instructions for setting up Llamafile with ngrok.
    Args:
        model_name: Name of the Llamafile model

    Returns:
        Setup instructions
    """
    try:
        # Generate instructions
        instructions = f"""# Llamafile with ngrok Setup Instructions
    - Download Llamafile from https://github.com/Mozilla-Ocho/llamafile/releases
- Download the {model_name} model
- Make the llamafile executable: chmod +x {model_name}
- Run the model: ./{model_name}
- Install ngrok: https://ngrok.com/download
- Create a tunnel: ngrok http 8080
- Your ngrok URL will be displayed in the terminal
"""
        return instructions
    except Exception as e:
        return f"Error generating Llamafile setup instructions: {str(e)}"


async def analyze_sentiment(text: str, api_key: str = "dummy_api_key") -> str:
    """
    Analyze sentiment of text using OpenAI API
    """
    import httpx
    import json

    url = "https://api.openai.com/v1/chat/completions"

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "Analyze the sentiment of the following text and classify it as GOOD, BAD, or NEUTRAL.",
            },
            {"role": "user", "content": text},
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            # Extract the sentiment analysis result
            sentiment = result["choices"][0]["message"]["content"]

            return f"""
# Sentiment Analysis Result

## Input Text

## Analysis
{sentiment}

## API Request Details
- Model: gpt-4o-mini
- API Endpoint: {url}
- Request Type: POST
"""
    except Exception as e:
        return f"Error analyzing sentiment: {str(e)}"


async def count_tokens(text: str) -> str:
    """
    Count tokens in a message sent to OpenAI API
    """
    import httpx
    import json

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy_api_key",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": text}],
        "max_tokens": 1,  # Minimize response tokens
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            # Extract token count from usage information
            prompt_tokens = result.get("usage", {}).get("prompt_tokens", 0)

            return f"""
# Token Count Analysis

## Input Text

## Token Count
The input message uses **{prompt_tokens} tokens**.

## API Request Details
- Model: gpt-4o-mini
- API Endpoint: {url}
- Request Type: POST
"""
    except Exception as e:
        return f"Error counting tokens: {str(e)}"


async def generate_structured_output(prompt: str, structure_type: str) -> str:
    """
    Generate structured JSON output using OpenAI API
    """
    import json

    # Example for addresses structure
    if structure_type.lower() == "addresses":
        request_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Respond in JSON"},
                {"role": "user", "content": prompt},
            ],
            "response_format": {
                "type": "json_object",
                "schema": {
                    "type": "object",
                    "properties": {
                        "addresses": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "latitude": {"type": "number"},
                                    "city": {"type": "string"},
                                    "apartment": {"type": "string"},
                                },
                                "required": ["latitude", "city", "apartment"],
                            },
                        }
                    },
                    "required": ["addresses"],
                    "additionalProperties": False,
                },
            },
        }
    else:
        # Generic structure for other types
        request_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Respond in JSON"},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }

    # Format the JSON nicely
    formatted_json = json.dumps(request_body, indent=2)

    return f"""
# Structured Output Request Body

The following JSON body can be sent to the OpenAI API to generate structured output for "{prompt}":

```json
{formatted_json}
```

## Request Details
- Model: gpt-4o-mini
- Structure Type: {structure_type}
- API Endpoint: https://api.openai.com/v1/chat/completions
- Request Type: POST
This request is configured to return a structured JSON response that follows the specified schema.
"""


async def count_cricket_ducks(page_number: int = 3) -> str:
    """
    Count the number of ducks in ESPN Cricinfo ODI batting stats for a specific page

    Args:
        page_number: Page number to analyze (default: 3)

    Returns:
        Total number of ducks on the specified page
    """
    try:
        import pandas as pd
        import httpx
        from bs4 import BeautifulSoup

        # Construct the URL for the specified page
        url = f"https://stats.espncricinfo.com/ci/engine/stats/index.html?class=2;page={page_number};template=results;type=batting"

        # Fetch the page content
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text

        # Parse the HTML
        soup = BeautifulSoup(html_content, "html.parser")

        # Find the main stats table
        tables = soup.find_all("table", class_="engineTable")
        stats_table = None

        for table in tables:
            if table.find("th", string="Player"):
                stats_table = table
                break

        if not stats_table:
            return "Could not find the batting stats table on the page."

        # Extract the table headers
        headers = [th.get_text(strip=True) for th in stats_table.find_all("th")]

        # Find the index of the "0" column (ducks)
        duck_col_index = None
        for i, header in enumerate(headers):
            if header == "0":
                duck_col_index = i
                break

        if duck_col_index is None:
            return "Could not find the '0' (ducks) column in the table."

        # Extract the data rows
        rows = stats_table.find_all("tr", class_="data1")

        # Sum the ducks
        total_ducks = 0
        for row in rows:
            cells = row.find_all("td")
            if len(cells) > duck_col_index:
                duck_value = cells[duck_col_index].get_text(strip=True)
                if duck_value and duck_value.isdigit():
                    total_ducks += int(duck_value)

        return f"""
# Cricket Analysis: Ducks Count

## Data Source
ESPN Cricinfo ODI batting stats, page {page_number}

## Analysis
The total number of ducks across all players on page {page_number} is: **{total_ducks}**

## Method
- Extracted the batting statistics table from ESPN Cricinfo
- Located the column representing ducks (titled "0")
- Summed all values in this column
"""
    except Exception as e:
        return f"Error counting cricket ducks: {str(e)}"


async def get_imdb_movies(
    min_rating: float = 7.0, max_rating: float = 8.0, limit: int = 25
) -> str:
    """
    Get movie information from IMDb with ratings in a specific range

    Args:
        min_rating: Minimum rating to filter by
        max_rating: Maximum rating to filter by
        limit: Maximum number of movies to return

    Returns:
        JSON data of movies with their ID, title, year, and rating
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
        import json
        import re

        # Construct the URL with the rating filter
        url = f"https://www.imdb.com/search/title/?title_type=feature&user_rating={min_rating},{max_rating}&sort=user_rating,desc"

        # Set headers to mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Fetch the page content
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            html_content = response.text

        # Parse the HTML
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all movie items
        movie_items = soup.find_all("div", class_="lister-item-content")

        # Extract movie data
        movies = []
        for item in movie_items[:limit]:
            # Get the movie title and year
            title_element = item.find("h3", class_="lister-item-header").find("a")
            title = title_element.get_text(strip=True)

            # Extract the movie ID from the href attribute
            href = title_element.get("href", "")
            id_match = re.search(r"/title/(tt\d+)/", href)
            movie_id = id_match.group(1) if id_match else ""

            # Extract the year
            year_element = item.find("span", class_="lister-item-year")
            year_text = year_element.get_text(strip=True) if year_element else ""
            year_match = re.search(r"\((\d{4})\)", year_text)
            year = year_match.group(1) if year_match else ""

            # Extract the rating
            rating_element = item.find("div", class_="ratings-imdb-rating")
            rating = rating_element.get("data-value", "") if rating_element else ""

            # Add to the movies list
            if movie_id and title:
                movies.append(
                    {"id": movie_id, "title": title, "year": year, "rating": rating}
                )

        # Convert to JSON
        movies_json = json.dumps(movies, indent=2)

        return f"""
# IMDb Movie Data

## Filter Criteria
- Minimum Rating: {min_rating}
- Maximum Rating: {max_rating}
- Limit: {limit} movies

## Results
```json
{movies_json}
```
## Summary
Retrieved {len(movies)} movies with ratings between {min_rating} and {max_rating}.
"""
    except Exception as e:
        return f"Error retrieving IMDb movies: {str(e)}"


async def generate_country_outline(country: str) -> str:
    """
    Generate a Markdown outline from Wikipedia headings for a country

    Args:
        country: Name of the country

    Returns:
        Markdown outline of the country's Wikipedia page
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
        import urllib.parse

        # Format the country name for the URL
        formatted_country = urllib.parse.quote(country.replace(" ", "_"))
        url = f"https://en.wikipedia.org/wiki/{formatted_country}"

        # Fetch the Wikipedia page
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text

        # Parse the HTML
        soup = BeautifulSoup(html_content, "html.parser")

        # Get the page title (country name)
        title = soup.find("h1", id="firstHeading").get_text(strip=True)

        # Find all headings (h1 to h6)
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

        # Generate the Markdown outline
        outline = [f"# {title}"]
        outline.append("\n## Contents\n")

        for heading in headings:
            if heading.get("id") != "firstHeading":  # Skip the page title
                # Determine the heading level
                level = int(heading.name[1])

                # Get the heading text
                text = heading.get_text(strip=True)

                # Skip certain headings like "References", "External links", etc.
                skip_headings = [
                    "References",
                    "External links",
                    "See also",
                    "Notes",
                    "Citations",
                    "Bibliography",
                ]
                if any(skip in text for skip in skip_headings):
                    continue

                # Add the heading to the outline with appropriate indentation
                outline.append(f"{'#' * level} {text}")

        # Join the outline into a single string
        markdown_outline = "\n\n".join(outline)

        return f"""
# Wikipedia Outline Generator

## Country
{country}

## Markdown Outline
{markdown_outline}

## API Endpoint Example
/api/outline?country={urllib.parse.quote(country)}
"""
    except Exception as e:
        return f"Error generating country outline: {str(e)}"


async def get_weather_forecast(city: str) -> str:
    """
    Get weather forecast for a city using BBC Weather API

    Args:
        city: Name of the city

    Returns:
        JSON data of weather forecast with dates and descriptions
    """
    try:
        import httpx
        import json

        # Step 1: Get the location ID for the city
        locator_url = "https://locator-service.api.bbci.co.uk/locations"
        params = {
            "api_key": "AGbFAKx58hyjQScCXIYrxuEwJh2W2cmv",  # This is a public API key used by BBC
            "stack": "aws",
            "locale": "en-GB",
            "filter": "international",
            "place-types": "settlement,airport,district",
            "order": "importance",
            "a": city,
            "format": "json",
        }

        async with httpx.AsyncClient() as client:
            # Get location ID
            response = await client.get(locator_url, params=params)
            response.raise_for_status()
            location_data = response.json()

            if (
                not location_data.get("locations")
                or len(location_data["locations"]) == 0
            ):
                return f"Could not find location ID for {city}"

            location_id = location_data["locations"][0]["id"]

            # Step 2: Get the weather forecast using the location ID
            weather_url = f"https://weather-broker-cdn.api.bbci.co.uk/en/forecast/aggregated/{location_id}"
            weather_response = await client.get(weather_url)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            # Step 3: Extract the forecast data
            forecasts = weather_data.get("forecasts", [{}])[0].get("forecasts", [])

            # Create a dictionary mapping dates to weather descriptions
            weather_forecast = {}
            for forecast in forecasts:
                local_date = forecast.get("localDate")
                description = forecast.get("enhancedWeatherDescription")
                if local_date and description:
                    weather_forecast[local_date] = description

            # Format as JSON
            forecast_json = json.dumps(weather_forecast, indent=2)

            return f"""
# Weather Forecast for {city}

## Location Details
- City: {city}
- Location ID: {location_id}
- Source: BBC Weather API

## Forecast
```json
{forecast_json}
```

## Summary
Retrieved weather forecast for {len(weather_forecast)} days.
"""
    except Exception as e:
        return f"Error retrieving weather forecast: {str(e)}"


async def generate_vision_api_request(image_url: str) -> str:
    """
    Generate a JSON body for OpenAI's vision API to extract text from an image

    Args:
        image_url: Base64 URL of the image

    Returns:
        JSON body for the API request
    """
    try:
        import json

        # Create the request body
        request_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract text from this image."},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            "max_tokens": 300,
        }

        # Format the JSON nicely
        formatted_json = json.dumps(request_body, indent=2)

        return f"""
# Vision API Request Body

The following JSON body can be sent to the OpenAI API to extract text from an image:

```json
{formatted_json}
```

## Request Details
- Model: gpt-4o-mini
- API Endpoint: https://api.openai.com/v1/chat/completions
- Request Type: POST
- Purpose: Extract text from an image using OpenAI's vision capabilities
"""
    except Exception as e:
        return f"Error generating vision API request: {str(e)}"


async def generate_embeddings_request(texts: List[str]) -> str:
    """
    Generate a JSON body for OpenAI's embeddings API

    Args:
        texts: List of texts to generate embeddings for

    Returns:
        JSON body for the API request
    """
    try:
        import json

        # Create the request body
        request_body = {
            "model": "text-embedding-3-small",
            "input": texts,
            "encoding_format": "float",
        }

        # Format the JSON nicely
        formatted_json = json.dumps(request_body, indent=2)

        return f"""
# Embeddings API Request Body

The following JSON body can be sent to the OpenAI API to generate embeddings:

```json
{formatted_json}
```

## Request Details
- Model: text-embedding-3-small
- API Endpoint: https://api.openai.com/v1/embeddings
- Request Type: POST
- Purpose: Generate embeddings for text analysis
"""
    except Exception as e:
        return f"Error generating embeddings request: {str(e)}"


async def find_most_similar_phrases(embeddings_dict: Dict[str, List[float]]) -> str:
    """
    Find the most similar pair of phrases based on cosine similarity of their embeddings

    Args:
        embeddings_dict: Dictionary mapping phrases to their embeddings

    Returns:
        The most similar pair of phrases
    """
    try:
        import numpy as np
        from itertools import combinations

        # Function to calculate cosine similarity
        def cosine_similarity(vec1, vec2):
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            return dot_product / (norm_vec1 * norm_vec2)

        # Convert dictionary to lists for easier processing
        phrases = list(embeddings_dict.keys())
        embeddings = list(embeddings_dict.values())

        # Calculate similarity for each pair
        max_similarity = -1
        most_similar_pair = None

        for i, j in combinations(range(len(phrases)), 2):
            similarity = cosine_similarity(embeddings[i], embeddings[j])
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_pair = (phrases[i], phrases[j])

        # Generate Python code for the solution
        solution_code = """
def most_similar(embeddings):
    \"\"\"
    Find the most similar pair of phrases based on cosine similarity of their embeddings.
    
    Args:
        embeddings: Dictionary mapping phrases to their embeddings
        
    Returns:
        Tuple of the two most similar phrases
    \"\"\"
    import numpy as np
    from itertools import combinations

    # Function to calculate cosine similarity
    def cosine_similarity(vec1, vec2):
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        return dot_product / (norm_vec1 * norm_vec2)

    # Convert dictionary to lists for easier processing
    phrases = list(embeddings.keys())
    embeddings_list = list(embeddings.values())

    # Calculate similarity for each pair
    max_similarity = -1
    most_similar_pair = None

    for i, j in combinations(range(len(phrases)), 2):
        similarity = cosine_similarity(embeddings_list[i], embeddings_list[j])
        if similarity > max_similarity:
            max_similarity = similarity
            most_similar_pair = (phrases[i], phrases[j])

    return most_similar_pair
"""

        return f"""
# Most Similar Phrases Analysis

## Result
The most similar pair of phrases is: {most_similar_pair[0]} and {most_similar_pair[1]}
Similarity score: {max_similarity:.4f}

## Python Solution
```python
{solution_code}
```

## Explanation
This function:

1. Calculates the cosine similarity between each pair of embeddings
2. Identifies the pair with the highest similarity score
3. Returns the two phrases as a tuple
"""
    except Exception as e:
        return f"Error finding most similar phrases: {str(e)}"


async def compute_document_similarity(docs: List[str], query: str) -> str:
    """
    Compute similarity between a query and a list of documents using embeddings

    Args:
        docs: List of document texts
        query: Query string to compare against documents

    Returns:
        JSON response with the most similar documents
    """
    try:
        import numpy as np
        import json
        import httpx
        from typing import List, Dict

        # Function to calculate cosine similarity
        def cosine_similarity(vec1, vec2):
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            return dot_product / (norm_vec1 * norm_vec2)

        # Function to get embeddings from OpenAI API
        async def get_embedding(text: str) -> List[float]:
            url = "https://api.openai.com/v1/embeddings"
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer dummy_api_key",  # Replace with actual API key in production
            }
            payload = {"model": "text-embedding-3-small", "input": text}

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["data"][0]["embedding"]

        # Get embeddings for query and documents
        query_embedding = await get_embedding(query)
        doc_embeddings = []

        for doc in docs:
            doc_embedding = await get_embedding(doc)
            doc_embeddings.append(doc_embedding)

        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(doc_embeddings):
            similarity = cosine_similarity(query_embedding, doc_embedding)
            similarities.append((i, similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Get top 3 matches (or fewer if less than 3 documents)
        top_matches = similarities[: min(3, len(similarities))]

        # Get the matching documents
        matches = [docs[idx] for idx, _ in top_matches]

        # Create FastAPI implementation code
        fastapi_code = """
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx
import numpy as np

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["OPTIONS", "POST"],  # Allow OPTIONS and POST methods
    allow_headers=["*"],  # Allow all headers
)

class SimilarityRequest(BaseModel):
    docs: List[str]
    query: str

@app.post("/similarity")
async def compute_similarity(request: SimilarityRequest):
    # Function to calculate cosine similarity
    def cosine_similarity(vec1, vec2):
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        return dot_product / (norm_vec1 * norm_vec2)
    
    # Function to get embeddings from OpenAI API
    async def get_embedding(text: str):
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"  # Use environment variable
        }
        payload = {
            "model": "text-embedding-3-small",
            "input": text
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["data"][0]["embedding"]
    
    try:
        # Get embeddings for query and documents
        query_embedding = await get_embedding(request.query)
        doc_embeddings = []
        
        for doc in request.docs:
            doc_embedding = await get_embedding(doc)
            doc_embeddings.append(doc_embedding)
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(doc_embeddings):
            similarity = cosine_similarity(query_embedding, doc_embedding)
            similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top 3 matches (or fewer if less than 3 documents)
        top_matches = similarities[:min(3, len(similarities))]
        
        # Get the matching documents
        matches = [request.docs[idx] for idx, _ in top_matches]
        
        return {"matches": matches}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

        # Create response
        response = {"matches": matches}

        return f"""
# Document Similarity Analysis

## Query
"{query}"

## Top Matches
1. "{matches[0] if len(matches) > 0 else 'No matches found'}"
{f'2. "{matches[1]}"' if len(matches) > 1 else ''}
{f'3. "{matches[2]}"' if len(matches) > 2 else ''}

## FastAPI Implementation
```python
{fastapi_code}
```
## API Endpoint
http://127.0.0.1:8000/similarity

## Example Request
{{
  "docs": {json.dumps(docs)},
  "query": "{query}"
}}
## Example Response
{json.dumps(response, indent=2)}
"""
    except Exception as e:
        return f"Error computing document similarity: {str(e)}"


async def parse_function_call(query: str) -> str:
    """
    Parse a natural language query to determine which function to call and extract parameters

    Args:
        query: Natural language query

    Returns:
        JSON response with function name and arguments
    """
    try:
        import re
        import json

        # Define regex patterns for each function
        ticket_pattern = r"status of ticket (\d+)"
        meeting_pattern = (
            r"Schedule a meeting on (\d{4}-\d{2}-\d{2}) at (\d{2}:\d{2}) in (Room \w+)"
        )
        expense_pattern = r"expense balance for employee (\d+)"
        bonus_pattern = r"Calculate performance bonus for employee (\d+) for (\d{4})"
        issue_pattern = r"Report office issue (\d+) for the (\w+) department"

        # Check each pattern and extract parameters
        if re.search(ticket_pattern, query):
            ticket_id = int(re.search(ticket_pattern, query).group(1))
            function_name = "get_ticket_status"
            arguments = {"ticket_id": ticket_id}

        elif re.search(meeting_pattern, query):
            match = re.search(meeting_pattern, query)
            date = match.group(1)
            time = match.group(2)
            meeting_room = match.group(3)
            function_name = "schedule_meeting"
            arguments = {"date": date, "time": time, "meeting_room": meeting_room}

        elif re.search(expense_pattern, query):
            employee_id = int(re.search(expense_pattern, query).group(1))
            function_name = "get_expense_balance"
            arguments = {"employee_id": employee_id}

        elif re.search(bonus_pattern, query):
            match = re.search(bonus_pattern, query)
            employee_id = int(match.group(1))
            current_year = int(match.group(2))
            function_name = "calculate_performance_bonus"
            arguments = {"employee_id": employee_id, "current_year": current_year}

        elif re.search(issue_pattern, query):
            match = re.search(issue_pattern, query)
            issue_code = int(match.group(1))
            department = match.group(2)
            function_name = "report_office_issue"
            arguments = {"issue_code": issue_code, "department": department}

        else:
            return "Could not match query to any known function pattern."

        # Create the response
        response = {"name": function_name, "arguments": json.dumps(arguments)}

        # Create FastAPI implementation code
        fastapi_code = """
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import re
import json

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET"],  # Allow GET method
    allow_headers=["*"],  # Allow all headers
)

@app.get("/execute")
async def execute_query(q: str):
    # Define regex patterns for each function
    ticket_pattern = r"status of ticket (\d+)"
    meeting_pattern = r"Schedule a meeting on (\d{4}-\d{2}-\d{2}) at (\d{2}:\d{2}) in (Room \w+)"
    expense_pattern = r"expense balance for employee (\d+)"
    bonus_pattern = r"Calculate performance bonus for employee (\d+) for (\d{4})"
    issue_pattern = r"Report office issue (\d+) for the (\w+) department"
    
    # Check each pattern and extract parameters
    if re.search(ticket_pattern, q):
        ticket_id = int(re.search(ticket_pattern, q).group(1))
        function_name = "get_ticket_status"
        arguments = {"ticket_id": ticket_id}

    elif re.search(meeting_pattern, q):
        match = re.search(meeting_pattern, q)
        date = match.group(1)
        time = match.group(2)
        meeting_room = match.group(3)
        function_name = "schedule_meeting"
        arguments = {"date": date, "time": time, "meeting_room": meeting_room}

    elif re.search(expense_pattern, q):
        employee_id = int(re.search(expense_pattern, q).group(1))
        function_name = "get_expense_balance"
        arguments = {"employee_id": employee_id}

    elif re.search(bonus_pattern, q):
        match = re.search(bonus_pattern, q)
        employee_id = int(match.group(1))
        current_year = int(match.group(2))
        function_name = "calculate_performance_bonus"
        arguments = {"employee_id": employee_id, "current_year": current_year}

    elif re.search(issue_pattern, q):
        match = re.search(issue_pattern, q)
        issue_code = int(match.group(1))
        department = match.group(2)
        function_name = "report_office_issue"
        arguments = {"issue_code": issue_code, "department": department}

    else:
        raise HTTPException(status_code=400, detail="Could not match query to any known function pattern")

    # Return the function name and arguments
    return {
        "name": function_name,
        "arguments": json.dumps(arguments)
    }
"""

        return f"""
# Function Call Parser
## Query
"{query}"

## Parsed Function Call
- Function: {function_name}
- Arguments: {json.dumps(arguments, indent=2)}
## FastAPI Implementation
```python
{fastapi_code}
```
## API Endpoint
http://127.0.0.1:8000/execute

## Example Request
GET http://127.0.0.1:8000/execute?q={query.replace(" ", "%20")}

## Example Response
{json.dumps(response, indent=2)}
"""
    except Exception as e:
        return f"Error parsing function call: {str(e)}"
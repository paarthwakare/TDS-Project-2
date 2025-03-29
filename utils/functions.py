import os
import zipfile
import pandas as pd
import httpx
import json
import shutil
import tempfile
from typing import Dict, Any, List, Optional

async def extract_zip_and_read_csv(file_path: str, column_name: Optional[str] = None) -> str:
    """
    Extract a zip file and read a value from a CSV file inside it.
    """
    # Create a temporary directory to extract the zip file
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Extract the zip file
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find CSV files in the extracted directory
        csv_files = [f for f in os.listdir(temp_dir) if f.endswith('.csv')]
        
        if not csv_files:
            return "No CSV files found in the zip file."
        
        # Read the first CSV file
        csv_path = os.path.join(temp_dir, csv_files[0])
        df = pd.read_csv(csv_path)
        
        # If a column name is specified, return the value from that column
        if column_name and column_name in df.columns:
            if column_name == "answer":
                return str(df[column_name].iloc[0])
            else:
                return str(df[column_name].values.tolist())
        
        # Otherwise, return the first value from the "answer" column if it exists
        elif "answer" in df.columns:
            return str(df["answer"].iloc[0])
        
        # If no specific column is requested, return a summary of the CSV
        else:
            return f"CSV contains columns: {', '.join(df.columns)}"
    
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

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

async def make_api_request(url: str, method: str, headers: Optional[Dict[str, str]] = None, data: Optional[Dict[str, Any]] = None) -> str:
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
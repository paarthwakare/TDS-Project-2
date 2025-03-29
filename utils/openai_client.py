import os
import httpx
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
AIPROXY_BASE_URL = "https://aiproxy.sanand.workers.dev/openai/v1"


async def get_openai_response(question: str, file_path: Optional[str] = None) -> str:
    """
    Get response from OpenAI via AI Proxy
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
    }

    # Define functions for OpenAI to call
    functions = [
        {
            "type": "function",
            "function": {
                "name": "extract_zip_and_read_csv",
                "description": "Extract data from a zip file containing CSV and read specific values",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the zip file",
                        },
                        "column_name": {
                            "type": "string",
                            "description": "Column name to extract value from",
                        },
                    },
                    "required": ["file_path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_statistics",
                "description": "Calculate statistics from a CSV file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the CSV file",
                        },
                        "operation": {
                            "type": "string",
                            "enum": ["sum", "average", "median", "max", "min"],
                            "description": "Statistical operation to perform",
                        },
                        "column_name": {
                            "type": "string",
                            "description": "Column name to perform operation on",
                        },
                    },
                    "required": ["file_path", "operation", "column_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "make_api_request",
                "description": "Make an API request to a specified URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to make the request to",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST"],
                            "description": "HTTP method to use",
                        },
                        "headers": {
                            "type": "object",
                            "description": "Headers to include in the request",
                        },
                        "data": {
                            "type": "object",
                            "description": "Data to include in the request body",
                        },
                    },
                    "required": ["url", "method"],
                },
            },
        },
    ]

    # Create the messages to send to the API
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant designed to solve data science assignment problems. You should use the provided functions when appropriate to solve the problem.",
        },
        {"role": "user", "content": question},
    ]

    # Add information about the file if provided
    if file_path:
        messages.append(
            {
                "role": "user",
                "content": f"I've uploaded a file that you can process. The file is stored at: {file_path}",
            }
        )

    # Prepare the request payload
    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "tools": functions,
        "tool_choice": "auto",
    }

    # Make the request to the AI Proxy
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AIPROXY_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60.0,
        )

        if response.status_code != 200:
            raise Exception(f"Error from OpenAI API: {response.text}")

        result = response.json()

        # Process the response
        message = result["choices"][0]["message"]

        # Check if there's a function call
        if "tool_calls" in message:
            tool_calls = message["tool_calls"]

            # For this example, we'll just return the result as a string
            # In a real implementation, you would execute the function
            # and return the actual result

            # Placeholder for function execution results
            function_results = []

            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])

                # Here you would actually execute the function
                # For now, we'll just return a placeholder
                function_results.append(
                    f"Function {function_name} would be called with args: {function_args}"
                )

            # Return the function results
            return "\n".join(function_results)

        # Return the content if no function call
        return message.get("content", "No response generated")
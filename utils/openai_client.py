import os
import httpx
import json
import re
import zipfile
import pandas as pd
import tempfile
import shutil
import subprocess
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from app.utils.functions import *

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
                "name": "execute_command",
                "description": "Execute a shell command and return its output",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The command to execute",
                        }
                    },
                    "required": ["command"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "extract_zip_and_read_csv",
                "description": "Extract a zip file and read a value from a CSV file inside it",
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
                "name": "extract_zip_and_process_files",
                "description": "Extract a zip file and process multiple files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the zip file",
                        },
                        "operation": {
                            "type": "string",
                            "description": "Operation to perform on files",
                        },
                    },
                    "required": ["file_path", "operation"],
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
        {
            "type": "function",
            "function": {
                "name": "sort_json_array",
                "description": "Sort a JSON array based on specified criteria",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "json_array": {
                            "type": "string",
                            "description": "JSON array to sort",
                        },
                        "sort_keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of keys to sort by",
                        },
                    },
                    "required": ["json_array", "sort_keys"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "count_days_of_week",
                "description": "Count occurrences of a specific day of the week between two dates",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in ISO format (YYYY-MM-DD)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in ISO format (YYYY-MM-DD)",
                        },
                        "day_of_week": {
                            "type": "string",
                            "enum": [
                                "Monday",
                                "Tuesday",
                                "Wednesday",
                                "Thursday",
                                "Friday",
                                "Saturday",
                                "Sunday",
                            ],
                            "description": "Day of the week to count",
                        },
                    },
                    "required": ["start_date", "end_date", "day_of_week"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "process_encoded_files",
                "description": "Process files with different encodings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the zip file containing encoded files",
                        },
                        "target_symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of symbols to search for",
                        },
                    },
                    "required": ["file_path", "target_symbols"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_spreadsheet_formula",
                "description": "Calculate the result of a spreadsheet formula",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "formula": {
                            "type": "string",
                            "description": "The formula to calculate",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["google_sheets", "excel"],
                            "description": "Type of spreadsheet",
                        },
                    },
                    "required": ["formula", "type"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "compare_files",
                "description": "Compare two files and analyze differences",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the zip file containing files to compare",
                        }
                    },
                    "required": ["file_path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_sql_query",
                "description": "Calculate a SQL query result",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query to run"}
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_markdown_documentation",
                "description": "Generate markdown documentation with specific elements",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Topic for the markdown documentation",
                        },
                        "elements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of markdown elements to include",
                        },
                    },
                    "required": ["topic"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "compress_image",
                "description": "Compress an image to a target size while maintaining quality",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the image file",
                        },
                        "target_size": {
                            "type": "integer",
                            "description": "Target size in bytes",
                        },
                    },
                    "required": ["file_path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_github_pages",
                "description": "Generate HTML content for GitHub Pages with email protection",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "Email address to include in the page",
                        },
                        "content": {
                            "type": "string",
                            "description": "Optional content for the page",
                        },
                    },
                    "required": ["email"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_colab_code",
                "description": "Simulate running code on Google Colab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to run",
                        },
                        "email": {
                            "type": "string",
                            "description": "Email address for authentication",
                        },
                    },
                    "required": ["code", "email"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_image_brightness",
                "description": "Analyze image brightness and count pixels above threshold",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the image file",
                        },
                        "threshold": {
                            "type": "number",
                            "description": "Brightness threshold",
                        },
                    },
                    "required": ["file_path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "deploy_vercel_app",
                "description": "Generate code for a Vercel app deployment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data_file": {
                            "type": "string",
                            "description": "Path to the data file",
                        },
                        "app_name": {
                            "type": "string",
                            "description": "Optional name for the app",
                        },
                    },
                    "required": ["data_file"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_github_action",
                "description": "Generate GitHub Action workflow with email in step name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "Email to include in step name",
                        },
                        "repository": {
                            "type": "string",
                            "description": "Optional repository name",
                        },
                    },
                    "required": ["email"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_docker_image",
                "description": "Generate Dockerfile and instructions for Docker Hub deployment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tag": {
                            "type": "string",
                            "description": "Tag for the Docker image",
                        },
                        "dockerfile_content": {
                            "type": "string",
                            "description": "Optional Dockerfile content",
                        },
                    },
                    "required": ["tag"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "filter_students_by_class",
                "description": "Filter students from a CSV file by class",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the CSV file",
                        },
                        "classes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of classes to filter by",
                        },
                    },
                    "required": ["file_path", "classes"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "setup_llamafile_with_ngrok",
                "description": "Generate instructions for setting up Llamafile with ngrok",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model_name": {
                            "type": "string",
                            "description": "Name of the Llamafile model",
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_sentiment",
                "description": "Analyze sentiment of text using OpenAI API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to analyze for sentiment",
                        },
                        "api_key": {
                            "type": "string",
                            "description": "Optional API key for OpenAI",
                        },
                    },
                    "required": ["text"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "count_tokens",
                "description": "Count tokens in a message sent to OpenAI API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to count tokens for",
                        },
                    },
                    "required": ["text"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_structured_output",
                "description": "Generate structured JSON output using OpenAI API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Prompt for generating structured output",
                        },
                        "structure_type": {
                            "type": "string",
                            "description": "Type of structure to generate (e.g., addresses, products)",
                        },
                    },
                    "required": ["prompt", "structure_type"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "count_cricket_ducks",
                "description": "Count the number of ducks in ESPN Cricinfo ODI batting stats for a specific page",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_number": {
                            "type": "integer",
                            "description": "Page number to analyze",
                        },
                    },
                    "required": ["page_number"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_imdb_movies",
                "description": "Get movie information from IMDb with ratings in a specific range",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "min_rating": {
                            "type": "number",
                            "description": "Minimum rating to filter by",
                        },
                        "max_rating": {
                            "type": "number",
                            "description": "Maximum rating to filter by",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of movies to return",
                        },
                    },
                    "required": ["min_rating", "max_rating"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_country_outline",
                "description": "Generate a Markdown outline from Wikipedia headings for a country",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "description": "Name of the country",
                        },
                    },
                    "required": ["country"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather_forecast",
                "description": "Get weather forecast for a city using BBC Weather API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Name of the city",
                        },
                    },
                    "required": ["city"],
                },
            },
        },
    ]

    # Create the messages to send to the API
    messages = [
        {
            "role": "system",
            "content": "You are an assistant designed to solve data science assignment problems. You should use the provided functions when appropriate to solve the problem.",
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
        answer = None

        # Process the response
        message = result["choices"][0]["message"]

        # Check if there's a function call
        if "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])

                # Execute the appropriate function
                if function_name == "execute_command":
                    answer = await execute_command(function_args.get("command"))

                elif function_name == "extract_zip_and_read_csv":
                    answer = await extract_zip_and_read_csv(
                        file_path=function_args.get("file_path", file_path),
                        column_name=function_args.get("column_name"),
                    )

                elif function_name == "extract_zip_and_process_files":
                    answer = await extract_zip_and_process_files(
                        file_path=function_args.get("file_path", file_path),
                        operation=function_args.get("operation"),
                    )

                elif function_name == "make_api_request":
                    answer = await make_api_request(
                        url=function_args.get("url"),
                        method=function_args.get("method"),
                        headers=function_args.get("headers"),
                        data=function_args.get("data"),
                    )

                elif function_name == "sort_json_array":
                    answer = sort_json_array(
                        json_array=function_args.get("json_array"),
                        sort_keys=function_args.get("sort_keys"),
                    )

                elif function_name == "count_days_of_week":
                    answer = count_days_of_week(
                        start_date=function_args.get("start_date"),
                        end_date=function_args.get("end_date"),
                        day_of_week=function_args.get("day_of_week"),
                    )

                elif function_name == "process_encoded_files":
                    answer = await process_encoded_files(
                        file_path=function_args.get("file_path", file_path),
                        target_symbols=function_args.get("target_symbols"),
                    )

                elif function_name == "calculate_spreadsheet_formula":
                    answer = calculate_spreadsheet_formula(
                        formula=function_args.get("formula"),
                        type=function_args.get("type"),
                    )

                elif function_name == "compare_files":
                    answer = await compare_files(
                        file_path=function_args.get("file_path", file_path)
                    )

                elif function_name == "run_sql_query":
                    answer = run_sql_query(query=function_args.get("query"))

                elif function_name == "generate_markdown_documentation":
                    answer = generate_markdown_documentation(
                        topic=function_args.get("topic"),
                        elements=function_args.get("elements"),
                    )

                elif function_name == "compress_image":
                    answer = await compress_image(
                        file_path=function_args.get("file_path", file_path),
                        target_size=function_args.get("target_size", 1500),
                    )

                elif function_name == "create_github_pages":
                    answer = await create_github_pages(
                        email=function_args.get("email"),
                        content=function_args.get("content"),
                    )

                elif function_name == "run_colab_code":
                    answer = await run_colab_code(
                        code=function_args.get("code"),
                        email=function_args.get("email"),
                    )

                elif function_name == "analyze_image_brightness":
                    answer = await analyze_image_brightness(
                        file_path=function_args.get("file_path", file_path),
                        threshold=function_args.get("threshold", 0.937),
                    )

                elif function_name == "deploy_vercel_app":
                    answer = await deploy_vercel_app(
                        data_file=function_args.get("data_file", file_path),
                        app_name=function_args.get("app_name"),
                    )

                elif function_name == "create_github_action":
                    answer = await create_github_action(
                        email=function_args.get("email"),
                        repository=function_args.get("repository"),
                    )

                elif function_name == "create_docker_image":
                    answer = await create_docker_image(
                        tag=function_args.get("tag"),
                        dockerfile_content=function_args.get("dockerfile_content"),
                    )

                elif function_name == "filter_students_by_class":
                    answer = await filter_students_by_class(
                        file_path=function_args.get("file_path", file_path),
                        classes=function_args.get("classes", []),
                    )

                elif function_name == "setup_llamafile_with_ngrok":
                    answer = await setup_llamafile_with_ngrok(
                        model_name=function_args.get(
                            "model_name", "Llama-3.2-1B-Instruct.Q6_K.llamafile"
                        ),
                    )
                elif function_name == "analyze_sentiment":
                    answer = await analyze_sentiment(
                        text=function_args.get("text"),
                        api_key=function_args.get("api_key", "dummy_api_key"),
                    )

                elif function_name == "count_tokens":
                    answer = await count_tokens(
                        text=function_args.get("text"),
                    )

                elif function_name == "generate_structured_output":
                    answer = await generate_structured_output(
                        prompt=function_args.get("prompt"),
                        structure_type=function_args.get("structure_type"),
                    )
                elif function_name == "count_cricket_ducks":
                    answer = await count_cricket_ducks(
                        page_number=function_args.get("page_number", 3),
                    )

                elif function_name == "get_imdb_movies":
                    answer = await get_imdb_movies(
                        min_rating=function_args.get("min_rating", 7.0),
                        max_rating=function_args.get("max_rating", 8.0),
                        limit=function_args.get("limit", 25),
                    )

                elif function_name == "generate_country_outline":
                    answer = await generate_country_outline(
                        country=function_args.get("country"),
                    )

                elif function_name == "get_weather_forecast":
                    answer = await get_weather_forecast(
                        city=function_args.get("city"),
                    )
                # Break after the first function call is executed
                break

        # If no function call was executed, return the content
        if answer is None:
            answer = message.get("content", "No answer could be generated.")

        return answer
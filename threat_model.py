import json
import requests
from anthropic import Anthropic
from mistralai import Mistral, UserMessage
from openai import OpenAI, AzureOpenAI
import streamlit as st
import re

import google.generativeai as genai
from groq import Groq
from utils import process_groq_response, create_reasoning_system_prompt

# Function to convert JSON to Markdown for display.    
def json_to_markdown(threat_model, improvement_suggestions):
    markdown_output = "## Threat Model\n\n"
    
    # Start the markdown table with headers
    markdown_output += "| Threat Type | Scenario | Potential Impact |\n"
    markdown_output += "|-------------|----------|------------------|\n"
    
    # Fill the table rows with the threat model data
    for threat in threat_model:
        markdown_output += f"| {threat['Threat Type']} | {threat['Scenario']} | {threat['Potential Impact']} |\n"
    
    markdown_output += "\n\n## Improvement Suggestions\n\n"
    for suggestion in improvement_suggestions:
        markdown_output += f"- {suggestion}\n"
    
    return markdown_output

# Function to create a prompt for generating a threat model
def create_threat_model_prompt(app_type, authentication, internet_facing, sensitive_data, app_input):
    prompt = f"""
Act as a cyber security expert with more than 20 years experience of using the STRIDE threat modelling methodology to produce comprehensive threat models for a wide range of applications. Your task is to analyze the provided code summary, README content, and application description to produce a list of specific threats for the application.

Pay special attention to the README content as it often provides valuable context about the project's purpose, architecture, and potential security considerations.

For each of the STRIDE categories (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege), list multiple (3 or 4) credible threats if applicable. Each threat scenario should provide a credible scenario in which the threat could occur in the context of the application. It is very important that your responses are tailored to reflect the details you are given.

When providing the threat model, use a JSON formatted response with the keys "threat_model" and "improvement_suggestions". Under "threat_model", include an array of objects with the keys "Threat Type", "Scenario", and "Potential Impact". 

Under "improvement_suggestions", include an array of strings that suggest what additional information or details the user could provide to make the threat model more comprehensive and accurate in the next iteration. Focus on identifying gaps in the provided application description that, if filled, would enable a more detailed and precise threat analysis. For example:
- Missing architectural details that would help identify more specific threats
- Unclear authentication flows that need more detail
- Incomplete data flow descriptions
- Missing technical stack information
- Unclear system boundaries or trust zones
- Incomplete description of sensitive data handling

Do not provide general security recommendations - focus only on what additional information would help create a better threat model.

APPLICATION TYPE: {app_type}
AUTHENTICATION METHODS: {authentication}
INTERNET FACING: {internet_facing}
SENSITIVE DATA: {sensitive_data}
CODE SUMMARY, README CONTENT, AND APPLICATION DESCRIPTION:
{app_input}

Example of expected JSON response format:
  
    {{
      "threat_model": [
        {{
          "Threat Type": "Spoofing",
          "Scenario": "Example Scenario 1",
          "Potential Impact": "Example Potential Impact 1"
        }},
        {{
          "Threat Type": "Spoofing",
          "Scenario": "Example Scenario 2",
          "Potential Impact": "Example Potential Impact 2"
        }},
        // ... more threats
      ],
      "improvement_suggestions": [
        "Please provide more details about the authentication flow between components to better analyze potential authentication bypass scenarios.",
        "Consider adding information about how sensitive data is stored and transmitted to enable more precise data exposure threat analysis.",
        // ... more suggestions for improving the threat model input
      ]
    }}
"""
    return prompt

def create_image_analysis_prompt():
    prompt = """
    You are a Senior Solution Architect tasked with explaining the following architecture diagram to 
    a Security Architect to support the threat modelling of the system.

    In order to complete this task you must:

      1. Analyse the diagram
      2. Explain the system architecture to the Security Architect. Your explanation should cover the key 
         components, their interactions, and any technologies used.
    
    Provide a direct explanation of the diagram in a clear, structured format, suitable for a professional 
    discussion.
    
    IMPORTANT INSTRUCTIONS:
     - Do not include any words before or after the explanation itself. For example, do not start your
    explanation with "The image shows..." or "The diagram shows..." just start explaining the key components
    and other relevant details.
     - Do not infer or speculate about information that is not visible in the diagram. Only provide information that can be
    directly determined from the diagram itself.
    """
    return prompt

# Function to get analyse uploaded architecture diagrams.
def get_image_analysis(api_key, model_name, prompt, base64_image):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        }
    ]

    payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": 4000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    # Log the response for debugging
    try:
        response.raise_for_status()  # Raise an HTTPError for bad responses
        response_content = response.json()
        return response_content
    except requests.exceptions.HTTPError:
        pass
    except Exception:
        pass
    return None


# Function to get threat model from the GPT response.
def get_threat_model(api_key, model_name, prompt):
    client = OpenAI(api_key=api_key)

    # For reasoning models (o1, o3-mini), use a structured system prompt
    if model_name in ["o1", "o3-mini"]:
        system_prompt = create_reasoning_system_prompt(
            task_description="Analyze the provided application description and generate a comprehensive threat model using the STRIDE methodology.",
            approach_description="""1. Carefully read and understand the application description
2. For each component and data flow:
   - Identify potential Spoofing threats
   - Identify potential Tampering threats
   - Identify potential Repudiation threats
   - Identify potential Information Disclosure threats
   - Identify potential Denial of Service threats
   - Identify potential Elevation of Privilege threats
3. For each identified threat:
   - Describe the specific scenario
   - Analyze the potential impact
4. Generate improvement suggestions based on identified threats
5. Format the output as a JSON object with 'threat_model' and 'improvement_suggestions' arrays"""
        )
        # Create completion with max_completion_tokens for o1/o3-mini
        response = client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=4000
        )
    else:
        system_prompt = "You are a helpful assistant designed to output JSON."
        # Create completion with max_tokens for other models
        response = client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000
        )

    # Convert the JSON string in the 'content' field to a Python dictionary
    response_content = json.loads(response.choices[0].message.content)

    return response_content


# Function to get threat model from the Azure OpenAI response.
def get_threat_model_azure(azure_api_endpoint, azure_api_key, azure_api_version, azure_deployment_name, prompt):
    client = AzureOpenAI(
        azure_endpoint = azure_api_endpoint,
        api_key = azure_api_key,
        api_version = azure_api_version,
    )

    response = client.chat.completions.create(
        model = azure_deployment_name,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": prompt}
        ]
    )

    # Convert the JSON string in the 'content' field to a Python dictionary
    response_content = json.loads(response.choices[0].message.content)

    return response_content


# Function to get threat model from the Google response.
def get_threat_model_google(google_api_key, google_model, prompt):
    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel(
        google_model,
        generation_config={"response_mime_type": "application/json"})
    response = model.generate_content(
        prompt,
        safety_settings={
            'DANGEROUS': 'block_only_high' # Set safety filter to allow generation of threat models
        })
    try:
        # Access the JSON content from the 'parts' attribute of the 'content' object
        response_content = json.loads(response.candidates[0].content.parts[0].text)
    except json.JSONDecodeError:

        return None

    return response_content

# Function to get threat model from the Mistral response.
def get_threat_model_mistral(mistral_api_key, mistral_model, prompt):
    client = Mistral(api_key=mistral_api_key)

    response = client.chat.complete(
        model = mistral_model,
        response_format={"type": "json_object"},
        messages=[
            UserMessage(content=prompt)
        ]
    )

    # Convert the JSON string in the 'content' field to a Python dictionary
    response_content = json.loads(response.choices[0].message.content)

    return response_content

# Function to get threat model from Ollama hosted LLM.
def get_threat_model_ollama(ollama_endpoint, ollama_model, prompt):
    """
    Get threat model from Ollama hosted LLM.
    
    Args:
        ollama_endpoint (str): The URL of the Ollama endpoint (e.g., 'http://localhost:11434')
        ollama_model (str): The name of the model to use
        prompt (str): The prompt to send to the model
        
    Returns:
        dict: The parsed JSON response from the model
        
    Raises:
        requests.exceptions.RequestException: If there's an error communicating with the Ollama endpoint
        json.JSONDecodeError: If the response cannot be parsed as JSON
    """
    if not ollama_endpoint.endswith('/'):
        ollama_endpoint = ollama_endpoint + '/'
    
    url = ollama_endpoint + "api/generate"

    system_prompt = "You are a helpful assistant designed to output JSON."
    full_prompt = f"{system_prompt}\n\n{prompt}"

    data = {
        "model": ollama_model,
        "prompt": full_prompt,
        "stream": False,
        "format": "json"
    }

    try:
        response = requests.post(url, json=data, timeout=60)  # Add timeout
        response.raise_for_status()  # Raise exception for bad status codes
        outer_json = response.json()
        
        try:
            # Parse the JSON response from the model's response field
            inner_json = json.loads(outer_json['response'])
            return inner_json
        except (json.JSONDecodeError, KeyError):

            raise
            
    except requests.exceptions.RequestException:

        raise

# Function to get threat model from the Claude response.
def get_threat_model_anthropic(anthropic_api_key, anthropic_model, prompt):
    client = Anthropic(api_key=anthropic_api_key)
    
    # Check if we're using Claude 3.7
    is_claude_3_7 = "claude-3-7" in anthropic_model.lower()
    
    # Check if we're using extended thinking mode
    is_thinking_mode = "thinking" in anthropic_model.lower()
    
    # If using thinking mode, use the actual model name without the "thinking" suffix
    actual_model = "claude-3-7-sonnet-latest" if is_thinking_mode else anthropic_model
    
    try:
        # For Claude 3.7, use a more explicit prompt structure
        if is_claude_3_7:
            # Add explicit JSON formatting instructions to the prompt
            json_prompt = prompt + "\n\nIMPORTANT: Your response MUST be a valid JSON object with the exact structure shown in the example above. Do not include any explanatory text, markdown formatting, or code blocks. Return only the raw JSON object."
            
            # Configure the request based on whether thinking mode is enabled
            if is_thinking_mode:
                response = client.messages.create(
                    model=actual_model,
                    max_tokens=24000,
                    thinking={
                        "type": "enabled",
                        "budget_tokens": 16000
                    },
                    system="You are a JSON-generating assistant. You must ONLY output valid, parseable JSON with no additional text or formatting.",
                    messages=[
                        {"role": "user", "content": json_prompt}
                    ],
                    timeout=600  # 10-minute timeout
                )
            else:
                response = client.messages.create(
                    model=actual_model,
                    max_tokens=4096,
                    system="You are a JSON-generating assistant. You must ONLY output valid, parseable JSON with no additional text or formatting.",
                    messages=[
                        {"role": "user", "content": json_prompt}
                    ],
                    timeout=300  # 5-minute timeout
                )
        else:
            # Standard handling for other Claude models
            response = client.messages.create(
                model=actual_model,
                max_tokens=4096,
                system="You are a helpful assistant designed to output JSON. Your response must be a valid, parseable JSON object with no additional text, markdown formatting, or explanation. Do not include ```json code blocks or any other formatting - just return the raw JSON object.",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                timeout=300  # 5-minute timeout
            )
        
        # Combine all text blocks into a single string
        if is_thinking_mode:
            # For thinking mode, we need to extract only the text content blocks
            full_content = ''.join(block.text for block in response.content if block.type == "text")
            
            # Store thinking content in session state for debugging/transparency (optional)
            thinking_content = ''.join(block.thinking for block in response.content if block.type == "thinking")
            if thinking_content:
                st.session_state['last_thinking_content'] = thinking_content
        else:
            # Standard handling for regular responses
            full_content = ''.join(block.text for block in response.content)
        
        # Parse the JSON response
        try:
            # Check for and fix common JSON formatting issues
            if is_claude_3_7:
                # Sometimes Claude 3.7 adds trailing commas which are invalid in JSON
                full_content = full_content.replace(",\n  ]", "\n  ]").replace(",\n]", "\n]")
                
                # Sometimes it adds comments which are invalid in JSON
                full_content = re.sub(r'//.*?\n', '\n', full_content)
            
            response_content = json.loads(full_content)
            return response_content
        except json.JSONDecodeError as e:
            # Create a fallback response
            fallback_response = {
                "threat_model": [
                    {
                        "Threat Type": "Error",
                        "Scenario": "Failed to parse Claude response",
                        "Potential Impact": "Unable to generate threat model"
                    }
                ],
                "improvement_suggestions": [
                    "Try again - sometimes the model returns a properly formatted response on subsequent attempts",
                    "Check the logs for detailed error information"
                ]
            }
            return fallback_response
            
    except Exception as e:
        # Handle timeout and other errors
        error_message = str(e)
        st.error(f"Error with Anthropic API: {error_message}")
        
        # Create a fallback response for timeout or other errors
        fallback_response = {
            "threat_model": [
                {
                    "Threat Type": "Error",
                    "Scenario": f"API Error: {error_message}",
                    "Potential Impact": "Unable to generate threat model"
                }
            ],
            "improvement_suggestions": [
                "For complex applications, try simplifying the input or breaking it into smaller components",
                "If you're using extended thinking mode and encountering timeouts, try the standard model instead",
                "Consider reducing the complexity of the application description"
            ]
        }
        return fallback_response

# Function to get threat model from LM Studio Server response.
def get_threat_model_lm_studio(lm_studio_endpoint, model_name, prompt):
    client = OpenAI(
        base_url=f"{lm_studio_endpoint}/v1",
        api_key="not-needed"  # LM Studio Server doesn't require an API key
    )

    # Define the expected response structure
    threat_model_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "threat_model_response",
            "schema": {
                "type": "object",
                "properties": {
                    "threat_model": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Threat Type": {"type": "string"},
                                "Scenario": {"type": "string"},
                                "Potential Impact": {"type": "string"}
                            },
                            "required": ["Threat Type", "Scenario", "Potential Impact"]
                        }
                    },
                    "improvement_suggestions": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["threat_model", "improvement_suggestions"]
            }
        }
    }

    response = client.chat.completions.create(
        model=model_name,
        response_format=threat_model_schema,
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4000,
    )

    # Convert the JSON string in the 'content' field to a Python dictionary
    response_content = json.loads(response.choices[0].message.content)

    return response_content

# Function to get threat model from the Groq response.
def get_threat_model_groq(groq_api_key, groq_model, prompt):
    client = Groq(api_key=groq_api_key)

    response = client.chat.completions.create(
        model=groq_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": prompt}
        ]
    )

    # Process the response using our utility function
    reasoning, response_content = process_groq_response(
        response.choices[0].message.content,
        groq_model,
        expect_json=True
    )
    
    # If we got reasoning, display it in an expander in the UI
    if reasoning:
        with st.expander("View model's reasoning process", expanded=False):
            st.write(reasoning)

    return response_content
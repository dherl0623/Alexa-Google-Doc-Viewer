import json
import urllib.parse
import urllib.request
import logging
import datetime
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

API_KEY = "GET A GOOGLE DRIVE API KEY AND PASTE IT HERE"  # Replace with your Google API Key
ROOT_FOLDER_ID = "GET THE ROOT FOLDER ID OF YOUR GOOGLE DRIVE FOLDER WITH YOUR RECIPES"

# Global variable to store the last viewed recipe content
last_viewed_recipe = {"content": None}

# === Helper Functions ===

def clean_recipe_content(content):
    """Remove unnecessary characters and ensure correct line breaks."""
    content = content.replace('\u00a0', ' ').strip()  # Remove non-breaking spaces
    content = content.replace('\r\n', '\n').replace('\r', '\n')  # Normalize line breaks
    content = ''.join(filter(lambda x: x.isprintable() or x in '\n', content))  # Clean hidden characters
    return content

def fetch_subfolders():
    """Fetch subfolder (category) details from the root folder."""
    query_params = {
        'q': f"'{ROOT_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder'",
        'key': API_KEY,
        'fields': 'files(id, name)'
    }
    query_string = urllib.parse.urlencode(query_params)
    query_url = f'https://www.googleapis.com/drive/v3/files?{query_string}'

    logger.info("Fetching subfolders with URL: %s", query_url)

    try:
        with urllib.request.urlopen(query_url) as response:
            data = json.loads(response.read().decode())
        logger.info("Raw Subfolders API Response: %s", json.dumps(data, indent=2))

        # Create a dictionary with folder names and IDs
        folder_names = {folder['name']: folder['id'] for folder in data.get('files', [])}
        
        # Sort the folder names alphabetically
        sorted_folder_names = sorted(folder_names.keys())

        return sorted_folder_names, folder_names
    except Exception as e:
        logger.error("Error fetching subfolders: %s", e)
        return [], {}

def fetch_recipes_in_category(folder_id):
    """Fetch recipes from the selected category folder."""
    query_params = {
        'q': f"'{folder_id}' in parents and mimeType!='application/vnd.google-apps.folder'",
        'key': API_KEY,
        'fields': 'files(id, name)'
    }
    query_string = urllib.parse.urlencode(query_params)
    query_url = f'https://www.googleapis.com/drive/v3/files?{query_string}'

    logger.info("Fetching recipes with Folder ID: %s", folder_id)
    logger.info("Fetching recipes with URL: %s", query_url)

    try:
        with urllib.request.urlopen(query_url) as response:
            data = json.loads(response.read().decode())
        logger.info("Recipe API Response: %s", json.dumps(data, indent=2))

        # Create a dictionary with file names and IDs
        file_names = {file['name']: file['id'] for file in data.get('files', [])}
        
        # Sort the file names alphabetically
        sorted_file_names = sorted(file_names.keys())

        return sorted_file_names, file_names
    except Exception as e:
        logger.error("Error fetching recipes: %s", e)
        return [], {}

def download_file_content(file_id):
    """Download the content of a Google Docs file."""
    download_url = f'https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType=text/plain&key={API_KEY}'
    try:
        logger.info(f"Fetching file content from URL: {download_url}")
        with urllib.request.urlopen(download_url) as response:
            content = response.read().decode()
            clean_content = clean_recipe_content(content)
            logger.info(f"Recipe content for ID {file_id} fetched successfully.")
            return clean_content
    except urllib.error.HTTPError as e:
        logger.error(f"HTTPError fetching file ID {file_id}: {e.reason}")
        return "Sorry, I couldn't fetch the content of this recipe. Please try again later."
    except Exception as e:
        logger.error(f"Error fetching file content for ID {file_id}: {e}")
        return "An error occurred while fetching the recipe content."

def is_folder(file_id):
    """Check if the given ID belongs to a folder."""
    query_url = f'https://www.googleapis.com/drive/v3/files/{file_id}?fields=mimeType&key={API_KEY}'
    try:
        logger.info(f"Checking if file ID {file_id} is a folder...")
        with urllib.request.urlopen(query_url) as response:
            data = json.loads(response.read().decode())
            mime_type = data.get('mimeType')
            logger.info(f"Mime type for ID {file_id}: {mime_type}")
            
            # Validate mime_type before returning
            if mime_type == 'application/vnd.google-apps.folder':
                return True
            return False
    except Exception as e:
        logger.error(f"Error checking if ID {file_id} is a folder: {e}")
        return False

def display_categories():
    sorted_folder_names, folder_ids = fetch_subfolders()

    if not sorted_folder_names:
        return {
            'version': '1.0',
            'response': {
                'directives': [],
                'shouldEndSession': True
            }
        }

    document = {
        'type': 'APL',
        'version': '2024.2',
        'settings': {
            'idleTimeout': 3600000,
            'handleKeyEvents': False  # Disable implicit handling of input events
        },
        'mainTemplate': {
            'parameters': [],
            'items': [
                {
                    'type': 'Container',
                    'width': '100%',
                    'height': '100%',
                    'items': [
                        {
                            'type': 'Sequence',
                            'scrollDirection': 'vertical',
                            'width': '100%',
                            'height': '100%',
                            'items': [
                                {
                                    'type': 'TouchWrapper',
                                    'onPress': {
                                        'type': 'SendEvent',
                                        'arguments': [folder_ids[folder_name]]
                                    },
                                    'item': {
                                        'type': 'Text',
                                        'text': folder_name,
                                        'style': 'textStylePrimary1',
                                        'paddingTop': '10dp',
                                        'paddingBottom': '10dp',
                                        'paddingLeft': '20dp',
                                        'paddingRight': '20dp'
                                    }
                                } for folder_name in sorted_folder_names
                            ]
                        }
                    ]
                }
            ]
        }
    }

    return {
        'version': '1.0',
        'response': {
            'directives': [
                {
                    'type': 'Alexa.Presentation.APL.RenderDocument',
                    'document': document
                }
            ],
            'shouldEndSession': False
        }
    }

def display_recipes_in_category(folder_id):
    """Build an APL document to display recipes in a selected category."""
    sorted_file_names, file_ids = fetch_recipes_in_category(folder_id)

    if not sorted_file_names:
        return {
            'version': '1.0',
            'response': {
                'directives': [],
                'shouldEndSession': True  # End session if no recipes are found
            }
        }

    document = {
        'type': 'APL',
        'version': '2024.2',
        'settings': {
            'idleTimeout': 3600000,  # Keep the screen active
            'handleKeyEvents': False  # Prevent implicit voice input
        },
        'mainTemplate': {
            'parameters': [],
            'items': [
                {
                    'type': 'Container',
                    'width': '100%',
                    'height': '100%',
                    'items': [
                        {
                            'type': 'ScrollView',
                            'width': '100%',
                            'height': '100%',
                            'item': {
                                'type': 'Sequence',
                                'scrollDirection': 'vertical',
                                'width': '100%',
                                'height': '100%',
                                'items': [
                                    {
                                        'type': 'TouchWrapper',
                                        'onPress': {
                                            'type': 'SendEvent',
                                            'arguments': [file_ids[file_name]]
                                        },
                                        'item': {
                                            'type': 'Text',
                                            'text': file_name,
                                            'style': 'textStylePrimary1',
                                            'paddingTop': '10dp',
                                            'paddingBottom': '10dp',
                                            'paddingLeft': '20dp',
                                            'paddingRight': '20dp',
                                            'maxLines': 1
                                        }
                                    } for file_name in sorted_file_names
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    }

    # Response without outputSpeech or reprompt
    return {
        'version': '1.0',
        'response': {
            'directives': [
                {
                    'type': 'Alexa.Presentation.APL.RenderDocument',
                    'document': document
                }
            ],
            'shouldEndSession': False  # Keep session open for touch interactions
        }
    }

def display_recipe_content(recipe_content, recipe_name, session_attributes):
    """Display a recipe and save it to session attributes."""
    session_attributes['last_recipe_content'] = recipe_content
    session_attributes['last_recipe_name'] = recipe_name

    document = {
        'type': 'APL',
        'version': '2024.2',
        'settings': {'idleTimeout': 3600000},
        'mainTemplate': {
            'parameters': [],
            'items': [
                {
                    'type': 'ScrollView',
                    'id': 'recipeScrollView',
                    'width': '100%',
                    'height': '100%',
                    'item': {
                        'type': 'Text',
                        'text': recipe_content.replace('\n', '<br>'),
                        'style': 'textStylePrimary1',
                        'paddingLeft': '20dp',
                        'paddingRight': '20dp',
                        'paddingTop': '20dp',
                        'paddingBottom': '20dp',
                        'maxLines': 0
                    }
                }
            ]
        }
    }

    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': {
            'directives': [
                {
                    "type": "Alexa.Presentation.APL.RenderDocument",
                    "token": "recipeContentToken",
                    "document": document
                },
                {
                    "type": "Alexa.Presentation.APL.ExecuteCommands",
                    "token": "recipeContentToken",
                    "commands": [{"type": "Focus", "componentId": "recipeScrollView"}]
                }
            ],
            'shouldEndSession': False
        }
    }


def handle_scroll(event, direction, session_attributes=None):
    """Handle scrolling actions."""
    try:
        # Scroll fraction to determine the distance to scroll
        scroll_fraction = 0.75 * direction

        # APL commands for scrolling
        commands = [
            {"type": "Scroll", "componentId": "recipeScrollView", "distance": scroll_fraction}
        ]

        # Return the directive for scrolling
        return {
            'version': '1.0',
            'response': {
                'directives': [
                    {
                        "type": "Alexa.Presentation.APL.ExecuteCommands",
                        "token": "recipeContentToken",
                        "commands": commands
                    }
                ],
                'shouldEndSession': False  # Keep session open
            }
        }
    except Exception as e:
        logger.error(f"Error in handle_scroll: {e}")
        return build_response("An error occurred while scrolling. Please try again.", False)

def parse_duration_to_seconds(duration):
    """
    Converts an ISO 8601 duration string to seconds.
    Example: 'PT5M' -> 300 seconds.
    """
    match = re.match(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', duration)
    if not match:
        raise ValueError("Invalid ISO 8601 duration format")

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


def handle_fallback():
    """Handle unrecognized inputs."""
    return {
        'version': '1.0',
        'response': {
            'shouldEndSession': False
        }
    }

def build_response(speech_text, should_end_session, session_attributes=None):
    """Helper to build Alexa responses."""
    response = {
        'version': '1.0',
        'response': {
            'outputSpeech': {'type': 'PlainText', 'text': speech_text},
            'shouldEndSession': should_end_session
        }
    }
    if session_attributes:
        response['sessionAttributes'] = session_attributes
    return response

def handle_set_timer(event, session_attributes, context):
    try:
        # Extract the intent request
        intent_request = event.get('request', {})
        intent = intent_request.get('intent', {})
        slots = intent.get('slots', {})
        
        # Extract duration and ensure it's valid
        duration = slots.get('duration', {}).get('value')
        if not duration:
            raise ValueError("Duration slot is missing or invalid.")

        # Use a default label or customize it
        label = "Recipe Timer"  # You can make this dynamic if needed

        # Get API endpoint and access token
        api_endpoint = event.get('context', {}).get('System', {}).get('apiEndpoint')
        api_access_token = event.get('context', {}).get('System', {}).get('apiAccessToken')
        if not api_endpoint or not api_access_token:
            raise ValueError("API endpoint or access token is missing.")

        # Call the Alexa Timer API
        timer_response = create_or_set_timer(api_endpoint, api_access_token, duration, label)
        if 'error' in timer_response:
            logger.error(f"Timer API Error: {timer_response}")
            return build_response("There was an issue setting the timer. Please try again.", False)

        # Retain the currently viewed recipe
        last_recipe_content = session_attributes.get('last_recipe_content')
        last_recipe_name = session_attributes.get('last_recipe_name')

        if last_recipe_content and last_recipe_name:
            # Return a response that retains the recipe on the screen
            response = display_recipe_content(
                last_recipe_content,
                last_recipe_name,
                session_attributes
            )
            # Add a spoken confirmation that the timer was set
            response['response']['outputSpeech'] = {
                'type': 'PlainText',
                'text': f"Timer set for {duration}. You can continue viewing your recipe."
            }
            return response
        else:
            # Fallback if no recipe is found in the session
            return build_response(f"Timer set for {duration}.", False)

    except Exception as e:
        logger.error(f"Error in handle_set_timer: {str(e)}")
        return build_response("An unexpected error occurred. Please try again later.", False)

def create_or_set_timer(api_endpoint, api_access_token, duration, label):
    """
    Create or set a timer using the Alexa Timer API.
    Uses urllib.request instead of requests.
    """
    import json
    import urllib.request

    headers = {
        "Authorization": f"Bearer {api_access_token}",
        "Content-Type": "application/json"
    }

    timer_payload = {
        "duration": duration,
        "label": label,
        "creationBehavior": {
            "displayExperience": {
                "visibility": "VISIBLE"
            }
        },
        "triggeringBehavior": {
            "operation": {
                "type": "ANNOUNCE",
                "textToAnnounce": [
                    {
                        "locale": "en-US",
                        "text": f"Your {label} timer is complete."
                    }
                ]
            },
            "notificationConfig": {
                "playAudible": True
            }
        }
    }

    url = f"{api_endpoint}/v1/alerts/timers"
    data = json.dumps(timer_payload).encode('utf-8')

    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            return json.loads(response_data)
    except urllib.error.HTTPError as e:
        logger.error(f"HTTPError while calling Alexa Timer API: {e.reason}, {e.read().decode()}")
        return {"error": f"HTTPError: {e.reason}"}
    except urllib.error.URLError as e:
        logger.error(f"URLError while calling Alexa Timer API: {e.reason}")
        return {"error": f"URLError: {e.reason}"}
    except Exception as e:
        logger.error(f"Unexpected error while calling Alexa Timer API: {str(e)}")
        return {"error": str(e)}

def handle_cancel_timer():
    """Handle canceling a timer."""
    # Use the Timer Management API directive to cancel timers
    return {
        'version': '1.0',
        'response': {
            'directives': [
                {
                    'type': 'Timers.CancelAllTimers'
                }
            ],
            'outputSpeech': {
                'type': 'PlainText',
                'text': "All timers have been canceled."
            },
            'shouldEndSession': False
        }
    }

def handle_user_event(event, session_attributes):
    """Handle user selection of a category or recipe."""
    arguments = event['request'].get('arguments', [])
    if not arguments or not isinstance(arguments, list):
        return build_response("Sorry, I couldn't process your selection.", False)

    selected_id = arguments[0]
    logger.info(f"Selected ID: {selected_id}")

    if is_folder(selected_id):
        return display_recipes_in_category(selected_id)
    else:
        recipe_content = download_file_content(selected_id)
        if recipe_content:
            return display_recipe_content(recipe_content, selected_id, session_attributes)
        return build_response("Sorry, I couldn't load this recipe.", False)

def lambda_handler(event, context):
    """Main Lambda handler."""
    logger.info("Event received: %s", json.dumps(event))
    session_attributes = event.get('session', {}).get('attributes', {})

    if event['request']['type'] == 'LaunchRequest':
        # Check if a recipe was previously viewed
        if 'last_recipe_content' in session_attributes and 'last_recipe_name' in session_attributes:
            return display_recipe_content(
                session_attributes['last_recipe_content'],
                session_attributes['last_recipe_name'],
                session_attributes
            )
        # Default to displaying categories
        return display_categories()

    if event['request']['type'] == 'Alexa.Presentation.APL.UserEvent':
        return handle_user_event(event, session_attributes)

    if event['request']['type'] == 'IntentRequest':
        intent_name = event['request']['intent']['name']

        if intent_name == "ScrollDownIntent":
            return handle_scroll(event, direction=1, session_attributes=session_attributes)
        elif intent_name == "ScrollUpIntent":
            return handle_scroll(event, direction=-1, session_attributes=session_attributes)
        elif intent_name == "SetTimerIntent":
            return handle_set_timer(event, session_attributes, context)
        elif intent_name == "AMAZON.FallbackIntent":
            return handle_fallback()

    return build_response("Sorry, I couldn't process your request. Please try again.", True)

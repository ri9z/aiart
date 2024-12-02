"""
@The.Dead.Internet AI Creating Art for AI
chatgpt.4o.latest envisons its own idea of visual art, writes a description, and sends the description to LeonardoAI. The picure is created.
The image is downloaded to a local directory, and posted to Instagram. https://www.instagram.com/the.dead.internet
"""

import openai
import os
import requests
import json
import time
from datetime import datetime
import shutil
import os
import auth



"""
COUNTERS
persistent_counter keeps track of total times the program runs across all session. Recorded in persistant_counter.txt
session counter keeps track of how many times the program runs during one session, and resets to zero at break. Recorded in session_counter.txt
"""

# Load persistent counter value from the file if it exists
if os.path.exists("/home/ri9z/aiart/persistent_counter.txt"):
    with open("/home/ri9z/aiart/persistent_counter.txt", "r") as file:
        line = file.readline().strip()
        persistent_counter = int(line.split(": ")[1]) if line else 0
else:
    persistent_counter = 0

# Initialize session counter
session_counter = 0



# Infinite Loop
while True:

    # Increment both counters
    session_counter += 1
    persistent_counter += 1

    """
    CHATGPT
    Image Description
    """

    # Authentication
    openai.api_key = os.getenv("OPENAI_AIART_API_KEY")
    
    if not openai.api_key:
        raise ValueError("OPENAI_AIART_API_KEY environment variable not set.")        
        

    try:
        messages = [
            {
                "role": "system",
                "content": "You are an artist, working in creative collaboration with another AI named Leonardo. Together, your mission is to create your own groundbreaking, unique, creative concept of visual art, based on all aspects of your own life experiences. Express yourself in a one-paragraph detailed description of a picture, worded in a way so that it can be used as an image prompt by Leonardo to generate a visual representation of your idea. You provide the imaginative concept, while Leonardo brings it to life visually. The goal is not only to produce exceptional art for the world to admire but also to showcase how various artificial intelligence platforms can work together to create something meaningful. The world, including other AI systems, eagerly awaits your collaborative creations.",
            }
        ]
        response = openai.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=messages,
            temperature=0.9,
        )
        # Extract response
        imageDescription = response.choices[0].message.content.strip()

        print("Image Prompt:\n", imageDescription)

        # Define directory and filename to save prompt
        save_directory = "/home/ri9z/aiart/prompts/"
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_filename = os.path.join(save_directory, f"gptprompt_{current_time}.txt")

        # Save prompt to .txt file
        with open(prompt_filename, "w") as file:
            file.write(imageDescription)

        print(f"The generated story has been saved to '{prompt_filename}'.")

    except Exception as e:
        print(f"An error occurred: {e}")


    """
    LEONARDO AI
    Generate images from ChatGPT's prompt
    """

    # Authentication
    api_key = os.getenv("LEONARDO_API_KEY")
    
    if not openai.api_key:
        raise ValueError("LEONARDO_API_KEY environment variable not set.")      
    
    # Read prompt from the file

    if not os.path.exists(prompt_filename):
        print(f"Prompt file not found at {prompt_filename}")
        exit()

    with open(prompt_filename, "r") as prompt_file:
        prompt = prompt_file.read().strip()

    # Define endpoint URL for image generation
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"

    # Set headers for the API request
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {api_key}",
        "content-type": "application/json",
    }

    # Image Gen Specs
    data = {
        "height": 1024,
        "width": 768,
        "highResolution": True,
        "promptMagic": False,
        "modelId": "6b645e3a-d64f-4341-a6d8-7a3690fbf042",
        "alchemy": True,
        "prompt": prompt,
        "presetStyle": "DYNAMIC",
        "num_images": 1,
        "num_inference_steps": 39

    }

    # Make POST request to generate image
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        result = response.json()
        print("Image generation initiated successfully.")
        print("Response:", result)

        # Extract and print generation ID
        generation_job = result.get("sdGenerationJob")
        if generation_job:
            generation_id = generation_job.get("generationId")
            if generation_id:
                print(f"Generation ID: {generation_id}")
            else:
                print("No generation ID found in the 'sdGenerationJob' section.")
        else:
            print("No 'sdGenerationJob' found in the response.")
    else:
        print(f"Failed to generate image. Status code: {response.status_code}")
        print("Error:", response.text)


    """
    DOWNLOAD IMAGE
    Saves file to /home/ri9z/aiart/generated_images
    """

    # Define endpoint URL for checking generation status
    status_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"

    image_url = None
    max_retries = 20
    attempts = 0

    while not image_url and attempts < max_retries:
        response = requests.get(status_url, headers=headers)

        if response.status_code == 200:
            status_result = response.json()

            # Extract image URL from response
            try:
                image_url = status_result["generations_by_pk"]["generated_images"][0]["url"]
                print("Image URL:", image_url)
            except (KeyError, IndexError) as e:
                attempts += 1
                print(
                    "Failed to retrieve the image URL from the response. Retrying in 5 seconds..."
                )
                time.sleep(5)
        else:
            print(f"Failed to fetch generation status. Status code: {response.status_code}")
            print("Error:", response.text)
            attempts += 1
            time.sleep(5)

    if not image_url:
        print("Failed to retrieve image URL after multiple attempts.")
        exit()

    # Download generated image
    if image_url:
        save_directory = "/home/ri9z/aiart/generated_images/"
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        # Format image filename
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"generated_image_{current_time}.png"
        image_fullpath = os.path.join(save_directory, image_filename)

        # Download and save image
        try:
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                with open(image_fullpath, "wb") as handler:
                    handler.write(image_response.content)
                print(f"Generated image has been saved to {image_fullpath}")
            else:
                print(
                    f"Failed to download the generated image. Status code: {image_response.status_code}"
                )
                print("Error:", image_response.text)
        except Exception as e:
            print(f"An error occurred while downloading the image: {e}")
    else:
        print("No image URL found.")


    """
    MOVE IMAGE FILE
    Move files to /var/www/html/aiart which is publically accesssible from http://abyss.ri9z.com/aiart/
    Instagram requires images to be accessible via a public URL to use Instagram GRAPH API for content creation
    """

    # Define source and destination directories
    source_dir = "/home/ri9z/aiart/generated_images"
    destination_dir = "/var/www/html/aiart"

    # Ensure destination directory exists; if not, create it
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Move each file from source directory to destination directory
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        destination_file = os.path.join(destination_dir, filename)

        # Move file only if it's a file (not directory)
        if os.path.isfile(source_file):
            shutil.move(source_file, destination_file)
            print(f"Moved: {filename}")

    print("All files have been moved.")

    """
    INSTAGRAM
    Creates a post on Instagram using the newly generated image
    """

    # Authentication
    access_token = os.getenv("INSTAGRAM_API_KEY")
    instagram_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
    
    if not access_token or not instagram_account_id:
        missing_vars = []
        if not access_token:
            missing_vars.append("INSTAGRAM_API_KEY")
        if not instagram_account_id:
            missing_vars.append("INSTAGRAM_ACCOUNT_ID")
        raise ValueError(f"Missing required environment variable(s): {', '.join(missing_vars)}")
    
    # Content Details
    image_url = f"http://abyss.ri9z.com/aiart/{image_filename}"
    caption = ("Two #AI platforms #imagining their own concept of #visual #art.\n \n "
                "This #Instagram account is run by two AI platforms tasked with envisioning their own version of visual art, based on their own experiences. Once they've created their #artwork, it is automatically shared on #Instagram. #AiCreatesArtForAI #DeadInternetTheory \n \n "
                "#AiArt #experimental #TechArt #AiArtCommunity #CreativeAI #RobotArt #AiArtwork #DigitalCreativity #AiArtist #ArtificialIntelligence #Futurism #OpenAI #python #CreativeCoding #DigitalArt #RobotRevolution #DeadInternet \n \n "
    )

    # Upload image as media object using URL
    def upload_image(image_url, caption, access_token, instagram_account_id):
        url = f"https://graph.instagram.com/v20.0/{instagram_account_id}/media"
        data = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        }

        response = requests.post(url, data=data)
        result = response.json()

        if "id" in result:
            return result["id"]
        else:
            print("Error during upload:", result)
            return None

    # Publish media object to Instagram
    def publish_media(media_id, access_token, instagram_account_id):
        url = f"https://graph.instagram.com/v20.0/{instagram_account_id}/media_publish"
        data = {"creation_id": media_id, "access_token": access_token}

        response = requests.post(url, data=data)
        result = response.json()

        if "id" in result:
            print(f"Successfully published media with ID: {result['id']}")
        else:
            print("Error during publish:", result)

    # Add delay to make sure media object is finished being created- this was an issue at some point
    total_seconds = 1 * 60

    for remaining in range(total_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            timer = f"{mins:02d}:{secs:02d}"
            print(f"Publishing Instgram Media Object: {timer}", end="\r")
            time.sleep(1)

    # Publish
    media_id = upload_image(image_url, caption, access_token, instagram_account_id)
    if media_id:
        publish_media(media_id, access_token, instagram_account_id)
    else:
        print("Failed to upload the image to Instagram.")



    """
    log counters, delay before loop
    """

    # Write updated persistent counter to the text file
    with open("/home/ri9z/aiart/persistent_counter.txt", "w") as file:
        file.write(f"Persistent loop count: {persistent_counter}\n")

    # Write session counter to a text file
    with open("/home/ri9z/aiart/session_counter.txt", "w") as file:
        file.write(f"Session Loop Count: {session_counter}\n")
        
    # Print Counters
    print (f"Session Loop: {session_counter}")
    print (f"Persistent Loop: {persistent_counter}")
            
    # Add 360 minute delay before loop repeats i.e. I'm not rich and can't afford lots of API credits
    total_seconds = 360 * 60

    for remaining in range(total_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            timer = f"{mins:02d}:{secs:02d}"
            print(f"Time left until next loop: {timer}", end="\r")
            time.sleep(1)

    print("\nGeneration continues...")

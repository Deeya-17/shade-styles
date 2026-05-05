from google.genai import Client
import base64
import os

client = Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_style_image(prompt, save_path):
    result = client.images.generate(
        model="gemini-2.0-flash",
        prompt=prompt,
        size="1024x1024"
    )

    img_base64 = result.images[0].image_bytes
    img_bytes = base64.b64decode(img_base64)

    with open(save_path, "wb") as f:
        f.write(img_bytes)

    return save_path

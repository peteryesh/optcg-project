import json
import os
import requests
from pathlib import Path

IMG_URL_BASE = "https://en.onepiece-cardgame.com/"

def download_images_from_json(json_filename="optcg_cards.json", output_dir="./optcg_images"):
    """Download images from URLs specified in a JSON file from the parent folder."""
    
    # Get the parent folder path
    parent_folder = Path(__file__).parent
    json_path = parent_folder / json_filename
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Load JSON file
    if not json_path.exists():
        print(f"Error: {json_path} not found")
        return
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Download images
    for item in data:
        if data[item]["img_path"]:
            url = IMG_URL_BASE + data[item]["img_path"]
            filename = data[item]["code"] + ".png"
            filepath = output_path / filename
            print(url)
            for alt in data[item]["alts"]:
                alt_filename = alt["alt_code"] + ".png"
                alt_filepath = output_path / alt_filename
                if not alt_filepath.exists():
                    alt_url = IMG_URL_BASE + alt["img_path"]
                    print(alt_url)
                    try:
                        response = requests.get(alt_url, timeout=10)
                        response.raise_for_status()
                        
                        with open(alt_filepath, 'wb') as img_file:
                            img_file.write(response.content)
                        
                        print(f"Downloaded: {alt_filename}")
                    except requests.RequestException as e:
                        print(f"Failed to download {alt_filename}: {e}")
            
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                with open(filepath, 'wb') as img_file:
                    img_file.write(response.content)
                
                print(f"Downloaded: {filename}")
            except requests.RequestException as e:
                print(f"Failed to download {filename}: {e}")

if __name__ == "__main__":
    download_images_from_json()
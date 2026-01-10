import os
import subprocess
import requests
import argparse
from pathlib import Path

BASE_URL = "https://github.com/notofonts/noto-cjk/raw/main/Serif/OTF/Japanese/"
WEIGHTS = [
    "Black",
    "Bold",
    "ExtraLight",
    "Light",
    "Medium",
    "Regular",
    "SemiBold"
]

def download_font(weight, output_dir):
    filename = f"NotoSerifCJKjp-{weight}.otf"
    url = f"{BASE_URL}{filename}"
    output_path = output_dir / f"NotoSerifJP-{weight}.otf"
    
    if output_path.exists():
        print(f"Skipping download: {output_path} already exists.")
        return output_path

    print(f"Downloading {filename} from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Successfully downloaded to {output_path}")
    return output_path

def extract_ufo(font_path):
    ufo_path = font_path.with_suffix(".otf.ufo")
    if ufo_path.exists():
        print(f"Skipping extraction: {ufo_path} already exists.")
        return

    print(f"Extracting UFO from {font_path}...")
    try:
        subprocess.run(
            ["uv", "run", "extractufo", "-m", "defcon", str(font_path)],
            check=True
        )
        print(f"Successfully extracted to {ufo_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during extraction of {font_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Setup font assets for NType-JP.")
    parser.add_argument(
        "--output-dir", 
        default="static",
        help="Directory to store fonts and UFOs (default: static)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force download and extraction even if files exist"
    )
    
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for weight in WEIGHTS:
        try:
            font_path = download_font(weight, output_dir)
            extract_ufo(font_path)
        except Exception as e:
            print(f"Failed to process {weight}: {e}")

    print("\nSetup complete!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Update author_images.json with real photo URLs for well-known people."""

import json
from pathlib import Path

# Known public image URLs for famous people (using Wikimedia Commons)
# These are publicly available, properly licensed images
REAL_IMAGES = {
    "Steve Jobs": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/Steve_Jobs_Headshot_2010-CROP_%28cropped_2%29.jpg/440px-Steve_Jobs_Headshot_2010-CROP_%28cropped_2%29.jpg",
    "Elon Musk": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Elon_Musk_Royal_Society_%28crop2%29.jpg/440px-Elon_Musk_Royal_Society_%28crop2%29.jpg",
    "Bill Gates": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Bill_Gates_2017_%28cropped%29.jpg/440px-Bill_Gates_2017_%28cropped%29.jpg",
    "Mark Zuckerberg": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Mark_Zuckerberg_F8_2019_Keynote_%2832830578717%29_%28cropped%29.jpg/440px-Mark_Zuckerberg_F8_2019_Keynote_%2832830578717%29_%28cropped%29.jpg",
    "Jeff Bezos": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Jeff_Bezos_visits_LAAFB_SMC_%283908618%29_%28cropped%29.jpg/440px-Jeff_Bezos_visits_LAAFB_SMC_%283908618%29_%28cropped%29.jpg",
    "Warren Buffett": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Warren_Buffett_KU_Visit.jpg/440px-Warren_Buffett_KU_Visit.jpg",
    "Barack Obama": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/President_Barack_Obama.jpg/440px-President_Barack_Obama.jpg",
    "Albert Einstein": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Albert_Einstein_Head.jpg/440px-Albert_Einstein_Head.jpg",
    "Nelson Mandela": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Nelson_Mandela-2008_%28cropped%29.jpg/440px-Nelson_Mandela-2008_%28cropped%29.jpg",
    "Martin Luther King Jr.": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Martin_Luther_King%2C_Jr..jpg/440px-Martin_Luther_King%2C_Jr..jpg",
    "Gandhi": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Mahatma-Gandhi%2C_studio%2C_1931.jpg/440px-Mahatma-Gandhi%2C_studio%2C_1931.jpg",
    "Nikola Tesla": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/N.Tesla.JPG/440px-N.Tesla.JPG",
    "Leonardo da Vinci": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Leonardo_self.jpg/440px-Leonardo_self.jpg",
    "Winston Churchill": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Sir_Winston_Churchill_-_19086236948.jpg/440px-Sir_Winston_Churchill_-_19086236948.jpg",
}

def main():
    # Load existing author_images.json
    image_file = Path("data/processed/author_images.json")

    print("Loading existing author images...")
    with open(image_file, 'r') as f:
        author_images = json.load(f)

    print(f"Loaded {len(author_images)} authors")

    # Update with real images
    updated_count = 0
    for author, url in REAL_IMAGES.items():
        if author in author_images:
            print(f"  Updating {author} with real photo")
            author_images[author] = url
            updated_count += 1
        else:
            print(f"  ⚠ {author} not found in dataset")

    # Save updated file
    print(f"\nSaving {updated_count} real image URLs...")
    with open(image_file, 'w') as f:
        json.dump(author_images, f, indent=2, ensure_ascii=False)

    print(f"✓ Updated {updated_count} authors with real photos")
    print("\nNext: Run migration to update database")

if __name__ == "__main__":
    main()

from PIL import Image
import numpy as np

def process_logo(input_path, output_path):
    # Open the image
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)

    # Define white threshold (e.g. pixels lighter than 200,200,200)
    # The image is black logo on white bg.
    r, g, b, a = data.T
    
    # Identify white background areas
    white_areas = (r > 200) & (g > 200) & (b > 200)
    
    # Identify black logo areas (dark pixels)
    black_areas = (r < 100) & (g < 100) & (b < 100)

    # 1. Make white background transparent
    data[..., 3] = 255 # Default fully opaque
    data[..., 3][white_areas.T] = 0 # Make white areas transparent

    # 2. Invert black logo to white (for dark website header)
    # We want the logo pixels to be white (255,255,255) but keep their alpha
    # Currently they are black (0,0,0) and opaque.
    # Where it's NOT transparent, make it white.
    # Actually, let's just make all non-transparent pixels white.
    non_transparent = data[..., 3] > 0
    data[..., 0][non_transparent] = 255 # R
    data[..., 1][non_transparent] = 255 # G
    data[..., 2][non_transparent] = 255 # B

    # Create new image
    new_img = Image.fromarray(data)
    new_img.save(output_path)
    print(f"Processed logo saved to {output_path}")

if __name__ == "__main__":
    process_logo(
        "/Users/ahmadabduallah/.gemini/antigravity/brain/86d01599-e687-4b77-804c-8e7995449648/uploaded_image_1766864800021.jpg", 
        "/Users/ahmadabduallah/ANTI GRAVITY/ASR_Website/logo-transparent.png"
    )

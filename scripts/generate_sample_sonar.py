"""
Generates synthetic Side Scan Sonar (SSS) placeholder images with realistic
acoustic characteristics: speckle noise, sand ripples, central nadir track,
bright acoustic debris returns, and trailing acoustic shadows.
"""

import os
import cv2
import numpy as np

def create_synthetic_sonar_image(width=1000, height=600, style="standard"):
    # 1. Base acoustic seabed backscatter (sepia / amber sonar palette or grayscale)
    base_gray = np.full((height, width), 110, dtype=np.uint8)
    
    # 2. Add realistic seabed ripple patterns
    y_coords, x_coords = np.indices((height, width))
    ripples = 18 * np.sin(x_coords * 0.05 + np.sin(y_coords * 0.02) * 4)
    base = np.clip(base_gray + ripples, 0, 255).astype(np.uint8)

    # 3. Add acoustic speckle noise (Rayleigh/Gaussian noise)
    noise = np.random.normal(0, 16, (height, width))
    noisy = np.clip(base.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    # 4. Central nadir trackline (water column / low return right under towfish)
    nadir_center = width // 2
    nadir_half_width = 25
    cv2.rectangle(noisy, (nadir_center - nadir_half_width, 0), (nadir_center + nadir_half_width, height), (30), -1)
    
    # Soften nadir boundary
    noisy = cv2.GaussianBlur(noisy, (3, 3), 0)

    # 5. Insert simulated man-made debris targets with bright reflection + dark acoustic shadow
    targets = [
        # Ghost net: diffuse bright entangled returns with trailing shadow
        {"x": int(width * 0.22), "y": int(height * 0.26), "w": 90, "h": 70, "type": "net"},
        # Shipwreck / large anomaly: high reflection hull and long acoustic shadow
        {"x": int(width * 0.65), "y": int(height * 0.45), "w": 130, "h": 65, "type": "hull"},
        # Pipe: elongated bright line + narrow shadow
        {"x": int(width * 0.32), "y": int(height * 0.72), "w": 160, "h": 22, "type": "pipe"},
        # Cylinder: compact bright target + shadow
        {"x": int(width * 0.80), "y": int(height * 0.20), "w": 40, "h": 35, "type": "cylinder"}
    ]

    for t in targets:
        tx, ty, tw, th = t["x"], t["y"], t["w"], t["h"]
        # Dark acoustic shadow cast outward from nadir
        shadow_dir = 1 if tx > nadir_center else -1
        shadow_x = tx + (tw if shadow_dir > 0 else -int(tw * 0.8))
        shadow_w = int(tw * 0.9)
        # Shadow region (very dark / no return)
        cv2.ellipse(
            noisy,
            (shadow_x + shadow_w // 2, ty + th // 2),
            (shadow_w // 2, th // 2),
            0, 0, 360, (20), -1
        )
        # Bright acoustic return (specular reflection)
        cv2.ellipse(
            noisy,
            (tx + tw // 2, ty + th // 2),
            (tw // 2, th // 2),
            0, 0, 360, (245), -1
        )
        if t["type"] == "net":
            # Add web-like tangled lines
            for _ in range(5):
                pt1 = (tx + np.random.randint(0, tw), ty + np.random.randint(0, th))
                pt2 = (tx + np.random.randint(0, tw), ty + np.random.randint(0, th))
                cv2.line(noisy, pt1, pt2, (255), 2)

    # 6. Apply classic copper/sepia marine sonar false color
    sonar_bgr = cv2.applyColorMap(noisy, cv2.COLORMAP_BONE)

    return sonar_bgr

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sonar_images")
    os.makedirs(out_dir, exist_ok=True)
    
    img1 = create_synthetic_sonar_image(1000, 600, style="standard")
    cv2.imwrite(os.path.join(out_dir, "sample_sonar_01.jpg"), img1)
    
    img2 = create_synthetic_sonar_image(1200, 700, style="wide")
    cv2.imwrite(os.path.join(out_dir, "sample_sonar_02.png"), img2)
    print("Synthetic sample sonar images created successfully.")

import numpy as np

def test_vector_logic():
    # Test intersection logic
    p1 = np.array([0, 0])
    p2 = np.array([10, 0])
    p3 = np.array([10, 10])
    
    # Vector 1: p1 -> p2
    v1 = p2 - p1
    # Vector 2: p2 -> p3
    v2 = p3 - p2
    
    # Cross product 2D
    cross = np.cross(v1, v2)
    print(f"Cross product (Left turn/CCW?): {cross}") # Should be positive if CCW
    
    # Dot product for angle
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    cos_theta = dot / norm
    angle = np.degrees(np.arccos(cos_theta))
    print(f"Angle: {angle}") # Should be 90 for orthogonal

    # Left side diagonal cut logic
    # Assume contour is clockwise (outer in TTF? No, PS is CCW, TTF is CW)
    # defcon/ufoLib usually handles PostScript outlines (CCW for outer)
    
test_vector_logic()

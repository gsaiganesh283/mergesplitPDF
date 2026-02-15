"""
Image Cropping Module
Handles automatic image cropping, detection, and batch processing
Uses edge detection and contour finding for accurate content detection
"""

from PIL import Image, ImageOps, ImageFilter
import numpy as np
import cv2
import os
from pathlib import Path
from typing import List, Tuple, Optional
import tempfile
import zipfile
from io import BytesIO


class ImageCropper:
    """Handles image cropping operations with automatic border detection using CV"""
    
    def __init__(self, auto_detect: bool = True, margin: int = 5, auto_rotate: bool = True):
        """
        Initialize the ImageCropper
        
        Args:
            auto_detect: Whether to automatically detect and crop borders
            margin: Extra margin to keep around detected content (in pixels)
            auto_rotate: Whether to automatically rotate images based on EXIF and document skew
        """
        self.auto_detect = auto_detect
        self.margin = margin
        self.auto_rotate = auto_rotate
    
    def correct_exif_orientation(self, image: Image.Image) -> Image.Image:
        """
        Correct image orientation based on EXIF data
        
        Args:
            image: PIL Image object
        
        Returns:
            Properly oriented image
        """
        try:
            # Try to use ImageOps.exif_transpose (recommended way)
            return ImageOps.exif_transpose(image)
        except Exception:
            return image
    
    def detect_document_rotation(self, image: Image.Image) -> float:
        """
        Detect small document skew angle using Hough line transform.
        Only corrects minor skew (up to 10 degrees), never rotates 90 degrees.
        
        Args:
            image: PIL Image object
        
        Returns:
            Rotation angle in degrees (positive = counterclockwise), max ±10°
        """
        try:
            # Convert to OpenCV format
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            img_array = np.array(image)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Use Hough line transform to detect lines
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, 
                                     minLineLength=min(gray.shape) // 4, maxLineGap=10)
            
            if lines is None or len(lines) == 0:
                return 0
            
            # Collect angles of detected lines — only near-horizontal or near-vertical
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 == 0:
                    continue
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                
                # Only consider near-horizontal lines (within ±15° of 0 or 180)
                if abs(angle) < 15:
                    angles.append(angle)
                elif abs(angle - 180) < 15:
                    angles.append(angle - 180)
                elif abs(angle + 180) < 15:
                    angles.append(angle + 180)
            
            if not angles:
                return 0
            
            # Get median angle (robust against outliers)
            median_angle = np.median(angles)
            
            # Only correct small skew — cap at ±10 degrees to prevent major rotation
            if abs(median_angle) > 10:
                return 0
            
            # Only rotate if skew is noticeable (> 1 degree)
            if abs(median_angle) > 1:
                return -median_angle  # negate to correct the skew
            
            return 0
        
        except Exception:
            return 0
    
    def rotate_image(self, image: Image.Image, angle: float) -> Image.Image:
        """
        Rotate image by specified angle
        
        Args:
            image: PIL Image object
            angle: Rotation angle in degrees (positive = counterclockwise)
        
        Returns:
            Rotated image
        """
        if abs(angle) < 0.5:
            return image
        
        # Rotate using PIL (expand=True to avoid cropping)
        return image.rotate(angle, expand=True, fillcolor='white')
    
    def auto_orient_image(self, image: Image.Image) -> Image.Image:
        """
        Automatically orient and straighten image using EXIF data and document skew detection
        
        Args:
            image: PIL Image object
        
        Returns:
            Properly oriented image
        """
        if not self.auto_rotate:
            return image
        
        # Step 1: Correct EXIF orientation
        image = self.correct_exif_orientation(image)
        
        # Step 2: Detect and correct document skew
        rotation_angle = self.detect_document_rotation(image)
        if abs(rotation_angle) > 0.5:
            image = self.rotate_image(image, rotation_angle)
        
        return image
    
    def detect_content_bounds(self, image: Image.Image) -> Tuple[int, int, int, int]:
        """
        Detect the bounds of a document in an image by finding where the 
        background ends and the actual content begins. Uses multiple detection methods.
        
        Returns:
            Tuple of (x, y, width, height)
        """
        try:
            # Convert PIL image to OpenCV format
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            img_array = np.array(image)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            height, width = img_cv.shape[:2]
            
            # Try multiple detection methods
            bounds = None
            
            # Method 1: Edge-based detection (most accurate for removing backgrounds)
            bounds = self._find_content_by_edges(img_cv)
            
            # Method 2: Color transition detection
            if not bounds:
                bounds = self._find_document_by_color_transition(img_cv)
            
            # Method 3: Fallback to light region detection
            if not bounds:
                bounds = self._find_largest_light_region(img_cv)
            
            if bounds:
                x, y, w, h = bounds
                # Validate bounds - must keep at least 20% of image (more lenient)
                if (w * h) >= (width * height * 0.2):
                    # Apply margin
                    x = max(0, x - self.margin)
                    y = max(0, y - self.margin)
                    w = min(width - x, w + 2 * self.margin)
                    h = min(height - y, h + 2 * self.margin)
                    return int(x), int(y), int(w), int(h)
            
            # Fallback: return full image
            return 0, 0, width, height
            
        except Exception as e:
            return 0, 0, image.width, image.height
    
    def _find_content_by_edges(self, img_cv) -> Optional[Tuple[int, int, int, int]]:
        """
        Find content boundaries using edge detection. Most effective for removing
        backgrounds with different colors or patterns.
        """
        height, width = img_cv.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Use Canny edge detection for strong edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate edges to connect nearby edge pixels
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        edges = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours from edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find largest contour
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        
        # Require minimum size
        if (w * h) >= (width * height * 0.15):
            return (x, y, w, h)
        
        return None
    
    def _find_document_by_color_transition(self, img_cv) -> Optional[Tuple[int, int, int, int]]:
        """
        Find document boundaries by detecting the transition from colorful 
        background to the white/light document area.
        """
        height, width = img_cv.shape[:2]
        
        # Convert to HSV
        hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1].astype(float)
        value = hsv[:, :, 2].astype(float)
        
        # Check if the image has colorful borders (high saturation on edges)
        border_width = max(20, width // 20)
        left_border_sat = np.mean(saturation[:, :border_width])
        right_border_sat = np.mean(saturation[:, -border_width:])
        
        # If borders are colorful (saturation > 40), find document edges
        if left_border_sat > 40 or right_border_sat > 40:
            # Scan from left to find where document starts (low saturation, high brightness)
            x_left = 0
            for x in range(0, width // 2):
                col_sat = np.mean(saturation[:, x:x+5])
                col_val = np.mean(value[:, x:x+5])
                # Document area: low saturation AND high brightness
                if col_sat < 35 and col_val > 160:
                    x_left = max(0, x - 5)
                    break
            
            # Scan from right to find where document ends
            x_right = width
            for x in range(width - 1, width // 2, -1):
                col_sat = np.mean(saturation[:, x-5:x])
                col_val = np.mean(value[:, x-5:x])
                if col_sat < 35 and col_val > 160:
                    x_right = min(width, x + 5)
                    break
            
            # Scan from top
            y_top = 0
            for y in range(0, height // 3):
                row_sat = np.mean(saturation[y:y+5, x_left:x_right])
                row_val = np.mean(value[y:y+5, x_left:x_right])
                if row_sat < 40 and row_val > 150:
                    y_top = max(0, y - 5)
                    break
            
            # Scan from bottom
            y_bottom = height
            for y in range(height - 1, height * 2 // 3, -1):
                row_sat = np.mean(saturation[y-5:y, x_left:x_right])
                row_val = np.mean(value[y-5:y, x_left:x_right])
                if row_sat < 40 and row_val > 150:
                    y_bottom = min(height, y + 5)
                    break
            
            w = x_right - x_left
            h = y_bottom - y_top
            
            # Only return if we found meaningful bounds
            if w > width * 0.3 and h > height * 0.3:
                return (x_left, y_top, w, h)
        
        # Fallback: Use contour detection for white regions
        return self._find_largest_light_region(img_cv)
    
    def _find_largest_light_region(self, img_cv) -> Optional[Tuple[int, int, int, int]]:
        """Find the largest content region using adaptive techniques."""
        height, width = img_cv.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Use adaptive thresholding for better results with varying lighting
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 11, 2)
        
        # Clean up with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find largest contour by area
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        
        # Must be at least 15% of image
        if (w * h) >= (width * height * 0.15):
            return (x, y, w, h)
        
        return None
    
    def crop_image(self, image_path: str, output_path: str = None, 
                   crop_box: Optional[Tuple[int, int, int, int]] = None) -> str:
        """
        Crop a single image
        
        Args:
            image_path: Path to input image
            output_path: Path to save cropped image (optional)
            crop_box: Manual crop box (x, y, width, height). If None, auto-detects
        
        Returns:
            Path to the cropped image
        """
        # Read image
        try:
            image = Image.open(image_path)
        except Exception as e:
            raise ValueError(f"Could not read image: {image_path} - {str(e)}")
        
        # Auto-orient image (EXIF + skew correction)
        image = self.auto_orient_image(image)
        
        # Determine crop box
        if crop_box is None and self.auto_detect:
            x, y, w, h = self.detect_content_bounds(image)
        elif crop_box:
            x, y, w, h = crop_box
        else:
            # No cropping
            x, y, w, h = 0, 0, image.width, image.height
        
        # Crop the image
        crop_area = (x, y, x + w, y + h)
        cropped = image.crop(crop_area)
        
        # Save if output path provided
        if output_path is None:
            # Generate output path in temp directory
            base_name = Path(image_path).stem
            ext = Path(image_path).suffix
            output_path = os.path.join(tempfile.gettempdir(), f"{base_name}_cropped{ext}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        cropped.save(output_path, quality=95)
        return output_path
    
    def crop_images_in_folder(self, folder_path: str, output_folder: str = None) -> List[str]:
        """
        Crop all images in a folder
        
        Args:
            folder_path: Path to folder containing images
            output_folder: Path to save cropped images (optional)
        
        Returns:
            List of paths to cropped images
        """
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        image_files = [f for f in os.listdir(folder_path) 
                      if Path(f).suffix.lower() in valid_extensions]
        
        cropped_images = []
        for image_file in image_files:
            input_path = os.path.join(folder_path, image_file)
            
            if output_folder:
                os.makedirs(output_folder, exist_ok=True)
                output_path = os.path.join(output_folder, f"cropped_{image_file}")
            else:
                output_path = None
            
            try:
                cropped_path = self.crop_image(input_path, output_path)
                cropped_images.append(cropped_path)
            except Exception as e:
                print(f"Error cropping {image_file}: {e}")
                continue
        
        return cropped_images
    
    def create_zip_from_images(self, image_paths: List[str], zip_path: str = None) -> bytes:
        """
        Create a ZIP file from multiple cropped images
        
        Args:
            image_paths: List of paths to images
            zip_path: Path to save ZIP file (optional)
        
        Returns:
            BytesIO object containing the ZIP file
        """
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for image_path in image_paths:
                if os.path.exists(image_path):
                    arcname = os.path.basename(image_path)
                    zip_file.write(image_path, arcname=arcname)
        
        zip_buffer.seek(0)
        
        # Save to file if path provided
        if zip_path:
            with open(zip_path, 'wb') as f:
                f.write(zip_buffer.getvalue())
        
        return zip_buffer
    
    def process_and_zip(self, folder_path: str, zip_path: str = None, 
                       cleanup: bool = True) -> bytes:
        """
        Complete workflow: crop all images in folder and create ZIP
        
        Args:
            folder_path: Path to folder with images
            zip_path: Path to save ZIP file (optional)
            cleanup: Whether to delete temporary cropped images
        
        Returns:
            BytesIO object containing the ZIP file
        """
        # Create temp output folder
        temp_output = os.path.join(tempfile.gettempdir(), 'cropped_images_' + 
                                   os.path.basename(folder_path))
        os.makedirs(temp_output, exist_ok=True)
        
        try:
            # Crop all images
            cropped_images = self.crop_images_in_folder(folder_path, temp_output)
            
            if not cropped_images:
                raise ValueError("No images found or cropped in the folder")
            
            # Create ZIP
            zip_buffer = self.create_zip_from_images(cropped_images, zip_path)
            
            return zip_buffer
        
        finally:
            # Cleanup temp folder
            if cleanup and os.path.exists(temp_output):
                import shutil
                shutil.rmtree(temp_output, ignore_errors=True)


def crop_uploaded_images(files_list: List, output_format: str = 'zip') -> Tuple[bytes, str]:
    """
    Process uploaded images and return cropped versions
    
    Args:
        files_list: List of file objects from Flask request
        output_format: 'zip' or 'folder'
    
    Returns:
        Tuple of (file_bytes, filename)
    """
    cropper = ImageCropper(auto_detect=True, margin=2, auto_rotate=True)
    
    # Create temp folder for uploaded images
    temp_input = os.path.join(tempfile.gettempdir(), 'uploaded_images_temp')
    os.makedirs(temp_input, exist_ok=True)
    
    # Save uploaded files
    for file in files_list:
        if file.filename:
            file.save(os.path.join(temp_input, file.filename))
    
    try:
        # Process images
        zip_buffer = cropper.process_and_zip(temp_input, cleanup=False)
        
        return zip_buffer.getvalue(), 'cropped_images.zip'
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_input, ignore_errors=True)

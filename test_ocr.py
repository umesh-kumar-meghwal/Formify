import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

image_path = r"C:\Users\umesh\Documents\Formify\test.jpg"

# Read image
image = cv2.imread(image_path)

# Resize 4x
image = cv2.resize(
    image,
    None,
    fx=4,
    fy=4,
    interpolation=cv2.INTER_CUBIC
)

# Grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Threshold
gray = cv2.threshold(
    gray,
    0,
    255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)[1]

# OCR
text = pytesseract.image_to_string(
    gray,
    lang="eng",
    config="--psm 6"
)

print("========== OCR RESULT ==========")
print(text)
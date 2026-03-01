import qrcode
from PIL import Image
import os

def create_qr_code(data, filename="qr_code.png"):
    """
    Creates a QR code from the given data and saves it as an image.
    
    Args:
        data (str): The data to encode in the QR code
        filename (str): The output filename for the QR code image
    """
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Add data and optimize
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create an image from the QR code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save the image
        img.save(filename)
        print(f"QR code saved as {filename}")
        return True
    except Exception as e:
        print(f"Error creating QR code: {e}")
        return False

def main():
    """Main function to demonstrate QR code generation"""
    # Example usage
    data = input("Enter the data to encode in QR code: ")
    filename = input("Enter the output filename (default: qr_code.png): ") or "qr_code.png"
    
    if create_qr_code(data, filename):
        print("QR code generated successfully!")
    else:
        print("Failed to generate QR code.")

if __name__ == "__main__":
    main()
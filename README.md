# Meu-QR

A simple Python application to generate QR codes from text input.

## Description

Meu-QR is a lightweight QR code generator that allows you to easily create QR codes from any text or URL. The generated QR codes are saved as PNG images.

## Features

- Simple and easy-to-use interface
- Generate QR codes from any text or URL
- Save QR codes as PNG images
- Customizable output filename

## Requirements

- Python 3.7+
- qrcode[pil]
- Pillow

## Installation

1. Clone the repository:
```bash
git clone https://github.com/joaovicampos18-pixel/Meu-QR.git
cd Meu-QR
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

Then follow the prompts:
- Enter the data to encode in the QR code
- Enter the output filename (or press Enter for default: `qr_code.png`)

## Example

```bash
$ python main.py
Enter the data to encode in QR code: https://github.com/joaovicampos18-pixel
Enter the output filename (default: qr_code.png): my_qr.png
QR code saved as my_qr.png
QR code generated successfully!
```

## License

This project is open source and available under the MIT License.

## Author

João Vitor Campos (@joaovicampos18-pixel)
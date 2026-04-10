import easyocr

if __name__ == "__main__":
    reader = easyocr.Reader(["en"])
    result = reader.readtext("OP12-086.png")
    print(result)
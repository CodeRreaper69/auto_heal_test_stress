# text to pdf 

from pdfminer.high_level import extract_text 

a = True
while a:
	pdf_loc = input("Enter Name of the pdf (should be in the same directory)!: ")
	text = extract_text(pdf_loc)
    ch = input("Do it again?: ")
    if ch.lower() == "n":
        a = False
    else:
        pass
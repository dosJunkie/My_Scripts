import fpdf
import os
import re

class Pdf_Gen():

    def __init__(self, link, ):
        self.logo_link = link


    def insert_image(self, font, lr_margin, t_margin, size):
        pdf=fpdf.FPDF("P", "mm", "A4")
        pdf.add_page()
        pdf.set_margins(left=lr_margin, top=t_margin, right=lr_margin)
        pdf.image(self.logo_link, x=67, y=8, w=70)
        pdf.set_font(font, size=size, style="B")
        pdf.cell(200,10, txt="TEAM         CompSec Direct", ln=1, align="L")
        #pdf.multi_cell
        #pdf.output("add_image.pdf")
        return pdf


    def csv(self, image, name, csv):
        name = name + ".pdf"
        info = re.compile("(.*)=(.*)")
        with open(csv) as file:
                for line in file.readlines():
                    args = line.strip()
                    # content = args[:-1]
                    output = info.search(args)
                    left = output.group(1)
                    right = output.group(2)
                    image.multi_cell(200,10, txt=left.upper()+":"+"         " + right, align="L")

        image.output(name)
        answer = str(os.path.abspath(name))
        return "Your PDF is located in: " + answer
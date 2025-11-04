import re
from PyPDF2 import PdfReader
import pandas as pd
import numpy as np

class PDFtoDataFrame:
    def __init__(self, pdf_path, password = None):
        self.pdf_path = pdf_path
        self.password = password

    def pdf_to_text(self):
        # open reader
        reader = PdfReader(self.pdf_path)

        if reader.is_encrypted:
            try:
                reader.decrypt(self.password)   # returns 0/1/2 depending on method
            except Exception as e:
                raise SystemExit(f"Failed to decrypt: {e}")

        # read text from pages
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")

        full_text = "\n".join(text)
        return full_text

    #text = pdf_to_text(pdf_path, password)

    def text_to_dataframe(self, text):
        transactions = re.split(r'\n(?=[A-Z][a-z]{2} \d{2}, \d{4})', text)
        transactions = [t.strip() for t in transactions if "Transaction ID" in t]

        trans = []
        for i in transactions:
            date = re.search(r'([A-Z][a-z]{2} \d{2}, \d{4})', i)
            time = re.search(r'(\d{2}:\d{2} [AP]M)', i)
            desc = re.search(r'(Paid to|Received from) (.+)', i)
            details = re.search(r'(Debited from|Credited to) (.+)', i)
            amount = re.search(r'(\d+\.\d+)', i)
            trans_id = re.search(r'Transaction ID\s*:\s*(\S+)', i)
            utr = re.search(r'UTR No\s*:\s*(\S+)', i)

            trans.append({
            "Date": date.group(0) if date else None,
            "Time": time.group(0) if time else None,
            "Description": desc.group(2) if desc else None,
            "Type": details.group(1).split(" ")[0] if details else None,
            "Account": details.group(2).split(" ")[0] if details else None,
            "Amount": amount.group(0) if amount else None,
            "Transaction_ID": trans_id.group(1) if trans_id else None,
            "UTR_No": utr.group(1) if utr else None,
            #"Currency": details.group(2).split(" ")[1] if details else None
            })

        df = pd.DataFrame(trans)
        df['Amount'] = df['Amount'].replace("", np.nan).astype(float)
        df["Date"] = pd.to_datetime(df["Date"], format="%b %d, %Y")
        df["Datetime"] = pd.to_datetime(df["Date"].astype(str) + " " + df["Time"])
        df = df.drop(['Date', 'Time'], axis = 1)
        df = df[['Datetime','Transaction_ID','UTR_No','Account', 'Type', 'Amount', 'Description']]
        return df

    #df = text_to_dataframe(text)

    def convert(self):
        text = self.pdf_to_text()

        return self.text_to_dataframe(text)

## Usage
#converter = PDFtoDataFrame('PhonePe_Transaction_Statement.pdf', password)
#converter.convert()

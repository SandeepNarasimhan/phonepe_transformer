import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

from pdf_to_df import PDFtoDataFrame

## Load password for pdf decryption
load_dotenv()
password = os.getenv('password')

## convert PhonePe pdf statement to dataframe
converter = PDFtoDataFrame("PhonePe_Transaction_Statement_all.pdf", password)
df = converter.convert()

## Daily Credit vs Debit
df.groupby([df["Datetime"].dt.date, "Type"])["Amount"].sum().unstack(fill_value=0)

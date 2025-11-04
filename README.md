# PhonePe Transaction Statement Visualizer

This project is aimed to convert PDF statement which can be downloaded from the payment app (PhonePe Only) to a proper Dataframe using python

The Converted Dataframe contains
Datetime - Date and time of transaction
Transaction ID
UTR Number
Account - Debited to or Credited From Account details (Masked by Phonepe)
Type - Debit/Credit
Amount - Amount of transaction in INR
Description - Amount paid to or received from Details

Plan:
To Build a Dashboard to analyse:
Timeseries, for example average transaction amount in a week or a month over period
Merchant, Most transactions (credit/debit) made with whom
Transaction Behaviours
Outliers 
Etc.
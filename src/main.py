"""PDF to CSV extractor"""

import csv
import re
import os
from PyPDF2 import PdfReader
import pandas as pd
from constatns import (
    PATH,
    SAMPLE_FILE,
    INGRAM_MICRO,
    SERIAL_NO,
    REPRINTED,
    D_L,
)

def main():
    """
    This function reads all pdf files from the directory and extracts the
    required information from the pdf files. Finaly it writes the resul of all
    pdf files into one csv.
    """
    columns = []
    with open(SAMPLE_FILE) as file:
        reader = csv.reader(file)
        columns = next(reader)

    data_frame = pd.DataFrame()

    for filename in os.listdir(PATH):
        if filename.startswith("."):
            continue
        pdf = PdfReader(os.path.join(PATH, filename))
        text = pdf.pages[0].extract_text()

        data_frame_rows = {}
        info = text.split("\n")

        data_frame_rows[columns[0]] = info[4][8:]
        data_frame_rows[columns[1]] = info[5]
        data_frame_rows[columns[2]] = info[6]
        data_frame_rows[columns[3]] = info[7][:-10]
        invoice_to = ""

        x = 0
        for row in info[8:]:
            if columns[5] in row:
                invoice_to += row[:-20]
                x = x + 1
                break
            invoice_to += row
            x = x + 1

        data_frame_rows[columns[4]] = invoice_to
        consignee = ""

        for row in info[x + 8 :]:
            if "Consignment Details" == row:
                break
            consignee += row
            x = x + 1

        data_frame_rows[columns[5]] = consignee
        data_frame_rows[columns[6]] = info[x + 12][20:]
        data_frame_rows[columns[7]] = info[x + 13]
        data_frame_rows[columns[8]] = info[x + 14].split(":")[1].strip()
        data_frame_rows[columns[9]] = info[x + 14].split(":")[2].strip()
        data_frame_rows[columns[10]] = info[x + 15]

        if info[x + 16] != "Our":
            data_frame_rows[columns[10]] = ", ".join(
                [data_frame_rows[columns[10]], info[x + 16]]
            )
            x = x + 1

        # Create empty list for multiple records
        for i in range(8):
            data_frame_rows[columns[i + 15]] = []

        previous_len = 0
        for item in info[x + 24 :]:
            r = item.strip().split(" ")

            if INGRAM_MICRO in item:
                if SERIAL_NO not in item:
                    if previous_len == 5:
                        data_frame_rows[columns[15]].append(r[0])
                        data_frame_rows[columns[16]].append(r[1])
                        data_frame_rows[columns[17]].append(" ".join(r[2:-8]))
                        data_frame_rows[columns[18]].append(r[-8])
                        data_frame_rows[columns[19]].append(r[-7])
                        data_frame_rows[columns[22]].append(r[-5])
                    else:
                        try:
                            data_frame_rows[columns[17]][-1] = " ".join(
                                [
                                    data_frame_rows[columns[17]][-1],
                                    " ".join(r[:-7])[:-1],
                                ]
                            )
                        except IndexError:
                            data_frame_rows[columns[17]].append(
                                " ".join(r[:-8])
                            )
                        data_frame_rows[columns[18]].append(
                            " ".join(r[:-7])[-1]
                        )
                        data_frame_rows[columns[19]].append(r[-7])
                        data_frame_rows[columns[22]].append(r[-5])
                break
            if SERIAL_NO not in item:
                if len(r) > 4 and item[-1] != " ":
                    data_frame_rows[columns[15]].append(r[0])
                    data_frame_rows[columns[16]].append(r[1])
                    data_frame_rows[columns[17]].append(" ".join(r[2:]))
                elif len(r) == 2:
                    data_frame_rows[columns[15]].append(r[0])
                    data_frame_rows[columns[16]].append(r[1])
                elif len(r) > 4 and previous_len == 2:
                    data_frame_rows[columns[17]].append(" ".join(r[:-4]))
                    data_frame_rows[columns[18]].append(r[-4])
                    data_frame_rows[columns[19]].append(r[-3])
                    data_frame_rows[columns[22]].append(r[-1])
                elif len(r) > 4 and previous_len != 2:
                    data_frame_rows[columns[15]].append(r[0])
                    data_frame_rows[columns[16]].append(r[1])
                    data_frame_rows[columns[17]].append(" ".join(r[2:-4]))
                    data_frame_rows[columns[18]].append(r[-4])
                    data_frame_rows[columns[19]].append(r[-3])
                    data_frame_rows[columns[22]].append(r[-1])
                elif len(r) == 4:
                    data_frame_rows[columns[17]][-1] = " ".join(
                        [data_frame_rows[columns[17]][-1], r[0][:-1]]
                    )
                    data_frame_rows[columns[18]].append(r[0][-1])
                    data_frame_rows[columns[19]].append(r[-3])
                    data_frame_rows[columns[22]].append(r[-1])
                elif len(r) == 3:
                    data_frame_rows[columns[17]].append(" ".join(r))
            x = x + 1
            previous_len = len(r)
        data_frame_rows[columns[11]] = re.search(
            "Date(.*)Invoice Number", info[x + 27]
        ).group()[8:-14]
        data_frame_rows[columns[12]] = re.search(
            "Invoice Number(.*)", info[x + 27]
        ).group()[17:]
        if REPRINTED in info[x + 28]:
            data_frame_rows[columns[13]] = re.search(
                "Account Number(.*)REPRINTED", info[x + 28]
            ).group()[17:-9]
        else:
            data_frame_rows[columns[13]] = re.search(
                "Account Number(.*)TAX INVOICE", info[x + 28]
            ).group()[17:-11]

        if D_L in info[x + 29]:
            data_frame_rows[columns[14]] = re.search(
                "Delivery Number(.*)D/L", info[x + 29]
            ).group()[16:-3]
        else:
            data_frame_rows[columns[14]] = re.search(
                "Delivery Number(.*)1 of 1", info[x + 29]
            ).group()[16:-6]

        list_length = len(data_frame_rows[columns[15]])
        for key, value in data_frame_rows.items():
            if type(value) != list:
                data_frame_rows[key] = [value] * list_length
            elif type(value) == list and len(value) == 0:
                data_frame_rows[key] = [None] * list_length

        data_frame = data_frame.append(pd.DataFrame.from_dict(data_frame_rows))

    data_frame.to_csv("ingram_micro.csv", index=False, header=True)


if __name__ == "__main__":
    main()
    print("end")

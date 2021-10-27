# Make sure pcaps are in same directory as this script
# Run "python3 sha_pcaps.py >> name.csv"
import glob
import hashlib
import os
import csv


class Pcap_Handler():

    def __init__(self):
        # path to pcap files
        self.pcap_path = "./good2/*.pcap"
        # name of output csv file
        self.csv_file = "good2.csv"

    def create_rowlist(self):
        row_list = []

        for name in glob.glob(self.pcap_path):
            with open(name, "rb") as f:
                bytes = f.read()  # read entire file as bytes
                readable_hash = hashlib.sha256(bytes).hexdigest()
                file_size = os.path.getsize(name)
                gb_size = self.bytesto(file_size, to="gb")
                row_list.append(
                    [os.path.basename(name), gb_size, readable_hash])

        return row_list

    def find_gb(self):
        final_size = 0
        for gb in self.create_rowlist():
            final_size += gb[1]
        return final_size

    def create_csv(self):
        row_list = self.create_rowlist()
        with open(self.csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "File Size in GB", "Sha256 Hash"])
            writer.writerow(
                ["Size of all Files Combined", f"{self.find_gb()} GB"])
            writer.writerows(row_list)

        return("Done!")

    def bytesto(self, bytes, to, bsize=1024):
        a = {'kb': 1, 'mb': 2, 'gb': 3, 'tb': 4, 'pb': 5, 'eb': 6}
        r = float(bytes)
        return bytes / (bsize ** a[to])

    def main(self):
        return self.create_csv()


if __name__ == "__main__":
    obj = Pcap_Handler()
    print(obj.main())

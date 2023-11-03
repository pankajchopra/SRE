import csv
import json

def csv_to_json(csv_file_path, json_file_path):
  """Converts a CSV file to a JSON file without using json.JSONWriter.

  Args:
    csv_file_path: The path to the CSV file.
    json_file_path: The path to the JSON file.
  """

  with open(csv_file_path, "r") as csv_file, open(json_file_path, "w") as json_file:
    reader = csv.DictReader(csv_file)

    json_data = []
    for row in reader:
      json_data.append(row)

    json_file.write(json.dumps(json_data, indent=4))

def main():
  csv_file_path = "emailssample.csv"
  json_file_path = "emailssample.json"

  csv_to_json(csv_file_path, json_file_path)

if __name__ == "__main__":
  main()

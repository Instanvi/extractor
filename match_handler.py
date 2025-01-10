import openai
import os
from dotenv import load_dotenv

# Ensure you have installed the latest OpenAI library
# pip install openai --upgrade

load_dotenv()

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_data_from_text(text):
  """
  Extracts data from the given text using a language model.

  Args:
    text: The text extracted from the image.

  Returns:
    A dictionary containing the extracted data.
  """

  prompt = f"""
  Extract the following data from the given text:

  * doc_type 
  * doc_number
  * issue_date
  * due_date
  * supplier_name
  * supplier_address
  * customer_name
  * customer_address
  * total_amount
  * tax_amount
  * currency
  * line_items (list of dictionaries, each containing: 
      - item_name
      - quantity
      - unit_price
      - amount
      - currency)

  **Text:**
  {text}

  **Example:**

  **Text:** 
  Invoice No: INV-2023-001
  Date: 15/11/2023
  Due Date: 30/11/2023
  Supplier: Acme Corp
  Supplier Address: 123 Main St, Anytown
  Customer: XYZ Inc
  Customer Address: 456 Elm St, Othertown
  ... (line items)

  **Output:**
  {{
      "doc_type": "Invoice",
      "doc_number": "INV-2023-001",
      "issue_date": "15/11/2023",
      "due_date": "30/11/2023",
      "supplier_name": "Acme Corp", 
      "supplier_address": "123 Main St, Anytown",
      "customer_name": "XYZ Inc",
      "customer_address": "456 Elm St, Othertown",
      "total_amount": "1000.00", 
      "tax_amount": "100.00",
      "currency": "$",
      "line_items": [
          {{"item_name": "Product A", "quantity": 2, "unit_price": "50.00", "amount": "100.00", "currency":"$"}},
          {{"item_name": "Product B", "quantity": 1, "unit_price": "50.00", "amount": "50.00", "currency":"$"}}
      ]
  }}
  """

  response = openai.completions.create(
      model="gpt-3.5-turbo-instruct",  # Choose an appropriate model
      prompt=prompt,
      max_tokens=1024,
      n=1,
      stop=None,
      temperature=0.7,  # Adjust temperature for creativity
  )

  try:
      extracted_data = response.choices[0].text.strip()  # Get the text directly
      return extracted_data
  except (SyntaxError, NameError):
      print("Error parsing the output from the language model.")
      return None

# # Example usage
# extracted_text = "Your extracted text from the image goes here"  # Replace with your actual text
# extracted_data = extract_data_from_text(extracted_text)

# if extracted_data:
#   print(extracted_data)
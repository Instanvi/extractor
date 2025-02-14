import os
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from collections import defaultdict

from dotenv import load_dotenv

load_dotenv()


azure_fr_endpoint = os.environ["AZURE_FR_ENDPOINT"]
AZURE_FR_API_KEY = os.environ["AZURE_FR_API_KEY"]

credential = AzureKeyCredential(AZURE_FR_API_KEY)



def combine_data_cells(cells, data_type="data", meta=True):
    curr_row = None
    all_data_rows, row_data = [], []

    if data_type == "data":
        for cell in cells:
            row_index = cell.row_index
            if meta:
                if row_index > 1:
                    if curr_row is None:
                        curr_row = row_index
                        row_data.append(cell.content)
                    elif curr_row == row_index:
                        row_data.append(cell.content)
                    elif curr_row != row_index:
                        all_data_rows.append(row_data)
                        row_data = []
                        curr_row =row_index
                        row_data.append(cell.content)
            else:
                if row_index > 0:
                    if curr_row is None:
                        curr_row = row_index
                        row_data.append(cell.content)
                    elif curr_row == row_index:
                        row_data.append(cell.content)
                    elif curr_row != row_index:
                        all_data_rows.append(row_data)
                        row_data = []
                        curr_row =row_index
                        row_data.append(cell.content)
        
        return all_data_rows
    
    elif data_type == "header":
        for cell in cells:
            curr_row_index = cell.row_index
            if meta:
                if curr_row_index == 1:
                    if curr_row is None:
                        curr_row = curr_row_index
                        row_data.append(cell.content)
                    elif curr_row == curr_row_index:
                        row_data.append(cell.content)
                elif curr_row_index > 1:
                    break
            else:
                if curr_row_index == 0:
                    if curr_row is None:
                        curr_row = curr_row_index
                        row_data.append(cell.content)
                    elif curr_row == curr_row_index:
                        row_data.append(cell.content)
                elif curr_row_index > 1:
                    break

        return row_data

    elif data_type == "metadata":
        for cell in cells:
            curr_row_index = cell.row_index
            
            if curr_row_index == 0:
                if curr_row is None:
                    curr_row = curr_row_index
                    row_data.append(cell.content)
                elif curr_row == curr_row_index:
                    row_data.append(cell.content)
            else:
                break
        
        return row_data




def organise_data_main(result_content, cells, extraction_result, page):

    #Get Metadata
    all_metadata_rows = combine_data_cells(cells, data_type="metadata")
    meta= True
    for idx, data in enumerate(all_metadata_rows):
        if data == "":
            all_metadata_rows.pop(idx)

    if "account receivables" in result_content or "account payables" in result_content:
        if len(all_metadata_rows) == 3:
            split_date = str(all_metadata_rows[2]).split()
            month = split_date[-2]
            year = split_date[-1].replace("/","")

        elif len(all_metadata_rows) == 4:
            split_date = str(all_metadata_rows[2]).split()
            month = split_date[-1]
            year = str(all_metadata_rows[3]).replace("/", "")
        elif len(all_metadata_rows) == 5:
            month = all_metadata_rows[4]
            year = str(all_metadata_rows[4]).replace("/", "")

        extraction_result[page]["metadata"] = {
            "doc_type": all_metadata_rows[0],
            "doc_id": all_metadata_rows[1],
            "month": month,
            "year": year
        }
    elif "expense sheet" in result_content:
        if str(all_metadata_rows[0]).lower().endswith("sheet"):
            doc_type = all_metadata_rows[0]
            doc_id = all_metadata_rows[1]
            date = all_metadata_rows[2]
            if date.endswith(")"):
                date = all_metadata_rows[3].split()
                if len(date) == 2:
                    month = date[0]
                    year = date[1].replace("/", "")
                elif len(date) ==1:
                    month = all_metadata_rows[3]
                    year = all_metadata_rows[4].replace("/", "")
            else:
                date = all_metadata_rows[2].split()
                if len(date) == 3:
                    month = date[-1]
                    year = all_metadata_rows[3].replace("/", "")
                elif len(date) == 4:
                    month = date[2]
                    year = date[3].replace("/", "")
        else:
            split_doc_type = str(all_metadata_rows[0]).split()
            doc_type = f"{split_doc_type[0]} {split_doc_type[1]}"
            doc_id = split_doc_type[-1]
            date = all_metadata_rows[1]
            if date.endswith(")"):
                date = all_metadata_rows[2].split()
                if len(date) == 2:
                    month = date[0]
                    year = date[1].replace("/", "")
                elif len(date) ==1:
                    month = all_metadata_rows[2]
                    year = all_metadata_rows[3].replace("/", "")
            else:
                date = all_metadata_rows[1].split()
                if len(date) == 3:
                    month = date[-1]
                    year = all_metadata_rows[2].replace("/", "")
                elif len(date) == 4:
                    month = date[2]
                    year = date[3].replace("/", "")
        
        extraction_result[page]["metadata"] = {
            "doc_type": doc_type,
            "doc_id": doc_id,
            "month": month,
            "year": year
        }

    elif "inventory" in result_content:
        
        if "inventory" not in str(all_metadata_rows[0]).lower():
            print(all_metadata_rows)
            metadata_list = str(result_content).splitlines()
            date = metadata_list[3].split()
            doc_type = metadata_list[0]
            doc_id = metadata_list[1]
            month = date[0]
            year = date[1].replace("/", "")
            meta = False

        elif len(all_metadata_rows) == 1:
            meta_split = all_metadata_rows[0].split()
            doc_type = meta_split[0]
            doc_id = meta_split[1]
            month = meta_split[4]
            year = meta_split[5].replace("/", "")
        elif len(all_metadata_rows) > 1:
            doc_type = all_metadata_rows[0]
            doc_id = all_metadata_rows[1]
            date = all_metadata_rows[2]

            if date.endswith(")"):
                date = all_metadata_rows[3].split()
                if len(date) == 2:
                    month = date[0]
                    year = date[1].replace("/", "")
                elif len(date) ==1:
                    month = all_metadata_rows[3]
                    year = all_metadata_rows[4].replace("/", "")
            else:
                date = all_metadata_rows[2].split()
                if len(date) == 3:
                    month = date[-1]
                    year = all_metadata_rows[3].replace("/", "")
                elif len(date) == 4:
                    month = date[2]
                    year = date[3].replace("/", "")

        extraction_result[page]["metadata"] = {
            "doc_type": doc_type,
            "doc_id": doc_id,
            "month": month,
            "year": year
        }

    elif "sales sheet" in result_content:
        if "sales sheet" not in str(all_metadata_rows[0]).lower():
            print(all_metadata_rows)
            metadata_list = str(result_content).splitlines()
            date = metadata_list[2].split()
            doc_head = metadata_list[0].split()
            doc_type = f"{doc_head[0]} {doc_head[1]}"
            doc_id = doc_head[2]
            month = date[0]
            year = date[1].replace("/", "")
            meta = False

        elif len(all_metadata_rows) == 1:
            meta_split = all_metadata_rows[0].split()
            doc_type = f"{meta_split[0]} {meta_split[1]}"
            doc_id = meta_split[2]
            if len(meta_split) == 7:
                month = meta_split[5]
                year = meta_split[6].replace("/", "")
            elif len(meta_split) == 6 and "/" in meta_split[5]:
                date = meta_split[5].split("/")
                month = date[0]
                year = date[1]
            elif len(meta_split) == 5 and "/" not in meta_split[5]:
                month = meta_split[5][:2]
                year = meta_split[5][2:]

        elif len(all_metadata_rows) > 1:
            if str(all_metadata_rows[0]).lower().endswith("sheet"):
                doc_type = all_metadata_rows[0]
                doc_id = all_metadata_rows[1]
                date = all_metadata_rows[2]

                if date.endswith(")"):
                    date = all_metadata_rows[3].split()
                    if len(date) == 2:
                        month = date[0]
                        year = date[1].replace("/", "")
                    elif len(date) ==1:
                        month = all_metadata_rows[3]
                        year = all_metadata_rows[4].replace("/", "")
                else:
                    
                    date = all_metadata_rows[2].split()
                    if len(date) == 3:
                        month = date[-1]
                        year = all_metadata_rows[3].replace("/", "")
                    elif len(date) == 4:
                        month = date[2]
                        year = date[3].replace("/", "")
            else:
                doc_head = all_metadata_rows[0].split()
                doc_type = f"{doc_head[0]} {doc_head[1]}"
                doc_id = doc_head[2]
                date = all_metadata_rows[1]

                if date.endswith(")"):
                    date = all_metadata_rows[2].split()
                    if len(date) == 2:
                        month = date[0]
                        year = date[1].replace("/", "")
                    elif len(date) ==1:
                        month = all_metadata_rows[2]
                        year = all_metadata_rows[3].replace("/", "")
                else:
                    
                    date = all_metadata_rows[2].split()
                    if len(date) == 3:
                        month = date[-1]
                        year = all_metadata_rows[3].replace("/", "")
                    elif len(date) == 4:
                        month = date[2]
                        year = date[3].replace("/", "")

        extraction_result[page]["metadata"] = {
            "doc_type": doc_type,
            "doc_id": doc_id,
            "month": month,
            "year": year
        }

    #Get all headers
    all_header_rows = combine_data_cells(cells, data_type="header", meta=meta)
    for idx, data in enumerate(all_header_rows):
        if data == "":
            all_header_rows.pop(idx)

    extraction_result[page]["header"] = all_header_rows

    
    if "account receivables" in result_content:
        all_data_rows = combine_data_cells(cells)
        print("In AR")
        # call combine_data_cells as from the 3rd row( 2nd index)
        if all_data_rows:
            for row_data in all_data_rows:
                if len(row_data) == 7:
                    row_data.pop(0)
                elif len(row_data) < 6:
                    print(row_data)
                    for i in range(6-len(row_data)): row_data.append(None)
                
                if "selected" in str(row_data[5]).lower():
                    row_data[5] = "selected"
                elif "unselected" in str(row_data[5]).lower():
                    row_data[5] = "unselected"
                
                # ['Date.', 'Customer', 'Telephone No.', 'Amount', 'Memo', 'S']
                data ={
                    "date": row_data[0].replace(" ","") if row_data[0] is not None else None,
                    "customer": row_data[1] if row_data[1] is not None else None,
                    "telephone_no": row_data[2].replace(" ","") if row_data[2] is not None else None,
                    "amount": row_data[3].replace(" ","") if row_data[3] is not None else None,
                    "memo": row_data[4].replace(" ","") if row_data[4] is not None else None,
                    "s": row_data[5] if row_data[5] is not None else None
                }

                #remove cells that are completely empty
                empty_count = 0
                for key in data:
                    key_value = data.get(key)
                    if key_value is not None and (not isinstance(key_value,str) or key_value.strip()):
                        pass
                    else:
                        empty_count += 1
                if empty_count < 6:
                    extraction_result[page]["data"].append(data)


    elif "account payables" in result_content:
        all_data_rows = combine_data_cells(cells)
        #Get table_cell data
        if all_data_rows:
            for row_data in all_data_rows:
                if len(row_data) < 6:
                    for i in range(6-len(row_data)): row_data.append(None)
                if "selected" in str(row_data[5]).lower():
                    row_data[5] = "selected"
                elif "unselected" in str(row_data[5]).lower():
                    row_data[5] = "unselected"
                
                data ={
                    "date": row_data[0].replace(" ","") if row_data[0] is not None else None,
                    "vendor": row_data[1] if row_data[1] is not None else None,
                    "vendor_tel": row_data[2].replace(" ","") if row_data[2] is not None else None,
                    "amount": row_data[3].replace(" ","") if row_data[3] is not None else None,
                    "ref_invoice": row_data[4].replace(" ","") if row_data[4] is not None else None,
                    "s": row_data[5] if row_data[5] is not None else None
                }

                #remove cells that are completely empty
                empty_count = 0
                for key in data:
                    key_value = data.get(key)
                    if key_value is not None and (not isinstance(key_value,str) or key_value.strip()):
                        pass
                    else:
                        empty_count += 1
                if empty_count < 6:
                    extraction_result[page]["data"].append(data)

    

    elif "expense sheet" in result_content:
        all_data_rows = combine_data_cells(cells)
        if all_data_rows:
            for row_data in all_data_rows:
                if len(row_data) < 5:
                    print(row_data)
                    for i in range(5-len(row_data)): row_data.append(None)
        
                data ={
                    "date": row_data[0].replace(" ","") if row_data[0] is not None else None,
                    "expense_description": row_data[1]  if row_data[1] is not None else None,
                    "category": row_data[2]  if row_data[2] is not None else None,
                    "total_price": row_data[3].replace(" ","")  if row_data[3] is not None else None,
                    "ref": row_data[4].replace(" ","")  if row_data[4] is not None else None
                }

                #remove cells that are completely empty
                empty_count = 0
                for key in data:
                    key_value = data.get(key)
                    if key_value is not None and (not isinstance(key_value,str) or key_value.strip()):
                        pass
                    else:
                        empty_count += 1
                if empty_count < 5:
                    extraction_result[page]["data"].append(data)

    elif "inventory" in result_content:
        all_data_rows = combine_data_cells(cells, meta= meta)
        if all_data_rows:
            for row_data in all_data_rows:
                if len(row_data) < 6:
                    print(row_data)
                    for i in range(6-len(row_data)): row_data.append(None)
        
                data ={
                    "date": row_data[0].replace(" ","") if row_data[0] is not None else None,
                    "item_name": row_data[1] if row_data[1] is not None else None,
                    "quantity": row_data[2].replace(" ","") if row_data[2] is not None else None,
                    "cost_price": row_data[3].replace(" ","") if row_data[3] is not None else None,
                    "selling_price": row_data[4].replace(" ","") if row_data[4] is not None else None,
                    "re_order_qty": row_data[5].replace(" ","") if row_data[5] is not None else None
                }

                #remove cells that are completely empty
                empty_count = 0
                for key in data:
                    key_value = data.get(key)
                    if key_value is not None and (not isinstance(key_value,str) or key_value.strip()):
                        pass
                    else:
                        empty_count += 1
                if empty_count < 6:
                    extraction_result[page]["data"].append(data)

    
    elif "sales sheet" in result_content:
        all_data_rows = combine_data_cells(cells, meta= meta)
        if all_data_rows:
            for row_data in all_data_rows:
                if len(row_data) == 6:
                    row_data.insert(1, "")
                elif len(row_data) < 7:
                    print(row_data)
                    for i in range(7-len(row_data)): row_data.append(None)
        
                data ={
                    "date": row_data[0].replace(" ","") if row_data[0] is not None else None,
                    "start_list": row_data[1] if row_data[1] is not None else None,
                    "item_name": f"{row_data[1]}{row_data[2]}" if row_data[1] is not None else row_data[2],
                    "qty": row_data[3].replace(" ","") if row_data[3] is not None else None,
                    "total_price": row_data[4].replace(" ","") if row_data[4] is not None else None,
                    "customer": row_data[5].replace(" ","") if row_data[5] is not None else None,
                    "ref": row_data[6].replace(" ","") if row_data[6] is not None else None
                }

                #remove cells that are completely empty
                empty_count = 0
                for key in data:
                    key_value = data.get(key)
                    if key_value is not None and (not isinstance(key_value,str) or key_value.strip()):
                        pass
                    else:
                        empty_count += 1
                if empty_count < 7:
                    extraction_result[page]["data"].append(data)

    return extraction_result
    





def equalizer(image_data):
    request = AnalyzeDocumentRequest(bytes_source=image_data)
    
    client = DocumentIntelligenceClient(endpoint=azure_fr_endpoint, credential=credential)
    poller = client.begin_analyze_document("prebuilt-layout", body=request)
    result = poller.result()
    
    extraction_result = {}
    for idx, table in enumerate(result.tables):
        result_content = str(result.content).lower()

        extraction_result[f"page{idx+1}"] = {
            "metadata": {},
            "header": [],
            "data": []
        }

        #For Extraction
        extraction_result = organise_data_main(result_content, table.cells, extraction_result, f"page{idx+1}")
        # print(f"\n\n{extraction_result}\n\n")

        return extraction_result
    
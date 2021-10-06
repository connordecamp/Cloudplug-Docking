from enum import Enum
from typing import List

import mysql.connector

from modules.core.sfp import SFP


class TableID(Enum):
    PAGE_A0 = 1
    PAGE_A2 = 2

def _get_number_of_columns_in_table(cursor, table_name: str) -> int:
    sql_statement = f"select count(*) as count from information_schema.columns where table_name=\'{table_name}\'"
    cursor.execute(sql_statement)
    result = cursor.fetchone()

    columns_in_table = result[0] - 1

    return columns_in_table

def insert_cloned_memory_to_database(cursor, page_a0_memory: List[int], page_a2_memory: List[int]) -> None:


    if len(page_a0_memory) != 256 or len(page_a2_memory) != 256:
        print("ERROR: Length of given memory is != 256")
        return

    # We can obtain identifying information from the page_a0 memory
    
    sfp = SFP(page_a0_memory, page_a2_memory)

    vendor_name = sfp.get_vendor_name()
    vendor_part_number = sfp.get_vendor_part_number()
    transceiver_type = sfp.get_transceiver_info()[0]

    table_name = "sfp"
    num_columns_in_table = _get_number_of_columns_in_table(cursor, table_name)

    

    sql_statement = f"INSERT INTO {table_name} (vendor_id, vendor_part_number, transceiver_type) VALUES (%s, %s, %s)"
    vals_to_insert = tuple([vendor_name, vendor_part_number, transceiver_type])

    if len(vals_to_insert) != num_columns_in_table:
        print("ERROR: Too few values to insert to database ID table")
    else:
        print(f'trying to execute: {sql_statement}')
        cursor.execute(sql_statement, vals_to_insert)

    # Now that we (hopefully) inserted the data into the ID table,
    # we call another function to actually insert the lists into
    # their corresponding tables in the database

    insert_to_page_table(cursor, TableID.PAGE_A0, page_a0_memory)
    # insert_to_page_table(cursor, TableID.PAGE_a2, page_a2_memory)

    

def insert_to_page_table(cursor, table_id: TableID, memory_page_values: List[int]):
    
    if len(memory_page_values) != 256:
        print(f"ERROR: Given {len(memory_page_values)} values but expected 256 values")

    if table_id == TableID.PAGE_A0:
        table_name = "page_a0"
    elif table_id == TableID.PAGE_A2:
        table_name = "page_a2"

    sql_statement = f'INSERT INTO {table_name} ('
    for i in range(255):
        sql_statement += f"`{i}`, "
    sql_statement += '`255`) VALUES ('
    for i in range(255):
        sql_statement += "%s, "
    sql_statement += "%s)"

    vals_to_insert = tuple(memory_page_values)

    cursor.execute(sql_statement, vals_to_insert)


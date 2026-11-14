import xml.etree.ElementTree as ET
import json
import os
import config_loader

# ==========================================
# CONFIGURATION (from config.yaml)
# ==========================================
INPUT_XML_FILE = config_loader.get('io.input_xml_file')
OUTPUT_JSON_FILE = config_loader.get('io.output_json_file')

# ==========================================
# UNIFIED SOURCE UDP NAMES
# ------------------------------------------
# The modeling team now emits a single, model-agnostic set of source UDP
# names in every Erwin XML (3NF / Data Vault / Business Vault / ...), so
# the parser reads the SAME UDP names regardless of conversion. One
# conversion-specific XML is supplied per run; the values behind these
# UDPs differ, but the UDP names do not.
# ==========================================
UDP_SOURCE_TABLE = "Source Table"
UDP_SOURCE_COLUMN = "Source Column"
UDP_TRANSFORMATION_RULE = "Transformation Rule"
# Column-level per-source filter (e.g. 'CRM: party_kind="Legal"'). Safe as a
# substring search — does not collide with "Columns to Filter if Null Text".
UDP_FILTER_RULE = "Filter Rule"

# `type_of_conversion` is NO LONGER used to pick UDP names here. It is
# retained only so it is available (via config.yaml) to the downstream
# query/DDL generators, which use it to select the TARGET model
# (Dimensional, Business Vault, ...). Default preserves prior behaviour.
DEFAULT_CONVERSION = "Data Vault to Dimensional"


def strip_ns(tag):
    """Removes namespace from tag."""
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

def get_text(node, tag_name):
    """Helper to safely get text from a child node."""
    if node is not None:
        for child in node:
            if strip_ns(child.tag) == tag_name:
                return child.text
    return ""

def get_udp_value(udp_group_node, search_string):
    """
    Searches for a UDP Instance where the 'name' attribute contains
    the search_string.
    """
    if udp_group_node is None:
        return None

    for udp in udp_group_node:
        name_attr = udp.get('name', '')
        if search_string in name_attr:
            return udp.text
    return None

def parse_erwin_full_mapping(xml_path, output_json_file=None):
    output_json_file = output_json_file or OUTPUT_JSON_FILE
    print(f"--- Processing {xml_path} ---")

    # `type_of_conversion` no longer influences UDP parsing — the source
    # UDP names are unified across models. It is read here only for
    # logging/traceability; the downstream generators consume it from
    # config.yaml to select the target model.
    conversion_type = config_loader.get(
        "generation.type_of_conversion", DEFAULT_CONVERSION
    )
    print(f"--- Conversion type (target model hint): {conversion_type} ---")

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"XML Parsing Error: {e}")
        return

    data_model_output = []

    for node in root.iter():
        tag = strip_ns(node.tag)

        # ==============================================
        # CHANGED: Only process Entities, skip Views
        # ==============================================
        obj_type = ""
        if tag == 'Entity':
            obj_type = 'Physical Table'
        # Views excluded — no processing for tag == 'View'

        if obj_type:
            # ======================================================
            # PHASE 1: IDENTIFY PRIMARY KEYS
            # ======================================================
            pk_attribute_ids = set()
            key_groups = None
            for child in node:
                if strip_ns(child.tag) == 'Key_Group_Groups':
                    key_groups = child
                    break

            if key_groups:
                for kg in key_groups:
                    kg_props = None
                    for child in kg:
                        if strip_ns(child.tag) == 'Key_GroupProps':
                            kg_props = child
                            break

                    is_pk = False
                    if kg_props:
                        kg_type = get_text(kg_props, 'Key_Group_Type')
                        if kg_type == 'PK':
                            is_pk = True

                    if is_pk:
                        member_groups = None
                        for child in kg:
                            if strip_ns(child.tag) == 'Key_Group_Member_Groups':
                                member_groups = child
                                break
                        if member_groups:
                            for member in member_groups:
                                mem_props = None
                                for child in member:
                                    if strip_ns(child.tag) == 'Key_Group_MemberProps':
                                        mem_props = child
                                        break
                                if mem_props:
                                    attr_ref = get_text(mem_props, 'Attribute_Ref')
                                    if attr_ref:
                                        pk_attribute_ids.add(attr_ref)

            # ======================================================
            # PHASE 2: EXTRACT TABLE INFO & UDP COLUMNS
            # ======================================================
            props_tag = f"{tag}Props"
            props_node = None
            for child in node:
                if strip_ns(child.tag) == props_tag:
                    props_node = child
                    break

            if not props_node: continue

            target_name = get_text(props_node, 'Physical_Name')
            if not target_name:
                target_name = get_text(props_node, 'Name') or "Unknown"

            definition = get_text(props_node, 'Definition')
            if not definition:
                definition = get_text(props_node, 'Comment')

            udp_node = None
            for child in props_node:
                if strip_ns(child.tag) == 'UDP_Instance_Groups':
                    udp_node = child
                    break

            # Existing UDP extractions
            src_dv_table_list = get_udp_value(
                udp_node, UDP_SOURCE_TABLE
            )


            src_logical_table_list = get_udp_value(
                udp_node, 'Business Model Logical Table'
            )

            # New UDP extractions
            business_key = get_udp_value(
                udp_node, 'Business Key Attribute'
            )
            scd_type = get_udp_value(udp_node, 'SCD')
            table_type_udp = get_udp_value(udp_node, 'Table Type')
            loading_order = get_udp_value(udp_node, 'Loading Order')
            dependency = get_udp_value(udp_node, 'Dependency')
            retention_type = get_udp_value(udp_node, 'Retention Type')
            retention_attribute = get_udp_value(
                udp_node, 'GDPR Retention Attribute'
            )
            retention_ref_table = get_udp_value(
                udp_node, 'GDPR Retention Reference Table'
            )
            where_clause = get_udp_value(udp_node, 'Where Clause')
            contains_pii = get_udp_value(udp_node, 'Contains PII Ind')
            database_name = get_udp_value(udp_node, 'Database Name')
            schema_name = get_udp_value(udp_node, 'Schema Name')

            # ======================================================
            # PHASE 3: EXTRACT COLUMNS & MAPPINGS
            # ======================================================
            column_mappings = []
            watermark_date_columns = []
            watermark_time_columns = []

            attr_group = None
            for child in node:
                if strip_ns(child.tag) == 'Attribute_Groups':
                    attr_group = child
                    break

            if attr_group:
                for attr in attr_group:
                    if strip_ns(attr.tag) != 'Attribute':
                        continue

                    attr_id = attr.get('id')
                    attr_props = None
                    for child in attr:
                        if strip_ns(child.tag) == 'AttributeProps':
                            attr_props = child
                            break

                    if not attr_props: continue

                    col_name = get_text(attr_props, 'Physical_Name')
                    if not col_name:
                        col_name = get_text(attr_props, 'Name')

                    # col_name = get_text(attr_props, 'Data Vault Source Column')
                    # if not col_name:
                    #     col_name = get_text(attr_props, 'Name')

                    col_type = get_text(attr_props, 'Logical_Data_Type')

                    col_order = get_text(attr_props, 'Physical_Order')
                    if not col_order:
                        col_order = get_text(attr_props, 'Column_Order')

                    col_desc = get_text(attr_props, 'Comment')
                    if not col_desc:
                        col_desc = get_text(attr_props, 'Definition')

                    is_pk_val = (
                        "Yes" if attr_id in pk_attribute_ids else "No"
                    )
                    parent_ref = get_text(
                        attr_props, 'Parent_Attribute_Ref'
                    )
                    is_fk_val = "Yes" if parent_ref else "No"

                    col_udp_node = None
                    for child in attr_props:
                        if strip_ns(child.tag) == 'UDP_Instance_Groups':
                            col_udp_node = child
                            break

                    src_col = get_udp_value(
                        col_udp_node, UDP_SOURCE_COLUMN
                    )
                    trans_rule = get_udp_value(
                        col_udp_node, UDP_TRANSFORMATION_RULE
                    )
                    col_specific_src_table = get_udp_value(
                        col_udp_node, UDP_SOURCE_TABLE
                    )
                    filter_rule = get_udp_value(
                        col_udp_node, UDP_FILTER_RULE
                    )

                    # Watermark detection
                    date_partition_ind = get_udp_value(
                        col_udp_node, 'Date Partition Ind'
                    )
                    time_partition_ind = get_udp_value(
                        col_udp_node, 'Time Partition Ind'
                    )

                    if (date_partition_ind and
                            date_partition_ind.strip().lower()
                            in ('y', 'yes', 'true', '1')):
                        watermark_date_columns.append(col_name)

                    if (time_partition_ind and
                            time_partition_ind.strip().lower()
                            in ('y', 'yes', 'true', '1')):
                        watermark_time_columns.append(col_name)

                    if col_name:
                        col_obj = {
                            "Target_Column": col_name,
                            "Data_Type": col_type,
                            "Column_Order": col_order,
                            "Is_PK": is_pk_val,
                            "Is_FK": is_fk_val,
                            "Column_Definition": col_desc,
                            "SourceMapping": {
                                "Source_Table": col_specific_src_table,
                                "Source_Column": src_col,
                                "Transformation_Logic": trans_rule,
                                "Filter_Rule": filter_rule
                            }
                        }
                        column_mappings.append(col_obj)

            # Sort columns by order
            column_mappings.sort(
                key=lambda x: int(x['Column_Order'])
                if x['Column_Order'] and x['Column_Order'].isdigit()
                else 999
            )

            table_obj = {
                "Target_Table": target_name,
                "Target_Table_Type": obj_type,
                "Table_Definition": definition,
                "Source_Data_Vault_Table": src_dv_table_list,
                "Source_Logical_Table": src_logical_table_list,
                "Business_Key": business_key,
                "SCD_Type": scd_type,
                "Table_Type": table_type_udp,
                "Loading_Order": loading_order,
                "Dependency": dependency,
                "Retention_Type": retention_type,
                "Retention_Attribute": retention_attribute,
                "Retention_Reference_Table": retention_ref_table,
                "Watermark_Date_Columns": (
                    watermark_date_columns
                    if watermark_date_columns else None
                ),
                "Watermark_Time_Columns": (
                    watermark_time_columns
                    if watermark_time_columns else None
                ),
                "Where_Clause": where_clause,
                "Contains_PII": contains_pii,
                "Database_Name": database_name,
                "Schema_Name": schema_name,
                "Column_Mappings": column_mappings
            }

            data_model_output.append(table_obj)

    # --- OUTPUT ---
    # Ensure the destination directory (e.g. ./output/sttm/) exists.
    os.makedirs(os.path.dirname(output_json_file) or ".", exist_ok=True)
    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(data_model_output, f, indent=4)

    print(f"Success. Processed {len(data_model_output)} tables.")
    print(f"Output saved to: {output_json_file}")

# --- RUN ---
# if __name__ == "__main__":
#     if os.path.exists(INPUT_XML_FILE):
#         parse_erwin_full_mapping(INPUT_XML_FILE)
#     else:
#         print(f"File {INPUT_XML_FILE} not found.")

import json
import re
from typing import (
    Dict,
    Any,
    Optional,
    List,
    Union,
)  # Union can be replaced with | for Python 3.10+


def parse_llm_response_to_json(response: str) -> Dict[str, Any]:
    """
    Robust parser for LLM responses that should contain JSON.
    Handles malformed JSON, missing fields, and various edge cases.

    Args:
        response (str): Raw LLM response text

    Returns:
        Dict[str, Any]: Parsed and validated JSON with default values for missing fields
    """

    def get_default_structure() -> Dict[str, Any]:
        """Return the expected structure with default values"""
        return {
            "internal_chs_analysis": {
                "primaryEmotion": "Unknown",
                "complexEmotion": "Unknown",
                "coordinates": [0.0, 0.0],
                "intensity": 0.0,
                "instability": 0.0,
                "collapseRisk": 0.0,
                "keyIndicators": [],
                "responseStrategy": "General Support",
                "riskFactors": [],
            },
            "user_facing_response": "",
        }

    def extract_json_from_text(text: str) -> Optional[str]:
        """Extract JSON content from text, handling markdown and various formats"""
        if not text or not isinstance(text, str):
            return None

        # Try to extract from markdown code block first
        # Handles ```json ... ``` or ``` ... ```
        md_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE
        )
        if md_match:
            return md_match.group(1).strip()

        # If not in markdown, try to find the largest JSON-like block
        # This looks for content starting with { and ending with }
        brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if brace_match:
            return brace_match.group(1).strip()

        return None

    def fix_common_json_errors(json_str: str) -> str:
        """Fix common JSON formatting issues like unquoted keys/strings and trailing commas."""
        if not json_str or not isinstance(json_str, str):
            return ""

        json_str = json_str.strip()

        # Add quotes around unquoted keys (e.g., { key: value } -> { "key": value })
        # Avoids adding quotes if already quoted or if it's part of a value.
        json_str = re.sub(r'(?<![\'"\w])([a-zA-Z_]\w*)\s*:', r'"\1":', json_str)

        # Replace single quotes with double quotes for keys and string values
        # For keys: 'key': -> "key":
        json_str = re.sub(r"(?<!\\)'([a-zA-Z_]\w*)'(?=\s*:)", r'"\1"', json_str)
        # For values: :'value' -> :"value"
        json_str = re.sub(r":\s*(?<!\\)'([^']*(?:\\.[^']*)*)'", r': "\1"', json_str)

        def fix_array_content(match_obj: re.Match) -> str:
            """Callback to fix elements within a JSON array string."""
            array_content = match_obj.group(1)
            if (
                array_content is None
            ):  # Should not happen with the regex, but good practice
                return match_obj.group(0)

            elements = []
            current_element = ""
            in_quotes = False
            quote_char = ""
            escape = False
            depth = 0  # To handle nested structures like objects or arrays within array elements

            for char in array_content:
                if escape:
                    current_element += char
                    escape = False
                    continue

                if char == "\\":
                    current_element += char
                    escape = True
                    continue

                if in_quotes:
                    current_element += char
                    if char == quote_char:
                        in_quotes = False
                else:
                    if char in ('"', "'"):
                        current_element += char
                        in_quotes = True
                        quote_char = char
                    elif char == "[" or char == "{":
                        depth += 1
                        current_element += char
                    elif char == "]" or char == "}":
                        depth -= 1
                        current_element += char
                    elif char == "," and depth == 0:
                        elements.append(current_element.strip())
                        current_element = ""
                    else:
                        current_element += char

            if current_element.strip():
                elements.append(current_element.strip())

            fixed_elements = []
            for elem in elements:
                elem = elem.strip()
                if not elem:
                    continue

                # Check if it's already a valid JSON string (double-quoted)
                if elem.startswith('"') and elem.endswith('"'):
                    fixed_elements.append(elem)
                # Check if it's single-quoted, convert to double
                elif elem.startswith("'") and elem.endswith("'"):
                    inner_content = elem[1:-1].replace(
                        '"', '\\"'
                    )  # Escape internal double quotes
                    fixed_elements.append(f'"{inner_content}"')
                # Check if it's a number (integer or float)
                elif re.fullmatch(r"-?\d+(\.\d+)?([eE][-+]?\d+)?", elem):
                    fixed_elements.append(elem)
                # Check if it's a boolean or null
                elif elem.lower() in ["true", "false", "null"]:
                    fixed_elements.append(elem.lower())
                # Otherwise, assume it's an unquoted string that needs double quotes
                else:
                    # Escape internal double quotes before wrapping
                    escaped_elem = elem.replace('"', '\\"')
                    fixed_elements.append(f'"{escaped_elem}"')

            return f'[{", ".join(fixed_elements)}]'

        # Apply fix_array_content to array structures.
        # This regex tries to find array contents: [...]
        # It's applied iteratively to handle nested arrays if necessary, though
        # fix_array_content itself is designed for a flat list of items that might be complex.
        try:
            # A robust regex for capturing array content, including nested structures if they are simple.
            # The main goal is to capture the content of an array that might contain unquoted strings.
            json_str = re.sub(
                r"\[\s*(.*?)\s*\]", fix_array_content, json_str, flags=re.DOTALL
            )
        except Exception as regex_err:
            print(f"Warning: Regex substitution for array fixing failed: {regex_err}")

        # Remove trailing commas before closing curly or square brackets
        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

        # Attempt to fix multiple commas
        json_str = re.sub(r"(,\s*,)+", ",", json_str)

        return json_str

    def safe_parse_value(value: Any, expected_type: type, default: Any) -> Any:
        """Safely parse and convert values to expected types with robust error handling."""
        if value is None:
            return default

        try:
            if expected_type == str:
                return str(value)
            elif expected_type == float:
                if isinstance(value, str):
                    value = value.strip()
                    if not value:
                        return default
                return float(value)
            elif expected_type == int:
                if isinstance(value, str):
                    value = value.strip()
                    if not value:
                        return default
                    return int(float(value))  # Convert to float first for "1.0"
                return int(value)
            elif expected_type == list:
                if isinstance(value, list):
                    return value
                if isinstance(value, str):
                    value = value.strip()
                    if value.startswith("[") and value.endswith("]"):
                        try:
                            # Try to parse as a valid JSON array string
                            parsed_list = json.loads(value)
                            if isinstance(parsed_list, list):
                                return parsed_list
                        except json.JSONDecodeError:
                            # If json.loads fails, it might be like "[item1, item2]" (unquoted)
                            # The fix_common_json_errors should ideally handle this,
                            # but as a fallback here:
                            content = value[1:-1].strip()
                            if not content:
                                return []  # Empty list string "[]"
                            # Simple split, assumes fix_common_json_errors did most of the heavy lifting
                            return [
                                item.strip().strip("\"'")
                                for item in content.split(",")
                                if item.strip()
                            ]
                    else:
                        # If it's a comma-separated string not in brackets
                        return [
                            item.strip().strip("\"'")
                            for item in value.split(",")
                            if item.strip()
                        ]
                # If it's a single item not fitting other types, wrap in a list
                return (
                    [str(value)] if value else []
                )  # Ensure empty list for empty non-list value
            return value  # Return as-is if type doesn't match above
        except (ValueError, TypeError, json.JSONDecodeError):
            return default

    def validate_and_fix_structure(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix the parsed data structure, ensuring all fields and types."""
        result = get_default_structure()

        if not isinstance(data, dict):  # Ensure data is a dict
            data = {}

        # Handle internal_chs_analysis
        analysis_data = data.get("internal_chs_analysis")
        if isinstance(analysis_data, dict):
            analysis_defaults = result[
                "internal_chs_analysis"
            ]  # Defaults for this section

            result["internal_chs_analysis"]["primaryEmotion"] = safe_parse_value(
                analysis_data.get("primaryEmotion"),
                str,
                analysis_defaults["primaryEmotion"],
            )
            result["internal_chs_analysis"]["complexEmotion"] = safe_parse_value(
                analysis_data.get("complexEmotion"),
                str,
                analysis_defaults["complexEmotion"],
            )

            coords_val = analysis_data.get(
                "coordinates", analysis_defaults["coordinates"]
            )
            parsed_coords_list = safe_parse_value(
                coords_val, list, analysis_defaults["coordinates"]
            )

            final_coords = [0.0, 0.0]
            if isinstance(parsed_coords_list, list) and len(parsed_coords_list) >= 2:
                try:
                    final_coords = [
                        safe_parse_value(parsed_coords_list[0], float, 0.0),
                        safe_parse_value(parsed_coords_list[1], float, 0.0),
                    ]
                except (IndexError, ValueError, TypeError):
                    pass  # Keep default [0.0, 0.0]
            result["internal_chs_analysis"]["coordinates"] = final_coords

            for field, default_val_type in [
                ("intensity", float),
                ("instability", float),
                ("collapseRisk", float),
            ]:
                default_numeric_val = analysis_defaults[field]
                raw_val = analysis_data.get(field)
                parsed_val = safe_parse_value(
                    raw_val, default_val_type, default_numeric_val
                )
                # Clamp values between 0.0 and 1.0
                result["internal_chs_analysis"][field] = max(0.0, min(1.0, parsed_val))

            for field in ["keyIndicators", "riskFactors"]:
                default_list_val = analysis_defaults[field]
                raw_val = analysis_data.get(field)
                result["internal_chs_analysis"][field] = safe_parse_value(
                    raw_val, list, default_list_val
                )

            result["internal_chs_analysis"]["responseStrategy"] = safe_parse_value(
                analysis_data.get("responseStrategy"),
                str,
                analysis_defaults["responseStrategy"],
            )

        # Handle user_facing_response
        result["user_facing_response"] = safe_parse_value(
            data.get("user_facing_response"),
            str,
            result["user_facing_response"],  # Default from get_default_structure
        )

        return result

    # --- Main parsing process ---
    parsed_data: Dict[str, Any] = {}

    try:
        # Step 1: Extract JSON content from response string
        json_content_str = extract_json_from_text(response)
        if not json_content_str:
            print(
                "Warning: No JSON-like content (e.g., {...}) found in response. Using default structure."
            )
            return get_default_structure()

        # Step 2: Try to parse the extracted string as-is
        try:
            parsed_data = json.loads(json_content_str)
            print("Successfully parsed JSON as-is.")
        except json.JSONDecodeError as e:
            print(f"Initial JSON parse failed: {e}. Attempting fixes.")

            # Step 3: Try to fix common issues and parse again
            fixed_json_content_str = fix_common_json_errors(json_content_str)
            print(
                f"Attempting to parse fixed JSON (first 300 chars): {fixed_json_content_str[:300]}..."
            )
            try:
                parsed_data = json.loads(fixed_json_content_str)
                print("Successfully parsed JSON after fixes!")
            except json.JSONDecodeError as e2:
                print(
                    f"JSON parse failed even after fixes: {e2}. Falling back to partial regex extraction."
                )
                # Step 3.5: Fallback to regex-based partial extraction from the original *full* response
                parsed_data = extract_partial_data(
                    response
                )  # Use original response for regex
                if not parsed_data.get("internal_chs_analysis") and not parsed_data.get(
                    "user_facing_response"
                ):
                    # Check if partial extraction yielded anything meaningful
                    print(
                        "Warning: Partial extraction yielded no significant data. Using default structure."
                    )
                    return get_default_structure()
                print("Partial data extracted using regex.")

        # Step 4: Validate the obtained data and fill in defaults
        return validate_and_fix_structure(parsed_data)

    except Exception as e:  # Catch any other unexpected errors during the process
        print(
            f"Critical error in parse_llm_response_to_json: {e}. Using default structure."
        )
        # Consider logging the 'response' and intermediate content for debugging
        return get_default_structure()


def extract_partial_data(response: str) -> Dict[str, Any]:
    """
    Last resort: extract partial data using regex when JSON parsing completely fails.
    This function attempts to find known fields in the raw response string.
    """
    # Initialize with a structure similar to get_default_structure but empty or with regex-found values
    # This ensures validate_and_fix_structure can work with its output.
    result: Dict[str, Any] = {
        "internal_chs_analysis": {
            "primaryEmotion": "Unknown",
            "complexEmotion": "Unknown",
            "coordinates": [0.0, 0.0],
            "intensity": 0.0,
            "instability": 0.0,
            "collapseRisk": 0.0,
            "keyIndicators": [],
            "responseStrategy": "General Support",
            "riskFactors": [],
        },
        "user_facing_response": "",
    }

    if not response or not isinstance(response, str):
        return result  # Return default-like structure if no response

    # Extract user_facing_response - flexible with quotes and potential truncation
    user_response_patterns = [
        r'"user_facing_response"\s*:\s*"((?:\\"|[^"])*)"',  # Double quotes, handles escaped quotes
        r"'user_facing_response'\s*:\s*'((?:\\'|[^'])*)'",  # Single quotes, handles escaped quotes
        r'"user_facing_response"\s*:\s*“((?:\\"|[^”])*)”',  # Smart double quotes
    ]
    for pattern in user_response_patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            result["user_facing_response"] = match.group(1).strip()
            break

    # Extract fields from internal_chs_analysis
    # Using a helper to avoid repetition
    def regex_extract(field_pattern: str, default_val: Any, val_type: type = str):
        match = re.search(field_pattern, response, re.IGNORECASE)
        if match:
            try:
                val_str = match.group(1).strip()
                if val_type == float:
                    return float(val_str)
                if val_type == int:
                    return int(float(val_str))  # for "1.0"
                return val_str  # default is string
            except (ValueError, TypeError):
                return default_val
        return default_val

    analysis_target = result["internal_chs_analysis"]  # type: ignore

    analysis_target["primaryEmotion"] = regex_extract(
        r'"primaryEmotion"\s*:\s*["“\']([^"”\']*)["”\']',
        analysis_target["primaryEmotion"],
    )
    analysis_target["complexEmotion"] = regex_extract(
        r'"complexEmotion"\s*:\s*["“\']([^"”\']*)["”\']',
        analysis_target["complexEmotion"],
    )
    analysis_target["responseStrategy"] = regex_extract(
        r'"responseStrategy"\s*:\s*["“\']([^"”\']*)["”\']',
        analysis_target["responseStrategy"],
    )

    analysis_target["intensity"] = regex_extract(
        r'"intensity"\s*:\s*([0-9.]+)', analysis_target["intensity"], float
    )
    analysis_target["instability"] = regex_extract(
        r'"instability"\s*:\s*([0-9.]+)', analysis_target["instability"], float
    )
    analysis_target["collapseRisk"] = regex_extract(
        r'"collapseRisk"\s*:\s*([0-9.]+)', analysis_target["collapseRisk"], float
    )

    # Extract coordinates - handle various formats like "[0.1, 0.2]" or "0.1,0.2"
    coord_match = re.search(
        r'"coordinates"\s*:\s*["\']?\[?([^\]"\']+)\]?["\']?', response
    )
    if coord_match:
        coords_str = coord_match.group(1)
        try:
            coords_parts = [
                float(x.strip()) for x in coords_str.split(",") if x.strip()
            ]
            if len(coords_parts) >= 2:
                analysis_target["coordinates"] = coords_parts[:2]
        except ValueError:
            pass  # Keep default if parsing fails

    # Extract list-like fields (keyIndicators, riskFactors)
    def regex_extract_list(field_name: str) -> List[str]:
        list_items = []
        # Pattern to find the array content, e.g., "keyIndicators": ["item1", "item2"] or unquoted
        pattern = rf'"{field_name}"\s*:\s*\[([^\]]*)\]'
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            content_str = match.group(1).strip()
            if content_str:
                # Split by comma, then strip quotes and whitespace from each item
                raw_items = content_str.split(",")
                for item in raw_items:
                    item = item.strip()
                    # Remove potential surrounding quotes (single or double)
                    if (item.startswith('"') and item.endswith('"')) or (
                        item.startswith("'") and item.endswith("'")
                    ):
                        item = item[1:-1]
                    if item:  # Add if not empty after stripping
                        list_items.append(item)
        return list_items

    analysis_target["keyIndicators"] = regex_extract_list("keyIndicators")
    analysis_target["riskFactors"] = regex_extract_list("riskFactors")

    return result

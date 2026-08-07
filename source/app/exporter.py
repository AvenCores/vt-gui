import os
import json

def export_report_to_file(data_dict, file_name, file_format="json"):
    """Export scan report or intelligence report to user Downloads folder."""
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    
    clean_name = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in file_name)
    out_filename = f"vt_report_{clean_name}.{file_format}"
    out_path = os.path.join(downloads_dir, out_filename)
    
    try:
        if file_format == "json":
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=4, ensure_ascii=False)
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"--- VIRUSTOTAL REPORT: {file_name} ---\n\n")
                if isinstance(data_dict, dict):
                    for k, v in data_dict.items():
                        f.write(f"{k}:\n{json.dumps(v, indent=2, ensure_ascii=False)}\n\n")
                else:
                    f.write(json.dumps(data_dict, indent=2, ensure_ascii=False))
        return True, out_path
    except Exception as ex:
        return False, str(ex)

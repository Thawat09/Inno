import csv


# =========================================================
# 7) CSV
# =========================================================
def sanitize_row_for_csv(row, headers):
    result = {}
    for h in headers:
        v = row.get(h)
        if isinstance(v, bool):
            result[h] = "true" if v else "false"
        elif v is None:
            result[h] = ""
        else:
            result[h] = v
    return result


def write_csv(filename, headers, rows):
    if not rows:
        print(f"ℹ️ No rows to write for {filename}")
        return

    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(sanitize_row_for_csv(row, headers))

    print(f"✅ Exported {len(rows)} rows to {filename}")

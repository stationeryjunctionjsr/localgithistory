from sqlalchemy import create_engine, inspect

urls = {
    "sjqadb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjqadb",
    "sjuatdb": "mysql+pymysql://stationeryjunction.jsr%40gmail.com:Jaimatadi$1607@127.0.0.1:13306/sjuatdb",
}


def compare_dbs():
    engine_qa = create_engine(urls["sjqadb"])
    engine_uat = create_engine(urls["sjuatdb"])

    insp_qa = inspect(engine_qa)
    insp_uat = inspect(engine_uat)

    tables_qa = set(insp_qa.get_table_names())
    tables_uat = set(insp_uat.get_table_names())

    if tables_qa != tables_uat:
        print("Table lists differ!")
        print(f"Only in QA: {tables_qa - tables_uat}")
        print(f"Only in UAT: {tables_uat - tables_qa}")
    else:
        print("Table lists are identical. Comparing schemas...")

    diffs_found = False
    for t in sorted(tables_qa.intersection(tables_uat)):
        cols_qa = {c["name"]: c["type"] for c in insp_qa.get_columns(t)}
        cols_uat = {c["name"]: c["type"] for c in insp_uat.get_columns(t)}

        if cols_qa != cols_uat:
            diffs_found = True
            print(f"\nDifferences in table {t}:")
            qa_only = set(cols_qa.keys()) - set(cols_uat.keys())
            uat_only = set(cols_uat.keys()) - set(cols_qa.keys())
            if qa_only:
                print(f"  Columns only in QA: {qa_only}")
            if uat_only:
                print(f"  Columns only in UAT: {uat_only}")

            common_cols = set(cols_qa.keys()).intersection(set(cols_uat.keys()))
            for c in common_cols:
                if str(cols_qa[c]) != str(cols_uat[c]):
                    print(f"  Column {c} type mismatch: QA={cols_qa[c]}, UAT={cols_uat[c]}")

    if not diffs_found:
        print("\nAll tables and columns (with types) match perfectly between sjqadb and sjuatdb!")


if __name__ == "__main__":
    compare_dbs()

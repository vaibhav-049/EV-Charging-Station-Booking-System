from pathlib import Path
from app_db import init_db, get_conn


def main():
    init_db()
    sql_path = Path("ev_charging_station.sql")
    if not sql_path.exists():
        print("SQL file not found:", sql_path)
        return
    sql = sql_path.read_text(encoding="utf-8")
    with get_conn() as conn:
        conn.executescript(
            "DROP TABLE IF EXISTS ev_charging_stations_reduced;"
        )
        conn.executescript(sql)
        conn.commit()
    print("Imported SQL into database/ev_stations.db with",
          "fresh schema and data")


if __name__ == "__main__":
    main()

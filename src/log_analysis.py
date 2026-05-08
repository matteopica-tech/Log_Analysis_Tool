from pathlib import Path
from collections import Counter, defaultdict
import re
import csv
import logging
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "input" / "application.log"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"(?P<level>INFO|WARN|ERROR)\s+"
    r"\[(?P<component>[^\]]+)\] "
    r"(?P<message>.*)$"
)


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=LOG_DIR / "app.log",
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        encoding="utf-8"
    )


def parse_log_file(file_path):
    if not file_path.exists():
        raise FileNotFoundError(f"File log non trovato: {file_path}")

    records = []

    with open(file_path, mode="r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            match = LOG_PATTERN.match(line)

            if not match:
                logging.warning(f"Riga non parsabile ignorata: {line_number}")
                continue

            records.append(match.groupdict())

    if not records:
        raise ValueError("Nessun record valido trovato nel file log.")

    return records


def analyze_logs(records):
    level_counter = Counter(record["level"] for record in records)
    component_counter = Counter(record["component"] for record in records)
    error_by_component = Counter(
        record["component"] for record in records if record["level"] == "ERROR"
    )

    errors = [record for record in records if record["level"] == "ERROR"]
    warnings = [record for record in records if record["level"] == "WARN"]

    keywords = defaultdict(int)
    for record in records:
        message = record["message"].lower()

        for keyword in ["timeout", "sql error", "connection refused", "http 500", "nullpointerexception"]:
            if keyword in message:
                keywords[keyword] += 1

    return {
        "total_records": len(records),
        "level_counter": level_counter,
        "component_counter": component_counter,
        "error_by_component": error_by_component,
        "errors": errors,
        "warnings": warnings,
        "keywords": dict(keywords),
    }


def export_report(analysis):
    OUTPUT_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"log_analysis_report_{timestamp}.csv"

    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["SEZIONE", "CHIAVE", "VALORE"])

        writer.writerow(["SUMMARY", "Total records", analysis["total_records"]])

        for level, count in analysis["level_counter"].items():
            writer.writerow(["LOG_LEVEL", level, count])

        for component, count in analysis["component_counter"].items():
            writer.writerow(["COMPONENT", component, count])

        for component, count in analysis["error_by_component"].items():
            writer.writerow(["ERROR_BY_COMPONENT", component, count])

        for keyword, count in analysis["keywords"].items():
            writer.writerow(["KEYWORD", keyword, count])

        for error in analysis["errors"]:
            writer.writerow([
                "ERROR_DETAIL",
                error["component"],
                f'{error["timestamp"]} | {error["message"]}'
            ])

    return output_file


def main():
    setup_logging()

    try:
        print("Avvio analisi log...")
        logging.info("Avvio analisi log")

        records = parse_log_file(INPUT_FILE)
        analysis = analyze_logs(records)
        output_file = export_report(analysis)

        print(f"Record analizzati: {analysis['total_records']}")
        print(f"ERROR trovati: {analysis['level_counter'].get('ERROR', 0)}")
        print(f"WARN trovati: {analysis['level_counter'].get('WARN', 0)}")
        print(f"Report generato: {output_file}")

        logging.info(f"Report generato correttamente: {output_file}")

    except Exception as error:
        print(f"Errore: {error}")
        logging.error(f"Errore durante analisi log: {error}")


if __name__ == "__main__":
    main()
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List

from app.config.table_schema import TABLES


class TableMapper:
    """
    Splits one incoming payload into table-wise records and
    performs lightweight normalization.
    """

    TRUE_VALUES = {"yes", "y", "true", "1", "t"}
    FALSE_VALUES = {"no", "n", "false", "0", "f"}

    def __init__(self):
        self.tables = TABLES

    def _normalize(self, value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if value == "":
                return None

            lower = value.lower()

            if lower in self.TRUE_VALUES:
                return True

            if lower in self.FALSE_VALUES:
                return False

            try:
                if "T" in value:
                    return datetime.fromisoformat(value).date()
                if len(value) == 10 and value.count("-") == 2:
                    return datetime.strptime(value, "%Y-%m-%d").date()
            except Exception:
                pass

            return value

        return value

    def split_record(self, record: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        result = {}

        for table_name, meta in self.tables.items():
            row = {}

            for column in meta["columns"]:
                row[column] = deepcopy(
                    self._normalize(record.get(column))
                )

            result[table_name] = row

        return result

    def split_records(
        self,
        records: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:

        output = {
            table_name: []
            for table_name in self.tables.keys()
        }

        for record in records:
            split = self.split_record(record)

            for table_name, row in split.items():
                output[table_name].append(row)

        return output


if __name__ == "__main__":

    sample = [{
        "udise_code": 123,
        "state_name": "Delhi",
        "academic_year": "2024-25",
        "school_name": "ABC School",
        "total_students": 100,
        "total_teachers": 5,
        "internet_availability": "Yes"
    }]

    mapper = TableMapper()

    result = mapper.split_records(sample)

    from pprint import pprint
    pprint(result)

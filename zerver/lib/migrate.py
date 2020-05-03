from psycopg2.extensions import cursor
from psycopg2.sql import Composable, Identifier, SQL
from typing import List, TypeVar

import time

CursorObj = TypeVar('CursorObj', bound=cursor)


def do_batch_update(cursor: CursorObj,
                    table: str,
                    assignments: List[Composable],
                    batch_size: int=10000,
                    sleep: float=0.1) -> None:  # nocoverage
    # The string substitution below is complicated by our need to
    # support multiple postgres versions.
    stmt = SQL('''
        UPDATE {}
        SET {}
        WHERE id >= %s AND id < %s
    ''').format(
        Identifier(table),
        SQL(', ').join(assignments),
    )

    cursor.execute(SQL("SELECT MIN(id), MAX(id) FROM {}").format(Identifier(table)))
    (min_id, max_id) = cursor.fetchone()
    if min_id is None:
        return

    print("\n    Range of rows to update: [%s, %s]" % (min_id, max_id))
    while min_id <= max_id:
        lower = min_id
        upper = min_id + batch_size
        print('    Updating range [%s,%s)' % (lower, upper))
        cursor.execute(stmt, [lower, upper])

        min_id = upper
        time.sleep(sleep)

        # Once we've finished, check if any new rows were inserted to the table
        if min_id > max_id:
            cursor.execute(SQL("SELECT MAX(id) FROM {}").format(Identifier(table)))
            (max_id,) = cursor.fetchone()

    print("    Finishing...", end='')

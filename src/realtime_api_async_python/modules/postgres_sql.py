import psycopg2
import pandas as pd

class Postgres:
    def __init__(self):
        self.connection = None

    def connect(self, url: str):
        self.connection = psycopg2.connect(url)

    def read_tables(self, schema: str = None) -> str:
        cursor = self.connection.cursor()
        if schema:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                """,
                (schema,)
            )
        else:
            cursor.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                """
            )
        tables = cursor.fetchall()

        table_defs = ""
        for table in tables:
            if schema:
                table_schema = schema
                table_name = table[0]
            else:
                table_schema, table_name = table
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                """,
                (table_schema, table_name)
            )
            columns = cursor.fetchall()
            table_defs += f"CREATE TABLE {table_schema}.{table_name} (\n"
            col_defs = []
            for col in columns:
                col_def = f"    {col[0]} {col[1]}"
                if col[3]:
                    col_def += f" DEFAULT {col[3]}"
                if col[2] == 'NO':
                    col_def += " NOT NULL"
                col_defs.append(col_def)
            table_defs += ",\n".join(col_defs)
            table_defs += "\n);\n\n"
        cursor.close()
        return table_defs

    def execute_sql(self, sql: str) -> pd.DataFrame:
        df = pd.read_sql_query(sql, self.connection)
        return df

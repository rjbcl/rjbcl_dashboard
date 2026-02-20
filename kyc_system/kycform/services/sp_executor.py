from django.db import connections

class StoredProcedureExecutor:

    @staticmethod
    def execute(proc_name: str, params: dict):
        with connections['sqlserver'].cursor() as cursor:
            placeholders = ', '.join([f'@{k}=%s' for k in params])
            sql = f'EXEC {proc_name} {placeholders}'

            cursor.execute(sql, list(params.values()))

            # 🔴 Skip non-result sets (rowcount, PRINT, etc.)
            while cursor.description is None:
                if not cursor.nextset():
                    return [], []

            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return columns, rows

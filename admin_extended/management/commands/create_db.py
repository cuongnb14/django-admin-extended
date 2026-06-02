"""Create the database for a configured connection if it does not exist."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser


class Command(BaseCommand):
    help = "Create the database for a configured connection if it does not exist (PostgreSQL or MySQL)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--database",
            default="default",
            help="Alias in settings.DATABASES to create (default: 'default').",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        alias = options["database"]
        try:
            db = settings.DATABASES[alias]
        except KeyError:
            raise CommandError(f"Database alias '{alias}' not found in settings.DATABASES.") from None

        engine = db.get("ENGINE", "")
        dbname = db["NAME"]

        if "postgresql" in engine:
            created = self._create_postgresql(db, dbname)
        elif "mysql" in engine:
            created = self._create_mysql(db, dbname)
        else:
            raise CommandError(f"Unsupported ENGINE '{engine}'. Only PostgreSQL and MySQL are supported.")

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created database '{dbname}'."))
        else:
            self.stdout.write(f"Database '{dbname}' already exists, skipping.")

    def _create_postgresql(self, db: dict[str, Any], dbname: str) -> bool:
        """Create a PostgreSQL database. Returns True if created, False if it already existed."""
        import psycopg  # type: ignore[import-not-found]
        from psycopg import sql

        # Connect to the system 'postgres' database (always present) to gain CREATE DATABASE rights.
        # autocommit=True is required: CREATE DATABASE cannot run inside a transaction block.
        try:
            conn = psycopg.connect(
                host=db["HOST"],
                port=db["PORT"],
                user=db["USER"],
                password=db["PASSWORD"],
                dbname="postgres",
                autocommit=True,
            )
        except psycopg.OperationalError as exc:
            raise CommandError(f"Could not connect to PostgreSQL: {exc}") from exc

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [dbname])
                if cur.fetchone():
                    return False
                # Database names cannot be parameterized; use Identifier for safe quoting.
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
                return True
        finally:
            conn.close()

    def _create_mysql(self, db: dict[str, Any], dbname: str) -> bool:
        """Create a MySQL database. Returns True if created, False if it already existed."""
        try:
            import MySQLdb as driver  # type: ignore[import-untyped]  # mysqlclient
        except ImportError:
            try:
                import pymysql as driver  # type: ignore[import-untyped]
            except ImportError:
                raise CommandError(
                    "No MySQL driver found. Install 'mysqlclient' or 'pymysql' to use this command with MySQL."
                ) from None

        # Connect to the server without selecting a schema, then create it if missing.
        try:
            conn = driver.connect(
                host=db["HOST"],
                # PORT is often left blank to use the default; int("") would raise ValueError.
                port=int(db["PORT"]) if db.get("PORT") else 3306,
                user=db["USER"],
                passwd=db["PASSWORD"],
            )
        except driver.Error as exc:
            raise CommandError(f"Could not connect to MySQL: {exc}") from exc

        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = %s", [dbname])
            if cur.fetchone():
                return False
            # Identifiers cannot be parameterized; escape backticks and quote the name.
            safe_name = dbname.replace("`", "``")
            cur.execute(f"CREATE DATABASE `{safe_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.commit()
            return True
        finally:
            conn.close()

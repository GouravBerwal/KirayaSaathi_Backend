try:
    import pymysql

    pymysql.version_info = (2, 2, 1, "final", 0)
    pymysql.install_as_MySQLdb()

    import MySQLdb

    MySQLdb.version_info = (2, 2, 1, "final", 0)
    MySQLdb.__version__ = "2.2.1"

    # Bypass Django's strict MySQL >= 8.4 check for TiDB Cloud (which reports 8.0.11)
    from django.db.backends.mysql.base import DatabaseWrapper

    DatabaseWrapper.check_database_version_supported = lambda self: None
except ImportError:
    pass
except Exception:
    pass

Helka Voy2py Setup and Usage (on linnea1)
=========================================

::

    $ cd ~/helka/odbc/  # Or another suitable place
    $ gtar -xzf voy2py.tar.gz  # Or whatever the tarball's path is
    $ echo "
    DB_INSTANCE = 'VGER'
    DB_RO_USER = 'readonly_db_instance_username_for_library'
    DB_RO_PW = 'SecretPassword4ThatUsername'" > db_login.py
    $ env LC_CTYPE=fi_FI.UTF-8 \
          NLS_LANG=.UTF8 \
          ORACLE_HOME=/oracle/app/oracle/product/12.1.0.2/db_1 \
          /opt/csw/bin/python3
    >>> from voy2py import *  # Depends on cx_Oracle, and maybe pymarc
    >>> Patron('2100120000').last_name  # Or give patron_id as int
    'Helkalanen'
    >>> query("select utl_raw.cast_to_raw(first_name) "
    ...    ## " as U_coltitle " # Would decode bytes as UTF-8, not Latin
    ...       "from patron "
    ...       "where patron_id = :pid ", Patron('2100120000'))
    ['UTL_RAW.CAST_TO_RAW(FIRST_NAME)']
    ['Testaaja']

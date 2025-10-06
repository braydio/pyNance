# SQLite vs PostgreSQL CLI Cheatsheet

| **Action**             | **SQLite (`sqlite3`)**  | **PostgreSQL (`psql`)**                      |
| ---------------------- | ----------------------- | -------------------------------------------- |
| Connect to database    | `sqlite3 my.db`         | `psql -h localhost -U user -d dbname`        |
| List all tables        | `.tables`               | `\dt`                                        |
| Show table schema      | `.schema tablename`     | `\d tablename`                               |
| List all databases     | n/a (one file = one DB) | `\l`                                         |
| Switch database        | open another file       | `\c dbname`                                  |
| Show indexes           | `.indexes tablename`    | `\di tablename*`                             |
| Run a query            | `SELECT * FROM table;`  | `SELECT * FROM table;`                       |
| Show current user/info | n/a                     | `\conninfo`                                  |
| Quit                   | `.quit`                 | `\q`                                         |
| Output to file         | `.output file.txt`      | `\o file.txt` … then `\o` to reset           |
| Expanded view          | n/a                     | `\x`                                         |
| Help                   | `.help`                 | `\?` (psql commands), `\h` (SQL syntax help) |

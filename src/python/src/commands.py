# Language differences between sqlite and mysql

def get_autoincrement(sqlite):
    if (sqlite):
        return "AUTOINCREMENT"
    else:
        return "AUTO_INCREMENT"

def get_string_type(sqlite):
    if (sqlite):
        return "TEXT"
    else:
        return "VARCHAR(255)"

# Sql Commands

def create_table_categories(sqlite):
    query = "CREATE TABLE IF NOT EXISTS categories ("
    query += "id INTEGER PRIMARY KEY " + get_autoincrement(sqlite) + ","
    query += "name " + get_string_type(sqlite) + " NOT NULL UNIQUE)"            
    
    return query
    
def create_table_facts(sqlite):
    query = "CREATE TABLE IF NOT EXISTS facts ("
    query += "id INTEGER PRIMARY KEY " + get_autoincrement(sqlite) + ","
    query += "name " + get_string_type(sqlite) + " NOT NULL UNIQUE)"

    return query

def create_table_entries(sqlite):
    query = "CREATE TABLE IF NOT EXISTS entries ("
    query += "id INTEGER PRIMARY KEY " + get_autoincrement(sqlite) + ","
    query += "category_id INTEGER, fact_id INTEGER,"
    query += "CONSTRAINT FK_ENTRY_CATEGORY FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE,"
    query += "CONSTRAINT FK_ENTRY_FACT FOREIGN KEY(fact_id) REFERENCES facts(id) ON DELETE CASCADE,"
    query += "CONSTRAINT UN_CATEGORY_FACT UNIQUE (category_id, fact_id))"
    
    return query

def create_table_urls(sqlite):
    query = "CREATE TABLE IF NOT EXISTS urls ("
    query += "id INTEGER PRIMARY KEY " + get_autoincrement(sqlite) + ","
    query += "name " + get_string_type(sqlite) + " NOT NULL UNIQUE)"

    return query

def create_table_fact_references(sqlite):
    query = "CREATE TABLE IF NOT EXISTS fact_references ("
    query += "id INTEGER PRIMARY KEY " + get_autoincrement(sqlite) + ","
    query += "fact_id INTEGER, url_id INTEGER,"
    query += "CONSTRAINT FK_REFERENCE_FACT FOREIGN KEY(fact_id) REFERENCES facts(id),"
    query += "CONSTRAINT FK_REFERENCE_URL FOREIGN KEY(url_id) REFERENCES urls(id))"
    return query

def create_trigger(sqlite):
    if (sqlite):
        return """CREATE TRIGGER IF NOT EXISTS TG_DELETE_FACTS
                  AFTER DELETE ON entries
                  WHEN (SELECT count() FROM entries WHERE fact_id == old.fact_id) == 0
                  BEGIN DELETE FROM facts WHERE facts.id == old.fact_id; END"""
    else: 
        return """CREATE TRIGGER TG_DELETE_FACTS
              AFTER DELETE ON entries
              FOR EACH ROW 
              BEGIN
                IF (SELECT count(*) FROM entries WHERE fact_id = OLD.fact_id) = 0 THEN
                    DELETE FROM facts WHERE facts.id = OLD.fact_id;
                END IF;
              END;"""

def mysql_insert_entries():
    return """INSERT INTO entries(fact_id, category_id)
              SELECT facts.id, categories.id
              FROM facts, categories
              WHERE facts.name = %s AND categories.name = %s"""

def mysql_delete_entries():
    return """DELETE FROM entries
              WHERE fact_id = (SELECT id FROM facts WHERE name = %s)
              AND category_id = (SELECT id FROM categories WHERE name = %s)"""
              
def mysql_insert_category():
    return """INSERT INTO categories(name) VALUES (%s)"""

def mysql_select_fact_names():
    return """SELECT name FROM facts WHERE name LIKE %s"""

def mysql_select_category_names():
    return """SELECT name FROM categories"""

def mysql_select_facts_by_category():
    return """SELECT facts.name
              FROM facts, entries, categories
              WHERE categories.name = %s AND categories.id = entries.category_id
              AND facts.id = entries.fact_id
              """
def mysql_select_unique_fact():
    return """ORDER BY facts.id ASC
              LIMIT 1
              OFFSET ?"""
def mysql_delete_category():
    return """DELETE FROM categories WHERE name = %s"""

def mysql_insert_fact():
    return """INSERT INTO facts(name) VALUES (%s)"""

# Mysql Commands

def create_table_categories(sqlite):
    autoincrement, string_type = "AUTO_INCREMENT", "VARCHAR(255)"
    if (sqlite):
        autoincrement = "AUTOINCREMENT"
        string_type = "TEXT"
    query = "CREATE TABLE IF NOT EXISTS categories ("
    query += "id INTEGER PRIMARY KEY " + autoincrement + ","
    query += "name " + string_type + " NOT NULL UNIQUE)"            
    
    return query
    
def mysql_create_table_facts():
    return """CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL UNIQUE
              )"""

def mysql_create_table_entries():
    return """CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                category_id INTEGER,
                fact_id INTEGER,
                CONSTRAINT FK_ENTRY_CATEGORY FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE,
                CONSTRAINT FK_ENTRY_FACT FOREIGN KEY(fact_id) REFERENCES facts(id) ON DELETE CASCADE,
                CONSTRAINT UN_CATEGORY_FACT UNIQUE (category_id, fact_id)
              )"""
def mysql_create_table_urls():
    return """CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                url VARCHAR(255) NOT NULL)"""

def mysql_create_table_fact_references():
    return """CREATE TABLE IF NOT EXISTS fact_references (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                fact_id INTEGER,
                url_id INTEGER,
                CONSTRAINT FK_REFERENCE_FACT FOREIGN KEY(fact_id) REFERENCES facts(id),
                CONSTRAINT FK_REFERENCE_URL FOREIGN KEY(url_id) REFERENCES urls(id)
              )"""

def mysql_create_trigger():
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
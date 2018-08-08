# -*- coding: utf-8 -*-
import sqlite3
import os


class _Fact(object):

    def __init__(self, _id, name):
        self.name = name
        self.id = _id


class _Category(object):

    def __init__(self, _id, name):
        self.name = name
        self.id = _id


class Adapter(object):

    def add_fact(self, fact, categories):
        raise NotImplementedError()

    def remove_fact(self, category, fact_id):
        raise NotImplementedError()

    def add_category(self, category):
        raise NotImplementedError()

    def search(self, pattern):
        raise NotImplementedError()

    def list_categories(self):
        raise NotImplementedError()

    def consult(self, category, fact_id=None):
        raise NotImplementedError()

    def remove_category(self, category):
        raise NotImplementedError()


class SQLite3Adapter(Adapter):

    def __init__(self, db_location):
        exists = os.path.isfile(db_location)
        self._connection = sqlite3.connect(db_location)
        if not exists:
            self._create_database()

    def _create_database(self):
        with self._connection as cursor:
            cursor.execute("""CREATE TABLE categories (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           name TEXT NOT NULL UNIQUE)""")
            cursor.execute("""CREATE TABLE facts (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           name TEXT NOT NULL UNIQUE)""")
            cursor.execute("""CREATE TABLE entries (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           category_id INTEGER,
                           fact_id INTEGER,
                           CONSTRAINT FK_ENTRY_CATEGORY FOREIGN KEY(category_id) REFERENCES 
                           categories(id) ON DELETE CASCADE,
                           CONSTRAINT FK_ENTRY_FACT FOREIGN KEY(fact_id) REFERENCES facts(id)
                           ON DELETE CASCADE,
                           CONSTRAINT UN_CATEGORY_FACT UNIQUE (category_id, fact_id))""")
            cursor.execute("""CREATE TABLE urls (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           url TEXT NOT NULL)""")
            cursor.execute("""CREATE TABLE fact_references (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           fact_id INTEGER,
                           url_id INTEGER,
                           CONSTRAINT FK_REFERENCE_FACT FOREIGN KEY(fact_id) REFERENCES facts(
                           id),
                           CONSTRAINT FK_REFERENCE_URL FOREIGN KEY(url_id) REFERENCES urls(id))""")

    def add_fact(self, fact, categories):
        try:
            self._add_fact(fact)
        except sqlite3.IntegrityError:
            pass

        for category in categories:
            try:
                self.add_category(category)
            except sqlite3.IntegrityError:
                pass

        with self._connection as cursor:
            for category in categories:
                cursor.execute("""INSERT INTO entries(fact_id, category_id)
                               SELECT facts.id, categories.id
                               FROM facts, categories
                               WHERE facts.name == ? AND categories.name == ?""",
                               (fact, category))

    def remove_fact(self, category, line_number):
        fact_name = self.consult(category, line_number)[0]
        with self._connection as cursor:
            cursor.execute("""DELETE FROM entries
                              WHERE fact_id == (SELECT id FROM facts WHERE name == ?)
                              AND category_id == (SELECT id FROM categories WHERE name == ?)""",
                           (fact_name, category))

    def add_category(self, category):
        with self._connection as cursor:
            cursor.execute("""INSERT INTO categories(name) VALUES (?)""", (category,))

    def search(self, pattern):
        pattern = "%{}%".format(pattern)
        with self._connection as cursor:
            result = list(cursor.execute("""SELECT name FROM facts WHERE name LIKE ?""",
                          (pattern,)))
        return [r[0] for r in result]

    def list_categories(self):
        with self._connection as cursor:
            result = list(cursor.execute("""SELECT name FROM categories"""))
        return [r[0] for r in result]

    def consult(self, category, fact_position=None):
        query = """SELECT facts.name
                   FROM facts, entries, categories
                   WHERE categories.name == ? AND categories.id == entries.category_id
                   AND facts.id == entries.fact_id
                   """
        if fact_position is not None:
            query += """ORDER BY facts.id ASC
                     LIMIT 1
                     OFFSET ?"""
        with self._connection as cursor:
            if fact_position is not None:
                result = list(cursor.execute(query, (category, fact_position - 1)))
            else:
                result = list(cursor.execute(query, (category,)))
        return [r[0] for r in result]

    def remove_category(self, category):
        with self._connection as cursor:
            cursor.execute("""DELETE FROM categories WHERE name == ?""", (category,))

    def _add_fact(self, fact):
        with self._connection as cursor:
            cursor.execute("""INSERT INTO facts(name) VALUES (?)""", (fact,))

    def __enter__(self):
        return self

    def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._connection is not None:
            self._connection.close()
        raise exc_type(exc_val, exc_tb)

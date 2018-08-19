# -*- coding: utf-8 -*-
import sqlite3
import mysql.connector as mysql


class Adapter(object):
    """
    Abstract adapter that defines all required methods. Subclasses should implements all of them.
    """

    def add_fact(self, fact, categories):
        """
        Add a new fact into the backend storage. The backend should not allow duplicates and
        raise a DuplicateException.

        :param fact: the fact the user wants to store
        :type fact: str
        :param categories: a list of categories with which the fact is related to.
        :type categories: list
        :raise DuplicateException if a
        """
        raise NotImplementedError()

    def remove_fact(self, category, line_number):
        """
        Remove a fact from a category.

        :param category: the category's name
        :type category: str
        :param line_number: the line where the fact is stored
        :type line_number: int
        """
        raise NotImplementedError()

    def add_category(self, category):
        """
        Add a category in the backend storage. Duplicates shouldn't be allowed and trying to make
        one must raise a DuplicateException

        :param category: the category's name
        :type category: str
        :raise DuplicateException
        """
        raise NotImplementedError()

    def search(self, pattern):
        """
        Search a fact matching the given pattern. No assumption is made on the pattern format,
        and so its interpretation is left to the subclass.

        :param pattern: the searched pattern
        :type pattern: str
        :return: a list of facts (str) matching the pattern
        """
        raise NotImplementedError()

    def list_categories(self):
        """
        List all registered categories in the backend database.

        :return: a list of categories (their name)
        """
        raise NotImplementedError()

    def consult(self, category, line_number=None):
        """
        Consult an entry in the database. If no line number is provided, should display the
        entire category.

        :param category: category's name
        :type category: str
        :param line_number: the line the user wants to consult
        :type line_number: int
        :return: a list of strings
        """
        raise NotImplementedError()

    def remove_category(self, category):
        """
        Remove a category according to its name.

        :param category: the category's name
        :type category: str
        """
        raise NotImplementedError()


class DuplicateException(Exception):
    """
    A simple exception indicating that the user tried to add a duplicate in the backend database.
    """
    pass


class SQLite3Adapter(Adapter):
    """
    This adapter backs data with an SQLite3 database. SQLite3Adapter use the DB configuration
    entry as the place to find the database file.
    """

    def __init__(self, conf):
        self._connection = sqlite3.connect(conf["DB"])
        self._create_database()

    def _create_database(self):
        with self._connection as cursor:
            cursor.execute("""CREATE TABLE IF NOT EXISTS categories (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           name TEXT NOT NULL UNIQUE)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS facts (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           name TEXT NOT NULL UNIQUE)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS entries (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           category_id INTEGER,
                           fact_id INTEGER,
                           CONSTRAINT FK_ENTRY_CATEGORY FOREIGN KEY(category_id) REFERENCES 
                           categories(id) ON DELETE CASCADE,
                           CONSTRAINT FK_ENTRY_FACT FOREIGN KEY(fact_id) REFERENCES facts(id)
                           ON DELETE CASCADE,
                           CONSTRAINT UN_CATEGORY_FACT UNIQUE (category_id, fact_id))""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS urls (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           url TEXT NOT NULL)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS fact_references (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           fact_id INTEGER,
                           url_id INTEGER,
                           CONSTRAINT FK_REFERENCE_FACT FOREIGN KEY(fact_id) REFERENCES facts(
                           id),
                           CONSTRAINT FK_REFERENCE_URL FOREIGN KEY(url_id) REFERENCES urls(id))""")
            cursor.execute("""CREATE TRIGGER IF NOT EXISTS TG_DELETE_FACTS
                           AFTER DELETE ON entries
                           WHEN (SELECT count() FROM entries WHERE fact_id == old.fact_id) == 0
                           BEGIN DELETE FROM facts WHERE facts.id == old.fact_id; END""")

    def add_fact(self, fact, categories):
        try:
            self._add_fact(fact)
        except sqlite3.IntegrityError:
            pass

        for category in categories:
            try:
                self.add_category(category)
            except DuplicateException:
                pass

        try:
            with self._connection as cursor:
                for category in categories:
                    cursor.execute("""INSERT INTO entries(fact_id, category_id)
                                   SELECT facts.id, categories.id
                                   FROM facts, categories
                                   WHERE facts.name == ? AND categories.name == ?""",
                                   (fact, category))
        except sqlite3.IntegrityError:
            raise DuplicateException()

    def remove_fact(self, category, line_number):
        fact_name = self.consult(category, line_number)[0]
        with self._connection as cursor:
            cursor.execute("""DELETE FROM entries
                              WHERE fact_id == (SELECT id FROM facts WHERE name == ?)
                              AND category_id == (SELECT id FROM categories WHERE name == ?)""",
                           (fact_name, category))

    def add_category(self, category):
        try:
            with self._connection as cursor:
                cursor.execute("""INSERT INTO categories(name) VALUES (?)""", (category,))
        except sqlite3.IntegrityError:
            raise DuplicateException()

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


class MySQLAdapter(Adapter):
    """
    An adapter for a MySQL / MariaDB backend.
    """

    def __init__(self, **kwargs):
        self._connection = mysql.connect(**kwargs)
        self._create_database()

    def _create_database(self):
        cursor = self._connection.cursor(buffered=True)
        cursor.execute("""CREATE TABLE IF NOT EXISTS categories (
                       id INTEGER PRIMARY KEY AUTO_INCREMENT,
                       name VARCHAR(255) NOT NULL UNIQUE)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS facts (
                       id INTEGER PRIMARY KEY AUTO_INCREMENT,
                       name VARCHAR(255) NOT NULL UNIQUE)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS entries (
                       id INTEGER PRIMARY KEY AUTO_INCREMENT,
                       category_id INTEGER,
                       fact_id INTEGER,
                       CONSTRAINT FK_ENTRY_CATEGORY FOREIGN KEY(category_id) REFERENCES 
                       categories(id) ON DELETE CASCADE,
                       CONSTRAINT FK_ENTRY_FACT FOREIGN KEY(fact_id) REFERENCES facts(id)
                       ON DELETE CASCADE,
                       CONSTRAINT UN_CATEGORY_FACT UNIQUE (category_id, fact_id))""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS urls (
                       id INTEGER PRIMARY KEY AUTO_INCREMENT,
                       url VARCHAR(255) NOT NULL)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS fact_references (
                       id INTEGER PRIMARY KEY AUTO_INCREMENT,
                       fact_id INTEGER,
                       url_id INTEGER,
                       CONSTRAINT FK_REFERENCE_FACT FOREIGN KEY(fact_id) REFERENCES facts(
                       id),
                       CONSTRAINT FK_REFERENCE_URL FOREIGN KEY(url_id) REFERENCES urls(id))""")
        try:
            cursor.execute("""CREATE TRIGGER TG_DELETE_FACTS
                       AFTER DELETE ON entries
                       FOR EACH ROW 
                       BEGIN
                          IF (SELECT count(*) FROM entries WHERE fact_id = OLD.fact_id) = 0 THEN
                              DELETE FROM facts WHERE facts.id = OLD.fact_id;
                          END IF;
                       END;""")
        except mysql.ProgrammingError:
            pass
        finally:
            self._connection.commit()
            cursor.close()

    def add_fact(self, fact, categories):
        try:
            self._add_fact(fact)
        except mysql.IntegrityError:
            pass

        for category in categories:
            try:
                self.add_category(category)
            except DuplicateException:
                pass

        cursor = self._connection.cursor(buffered=True)
        try:
            for category in categories:
                cursor.execute("""INSERT INTO entries(fact_id, category_id)
                               SELECT facts.id, categories.id
                               FROM facts, categories
                               WHERE facts.name = %s AND categories.name = %s""",
                               (fact, category))
            self._connection.commit()
        except mysql.IntegrityError:
            raise DuplicateException()
        finally:
            cursor.close()

    def remove_fact(self, category, line_number):
        fact_name = self.consult(category, line_number)[0]
        cursor = self._connection.cursor(buffered=True)
        cursor.execute("""DELETE FROM entries
                          WHERE fact_id = (SELECT id FROM facts WHERE name = %s)
                          AND category_id = (SELECT id FROM categories WHERE name = %s)""",
                       (fact_name, category))
        self._connection.commit()
        cursor.close()

    def add_category(self, category):
        cursor = self._connection.cursor(buffered=True)
        try:
            cursor.execute("""INSERT INTO categories(name) VALUES (%s)""", (category,))
            self._connection.commit()
        except mysql.IntegrityError:
            raise DuplicateException()
        finally:
            cursor.close()

    def search(self, pattern):
        pattern = "%{}%".format(pattern)

        cursor = self._connection.cursor(buffered=True)
        cursor.execute("""SELECT name FROM facts WHERE name LIKE %s""", (pattern,))
        result = cursor.fetchall()

        cursor.close()
        return [r[0] for r in result]

    def list_categories(self):
        cursor = self._connection.cursor(buffered=True)
        cursor.execute("""SELECT name FROM categories""")
        result = cursor.fetchall()

        cursor.close()
        return [r[0] for r in result]

    def consult(self, category, fact_position=None):
        query = """SELECT facts.name
                   FROM facts, entries, categories
                   WHERE categories.name = %s AND categories.id = entries.category_id
                   AND facts.id = entries.fact_id
                   """
        if fact_position is not None:
            query += """ORDER BY facts.id ASC
                     LIMIT 1
                     OFFSET ?"""

        cursor = self._connection.cursor(buffered=True)
        if fact_position is not None:
            cursor.execute(query, (category, fact_position - 1))
        else:
            cursor.execute(query, (category,))
        result = cursor.fetchall()

        cursor.close()
        return [r[0] for r in result]

    def remove_category(self, category):
        cursor = self._connection.cursor(buffered=True)
        cursor.execute("""DELETE FROM categories WHERE name = %s""", (category,))
        self._connection.commit()
        cursor.close()

    def _add_fact(self, fact):
        cursor = self._connection.cursor(buffered=True)
        cursor.execute("""INSERT INTO facts(name) VALUES (%s)""", (fact,))
        self._connection.commit()
        cursor.close()

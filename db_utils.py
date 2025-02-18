# -*- coding: utf-8 -*-
import os
import sqlite3
import gettext

_ = gettext.gettext


class DB:
	def __init__(self, db_name="Tefter.db"):
		"""
		Initialize the database connection.
		:param db_name: The name of the SQLite database file.
		"""
		self.db_path = db_name
		self.conn = sqlite3.connect(self.db_path)
		self.conn.row_factory = sqlite3.Row  # Enable dictionary-like row access
		self.cursor = self.conn.cursor()
		self.create_tables()
	
	def create_tables(self):
		"""Create necessary tables if they don't exist."""
		self.execute("""
			CREATE TABLE IF NOT EXISTS contacts (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				phone TEXT,
				email TEXT,
				comment TEXT
			)
		""")
		self.execute("SELECT COUNT(*) FROM contacts")
		if self.cursor.fetchone()[0] == 0:
			self.execute("INSERT INTO contacts (name, phone, email, comment) VALUES (?, ?, ?, ?)", ("--- " + _('nobody') + " ---", "", "", _('Default "nobody" contact')))
			self.execute("UPDATE contacts SET id=0 WHERE id=1")
			# self.conn.commit()
		self.execute("""
			CREATE TABLE IF NOT EXISTS appointments (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				contact_id INTEGER NOT NULL,
				year INTEGER NOT NULL,
				month INTEGER NOT NULL,
				day INTEGER NOT NULL,
				hour INTEGER NOT NULL,
				minute INTEGER NOT NULL,
				title TEXT NOT NULL,
				details TEXT,
				importance INTEGER NOT NULL,
				FOREIGN KEY (contact_id) REFERENCES contacts(id)
			);
		""")
		# self.conn.commit()
	
	def execute(self, query, params=()):
		"""
		Execute an SQL query.
		:param query: The SQL query string.
		:param params: A tuple of parameters for parameterized queries.
		:return: The cursor object.
		"""
		try:
			self.cursor.execute(query, params)
			self.conn.commit()
			return self.cursor
		except sqlite3.Error as e:
			print(f"Database error: {e}")
			self.conn.rollback()
			return None
	
	def fetch_all(self, query, params=()):
		"""
		Fetch all results from an SQL query.
		:param query: The SQL query string.
		:param params: A tuple of parameters for parameterized queries.
		:return: A list of rows (sqlite3.Row objects).
		"""
		self.execute(query, params)
		return self.cursor.fetchall()
	
	def fetch_one(self, query, params=()):
		"""
		Fetch a single result from an SQL query.
		:param query: The SQL query string.
		:param params: A tuple of parameters for parameterized queries.
		:return: A single row (sqlite3.Row object) or None.
		"""
		self.execute(query, params)
		return self.cursor.fetchone()
	
	def close(self):
		"""Close the database connection."""
		self.conn.close()
	
	# additional utilities
	
	def get_next_id(self, table_name):
		result = self.fetch_one(f"SELECT MAX(id) FROM {table_name}")
		return (result[0] or 0) + 1

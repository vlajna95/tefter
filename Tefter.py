# -*- coding: utf-8 -*-
import sys
import wx
import wx.adv
import sqlite3
import gettext
import builtins
import datetime
import time
import win32con
import db_utils

sr = gettext.translation("Tefter", localedir="locale", languages=["sr"])
sr.install()
builtins.__dict__["_"] = sr.gettext

name = ""
phone = ""
email = ""
comment = ""

db = db_utils.DB("Tefter.sqlite")


class Frame(wx.Frame):
	def __init__(self, parent, title):
		super(Frame, self).__init__(parent, wx.ID_ANY, title=title)
		self.panel = wx.Panel(self)
		self.panel.SetLabel(title)
		self.tbIcon = TBIcon(self)
		self.timer = wx.PyTimer(self.check_appointments)
		self.RegHK()
		MenuBar = wx.MenuBar()
		FileMenu = wx.Menu()
		ExitItem = FileMenu.Append(wx.ID_ANY, _("E&xit\tAlt+F4"), _("Close the program"))
		self.Bind(wx.EVT_MENU, self.exit, ExitItem)
		MenuBar.Append(FileMenu, _("&File"))
		ContactsMenu = wx.Menu()
		NewContactItem = ContactsMenu.Append(wx.ID_ANY, _("&New contact\tCtrl+N"), _("Add a new contact"))
		self.Bind(wx.EVT_MENU, self.onNC, NewContactItem)
		EditContactItem = ContactsMenu.Append(wx.ID_ANY, _("&Edit contact\tCtrl+E"), _("Edit contact info"))
		self.Bind(wx.EVT_MENU, self.onEC, EditContactItem)
		DeleteContactItem = ContactsMenu.Append(wx.ID_ANY, _("&Delete contact\tCtrl+Delete"), _("Delete one or more contacts from your database"))
		self.Bind(wx.EVT_MENU, self.DeleteContact, DeleteContactItem)
		ExportContactsItem = ContactsMenu.Append(wx.ID_ANY, _("Exp&ort contacts\tAlt+E"), _("Export your contacts to a textual document"))
		self.Bind(wx.EVT_MENU, self.ExportContacts, ExportContactsItem)
		RefreshContactsItem = ContactsMenu.Append(wx.ID_ANY, _("Re&fresh contacts\tCtrl+F5"), _("Display all contacts in the list"))
		self.Bind(wx.EVT_MENU, self.ShowAllContacts, RefreshContactsItem)
		MenuBar.Append(ContactsMenu, _("&Contacts"))
		AppointmentsMenu = wx.Menu()
		NewAppointmentItem = AppointmentsMenu.Append(1, _("&New appointment\tCtrl+Shift+N"), _("Add a new appointment"))
		self.Bind(wx.EVT_MENU, self.AddNewAppointment, NewAppointmentItem)
		EditAppointmentItem = AppointmentsMenu.Append(2, _("&Edit appointment\tCtrl+Shift+E"), _("Edit the selected appointment"))
		self.Bind(wx.EVT_MENU, self.EditAppointment, EditAppointmentItem)
		DeleteAppointmentItem = AppointmentsMenu.Append(3, _("&Delete appointment\tCtrl+Shift+Delete"), _("Delete the selected appointment"))
		self.Bind(wx.EVT_MENU, self.DeleteAppointment, DeleteAppointmentItem)
		ExportAppointmentsItem = AppointmentsMenu.Append(wx.ID_ANY, _("Exp&ort appointments\tAlt+Shift+E"), _("Export your appointments to a textual document"))
		self.Bind(wx.EVT_MENU, self.ExportAppointments, ExportAppointmentsItem)
		RefreshAppointmentsItem = AppointmentsMenu.Append(wx.ID_ANY, _("Re&fresh appointments\tCtrl+Shift+F5"), _("Display all appointments in the list"))
		self.Bind(wx.EVT_MENU, self.ShowAllAppointments, RefreshAppointmentsItem)
		MenuBar.Append(AppointmentsMenu, _("&Appointments"))
		self.SetMenuBar(MenuBar)
		self.notebook = wx.Notebook(self.panel, style=wx.NB_TOP|wx.NB_FIXEDWIDTH)
		# Contacts Panel
		self.contacts_panel = wx.Panel(self.notebook)
		self.contacts_panel.SetLabel(_("Contacts"))
		sf_label = wx.StaticText(self.contacts_panel, label=_("Search contacts"))
		self.sf = wx.TextCtrl(self.contacts_panel, wx.ID_ANY, name=_(sf_label.GetLabel())) # search field
		self.sf.Bind(wx.EVT_TEXT, self.SearchContacts)
		self.sf.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		cl_label = wx.StaticText(self.contacts_panel, label=_("List of contacts"))
		self.cl = wx.ListCtrl(self.contacts_panel, wx.ID_ANY, style=wx.LC_REPORT, name=_(sf_label.GetLabel())) # contacts list
		self.cl.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.OnContactsItemChange)
		self.cl.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ShowContacts()
		df_label = wx.StaticText(self.contacts_panel, label=_("Details about the selected contacts"))
		self.df = wx.TextCtrl(self.contacts_panel, wx.ID_ANY, style=wx.TE_MULTILINE|wx.TE_READONLY, name=_(df_label.GetLabel())) # details field
		self.df.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		contacts_sizer = wx.BoxSizer(wx.VERTICAL)
		contacts_sizer.Add(sf_label, 0, wx.ALL, 5)
		contacts_sizer.Add(self.sf, 0, wx.EXPAND|wx.ALL, 5)
		contacts_sizer.Add(cl_label, 0, wx.ALL, 5)
		contacts_sizer.Add(self.cl, 1, wx.EXPAND|wx.ALL, 5)
		contacts_sizer.Add(df_label, 0, wx.ALL, 5)
		contacts_sizer.Add(self.df, 1, wx.EXPAND|wx.ALL, 5)
		self.contacts_panel.SetSizer(contacts_sizer)
		# Appointments Panel
		self.appointments_panel = wx.Panel(self.notebook)
		self.appointments_panel.SetLabel(_("Appointments"))
		asf_label = wx.StaticText(self.appointments_panel, label=_("Search appointments"))
		self.asf = wx.TextCtrl(self.appointments_panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(asf_label.GetLabel())) # appointments search field
		self.asf.Bind(wx.EVT_TEXT_ENTER, self.ShowAppointmentsByText)
		self.asf.Bind(wx.EVT_SET_FOCUS, self.Appointments_OnFocused)
		al_label = wx.StaticText(self.appointments_panel, label=_("List of appointments"))
		self.al = wx.ListCtrl(self.appointments_panel, wx.ID_ANY, style=wx.LC_REPORT, name=_(al_label.GetLabel())) # appointments list
		self.al.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.OnAppointmentsItemChange)
		self.al.Bind(wx.EVT_SET_FOCUS, self.Appointments_OnFocused)
		self.ShowAppointments()
		adf_label = wx.StaticText(self.appointments_panel, label=_("Details about the selected appointments"))
		self.adf = wx.TextCtrl(self.appointments_panel, wx.ID_ANY, style=wx.TE_MULTILINE|wx.TE_READONLY, name=_(adf_label.GetLabel())) # appointments details field
		self.adf.Bind(wx.EVT_SET_FOCUS, self.Appointments_OnFocused)
		a_year_label = wx.StaticText(self.appointments_panel, label=_("Year"))
		year_list = []
		for y in range(wx.DateTime().GetCurrentYear(), 2101):
			year_list.append(str(y))
		self.a_year = wx.Choice(self.appointments_panel, wx.ID_ANY, choices=year_list, name=_(a_year_label.GetLabel()))
		self.a_year.SetSelection(self.a_year.FindString(str(wx.DateTime().GetCurrentYear())))
		self.a_year.Bind(wx.EVT_CHOICE, self.OnCalcAppointmentDays)
		self.a_year.Bind(wx.EVT_SET_FOCUS, self.Appointments_OnFocused)
		self.a_year_btn = wx.Button(self.appointments_panel, label=_("Search by year"))
		self.a_year_btn.Bind(wx.EVT_BUTTON, self.ShowAppointmentsByYear)
		self.a_year_btn.Bind(wx.EVT_SET_FOCUS, self.Appointments_OnFocused)
		a_month_label = wx.StaticText(self.appointments_panel, label=_("Month"))
		month_list = []
		for m in range(12):
			month_list.append(str(m+1))
		self.a_month = wx.Choice(self.appointments_panel, wx.ID_ANY, choices=month_list, name=_(a_month_label.GetLabel()))
		self.a_month.SetSelection(0)
		self.a_month.Bind(wx.EVT_CHOICE, self.OnCalcAppointmentDays)
		self.a_month.Bind(wx.EVT_SET_FOCUS, self.Appointments_OnFocused)
		self.a_month_btn = wx.Button(self.appointments_panel, label=_("Search by month"))
		self.a_month_btn.Bind(wx.EVT_BUTTON, self.ShowAppointmentsByMonth)
		self.a_month_btn.Bind(wx.EVT_SET_FOCUS, self.Appointments_OnFocused)
		a_day_label = wx.StaticText(self.appointments_panel, label=_("Day"))
		day_list = self.CalcAppointmentDays(int(self.a_year.GetString(self.a_year.GetSelection())), int(self.a_month.GetString(self.a_month.GetSelection())))
		self.a_day = wx.Choice(self.appointments_panel, wx.ID_ANY, choices=day_list, name=_(a_day_label.GetLabel()))
		self.a_day.Bind(wx.EVT_SET_FOCUS, self.Appointments_OnFocused)
		self.a_date_btn = wx.Button(self.appointments_panel, label=_("Search by date"))
		self.a_date_btn.Bind(wx.EVT_BUTTON, self.ShowAppointmentsByDate)
		self.a_date_btn.Bind(wx.EVT_SET_FOCUS, self.Appointments_OnFocused)
		appointments_sizer = wx.BoxSizer(wx.VERTICAL)
		appointments_sizer.Add(asf_label, 1)
		appointments_sizer.Add(self.asf, 1, wx.EXPAND)
		appointments_sizer.Add(al_label, 1)
		appointments_sizer.Add(self.al, 1, wx.EXPAND)
		appointments_sizer.Add(adf_label, 1)
		appointments_sizer.Add(self.adf, 1, wx.EXPAND)
		appointments_sizer.Add(a_year_label, 1)
		appointments_sizer.Add(self.a_year, 1)
		appointments_sizer.Add(self.a_year_btn, 1, wx.EXPAND)
		appointments_sizer.Add(a_month_label, 1)
		appointments_sizer.Add(self.a_month, 1)
		appointments_sizer.Add(self.a_month_btn, 1, wx.EXPAND)
		appointments_sizer.Add(a_day_label, 1)
		appointments_sizer.Add(self.a_day, 1, wx.EXPAND)
		appointments_sizer.Add(self.a_date_btn, 1, wx.EXPAND)
		self.appointments_panel.SetSizer(appointments_sizer)
		self.appointments_panel.Fit()
		# add pages to the notebook
		self.notebook.AddPage(self.contacts_panel, _("Contacts"))
		# accelTable = wx.AcceleratorTable([(wx.ACCEL_NORMAL, wx.WXK_DELETE, DeleteContactItem.GetId()), (wx.ACCEL_ALT, ord('2'), self.goTo2)])
		# self.SetAcceleratorTable(accelTable)
		self.notebook.AddPage(self.appointments_panel, _("Appointments"))
		# self.accelTbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('n'), fmNewAppointment.GetId()), (wx.ACCEL_NORMAL, wx.WXK_DELETE, fmDeleteAppointment.GetId()), (wx.ACCEL_ALT, ord('1'), self.agoTo1), (wx.ACCEL_ALT, wx.WXK_F4, fmExit.GetId())])
		# self.SetAcceleratorTable(self.aaccelTbl)
		self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChange)
		main_box = wx.BoxSizer(wx.VERTICAL)
		main_box.Add(self.notebook, 1, wx.EXPAND)
		self.panel.SetSizer(main_box)
		self.panel.Fit()
		self.Center()
		self.Show(True)
		self.Bind(wx.EVT_HOTKEY, self.HandleHK, id=self.HotKeyId)
		self.Bind(wx.EVT_ICONIZE, self.OnMinimize)
		self.Bind(wx.EVT_CLOSE, self.OnExit)
	
	def RegHK(self):
		# Alt+V
		self.HotKeyId = 1001
		self.RegisterHotKey(self.HotKeyId, win32con.MOD_ALT, ord('v'))
	
	def HandleHK(self, event):
		print("Global hotkey used")
	
	def onNC(self, event):
		self.Destroy()
		ncDialog(parent=self, title=_("New contact")).Show(True)
	
	def onEC(self, event):
		id = self.cl.GetItemText(self.cl.GetFocusedItem(), 0)
		name = self.cl.GetItemText(self.cl.GetFocusedItem(), 1)
		phone = self.cl.GetItemText(self.cl.GetFocusedItem(), 2)
		email = self.cl.GetItemText(self.cl.GetFocusedItem(), 3)
		comment = self.cl.GetItemText(self.cl.GetFocusedItem(), 4)
		self.Destroy()
		ecDialog(parent=self, title=_("Edit contact"), cID=id, cName=name, cNum=phone, cEmail=email, cCom=comment, cContainer=self).Show(True)
	
	def display_contacts(self, sql="SELECT * FROM contacts ORDER BY name ASC", change_focus=True):
		if change_focus:
			self.cl.SetFocus()
		rows = db.execute(sql)
		if rows.rowcount == 0:
			wx.MessageDialog(None, _("There are no appointments for this year."), _("Oops"), wx.OK|wx.ICON_INFORMATION).ShowModal()
			return False
		self.cl.ClearAll()
		self.cl.InsertColumn(0, _("#"), width=100)
		self.cl.InsertColumn(1, _("Name"), wx.LIST_FORMAT_RIGHT, 100)
		self.cl.InsertColumn(2, _("Phone"), wx.LIST_FORMAT_RIGHT, 100)
		self.cl.InsertColumn(3, _("Email"), wx.LIST_FORMAT_RIGHT, 100)
		self.cl.InsertColumn(4, _("Comments"), wx.LIST_FORMAT_RIGHT, 100)
		rows = rows.fetchall()
		for row in rows:
			if row["id"] == 0:
				continue
			index = self.cl.InsertItem(self.cl.GetItemCount(), str(row[0]))
			self.cl.SetItem(index, 1, row[1])
			self.cl.SetItem(index, 2, row[2])
			self.cl.SetItem(index, 3, row[3])
			self.cl.SetItem(index, 4, row[4])
		return True
	
	def ShowContacts(self):
		self.timer.Start(20000)
		self.display_contacts()
	
	def ShowAllContacts(self, event):
		self.display_contacts()
	
	def SearchContacts(self, event):
		sql = "SELECT * FROM contacts WHERE name LIKE '%" + self.sf.GetValue() + "%' OR phone LIKE '%" + self.sf.GetValue() + "%' OR email LIKE '%" + self.sf.GetValue() + "%' OR comment LIKE '%" + self.sf.GetValue() + "%' ORDER BY name ASC;"
		self.display_contacts(sql, change_focus=False)
	
	def OnContactsItemChange(self, event):
		self.snd = wx.adv.Sound("sounds/change_item.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
		self.df.Clear()
		count = self.cl.GetColumnCount()
		for x in range(count):
			self.df.AppendText("%s: %s \n" % (self.cl.GetColumn(x).GetText(), self.cl.GetItemText(self.cl.GetFocusedItem(), x)))
	
	def DeleteContact(self, event):
		id = self.cl.GetItemText(self.cl.GetFocusedItem(), 0)
		dcsl = []
		dcl = []
		dcl_str = ""
		if self.cl.GetSelectedItemCount() > 1:
			first = self.cl.GetFirstSelected()
			dcsl.append(first)
			dcl.append(self.cl.GetItemText(first, 0))
			dcl_str += self.cl.GetItemText(first, 1) + " \n" + _("Phone") + ": " + self.cl.GetItemText(first, 2) + " \n" + _("Email") + ": " + self.cl.GetItemText(first, 3) + " \n" + _("Comments") + ": " + self.cl.GetItemText(first, 4) + " \n\n"
			next = self.cl.GetNextSelected(first)
			dcsl.append(next)
			dcl.append(self.cl.GetItemText(next, 0))
			dcl_str += self.cl.GetItemText(next, 1) + " \n" + _("Phone") + ": " + self.cl.GetItemText(next, 2) + " \n" + _("Email") + ": " + self.cl.GetItemText(next, 3) + " \n" + _("Comments") + ": " + self.cl.GetItemText(next, 4) + " \n\n"
			while next != -1:
				next = self.cl.GetNextSelected(next)
				if not next == -1:
					dcsl.append(next)
					dcl.append(self.cl.GetItemText(next, 0))
					dcl_str += self.cl.GetItemText(next, 1) + " \n" + _("Phone") + ": " + self.cl.GetItemText(next, 2) + " \n" + _("Email") + ": " + self.cl.GetItemText(next, 3) + " \n" + _("Comments") + ": " + self.cl.GetItemText(next, 4) + " \n\n"
			self.yn = wx.MessageDialog(None, dcl_str, _("Are you sure you want to delete these contacts?"), style=wx.YES_NO|wx.ICON_QUESTION)
		else:
			dcsl = [self.cl.GetFocusedItem()]
			dcl = [self.cl.GetItemText(self.cl.GetFocusedItem(), 0)]
			selected_contact = self.cl.GetFocusedItem()
			self.yn = wx.MessageDialog(None, "%s \n%s: %s \n%s: %s \n%s: %s \n" % (self.cl.GetItemText(selected_contact, 1), _("Phone"), self.cl.GetItemText(selected_contact, 2), _("Email"), self.cl.GetItemText(selected_contact, 3), _("Comments"), self.cl.GetItemText(selected_contact, 4)), _("Are you sure you want to delete this contact?"), wx.YES_NO|wx.ICON_QUESTION)
		if self.yn.ShowModal() == wx.ID_YES:
			print(dcl)
			for x in dcl:
				sql = "DELETE FROM contacts WHERE id = %s" % x
				print(sql)
				rows = db.execute(sql)
			self.snd = wx.adv.Sound("sounds/delete.wav")
			self.snd.Play(wx.adv.SOUND_ASYNC)
		else:
			self.snd = wx.adv.Sound("sounds/cancel.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
		self.ShowContacts()
	
	def OnMinimize(self, event):
		if self.IsIconized():
			self.Hide()
	
	def OnExit(self, event):
		self.tbIcon.RemoveIcon()
		self.tbIcon.Destroy()
		self.snd = wx.adv.Sound("sounds/exit.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
		self.Destroy()
		# db.close()
		self.exit()
		sys.exit(0)
	
	def exit(self, event=None):
		self.tbIcon.RemoveIcon()
		self.tbIcon.Destroy()
		self.snd = wx.adv.Sound("sounds/exit.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
		self.Destroy()
		# db.close()
		sys.exit(0)
	
	def cancel(self, event):
		self.snd = wx.adv.Sound("sounds/cancel.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
		ncDialog.Destroy()
		ecDialog.Destroy()
		self.Destroy()
		main(False)
	
	def OnFocused(self, e):
		try:
			if (e.GetEventObject().GetId() == self.df.GetId()):
				self.snd = wx.adv.Sound("sounds/text_field.wav")
				self.snd.Play(wx.adv.SOUND_ASYNC)
			elif e.GetEventObject().GetId() == self.sf.GetId():
				self.snd = wx.adv.Sound("sounds/search_field.wav")
				self.snd.Play(wx.adv.SOUND_ASYNC)
			elif e.GetEventObject().GetId() == self.cl.GetId():
				self.snd = wx.adv.Sound("sounds/list.wav")
				self.snd.Play(wx.adv.SOUND_ASYNC)
		except AttributeError:
			pass
	
	def display_appointments(self, sql="SELECT * FROM appointments ORDER BY year, month, day DESC", change_focus=False):
		if change_focus:
			self.al.SetFocus()
		rows = db.execute(sql)
		self.al.ClearAll()
		self.al.InsertColumn(0, _("#"))
		self.al.InsertColumn(1, _("Contact"))
		self.al.InsertColumn(2, _("Year"))
		self.al.InsertColumn(3, _("Month"))
		self.al.InsertColumn(4, _("Day"))
		self.al.InsertColumn(5, _("Time"))
		self.al.InsertColumn(6, _("Title"))
		self.al.InsertColumn(7, _("Details"))
		self.al.InsertColumn(8, _("Importance"))
		rows = rows.fetchall()
		for r in rows:
			contact_sql = "SELECT * FROM contacts WHERE id = '%s'" % r[1]
			contact = db.execute(contact_sql).fetchone()["name"]
			index = self.al.InsertItem(self.al.GetItemCount(), str(r[0])) # ID
			self.al.SetItem(index, 1, contact) # related contact
			self.al.SetItem(index, 2, str(r[2])) # year
			self.al.SetItem(index, 3, str(r[3])) # month
			self.al.SetItem(index, 4, str(r[4])) # day
			self.al.SetItem(index, 5, str(r[5]) + ":" + str(r[6])) # hour:minute
			self.al.SetItem(index, 6, r[7]) # title
			self.al.SetItem(index, 7, r[8]) # details
			self.al.SetItem(index, 8, str(r[9])) # importance
		return True
	
	def ShowAppointments(self):
		self.display_appointments(change_focus=True)
	
	def ShowAllAppointments(self, event):
		self.display_appointments(change_focus=True)
	
	def ShowAppointmentsByText(self, event):
		sql = "SELECT * FROM appointments WHERE year LIKE '%" + self.asf.GetValue() + "%' OR month LIKE '%" + self.asf.GetValue() + "%' OR day LIKE '%" + self.asf.GetValue() + "%' OR title LIKE '%" + self.asf.GetValue() + "%' OR details LIKE '%" + self.asf.GetValue() + "%';"
		self.display_appointments(sql)
	
	def ShowAppointmentsByYear(self, event):
		Year = self.a_year.GetString(self.a_year.GetSelection())
		sql = "SELECT * FROM appointments WHERE year = %s ORDER BY year ASC" % Year
		self.display_appointments(sql)
	
	def ShowAppointmentsByMonth(self, event):
		Month = self.a_month.GetString(self.a_month.GetSelection())
		sql = "SELECT * FROM appointments WHERE month = %s ORDER BY year, month, day ASC" % Month
		self.display_appointments(sql)
	
	def ShowAppointmentsByDate(self, event):
		Year = self.a_year.GetString(self.a_year.GetSelection())
		Month = self.a_month.GetString(self.a_month.GetSelection())
		Day = self.a_day.GetString(self.a_day.GetSelection())
		print(Year, Month, Day)
		sql = "SELECT * FROM appointments WHERE year = %s AND month = %s AND day = %s" % (Year, Month, Day)
		self.display_appointments(sql)
	
	def CalcAppointmentDays(self, year, month):
		md = [(1, 31), (2, 28), (3, 31), (4, 30), (5, 31), (6, 30), (7, 31), (8, 31), (9, 30), (10, 31), (11, 30), (12, 31)]
		if year % 4 == 0:
			md[1] = (2, 29)
		daysList = []
		for x in md:
			if month == x[0]:
				for d in range(x[1]):
					daysList.append(str(d+1))
		return daysList
	
	def OnCalcAppointmentDays(self, event):
		# f = event.GetEventObject().GetParent().GetParent()
		dl = self.CalcAppointmentDays(int(self.a_year.GetString(self.a_year.GetSelection())), int(self.a_month.GetString(self.a_month.GetSelection())))
		self.a_day.SetItems(dl)
		self.Layout()
	
	def AddNewAppointment(self, event):
		self.NewAppointment()
	
	def NewAppointment(self):
		contacts = [] # ["0. Nijedan"]
		for x in db.execute("SELECT * FROM contacts").fetchall():
			contacts.append(str(x[0]) + ". " + x[1])
		self.new_appointment = wx.Dialog(parent=self, title=_("New appointment"), style=wx.OK_CANCEL)
		self.new_appointment.panel = wx.Panel(self.new_appointment, name=_("New appointment"))
		self.new_appointment.contact_id_label = wx.StaticText(self.new_appointment.panel, label=_("Contact"))
		self.new_appointment.contact_id = wx.Choice(self.new_appointment.panel, wx.ID_ANY, choices=contacts, name=_(self.new_appointment.contact_id_label.GetLabel()))
		self.new_appointment.contact_id.SetSelection(0)
		self.new_appointment.contact_id.Bind(wx.EVT_KEY_UP, self.A_new_AddAppointment)
		self.new_appointment.day_label = wx.StaticText(self.new_appointment.panel, label=_("Day"))
		self.new_appointment.day = wx.TextCtrl(self.new_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.new_appointment.day_label.GetLabel()))
		self.new_appointment.day.Bind(wx.EVT_TEXT_ENTER, self.A_new_AddAppointment)
		self.new_appointment.month_label = wx.StaticText(self.new_appointment.panel, label=_("Month"))
		self.new_appointment.month = wx.TextCtrl(self.new_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.new_appointment.month_label.GetLabel()))
		self.new_appointment.month.Bind(wx.EVT_TEXT_ENTER, self.A_new_AddAppointment)
		self.new_appointment.year_label = wx.StaticText(self.new_appointment.panel, label=_("Year"))
		self.new_appointment.year = wx.TextCtrl(self.new_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.new_appointment.year_label.GetLabel()))
		self.new_appointment.year.Bind(wx.EVT_TEXT_ENTER, self.A_new_AddAppointment)
		self.new_appointment.hour_label = wx.StaticText(self.new_appointment.panel, label=_("Hour"))
		self.new_appointment.hour = wx.TextCtrl(self.new_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.new_appointment.hour_label.GetLabel()))
		self.new_appointment.hour.Bind(wx.EVT_TEXT_ENTER, self.A_new_AddAppointment)
		self.new_appointment.minute_label = wx.StaticText(self.new_appointment.panel, label=_("Minutes"))
		self.new_appointment.minute = wx.TextCtrl(self.new_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.new_appointment.minute_label.GetLabel()))
		self.new_appointment.minute.Bind(wx.EVT_TEXT_ENTER, self.A_new_AddAppointment)
		self.new_appointment.title_label = wx.StaticText(self.new_appointment.panel, label=_("Title"))
		self.new_appointment.title = wx.TextCtrl(self.new_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.new_appointment.title_label.GetLabel()))
		self.new_appointment.title.Bind(wx.EVT_TEXT_ENTER, self.A_new_AddAppointment)
		self.new_appointment.details_label = wx.StaticText(self.new_appointment.panel, label=_("Appointment"))
		self.new_appointment.details = wx.TextCtrl(self.new_appointment.panel, wx.ID_ANY, style=wx.TE_MULTILINE, name=_(self.new_appointment.details_label.GetLabel()))
		importance = []
		for i in range(6):
			importance.append(str(i))
		self.new_appointment.importance_label = wx.StaticText(self.new_appointment.panel, label=_("How important is this appointment?"))
		self.new_appointment.importance = wx.Choice(self.new_appointment.panel, wx.ID_ANY, choices=importance, name=_(self.new_appointment.importance_label.GetLabel()))
		self.new_appointment.importance.SetSelection(0)
		self.new_appointment.OK = wx.Button(self.new_appointment.panel, label=_("Add"))
		self.new_appointment.OK.Bind(wx.EVT_BUTTON, self.A_new_AddAppointment)
		self.new_appointment.OK.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.new_appointment.Cancel = wx.Button(self.new_appointment.panel, label=_("Cancel"))
		self.new_appointment.Cancel.Bind(wx.EVT_BUTTON, self.NewAppointment_Close)
		self.new_appointment.Cancel.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		nox = wx.BoxSizer(wx.VERTICAL)
		nox.Add(self.new_appointment.contact_id_label, 1)
		nox.Add(self.new_appointment.contact_id, 1, wx.EXPAND)
		nox.Add(self.new_appointment.day_label, 1)
		nox.Add(self.new_appointment.day, 1, wx.EXPAND)
		nox.Add(self.new_appointment.month_label, 1)
		nox.Add(self.new_appointment.month, 1, wx.EXPAND)
		nox.Add(self.new_appointment.year_label, 1)
		nox.Add(self.new_appointment.year, 1, wx.EXPAND)
		nox.Add(self.new_appointment.hour_label, 1)
		nox.Add(self.new_appointment.hour, 1, wx.EXPAND)
		nox.Add(self.new_appointment.minute_label, 1)
		nox.Add(self.new_appointment.minute, 1, wx.EXPAND)
		nox.Add(self.new_appointment.title_label, 1)
		nox.Add(self.new_appointment.title, 1, wx.EXPAND)
		nox.Add(self.new_appointment.details_label, 1)
		nox.Add(self.new_appointment.details, 1, wx.EXPAND)
		nox.Add(self.new_appointment.importance_label, 1)
		nox.Add(self.new_appointment.importance, 1, wx.EXPAND)
		nox.Add(self.new_appointment.OK, 1, wx.ALIGN_CENTER_HORIZONTAL)
		nox.Add(self.new_appointment.Cancel, 1, wx.ALIGN_CENTER_HORIZONTAL)
		self.new_appointment.panel.SetSizer(nox)
		self.new_appointment_close_ID = wx.ID_ANY
		self.Bind(wx.EVT_MENU, self.NewAppointment_Close, id=self.new_appointment_close_ID)
		# at = wx.AcceleratorTable([(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, self.new_appointment.Cancel.GetId()), (wx.ACCEL_ALT, wx.WXK_F4, self.new_appointment_close_ID)])
		# self.new_appointment.SetAcceleratorTable(at)
		self.new_appointment.panel.Fit()
		self.new_appointment.ShowModal()
	
	def A_new_AddAppointment(self, event):
		if event.GetEventObject() == self.new_appointment.contact_id and event.GetKeyCode() != wx.WXK_RETURN:
			pass
		elif event.GetEventObject() != self.new_appointment.contact_id and event.GetKeyCode() == wx.WXK_RETURN:
			# self.NewAppointment()
			# elif event.GetEventObject() != self.new_appointment.contact_id:
			p = event.GetEventObject().GetParent().GetParent()
			contact_id = p.contact_id.GetString(p.contact_id.GetSelection()).split(".")[0]
			importance = p.importance.GetString(p.importance.GetSelection())
			next_id = db.get_next_id("appointments")
			sql = "INSERT INTO appointments (id, contact_id, year, month, day, hour, minute, title, details, importance) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (next_id, contact_id, p.year.GetValue(), p.month.GetValue(), p.day.GetValue(), p.hour.GetValue(), p.minute.GetValue(), p.title.GetValue(), p.details.GetValue(), importance)
			print(sql.encode('utf-8'))
			rows = db.execute(sql)
			self.NewAppointment_Destroy()
		self.display_appointments(change_focus=True)
	
	def NewAppointment_Close(self, event):
		self.new_appointment.Destroy()
	
	def EditAppointment(self, event):
		self.edit_appointment = wx.Frame(self, wx.ID_ANY, name=_("Edit appointment"))
		self.edit_appointment.panel = wx.Panel(self.edit_appointment)
		self.edit_appointment.edLabel = wx.StaticText(self.edit_appointment.panel, label=_("Edit day"))
		self.edit_appointment.ed = wx.TextCtrl(self.edit_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.edit_appointment.edLabel.GetLabel()))
		self.edit_appointment.emLabel = wx.StaticText(self.edit_appointment.panel, label=_("Edit month"))
		self.edit_appointment.em = wx.TextCtrl(self.edit_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.edit_appointment.emLabel.GetLabel()))
		self.edit_appointment.eyLabel = wx.StaticText(self.edit_appointment.panel, label=_("Edit year"))
		self.edit_appointment.ey = wx.TextCtrl(self.edit_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.edit_appointment.eyLabel.GetLabel()))
		self.edit_appointment.ehLabel = wx.StaticText(self.edit_appointment.panel, label=_("Edit hour"))
		self.edit_appointment.eh = wx.TextCtrl(self.edit_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.edit_appointment.ehLabel.GetLabel()))
		self.edit_appointment.enLabel = wx.StaticText(self.edit_appointment.panel, label=_("Edit minutes"))
		self.edit_appointment.en = wx.TextCtrl(self.edit_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.edit_appointment.enLabel.GetLabel()))
		self.edit_appointment.etLabel = wx.StaticText(self.edit_appointment.panel, label=_("Edit title"))
		self.edit_appointment.et = wx.TextCtrl(self.edit_appointment.panel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER, name=_(self.edit_appointment.etLabel.GetLabel()))
		self.edit_appointment.eaLabel = wx.StaticText(self.edit_appointment.panel, label=_("Edit appointment"))
		self.edit_appointment.ea = wx.TextCtrl(self.edit_appointment.panel, wx.ID_ANY, name=_(self.edit_appointment.eaLabel.GetLabel()))
		importance = []
		for i in range(6):
			importance.append(str(i))
		self.edit_appointment.eiLabel = wx.StaticText(self.edit_appointment.panel, label=_("Edit importance"))
		self.edit_appointment.ei = wx.Choice(self.edit_appointment.panel, wx.ID_ANY, choices = importance, name=_(self.edit_appointment.eiLabel.GetLabel()))
		p = self.edit_appointment
		aid = self.al.GetItemText(self.al.GetFocusedItem(), 0)
		r = db.execute("SELECT * FROM appointments WHERE id = ?", aid).fetchone()
		p.ed.SetValue(str(r[4]))
		p.em.SetValue(str(r[3]))
		p.ey.SetValue(str(r[2]))
		p.eh.SetValue(str(r[5]))
		p.en.SetValue(str(r[6]))
		p.et.SetValue(r[7])
		p.ea.SetValue(r[8])
		p.ei.SetSelection(p.ei.FindString(str(r[9])))
		self.edit_appointment.ed.Bind(wx.EVT_TEXT_ENTER, self.EditAppointment_SaveChanges)
		self.edit_appointment.em.Bind(wx.EVT_TEXT_ENTER, self.EditAppointment_SaveChanges)
		self.edit_appointment.ey.Bind(wx.EVT_TEXT_ENTER, self.EditAppointment_SaveChanges)
		self.edit_appointment.eh.Bind(wx.EVT_TEXT_ENTER, self.EditAppointment_SaveChanges)
		self.edit_appointment.en.Bind(wx.EVT_TEXT_ENTER, self.EditAppointment_SaveChanges)
		self.edit_appointment.et.Bind(wx.EVT_TEXT_ENTER, self.EditAppointment_SaveChanges)
		self.edit_appointment.OK = wx.Button(self.edit_appointment.panel, label=_("Save changes"))
		self.edit_appointment.OK.Bind(wx.EVT_BUTTON, self.EditAppointment_SaveChanges)
		self.edit_appointment.Cancel = wx.Button(self.edit_appointment.panel, wx.ID_ANY, label=_("Cancel"))
		self.edit_appointment.Cancel.Bind(wx.EVT_BUTTON, self.EditAppointment_Cancel)
		eox = wx.BoxSizer(wx.VERTICAL)
		eox.Add(self.edit_appointment.edLabel, 1)
		eox.Add(self.edit_appointment.ed, 1, wx.EXPAND)
		eox.Add(self.edit_appointment.emLabel, 1)
		eox.Add(self.edit_appointment.em, 1, wx.EXPAND)
		eox.Add(self.edit_appointment.eyLabel, 1)
		eox.Add(self.edit_appointment.ey, 1, wx.EXPAND)
		eox.Add(self.edit_appointment.ehLabel, 1)
		eox.Add(self.edit_appointment.eh, 1, wx.EXPAND)
		eox.Add(self.edit_appointment.enLabel, 1)
		eox.Add(self.edit_appointment.en, 1, wx.EXPAND)
		eox.Add(self.edit_appointment.etLabel, 1)
		eox.Add(self.edit_appointment.et, 1, wx.EXPAND)
		eox.Add(self.edit_appointment.eaLabel, 1)
		eox.Add(self.edit_appointment.ea, 1, wx.EXPAND)
		eox.Add(self.edit_appointment.eiLabel, 1)
		eox.Add(self.edit_appointment.ei, 1, wx.EXPAND)
		eox.Add(self.edit_appointment.OK, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
		eox.Add(self.edit_appointment.Cancel, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
		self.edit_appointment.panel.SetSizer(eox)
		self.edit_appointment.Fit()
		self.edit_appointment.accelTbl = wx.AcceleratorTable([(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, self.edit_appointment.Cancel.GetId()), (wx.ACCEL_ALT, wx.WXK_F4, self.edit_appointment.Cancel.GetId())])
		self.edit_appointment.SetAcceleratorTable(self.edit_appointment.accelTbl)
		self.edit_appointment.Show()
	
	def EditAppointment_SaveChanges(self, event):
		p = event.GetEventObject().GetParent().GetParent()
		d = p.ed.GetValue()
		m = p.em.GetValue()
		y = p.ey.GetValue()
		h = p.eh.GetValue()
		n = p.en.GetValue()
		t = p.et.GetValue()
		a = p.ea.GetValue()
		i = p.ei.GetString(p.ei.GetSelection())
		aid = self.al.GetItemText(self.al.GetFocusedItem(), 0)
		sql = "UPDATE appointments SET year = %s, month = %s, day = %s, hour = %s, minute = %s, title = '%s', details = '%s', importance = %s WHERE id = %s" % (y, m, d, h, n, t, a, i, aid)
		print(sql.encode('utf-8'))
		rows = db.execute(sql)
		self.edit_appointment.Destroy()
		self.ShowAppointments()
	
	def OnAppointmentsItemChange(self, event):
		self.snd = wx.adv.Sound("sounds/change_item.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
		self.adf.Clear()
		count = self.al.GetColumnCount()
		for x in range(count):
			self.adf.AppendText("%s: %s \n" % (self.al.GetColumn(x).GetText(), self.al.GetItemText(self.al.GetFocusedItem(), x)))
	
	def Appointments_OnFocused(self, e):
		try:
			if (e.GetEventObject().GetId() == self.adf.GetId()):
				self.snd = wx.adv.Sound("sounds/text_field.wav")
				self.snd.Play(wx.adv.SOUND_ASYNC)
			elif e.GetEventObject().GetId() == self.asf.GetId():
				self.snd = wx.adv.Sound("sounds/search_field.wav")
				self.snd.Play(wx.adv.SOUND_ASYNC)
			elif e.GetEventObject().GetId() == self.al.GetId():
				self.snd = wx.adv.Sound("sounds/list.wav")
				self.snd.Play(wx.adv.SOUND_ASYNC)
			elif e.GetEventObject().GetId() == self.a_year_btn.GetId() or e.GetEventObject().GetId() == self.a_month_btn.GetId() or e.GetEventObject().GetId() == self.a_date_btn.GetId():
				self.snd = wx.adv.Sound("sounds/button.wav")
				self.snd.Play(wx.adv.SOUND_ASYNC)
			elif e.GetEventObject().GetId() == self.a_year.GetId() or e.GetEventObject().GetId() == self.a_month.GetId() or e.GetEventObject().GetId() == self.a_day.GetId():
				self.snd = wx.adv.Sound("sounds/combobox.wav")
				self.snd.Play(wx.adv.SOUND_ASYNC)
		except AttributeError:
			pass
	
	def EditAppointment_Cancel(self, event):
		self.edit_appointment.Destroy()
		self.ShowAppointments()
	
	def DeleteAppointment(self, event):
		id = self.al.GetItemText(self.al.GetFocusedItem(), 0)
		dasl = []
		dal = []
		dal_str = ""
		if self.al.GetSelectedItemCount() > 1:
			f = self.al.GetFirstSelected()
			dasl.append(f)
			dal.append(self.al.GetItemText(f, 0))
			dal_str += self.al.GetItemText(f, 1) + " \n" + _("Date") + ": " + self.al.GetItemText(f, 4) + ". " + self.al.GetItemText(f, 3) + ". " + self.al.GetItemText(f, 2) + ". \n" + _("Title") + ": " + self.al.GetItemText(f, 5) + " \n" + _("Details") + ": " + self.al.GetItemText(f, 6) + " \n\n"
			n = self.al.GetNextSelected(f)
			dasl.append(n)
			dal.append(self.al.GetItemText(n, 0))
			dal_str += self.al.GetItemText(n, 1) + " \n" + _("Date") + ": " + self.al.GetItemText(n, 4) + ". " + self.al.GetItemText(n, 3) + ". " + self.al.GetItemText(n, 2) + ". \n" + _("Title") + ": " + self.al.GetItemText(n, 5) + " \n" + _("Details") + ": " + self.al.GetItemText(n, 6) + " \n\n"
			while n != -1:
				n = self.al.GetNextSelected(n)
				if not n == -1:
					dasl.append(n)
					dal.append(self.al.GetItemText(n, 0))
					dal_str += self.al.GetItemText(n, 1) + " \n" + _("Date") + ": " + self.al.GetItemText(n, 4) + ". " + self.al.GetItemText(n, 3) + ". " + self.al.GetItemText(n, 2) + ". \n" + _("Title") + ": " + self.al.GetItemText(n, 5) + " \n" + _("Details") + ": " + self.al.GetItemText(n, 6) + " \n\n"
			self.A_yn = wx.MessageDialog(None, dal_str, _("Are you sure you want to delete these appointments?"), style=wx.YES_NO|wx.ICON_QUESTION)
		else:
			dasl = [self.al.GetFirstSelected()]
			dal = [self.al.GetItemText(self.al.GetFocusedItem(), 0)]
			self.A_yn = wx.MessageDialog(None, "%s: %s \n%s: %s \n%s: %s \n%s: %s \n\n" % (_("Contact"), self.al.GetItemText(dasl[0], 1), _("Date"), self.al.GetItemText(dasl[0], 4) + ". " + self.al.GetItemText(dasl[0], 3) + ". " + self.al.GetItemText(dasl[0], 2) + ".", _("Title"), self.al.GetItemText(dasl[0], 5), _("Details"), self.al.GetItemText(dasl[0], 6)), _("Are you sure you want to delete this appointment?"), wx.YES_NO|wx.ICON_QUESTION)
		if self.A_yn.ShowModal() == wx.ID_YES:
			for x in dal:
				if db.execute("DELETE FROM appointments WHERE id = :x", {"x": x}):
					self.snd = wx.adv.Sound("sounds/delete.wav")
					self.snd.Play(wx.adv.SOUND_ASYNC)
			self.ShowAppointments()
		else:
			self.ShowAppointments()
			self.snd = wx.adv.Sound("sounds/cancel.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
	
	def A_Exit(self, event):
		self.tbIcon.RemoveIcon()
		self.tbIcon.Destroy()
		db.close()
		sys.exit(0)
	
	"""
	def threads(self, func, interval):
		self.interval = interval
		thread = threading.Thread(target=func, args=())
		thread.daemon = True
		thread.start()
	"""
	
	def check_appointments(self):
		dt = datetime.datetime.now()
		y = dt.year
		m = dt.month
		d = dt.day
		h = dt.hour
		n = dt.minute
		# print("Trenutno: ", y, "/", m, "/", d, " ", h, ":", n)
		for a in db.execute("SELECT * FROM appointments").fetchall():
			# print("Iz baze: ", a["year"], "/", a["month"], "/", a["day"], " ", a["hour"], ":", a["minute"])
			if a["year"] == y and a["month"] == m and a["day"] == d and int(a["hour"]) == h and int(a["minute"]) == n:
				# print("Isto je!", a)
				self.tbIcon.ShowBalloon(a["title"], a["details"], 10)
				if a["importance"] == 1 or a["importance"] == 2:
					wx.adv.Sound("sounds/alarm" + str(a["importance"]) + ".wav").Play(wx.adv.SOUND_ASYNC)
				if a["importance"] in range(3, 5):
					if (a["day"], a["month"], a["year"], int(a["hour"]), int(a["minute"])) == (d, m, y, h, n):
						wx.adv.Sound("sounds/alarm" + str(a["importance"]) + ".wav").Play(wx.adv.SOUND_ASYNC)
						time.sleep(5)
			else:
				# print("Nije isto: ", a)
				pass
	
	def ExportContacts(self, event):
		contacts = ""
		rows = db.fetch_all("SELECT * FROM contacts")
		for row in rows:
			if row[0] != 0:
				contacts += "%s \n%s: %s \n%s: %s \n%s: %s \n----------\n" % (row[1], _("Phone"), row[2], _("Email"), row[3], _("Comments"), row[4])
		contacts = contacts.encode('utf-8')
		print(contacts)
		contacts_file = open(_("Exported contacts")+".txt", "w")
		contacts_file.writelines(contacts)
		wx.adv.Sound("sounds/exported_contacts.wav").Play(wx.adv.SOUND_ASYNC)
	
	def ExportAppointments(self, event):
		appointments = ""
		rows = db.fetch_all("SELECT * FROM appointments ORDER BY year, month, day, hour DESC")
		for r in rows:
			if r["contact_id"] != 0:
				contact_sql = "SELECT * FROM contacts WHERE id = %s" % r[1]
				contact = db.fetch_one(contact_sql)["name"]
				appointments += "%s: %s \n%s: %s. %s. %s. %s:%s \n%s: %s \n%s: %s \n%s: %s \n----------\n" % (_("Contact"), contact, _("Time"), r["day"], r["month"], r["year"], r["hour"], r["minute"], _("Title"), r["title"], _("Details"), r["details"], _("Importance"), r["importance"])
			else:
				appointments += "%s: %s. %s. %s. %s:%s \n%s: %s \n%s: %s \n%s: %s \n----------\n" % (_("Time"), r["day"], r["month"], r["year"], r["hour"], r["minute"], _("Title"), r["title"], _("Details"), r["details"], _("Importance"), r["importance"])
		appointments = appointments.encode('utf-8')
		print(appointments)
		appointments_file = open(_("Exported appointments")+".txt", "w")
		appointments_file.writelines(appointments)
		wx.adv.Sound("sounds/exported_appointments.wav").Play(wx.adv.SOUND_ASYNC)
	
	def OnPageChange(self, event):
		page = self.notebook.GetPageText(self.notebook.GetSelection())
		if page == _("Contacts"):
			self.snd = wx.adv.Sound("sounds/tab_contacts.wav")
		elif page == _("Appointments"):
			self.snd = wx.adv.Sound("sounds/tab_appointments.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)


class ncDialog(wx.Dialog):
	def __init__(self, parent, title=_("New contact")):
		super(ncDialog, self).__init__(None, title=title)
		self.ncBox = wx.BoxSizer(wx.VERTICAL)
		self.ncNameLabel = wx.StaticText(self, label=_("Name"))
		self.ncBox.Add(self.ncNameLabel, 1)
		self.ncName = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
		self.ncName.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ncName.Bind(wx.EVT_KEY_DOWN, self.ncKeyDown)
		self.ncName.Bind(wx.EVT_TEXT_ENTER, self.NC)
		self.ncBox.Add(self.ncName, 1, wx.EXPAND)
		self.ncNumLabel = wx.StaticText(self, label=_("Phone"))
		self.ncBox.Add(self.ncNumLabel, 1)
		self.ncNum = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
		self.ncNum.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ncNum.Bind(wx.EVT_KEY_DOWN, self.ncKeyDown)
		self.ncNum.Bind(wx.EVT_TEXT_ENTER, self.NC)
		self.ncBox.Add(self.ncNum, 1, wx.EXPAND)
		self.ncEmailLabel = wx.StaticText(self, label=_("Email"))
		self.ncBox.Add(self.ncEmailLabel, 1)
		self.ncEmail = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
		self.ncEmail.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ncEmail.Bind(wx.EVT_KEY_DOWN, self.ncKeyDown)
		self.ncEmail.Bind(wx.EVT_TEXT_ENTER, self.NC)
		self.ncBox.Add(self.ncEmail, 1, wx.EXPAND)
		self.ncComLabel = wx.StaticText(self, label=_("Comments"))
		self.ncBox.Add(self.ncComLabel, 1)
		self.ncCom = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_MULTILINE)
		self.ncCom.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ncCom.Bind(wx.EVT_KEY_DOWN, self.ncKeyDown)
		self.ncBox.Add(self.ncCom, 1, wx.EXPAND)
		self.ncOK = wx.Button(self, label=_("Add"))
		self.ncOK.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ncOK.Bind(wx.EVT_KEY_DOWN, self.ncKeyDown)
		self.ncOK.Bind(wx.EVT_BUTTON, self.NC)
		self.ncBox.Add(self.ncOK, 1, wx.ALIGN_CENTER_HORIZONTAL)
		self.ncCancel = wx.Button(self, label=_("Cancel"))
		self.ncCancel.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ncCancel.Bind(wx.EVT_KEY_DOWN, self.ncKeyDown)
		self.ncCancel.Bind(wx.EVT_BUTTON, self.cancel)
		self.ncBox.Add(self.ncCancel, 1, wx.ALIGN_CENTER_HORIZONTAL)
		self.SetSizer(self.ncBox)
		self.Fit()
	
	def NewContact(self, event):
		self.snd = wx.adv.Sound("sounds/new.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
		self.ncName.SetFocus()
	
	def NC(self, event):
		next_id = db.get_next_id("contacts")
		rows = db.execute("INSERT INTO contacts (id, name, phone, email, comment) VALUES (?, ?, ?, ?, ?)", (next_id, self.ncName.GetValue(), self.ncNum.GetValue(), self.ncEmail.GetValue(), self.ncCom.GetValue()))
		self.snd = wx.adv.Sound("sounds/add_contact.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
		# print(event.GetEventObject() #.GetParent().GetParent())
		self.Destroy()
		main(False)
	
	def OnFocused(self, e):
		if (e.GetEventObject().GetId() == self.ncName.GetId()) or (e.GetEventObject().GetId() == self.ncNum.GetId()) or (e.GetEventObject().GetId() == self.ncEmail.GetId()) or (e.GetEventObject().GetId() == self.ncCom.GetId()):
			self.snd = wx.adv.Sound("sounds/text_field.wav")
			self.snd.Play(wx.adv.SOUND_ASYNC)
		elif e.GetEventObject().GetId() == self.ncOK.GetId() or e.GetEventObject().GetId() == self.ncCancel.GetId():
			self.snd = wx.adv.Sound("sounds/button.wav")
			self.snd.Play(wx.adv.SOUND_ASYNC)
	
	def ncKeyDown(self, event):
		kc = event.KeyCode
		if kc == wx.WXK_ESCAPE:
			self.cancel(event=None)
			event.Skip()
		else:
			event.Skip()
	
	def cancel(self, event):
		self.snd = wx.adv.Sound("sounds/cancel.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
		self.Destroy()
		main(False)


class ecDialog(wx.Dialog):
	def __init__(self, parent, title, cID, cName, cNum, cemail, cCom, cContainer=None):
		super(ecDialog, self).__init__(None, name=_("Edit contact"))
		self.mFrame = cContainer
		self.cid = int(cID)
		ime = cName
		broj = cNum
		email = cemail
		komentar = cCom
		self.ecBox = wx.BoxSizer(wx.VERTICAL)
		self.ecNameLabel = wx.StaticText(self, label=_("New title"))
		self.ecBox.Add(self.ecNameLabel, 1)
		self.ecName = wx.TextCtrl(self, wx.ID_ANY, ime, style=wx.TE_PROCESS_ENTER)
		self.ecName.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ecName.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.ecName.Bind(wx.EVT_TEXT_ENTER, self.EC)
		self.ecBox.Add(self.ecName, 1, wx.EXPAND)
		self.ecNumLabel = wx.StaticText(self, label=_("New phone"))
		self.ecBox.Add(self.ecNumLabel, 1)
		self.ecNum = wx.TextCtrl(self, wx.ID_ANY, broj, style=wx.TE_PROCESS_ENTER)
		self.ecNum.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ecNum.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.ecNum.Bind(wx.EVT_TEXT_ENTER, self.EC)
		self.ecBox.Add(self.ecNum, 1, wx.EXPAND)
		self.ecEmailLabel = wx.StaticText(self, label=_("New email"))
		self.ecBox.Add(self.ecEmailLabel, 1)
		self.ecEmail = wx.TextCtrl(self, wx.ID_ANY, email, style=wx.TE_PROCESS_ENTER)
		self.ecEmail.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ecEmail.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.ecEmail.Bind(wx.EVT_TEXT_ENTER, self.EC)
		self.ecBox.Add(self.ecEmail, 1, wx.EXPAND)
		self.ecComLabel = wx.StaticText(self, label=_("New comments"))
		self.ecBox.Add(self.ecComLabel, 1)
		self.ecCom = wx.TextCtrl(self, wx.ID_ANY, komentar, style=wx.TE_PROCESS_ENTER)
		self.ecCom.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ecCom.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.ecCom.Bind(wx.EVT_TEXT_ENTER, self.EC)
		self.ecBox.Add(self.ecCom, 1, wx.EXPAND)
		self.ecOK = wx.Button(self, label=_("Save changes"))
		self.ecOK.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ecOK.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.ecOK.Bind(wx.EVT_BUTTON, self.EC)
		self.ecBox.Add(self.ecOK, 1, wx.ALIGN_CENTER_HORIZONTAL)
		self.ecCancel = wx.Button(self, label=_("Cancel"))
		self.ecCancel.Bind(wx.EVT_SET_FOCUS, self.OnFocused)
		self.ecCancel.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.ecCancel.Bind(wx.EVT_BUTTON, self.cancel)
		self.ecBox.Add(self.ecCancel, 1, wx.ALIGN_CENTER_HORIZONTAL)
		self.SetSizer(self.ecBox)
		self.Fit()
	
	def EC(self, event):
		sql = "UPDATE contacts SET name = '%s', phone = '%s', email = '%s', comment = '%s' WHERE id = %s" % (self.ecName.GetValue(), self.ecNum.GetValue(), self.ecEmail.GetValue(), self.ecCom.GetValue(), self.cid)
		print(sql.encode('utf-8'))
		rows = db.execute(sql)
		self.snd = wx.adv.Sound("sounds/add_contact.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
		self.Destroy()
		main(False)
	
	def OnFocused(self, e):
		if (e.GetEventObject().GetId() == self.ecName.GetId()) or (e.GetEventObject().GetId() == self.ecNum.GetId()) or (e.GetEventObject().GetId() == self.ecEmail.GetId()) or (e.GetEventObject().GetId() == self.ecCom.GetId()):
			self.snd = wx.adv.Sound("sounds/text_field.wav")
			self.snd.Play(wx.adv.SOUND_ASYNC)
		elif e.GetEventObject().GetId() == self.ecOK.GetId() or e.GetEventObject().GetId() == self.ecCancel.GetId():
			self.snd = wx.adv.Sound("sounds/button.wav")
			self.snd.Play(wx.adv.SOUND_ASYNC)
	
	def onKeyDown(self, event):
		kc = event.KeyCode
		if kc == wx.WXK_ESCAPE:
			self.cancel(event=None)
			event.Skip()
		else:
			event.Skip()
	
	def cancel(self, event):
		self.snd = wx.adv.Sound("sounds/cancel.wav")
		self.snd.Play(wx.adv.SOUND_ASYNC)
		self.Destroy()
		self.mFrame.Destroy()
		main(False)


class TBIcon(wx.adv.TaskBarIcon):
	def __init__(self, frame):
		wx.adv.TaskBarIcon.__init__(self)
		self.frame = frame
		img = wx.Image("icon.png", wx.BITMAP_TYPE_ANY)
		bmp = wx.Bitmap(img)
		self.icon = wx.Icon()
		self.icon.CopyFromBitmap(bmp)
		self.SetIcon(self.icon, "Pametni tefter")
		self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarLeftClick)
		# self.Bind(wx.EVT_TEXT_ENTER, self.OnTaskBarActivate)
	
	def OnTaskBarActivate(self, event):
		print("TaskBar activated")
	
	def OnTaskBarClose(self, event):
		self.frame.Close()
	
	def OnTaskBarLeftClick(self, event):
		self.frame.Show()
		self.frame.Restore()
		self.frame.cl.SetFocus()


# functions

app_title = _("Smart notebook")

def main(first_call):
	app = wx.App()
	frame = Frame(None, app_title)
	frame.cl.SetFocus()
	if first_call:
		wx.adv.Sound("sounds/start.wav").Play(wx.adv.SOUND_SYNC)
	else:
		wx.adv.Sound("")
	app.MainLoop()

main(True)

db.close()
sys.exit(0)

# 442
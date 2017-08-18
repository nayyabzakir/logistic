from odoo import models, fields, api
from datetime import datetime,date

class Exportlogic(models.Model):
	_name = 'export.logic'
	_rec_name = 'sr_no'

	customer         = fields.Many2one('res.partner',string="Customer",required=True)
	sr_no       	 = fields.Char(string="SR No", readonly=True)
	bill_bol         = fields.Boolean(string="B/L")
	contain          = fields.Boolean(string="Contain")
	bill_types       = fields.Char(string="Billing Type")
	our_job_no       = fields.Char(string="Our Job No", readonly=True,)
	customer_ref     = fields.Char(string="Customer Ref")
	shipper_date     = fields.Date(string="DOC Received Date",default=date.today())
	mani_date        = fields.Date(string="Manifest Date")
	date             = fields.Date(string="Date",required=True,default=date.today())
	bill_no          = fields.Char(string="B/L Number")
	bill_attach      = fields.Binary(string=" ")
	eta              = fields.Char(string="ETA")
	about            = fields.Char(string="On Or About")
	twen_ft          = fields.Integer(string="20 ft")
	fort_ft          = fields.Integer(string="40 ft")
	bayan_no         = fields.Char(string="Bayan No")
	bayan_attach     = fields.Binary(string=" ")
	final_bayan      = fields.Char(string="Final Bayan")
	final_attach     = fields.Binary(string="Final Bayan")
	pre_bayan        = fields.Char(string="Pre Bayan")
	# cus_count_no     = fields.Char(string="Custom Exam of Cont. No")
	custom_exam      = fields.Boolean(string="Open Custom Examination")
	bayan_date       = fields.Date(string="Initial Bayan Date")
	fin_bayan_date   = fields.Date(string="Final Bayan Date")
	status           = fields.Many2one('import.status',string="Status")
	site             = fields.Many2one('import.site',string="Site")
	remarks          = fields.Text(string="Remarks")
	# site_customer 	 = fields.Char(string="Site Under Customer Ref. No.")
	vessel_date 	 = fields.Date(string="Vessel Arrival Date")
	export_link 	 = fields.One2many('logistic.export.tree','export_tree')
	export_id 	     = fields.One2many('export.tree','crt_tree')
	export_serv 	 = fields.One2many('logistic.service.tree','service_tree')
	state 			 = fields.Selection([
					 ('draft', 'Draft'),
					 ('pre', 'Pre Bayan'),
					 ('initial', 'Initial Bayan'),
					 ('final', 'Final Bayan'),
					 ('custom_exam', 'Custom Examination'),
					 ('done', 'Done'),
					 ],default='draft')
	
	

	@api.onchange('custom_exam')
	def change_state(self):
		if self.custom_exam == True:
			self.state='custom_exam'

	@api.onchange('customer')
	def get_bill(self):
		records = self.env['res.partner'].search([('id','=',self.customer.id)])
		print records
		if self.customer:
			self.bill_types = records.bill_type


	@api.onchange('bill_types')
	def get_tree(self):
		if self.bill_types == "B/L Number":
			self.bill_bol = True
		else:
			self.bill_bol = False



	# @api.onchange('bill_types')
	# def get_tree(self):
	# 	if self.bill_types == "Container Wise":
	# 		self.contain = True
	# 	else:
	# 		self.contain = False





	@api.model
	def create(self, vals):
		vals['sr_no'] = self.env['ir.sequence'].next_by_code('export.logics')
		vals['our_job_no'] = self.env['ir.sequence'].next_by_code('export.job.num')
		print "Something"
		new_record = super(Exportlogic, self).create(vals)

		return new_record

	@api.multi
	def prebay(self):
		self.state = "pre"


	@api.multi
	def initialbay(self):
		self.state = "initial"


	@api.multi
	def finalbay(self):
		self.state = "final"


	@api.multi
	def over(self):
		self.state = "done"

	# @api.multi
	# def booker(self):
	# 	pass

	@api.multi
	def create_sale(self):
		prev_rec = self.env['sale.order'].search([('sales_id','=',self.id)])
		prev_rec.unlink()
		# if not prev_rec:
		for data in self.export_id:
			records = self.env['sale.order'].create({
				'partner_id':self.customer.id,
				'date_order':self.date,
				'suppl_name':data.transporter.id,
				'suppl_freight':data.trans_charge,
				'form':data.form.name,
				'to':data.to.name,
				'state':"sale",
				'sales_id': self.id,


				})

			records.order_line.create({
				'product_id':1,
				'name':'Container',
				'product_uom_qty':1.0,
				'price_unit':1.0,
				'crt_no':data.crt_no,
				'product_uom':1,
				'order_id':records.id,
				})


	@api.multi
	def booker(self):
		lisst = []
		for x in self.export_link:
			if x.broker not in lisst:
				lisst.append(x.broker)

		purchase_order = self.env['export.logic'].search([])
		invoice = self.env['account.invoice'].search([])
		invoice_lines = self.env['account.invoice.line'].search([])

		for line in lisst:
			print line
			print "lllllllllllllllllllllllllllllllllllllllllllllll"
			create_invoice = invoice.create({
				'journal_id': 1,
				'partner_id':line.id,
				'customer':self.customer.id,
				'date_invoice' : self.date,
				'type':"in_invoice",
				})
			for x in self.export_link:
				if x.broker.name == line.name: 
					print "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
					print x.broker.name
					print line
					create_invoice_lines= invoice_lines.create({
						'product_id':1,
						'quantity':1,
						'price_unit':x.amt_paid,
						'account_id': 3,
						'name' :'Broker Amount',
						'crt_no':x.container_no,
						'invoice_id' : create_invoice.id
						})


	@api.multi
	def create_custom_charges(self):

		invoice = self.env['account.invoice'].search([])
		invoice_lines = self.env['account.invoice.line'].search([])

		if self.bill_types == "B/L Number":

			create_invoice = invoice.create({
				'journal_id': 1,
				'partner_id':self.customer.id,
				'date_invoice': self.date,
				'billng_type':self.bill_types,
				'bill_num':self.bill_no,
				})

			for x in self.export_serv:
				create_invoice_lines= invoice_lines.create({
					'quantity':1,
					'price_unit':x.sevr_charge,
					'account_id': 3,
					'name' :x.sevr_type.name,
					'invoice_id' : create_invoice.id
					})

		if self.bill_types == "Container Wise":

			for x in self.export_id:
				create_invoice = invoice.create({
					'journal_id': 1,
					'partner_id':self.customer.id,
					'date_invoice': self.date,
					'billng_type':self.bill_types,
					'bill_num':self.bill_no,
					})

				create_invoice_lines= invoice_lines.create({
					'product_id':1,
					'quantity':1,
					'price_unit':x.sev_charge,
					'account_id': 3,
					'name' :x.sev_types.name,
					'crt_no':x.crt_no,
					'invoice_id' : create_invoice.id
					})





	# @api.multi
	# def booker(self):
	# 	purchase_order = self.env['export.logic'].search([])
	# 	invoice = self.env['account.invoice'].search([])
	# 	invoice_lines = self.env['account.invoice.line'].search([])

	# 	for line in export_link:
	# 		create_invoice = invoice.create({
	# 			'journal_id': 1,
	# 			'partner_id':purchase_order.export_link.id,
	# 			'date_invoice' : purchase_order.date_order,
	# 			'type':"in_invoice",
	# 			})
	# 		for x in purchase_order.order_line:
	# 			create_invoice_lines= invoice_lines.create({
	# 				'product_id':1,
	# 				'quantity':x.product_uom_qty,
	# 				'price_unit':purchase_order.suppl_freight,
	# 				'account_id': 3,
	# 				'name' : x.name,
	# 				'invoice_id' : create_invoice.id
	# 				})

		# else:
		# 	for line in prev_rec:
		# 		line.partner_id       				= self.customer.id
		# 		line.date_order       				= self.date
		# 		line.suppl_name       				= self.export_id.transporter.id
		# 		line.form             				= self.export_id.form.name
		# 		line.to               				= self.export_id.to.name
		# 		line.order_line.name  				= 'Container'
		# 		line.order_line.product_uom_qty		= 1.0
		# 		line.order_line.price_unit          = 2.0
		# 		line.order_line.crt_no              = self.export_id.crt_no
		# 		line.order_line.product_uom         = 1

		


class logistics_export_tree(models.Model):
	_name = 'logistic.export.tree'

	container_no = fields.Char(string="Container No.",required=True)
	new_seal     = fields.Char(string="New Seal No")
	broker       = fields.Many2one('res.partner',string="Broker")
	amt_paid     = fields.Float(string="Paid Amount")

	export_tree = fields.Many2one('export.logic')


class service_export_tree(models.Model):
	_name = 'logistic.service.tree'

	sevr_type       = fields.Many2one('sev.type',string="Service Type")
	sevr_charge     = fields.Integer(string="Service Charges")

	service_tree = fields.Many2one('export.logic')

class export_tree(models.Model):
	_name = 'export.tree'

	crt_no       = fields.Char(string="Container No.",required=True)
	form         = fields.Many2one('from.qoute',string="From")
	to           = fields.Many2one('to.quote',string="To")
	fleet_type   = fields.Many2one('fleet',string="Fleet Type")
	sev_charge   = fields.Integer(string="Service Charges")
	sev_types    = fields.Many2one('sev.type',string="Service Type")
	transporter  = fields.Many2one('res.partner',string="Transporter")
	trans_charge = fields.Char(string="Transporter Charges")
	types        = fields.Selection([
					('twen', '20 ft'),
					('forty', '40 ft')],string="Type")

	crt_tree     = fields.Many2one('export.logic')


class export_service(models.Model):
	_name = 'sev.type'

	name  = fields.Char(string="Service Type")


	@api.onchange('transporter','form','to')
	def add_charges(self):
		if self.transporter.id and self.form.id and self.to.id:
			trans = self.env['res.partner'].search([('id','=',self.transporter.id)])
			for x in trans.route_id:
				if self.form.id == x.form.id and self.to.id == x.to.id:
					self.trans_charge = x.trans_charges






class Importlogic(models.Model):
	_name = 'import.logic'
	_rec_name = 's_no'


	customer         = fields.Many2one('res.partner',string="Customer",required=True)
	bill_types       = fields.Char(string="Billing Type")
	bill_bol         = fields.Boolean(string="B/L")
	contain          = fields.Boolean(string="Contain")
	s_no       	     = fields.Char(string="SR No", readonly=True)
	job_no           = fields.Char(string="Job No", readonly=True)
	date             = fields.Date(string="Date" ,required=True,default=date.today())
	customer_ref     = fields.Char(string="Customer Ref")
	site             = fields.Many2one('import.site',string="Site")
	shipper_date     = fields.Date(string="DOC Received Date",default=date.today())
	vessel_date      = fields.Date(string="Vessel Arrival Date")
	bill_attach      = fields.Binary(string=" ")
	bill_no          = fields.Char(string="B/L Number")
	twen_ft          = fields.Integer(string="20 ft")
	fort_ft          = fields.Integer(string="40 ft")
	do_attach        = fields.Binary(string=" ")
	do_no            = fields.Char(string="Do No.")
	bayan_attach     = fields.Binary(string=" ")
	final_bayan      = fields.Char(string="Final Bayan")
	final_attach     = fields.Binary(string="Final Bayan")
	bayan_no         = fields.Char(string="Bayan No.")
	bayan_date       = fields.Date(string="Bayan Date")
	fin_bayan_date   = fields.Date(string="Final Bayan Date")
	status           = fields.Many2one('import.status',string="Status")
	import_id 	     = fields.One2many('import.tree','crt_tree')
	import_serv 	 = fields.One2many('import.service.tree','import_tree')
	remarks          = fields.Text(string="Remarks")
	stages 			 = fields.Selection([
					 ('draft', 'Draft'),
					 ('pre', 'Pre Bayan'),
					 ('initial', 'Initial Bayan'),
					 ('final', 'Final Bayan'),
					 ('done', 'Done'),
					 ],default='draft')


	@api.model
	def create(self, vals):
		vals['s_no'] = self.env['ir.sequence'].next_by_code('import.logics')
		vals['job_no'] = self.env['ir.sequence'].next_by_code('import.job.num')

		new_record = super(Importlogic, self).create(vals)

		return new_record

	@api.onchange('customer')
	def get_bill(self):
		records = self.env['res.partner'].search([('id','=',self.customer.id)])
		print records
		print "88888888888888888888888888888888888lllllllllllll"
		if self.customer:
			self.bill_types = records.bill_type


	@api.onchange('bill_types')
	def get_tree(self):
		if self.bill_types == "B/L Number":
			self.bill_bol = True
		else:
			self.bill_bol = False


	@api.multi
	def prebay(self):
		self.stages = "pre"


	@api.multi
	def initialbay(self):
		self.stages = "initial"


	@api.multi
	def finalbay(self):
		self.stages = "final"


	@api.multi
	def over(self):
		self.stages = "done"


	@api.multi
	def create_sale(self):
		prev_rec = self.env['sale.order'].search([('sales_id','=',self.id)])
		prev_rec.unlink()
		# if not prev_rec:
		for data in self.import_id:
			records = self.env['sale.order'].create({
				'partner_id':self.customer.id,
				'date_order':self.date,
				'suppl_name':data.transporter.id,
				'suppl_freight':data.trans_charge,
				'form':data.form.name,
				'to':data.to.name,
				'state':"sale",
				'sales_id': self.id

				})

			records.order_line.create({
				'name':'Container',
				'product_uom_qty':1.0,
				'price_unit':1.0,
				'crt_no':data.crt_no,
				'product_uom':1,
				'order_id':records.id,
				})

class export_tree(models.Model):
	_name = 'import.tree'

	crt_no       = fields.Char(string="Container No.",required=True)
	form         = fields.Many2one('from.qoute',string="From")
	to           = fields.Many2one('to.quote',string="To")
	fleet_type   = fields.Many2one('fleet',string="Fleet Type")
	sev_charge   = fields.Integer(string="Service Charges")
	sev_types    = fields.Many2one('sev.type',string="Service Type")
	transporter  = fields.Many2one('res.partner',string="Transporter")
	trans_charge = fields.Char(string="Transporter Charges")
	types        = fields.Selection([
					('twen', '20 ft'),
					('forty', '40 ft')],string="Type")

	crt_tree     = fields.Many2one('import.logic')

class service_import_tree(models.Model):
	_name = 'import.service.tree'

	sevr_type       = fields.Many2one('sev.type',string="Service Type")
	sevr_charge     = fields.Integer(string="Service Charges")

	import_tree     = fields.Many2one('import.logic')


class export_service(models.Model):
	_name = 'sev.type'

	name  = fields.Char(string="Service Type")


	@api.onchange('transporter','form','to')
	def add_charges(self):
		if self.transporter.id and self.form.id and self.to.id:
			trans = self.env['res.partner'].search([('id','=',self.transporter.id)])
			for x in trans.route_id:
				if self.form.id == x.form.id and self.to.id == x.to.id:
					self.trans_charge = x.trans_charges



class Sitelogic(models.Model):
	_name = 'import.site'
	_rec_name = 'site_name'
	
	site_name = fields.Char(string="Site Name")
	city      = fields.Char(string="City")
	address   = fields.Char(string="Address")
	cnt_num   = fields.Char(string="Contact No")


class Statuslogic(models.Model):
	_name = 'import.status'
	_rec_name = 'comment'
	
	comment = fields.Char(string="status")

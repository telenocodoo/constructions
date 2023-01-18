# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from datetime import datetime, timedelta


class CustodyDescription(models.Model):
    _name = 'custody.description'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()


class CustodyRequest(models.Model):
    _name = 'custody.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "employee_id"
    _order = "state"

    name = fields.Char()
    expense_account_move_id = fields.Many2one('account.move', 'Journal Expense')
    liquidated_account_move_id = fields.Many2one('account.move', 'Journal Liquidated')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    description = fields.Text()
    reason = fields.Text()
    amount = fields.Float()
    remaining_amount = fields.Float(compute='get_remaining_amount', store=True)
    date = fields.Date(default=fields.date.today())
    exchange_item_ids = fields.One2many('custody.request.line', 'custody_id')
    move_line_ids = fields.One2many('account.move.line', 'custody_id',
                                    domain=lambda self: [('move_id', '=', self.expense_account_move_id.id)])
    liquidated_move_line_ids = fields.One2many('account.move.line', 'custody_id',
                                               domain=lambda self: [('move_id', '=', self.liquidated_account_move_id.id)])
    is_direct_manager = fields.Boolean(compute='get_direct_manager')
    is_liquidated = fields.Boolean(compute='get_is_liquidated')

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    state = fields.Selection([('draft', 'Draft'),
                              ('direct_manager_approve', 'Direct Manager Approved'),
                              ('department_manager_approve', 'Department Manager Approved'),
                              ('center_manager_approve', 'Center Manager Approved'),
                              ('accounting_approve', 'Accounting Approved'),
                              ('paid', 'Paid'),
                              ('in_progress', 'In Progress'),
                              ('liquidated', 'Liquidated'),
                              ('refuse', 'Refused'),
                              ('done', 'Done'),
                              ], default='draft',  translate=True ,tracking=True, group_expand='_expand_states')
    color = fields.Integer(compute="compute_color")

    def _get_state_desc(self):
        value = dict(self.env['custody.request'].fields_get(allfields=['state'])['state']['selection'])

        for record in self:
            if record.state:
                record.state_desc = value[record.state]
            else:
                record.state_desc = ''

    state_desc = fields.Char(compute="_get_state_desc")

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     employee = self.env.user.has_group('ncss_custody_request.custody_employee')
    #     direct_manager = self.env.user.has_group('ncss_custody_request.custody_direct_manager')
    #     department_manager = self.env.user.has_group('ncss_custody_request.custody_department_manager')
    #     accounting_manager = self.env.user.has_group('ncss_custody_request.custody_accounting_manager')
    #     center_manager = self.env.user.has_group('ncss_custody_request.custody_center_manager')
    #
    #     if employee:
    #         args += [('create_uid', '=', self.env.user.id)]
    #     if direct_manager:
    #         current_user_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).id
    #         args += ['|', ('employee_id.parent_id.id', '=', current_user_id), ('create_uid.id', '=', self.env.user.id)]
    #     # if department_manager:
    #     #     current_user_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).id
    #     #     args += ['|', '|', ('employee_id.department_id.manager_id.id', '=', current_user_id),
    #     #              ('employee_id.parent_id.id', '=', current_user_id),
    #     #              ('create_uid.id', '=', self.env.user.id)]
    #     if accounting_manager:
    #         current_user_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).id
    #         args += ['|', '|', ('create_uid.id', '=', self.env.user.id),
    #                  ('employee_id.parent_id.id', '=', current_user_id),
    #                  ('state', 'in', ['center_manager_approve', 'accounting_approve','paid', 'in_progress', 'liquidated', 'refuse', 'done'])
    #                  ]
    #     if center_manager:
    #         args += []
    #     return super(CustodyRequest, self).search(args=args, offset=offset, limit=limit, order=order, count=count)

    @api.depends('state')
    def compute_color(self):
        for record in self:
            if record.state == 'draft':
                record.color = 1
            elif record.state == 'direct_manager_approve':
                record.color = 2
            elif record.state == 'department_manager_approve':
                record.color = 3
            elif record.state == 'center_manager_approve':
                record.color = 4
            elif record.state == 'accounting_approve':
                record.color = 5
            elif record.state == 'paid':
                record.color = 6
            elif record.state == 'in_progress':
                record.color = 7
            elif record.state == 'liquidated':
                record.color = 8
            elif record.state == 'refuse':
                record.color = 9
            else:
                record.color = 10

    def get_direct_manager(self):
        current_user_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).id
        for record in self:
            if record.employee_id and record.employee_id.parent_id:
                if record.employee_id.parent_id.id == current_user_id:
                    record.is_direct_manager = True
                else:
                    record.is_direct_manager = False
            else:
                record.is_direct_manager = False

    def get_is_liquidated(self):
        for record in self:
            if record.remaining_amount == 0.0:
                record.is_liquidated = True
                user_ids = list(self.get_users("ncss_custody_request.custody_request_liquidated_button"))
                if user_ids:
                    for rec in user_ids:
                        self.make_activity(rec)
            else:
                record.is_liquidated = False

    @api.depends('amount', 'exchange_item_ids')
    def get_remaining_amount(self):
        for record in self:
            total_amount = sum([line.amount for line in self.exchange_item_ids])
            record.remaining_amount = record.amount-total_amount

    @api.constrains('amount', 'exchange_item_ids', 'remaining_amount')
    def _constrains_remaining_amount(self):
        for record in self:
            total_amount = sum([line.amount for line in record.exchange_item_ids])
            if record.amount < total_amount:
                raise UserError(_("Remaining Amount Must Be Less Than Or Equal To Amount"))

    def make_activity(self, user_ids):
        print("j...", user_ids)
        now = datetime.now()
        date_deadline = now.date()
        if self:
            if user_ids:
                actv_id=self.sudo().activity_schedule(
                    'mail.mail_activity_data_todo', date_deadline,
                    note=_(
                        '<a href="#" data-oe-model="%s" data-oe-id="%s">Task </a> for <a href="#" data-oe-model="%s" data-oe-id="%s">%s\'s</a> Review') % (
                             self._name, self.id, self.employee_id._name,
                             self.employee_id.id, self.employee_id.display_name),
                    user_id=user_ids,
                    res_id=self.id,
                    summary=_("Request Approve")
                    )
                print("active" ,actv_id)
                # now = datetime.now()
                # start_date = now.date()
                # end_date = start_date + timedelta(days=1)
                # notify_id = self.env['hr.notification'].sudo().create({'notification_MSG': message,
                #                                                        'date_start': start_date,
                #                                                        'date_end': end_date,
                #                                                        'state': 'notify',
                #                                                        'employee_id': self.employee_id.id})
                # print("notify_id", notify_id)

    def make_notification(self, message):
        now = datetime.now()
        start_date = now.date()
        end_date = start_date + timedelta(days=1)
        notify_id = self.env['hr.notification'].sudo().create({'notification_MSG': message,
                                                               'date_start': start_date,
                                                               'date_end': end_date,
                                                               'state': 'notify',
                                                               'employee_id': self.employee_id.id})
        print("notify_id", notify_id)

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('custody.sequence')
        res = super(CustodyRequest, self).create(values)
        user_ids = res.mapped('employee_id.parent_id.user_id').ids or [self.env.uid]
        if user_ids:
            res.make_activity(user_ids[0])
        message = 'تم انشاء طلب العهده الخاص بك (%s)' % res['name']
        res.make_notification(message)
        return res

    def action_refuse(self):
        for record in self:
            if not record.reason:
                raise UserError(_("Please Add the reason of Refuse"))
            else:
                self.state = 'refuse'

    def action_direct_manager_approve(self):
        user_ids = self.mapped('employee_id.department_id.manager_id.user_id').ids
        print(user_ids)
        if user_ids:
            self.make_activity(user_ids[0])
        message = 'تمت موافقه المدير المباشر علي طلب العهده الخاص بك (%s)' % self.name
        self.make_notification(message)
        self.state = 'direct_manager_approve'

    def get_users(self, groupidxml):
        myuserlist = []
        groupid = self.env.ref(groupidxml).id
        groupObj = self.env['res.groups'].search([('id', '=', groupid)])
        if groupObj:
            for rec in groupObj.users:
                myuserlist.append(rec.id)

        return myuserlist

    def action_department_manager_approve(self):
        user_ids = list(self.get_users("ncss_custody_request.custody_request_center_manager_button"))
        print(user_ids)
        if user_ids:
            for rec in user_ids:
                self.make_activity(rec)
        message = 'تمت موافقه مدير القسم علي طلب العهده الخاص بك (%s)' % self.name
        self.make_notification(message)
        self.state = 'department_manager_approve'

    def center_manager_approve(self):
        user_ids = list(self.get_users("ncss_custody_request.custody_request_accounting_manager_button"))
        print(user_ids)
        if user_ids:
            for rec in user_ids:
                self.make_activity(rec)
        message = 'تمت موافقه مدير المركز علي طلب العهده الخاص بك (%s)' % self.name
        self.make_notification(message)
        self.state = 'center_manager_approve'

    def accounting_approve(self):
        user_ids = list(self.get_users("ncss_custody_request.custody_request_in_progress_button"))
        print(user_ids)
        if user_ids:
            for rec in user_ids:
                self.make_activity(rec)
        message = 'تمت موافقه مدير الحسابات علي طلب العهده الخاص بك (%s)' % self.name
        self.make_notification(message)
        self.state = 'accounting_approve'

    def create_account_move(self, journal, label, debit_account_id, credit_account_id, amount, address_home_id):
        account_move_obj = self.env['account.move']
        account_move_id = account_move_obj.sudo().create({
            'journal_id': journal,
            'ref': label,
        })
        journal_line = self.with_context(dict(self._context, check_move_validity=False)).env['account.move.line']
        journal_line.sudo().create({
            'move_id': account_move_id.id,
            'account_id': debit_account_id,
            'name': label,
            'debit': amount,
            'credit': 0.0,
            'partner_id': address_home_id,
            'custody_id': self.id,
        })
        journal_line.sudo().create({
            'move_id': account_move_id.id,
            'account_id': credit_account_id,
            'name': label,
            'debit': 0.0,
            'credit': amount,
            'partner_id': address_home_id,
            'custody_id': self.id,
        })
        return account_move_id

    def paid_action(self):
        journal = self.env.user.company_id.custody_journal_id.id
        label = self.env.user.company_id.label
        debit_account_id = self.env.user.company_id.debit_account_id.id
        credit_account_id = self.env.user.company_id.credit_account_id.id
        amount = self.amount
        address_home_id = self.sudo().employee_id.address_home_id.id
        account_move_obj = self.sudo().create_account_move(journal, label, debit_account_id, credit_account_id, amount, address_home_id)
        self.expense_account_move_id = account_move_obj.id

        user_ids = list(self.get_users("ncss_custody_request.custody_request_liquidated_button"))
        print(user_ids)
        if user_ids:
            for rec in user_ids:
                self.make_activity(rec)
        message = 'تمت صرف العهده المطلوبه (%s)' % self.name
        self.make_notification(message)
        self.state = 'paid'

    def in_progress_action(self):
        journal = self.env.user.company_id.custody_journal_id.id
        label = self.env.user.company_id.label
        debit_account_id = self.env.user.company_id.debit_account_id.id
        credit_account_id = self.env.user.company_id.credit_account_id.id
        amount = self.amount
        address_home_id = self.sudo().employee_id.address_home_id.id
        account_move_obj = self.sudo().create_account_move(journal, label, debit_account_id, credit_account_id, amount, address_home_id)
        self.expense_account_move_id = account_move_obj.id

        # user_ids = list(self.get_users("ncss_custody_request.custody_request_done_button"))
        # print(user_ids)
        # if user_ids:
        #     for rec in user_ids:
        #         self.make_activity(rec)
        message = 'جارى اهلاك العهده الخاصه بك (%s)' % self.name
        self.make_notification(message)
        self.state = 'in_progress'

    def make_liquidated_action(self):
        user_ids = list(self.get_users("ncss_custody_request.custody_request_done_button"))
        print(":::::::::::::::::", user_ids)
        if user_ids:
            for rec in user_ids:
                self.make_activity(rec)
        message = 'تم طلب تصفيه العهده الخاصه بك (%s)' % self.name
        self.make_notification(message)
        self.state = 'liquidated'

    def liquidated_action(self):
        journal = self.env.user.company_id.custody_journal_id.id
        label = self.env.user.company_id.label
        credit_account_id = self.env.user.company_id.debit_account_id.id
        debit_account_id = self.env.user.company_id.expense_account_id.id
        amount = self.amount
        address_home_id = self.sudo().employee_id.address_home_id.id
        account_move_obj = self.sudo().create_account_move(journal, label, debit_account_id, credit_account_id, amount, address_home_id)
        self.liquidated_account_move_id = account_move_obj.id
        message = 'تمت تسويه العهده الخاصه بك (%s)' % self.name
        self.make_notification(message)
        self.state = 'done'

    def set_to_draft(self):
        message = 'تمت اعاده العهده الخاصه بك كجديده (%s)' % self.name
        self.make_notification(message)
        self.state = 'draft'


class CustodyRequestLine(models.Model):
    _name = 'custody.request.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    amount = fields.Float()
    date = fields.Date(default=fields.date.today())
    description = fields.Text()
    # attach_invoice = fields.Binary()
    attach_invoice = fields.Many2many('ir.attachment', 'cust_attach_rel', 'doc_id', 'attach_id3', string="Attachment",
                                 help='You can attach the copy of your document', copy=False)

    custody_description_id = fields.Many2one('custody.description')
    custody_id = fields.Many2one('custody.request')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    custody_id = fields.Many2one('custody.request')

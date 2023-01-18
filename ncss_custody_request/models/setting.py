from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    debit_account_id = fields.Many2one('account.account')
    credit_account_id = fields.Many2one('account.account')
    custody_journal_id = fields.Many2one('account.journal')
    expense_account_id = fields.Many2one('account.account')
    expense_label = fields.Char()
    label = fields.Char()


class RequisitionConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    debit_account_id = fields.Many2one('account.account',
                                       default=lambda self: self.env.user.company_id.debit_account_id)
    credit_account_id = fields.Many2one('account.account',
                                        default=lambda self: self.env.user.company_id.credit_account_id)
    custody_journal_id = fields.Many2one('account.journal',
                                        default=lambda self: self.env.user.company_id.custody_journal_id)

    expense_account_id = fields.Many2one('account.account',
                                         default=lambda self: self.env.user.company_id.expense_account_id)
    expense_label = fields.Char(default=lambda self: self.env.user.company_id.expense_label)

    label = fields.Char(default=lambda self: self.env.user.company_id.label)

    @api.model
    def create(self, vals):
        if 'company_id' in vals\
                or 'debit_account_id' in vals \
                or 'expense_account_id' in vals \
                or 'expense_label' in vals \
                or 'label' in vals \
                or 'credit_account_id' in vals or 'custody_journal_id' in vals:
            self.env.user.company_id.write({
                    'debit_account_id': vals['debit_account_id'],
                    'credit_account_id': vals['credit_account_id'],
                    'custody_journal_id': vals['custody_journal_id'],
                    'expense_account_id': vals['expense_account_id'],
                    'expense_label': vals['expense_label'],
                    'label': vals['label'],
                 })
        res = super(RequisitionConfigSettings, self).create(vals)
        return res

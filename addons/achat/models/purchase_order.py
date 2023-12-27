# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import fields, models, api
from odoo.tools import float_compare
from itertools import groupby
from lxml import etree


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    all_picking_ids = fields.One2many(
        "stock.picking", string="All Pickings", compute="_compute_all_pickings"
    )
    all_picking_count = fields.Integer(
        "All Pickings Count", compute="_compute_all_picking_count"
    )

    def _compute_all_picking_count(self):
        for rec in self:
            rec.all_picking_count = len(rec.all_picking_ids)

    def _compute_all_pickings(self):
        for rec in self:
            groups = rec.mapped("picking_ids.group_id")
            all_picking_ids = self.env["stock.picking"].search(
                [("group_id", "in", groups.ids)]
            )
            rec.all_picking_ids = all_picking_ids

    def action_view_all_pickings(self):
        return self._get_action_view_all_pickings(self.all_picking_ids)

    def _get_action_view_all_pickings(self, picking_ids):
        """Similar to the _get_action_view_picking method in the purchase module"""
        self.ensure_one()
        result = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        # override the context to get rid of the default filtering on picking type
        result["context"] = {}

        if not picking_ids or len(picking_ids) > 1:
            result["domain"] = [("id", "in", picking_ids.ids)]
        elif len(picking_ids) == 1:
            res = self.env.ref("stock.view_picking_form", False)
            form_view = [(res and res.id or False, "form")]
            result["views"] = form_view + [
                (state, view)
                for state, view in result.get("views", [])
                if view != "form"
            ]
            result["res_id"] = picking_ids.id
        return result

    def _check_split_pickings(self):
        # Avoid one search query per order
        purchases_moves = self.env["stock.move"].search(
            [
                ("purchase_line_id", "in", self.order_line.ids),
                ("state", "not in", ("cancel", "done")),
            ]
        )
        for order in self:
            moves = purchases_moves.filtered(
                lambda move: move.purchase_line_id.id in order.order_line.ids
            )
            pickings = moves.mapped("picking_id")
            pickings_by_date = {}
            for pick in pickings:
                pickings_by_date[pick.scheduled_date.date()] = pick

            order_lines = moves.mapped("purchase_line_id")
            date_groups = groupby(
                order_lines, lambda l: l._get_group_keys(l.order_id, l)
            )
            for key, lines in date_groups:
                date_key = fields.Date.from_string(key[0]["date_planned"])
                for line in lines:
                    for move in line.move_ids:
                        if move.state in ("cancel", "done"):
                            continue
                        if (
                            move.picking_id.scheduled_date.date() != date_key
                            or pickings_by_date.get(date_key) != move.picking_id
                        ):
                            if date_key not in pickings_by_date:
                                copy_vals = line._first_picking_copy_vals(key, line)
                                new_picking = move.picking_id.copy(copy_vals)
                                pickings_by_date[date_key] = new_picking
                            move._do_unreserve()
                            move.update(
                                {
                                    "picking_id": pickings_by_date[date_key],
                                    "date_deadline": date_key,
                                }
                            )
                            move._action_assign()
            pickings.filtered(lambda picking: not picking.move_ids).write(
                {"state": "cancel"}
            )

    state = fields.Selection(selection_add=[("approved", "Approved"), ("purchase",)])

    READONLY_STATES = {
        "purchase": [("readonly", True)],
        "done": [("readonly", True)],
        "cancel": [("readonly", True)],
        "approved": [("readonly", True)],
    }

    # Update the readonly states:
    origin = fields.Char(states=READONLY_STATES)
    date_order = fields.Datetime(states=READONLY_STATES)
    partner_id = fields.Many2one(states=READONLY_STATES)
    dest_address_id = fields.Many2one(states=READONLY_STATES)
    currency_id = fields.Many2one(states=READONLY_STATES)
    order_line = fields.One2many(states=READONLY_STATES)
    company_id = fields.Many2one(states=READONLY_STATES)
    picking_type_id = fields.Many2one(states=READONLY_STATES)

    def button_release(self):
        return super(PurchaseOrder, self).button_approve()

    def button_approve(self, force=False):
        two_steps_purchase_approval_ids = []
        for rec in self:
            partner_requires_approve = (
                rec.partner_id.purchase_requires_second_approval == "always"
            )
            company_requires_approve = (
                rec.partner_id.purchase_requires_second_approval == "based_on_company"
                and rec.company_id.purchase_approve_active
            )
            if rec.state != "approved" and (
                partner_requires_approve or company_requires_approve
            ):
                two_steps_purchase_approval_ids.append(rec.id)
        two_steps_purchase_approval = self.browse(two_steps_purchase_approval_ids)
        two_steps_purchase_approval.write({"state": "approved"})
        one_step_purchase_approval = self - two_steps_purchase_approval
        return super(PurchaseOrder, one_step_purchase_approval).button_approve(
            force=force
        )

    active = fields.Boolean(default=True)

    def toggle_active(self):
        if self.filtered(lambda po: po.state not in ["done", "cancel"] and po.active):
            raise UserError(_("Only 'Locked' or 'Canceled' orders can be archived"))
        return super().toggle_active()

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        res = super().get_view(view_id, view_type, **options)

        if view_type == "form":
            purchase_xml = etree.XML(res["arch"])
            partner_fields = purchase_xml.xpath('//field[@name="partner_id"]')

            if partner_fields:
                partner_fields = partner_fields[0]
                domain = partner_fields.get("domain", "[]").replace(
                    "[", "[('purchase_selectable', '=', True),"
                )
                partner_fields.attrib["domain"] = domain
                res["arch"] = etree.tostring(purchase_xml, encoding="unicode")

        return res

    reception_status = fields.Selection(
        [
            ("no", "Nothing Received"),
            ("partial", "Partially Received"),
            ("received", "Fully Received"),
        ],
        compute="_compute_reception_status",
        store=True,
    )
    force_received = fields.Boolean(
        readonly=True,
        states={"done": [("readonly", False)]},
        copy=False,
        help="If true, the reception status will be forced to Fully Received, "
        "even if some lines are not fully received. "
        "To be able to modify this field, you must first lock the order.",
    )

    @api.depends(
        "state", "force_received", "order_line.qty_received", "order_line.product_qty"
    )
    def _compute_reception_status(self):
        prec = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        for order in self:
            status = "no"
            if order.state in ("purchase", "done"):
                if order.force_received:
                    status = "received"
                elif all(
                    [
                        float_compare(
                            line.qty_received, line.product_qty, precision_digits=prec
                        )
                        >= 0
                        for line in order.order_line
                    ]
                ):
                    status = "received"
                elif any(
                    [
                        float_compare(line.qty_received, 0, precision_digits=prec) > 0
                        for line in order.order_line
                    ]
                ):
                    status = "partial"
            order.reception_status = status

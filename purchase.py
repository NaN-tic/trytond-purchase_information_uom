# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval, Bool
from ..account_invoice_information_uom.invoice import InformationUomMixin
from trytond.modules.product import price_digits
from decimal import Decimal

__all__ = ['PurchaseLine', 'CreatePurchase']

STATES = {
    'invisible': ~Bool(Eval('show_info_unit')),
    }
DEPENDS = ['show_info_unit']


class PurchaseLine(InformationUomMixin, metaclass=PoolMeta):
    __name__ = 'purchase.line'

    def get_invoice_line(self):
        lines = super(PurchaseLine, self).get_invoice_line()
        if not lines:
            return lines
        for line in lines:
            if self.show_info_unit:
                line.info_quantity = self.info_quantity
                line.info_unit_price = self.info_unit_price
        return lines


class CreatePurchase(metaclass=PoolMeta):
    __name__ = 'purchase.request.create_purchase'

    @classmethod
    def compute_purchase_line(cls, key, requests, purchase):
        line = super().compute_purchase_line(key, requests, purchase)
        line.on_change_unit_price()
        return line


class ProductSupplierPrice(metaclass=PoolMeta):
    __name__ = 'purchase.product_supplier.price'

    show_info_unit = fields.Function(fields.Boolean('Show Information UOM'),
        'on_change_with_show_info_unit')
    info_unit = fields.Function(fields.Many2One('product.uom',
            'Information UOM', states=STATES, depends=DEPENDS),
        'on_change_with_info_unit')
    info_unit_digits = fields.Function(fields.Integer(
        'Information Unit Digits', states=STATES, depends=DEPENDS),
        'on_change_with_info_unit_digits')
    info_quantity = fields.Float('Information Quantity',
        digits=(16, Eval('info_unit_digits', 2)),
        states={
            'invisible': ~Bool(Eval('show_info_unit')),
            },
        depends=['info_unit_digits', 'show_info_unit'])
    info_unit_price = fields.Numeric('Information Unit Price',
        digits=price_digits,
        states={
            'invisible': ~Bool(Eval('show_info_unit')),
            },
        depends=['show_info_unit'])
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    product = fields.Function(fields.Many2One('product.product', 'Product'),
        'get_product')

    def get_product(self, name=None):
        return (self.product_supplier.product and
            self.product_supplier.product.id)

    def on_change_with_currency_digits(self, name=None):
        return 2

    @staticmethod
    def default_info_unit_digits():
        return 2

    @fields.depends('product')
    def on_change_with_info_unit_digits(self, name=None):
        if self.info_unit:
            return self.info_unit.digits
        return 2

    @fields.depends('product')
    def on_change_with_show_info_unit(self, name=None):
        if self.product and self.product.template.use_info_unit:
            return True
        return False

    @fields.depends('product')
    def on_change_with_info_unit(self, name=None):
        if (self.product and self.product.template.use_info_unit):
            return self.product.template.info_unit.id
        return None

    @fields.depends('product', 'quantity', 'uom')
    def on_change_with_info_quantity(self, name=None):
        if not self.product or not self.quantity:
            return
        return self.product.template.calc_info_quantity(self.quantity, self.uom)

    @fields.depends('product', 'info_quantity', 'uom',)
    def on_change_info_quantity(self):
        if not self.product:
            return
        qty = self.product.template.calc_quantity(self.info_quantity, self.uom)
        self.quantity = float(qty)

    @fields.depends('product', 'unit_price', 'product', 'info_unit')
    def on_change_with_info_unit_price(self, name=None):
        if not self.product or not self.unit_price:
            return
        return self.product.template.get_info_unit_price(
            self.unit_price, self.info_unit)

    @fields.depends('product', 'info_unit_price', 'uom')
    def on_change_info_unit_price(self):
        if not self.product or not self.info_unit_price:
            return
        self.unit_price = self.product.template.get_unit_price(
            self.info_unit_price, unit=self.uom)
        if hasattr(self, 'gross_unit_price'):
            self.gross_unit_price = self.unit_price
            self.discount = Decimal('0.0')

    @fields.depends('product', 'quantity', 'uom')
    def on_change_quantity(self):
        if not self.product:
            return
        qty = self.product.template.calc_info_quantity(self.quantity, self.uom)
        self.info_quantity = float(qty)

    @fields.depends('product', 'unit_price', 'info_unit')
    def on_change_unit_price(self):
        if not self.product:
            return
        if self.unit_price:
            self.info_unit_price = self.product.template.get_info_unit_price(
                self.unit_price, self.info_unit)
        else:
            self.info_unit_price = self.unit_price

# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.modules.account_invoice_information_uom import InformationUomMixin

__all__ = ['PurchaseLine']
__metaclass__ = PoolMeta


class PurchaseLine(InformationUomMixin):
    __name__ = 'purchase.line'

    @classmethod
    def __setup__(cls):
        super(PurchaseLine, cls).__setup__()
        for value in cls.amount.on_change_with:
            if value not in cls.info_quantity.on_change:
                cls.info_quantity.on_change.append(value)
            if value not in cls.info_unit_price.on_change:
                cls.info_unit_price.on_change.append(value)
        if not 'purchase' in cls.currency_digits.on_change_with:
            cls.currency_digits.on_change_with.append('purchase')

    def on_change_with_currency_digits(self, name=None):
        if self.purchase:
            return self.purchase.currency_digits
        return 2

    def on_change_with_info_unit_price(self, name=None):
        super(PurchaseLine, self).on_change_with_info_unit_price(name)
        if not self.product:
            return
        if not self.unit_price:
            return self.unit_price
        return self.product.get_info_cost_price(self.unit_price,
            unit=self.unit)

    def get_invoice_line(self, invoice_type):
        lines = super(PurchaseLine, self).get_invoice_line(invoice_type)
        if not lines:
            return lines
        for line in lines:
            if self.show_info_unit:
                line.info_quantity = self.info_quantity
                line.info_unit_price = self.info_unit_price
        return lines

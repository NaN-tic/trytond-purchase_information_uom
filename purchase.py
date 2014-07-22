# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.modules.account_invoice_information_uom import InformationUomMixin

__all__ = ['PurchaseLine']
__metaclass__ = PoolMeta


class PurchaseLine(InformationUomMixin):
    __name__ = 'purchase.line'

    def get_invoice_line(self, invoice_type):
        lines = super(PurchaseLine, self).get_invoice_line(invoice_type)
        if not lines:
            return lines
        for line in lines:
            if self.show_info_unit:
                line.info_quantity = self.info_quantity
                line.info_unit_price = self.info_unit_price
        return lines

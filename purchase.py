# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta
from ..account_invoice_information_uom.invoice import InformationUomMixin

__all__ = ['PurchaseLine', 'CreatePurchase']


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

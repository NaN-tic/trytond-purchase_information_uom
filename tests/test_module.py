
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.modules.company.tests import CompanyTestMixin
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction


class PurchaseInformationUomTestCase(CompanyTestMixin, ModuleTestCase):
    'Test PurchaseInformationUom module'
    module = 'purchase_information_uom'

    @with_transaction()
    def test_supplier_price_information_quantity(self):
        "Test supplier price quantities in both directions, including zero."
        pool = Pool()
        Template = pool.get('product.template')
        Product = pool.get('product.product')
        ProductSupplier = pool.get('purchase.product_supplier')
        Price = pool.get('purchase.product_supplier.price')
        Uom = pool.get('product.uom')

        metre, = Uom.search([('name', '=', 'Meter')])
        kilogram, = Uom.search([('name', '=', 'Kilogram')])
        template = Template(default_uom=metre, purchase_uom=metre,
            use_info_unit=True, info_unit=kilogram, info_ratio=0.046)
        product = Product(template=template)
        supplier = ProductSupplier(template=template, product=product)
        price = Price(product_supplier=supplier, product=product,
            unit=metre, show_info_unit=True)

        # Apply dependent calculations as the client does, so an inverse
        # on_change_with cannot silently overwrite the correct result.
        quantity_dependents = [name for name, definition in Price._fields.items()
            if 'quantity' in definition.on_change_with]
        info_quantity_dependents = [
            name for name, definition in Price._fields.items()
            if 'info_quantity' in definition.on_change_with]

        price.quantity = 341.0
        price.on_change(['quantity'])
        price.on_change_with(quantity_dependents)
        self.assertAlmostEqual(price.info_quantity, 15.69, places=2)

        price.info_quantity = 15.69
        price.on_change(['info_quantity'])
        price.on_change_with(info_quantity_dependents)
        self.assertAlmostEqual(price.quantity, 341.09, places=2)

        price.quantity = 0.0
        price.on_change(['quantity'])
        price.on_change_with(quantity_dependents)
        self.assertEqual(price.info_quantity, 0.0)

        price.quantity = 341.0
        price.on_change(['quantity'])
        price.on_change_with(quantity_dependents)
        price.info_quantity = 0.0
        price.on_change(['info_quantity'])
        price.on_change_with(info_quantity_dependents)
        self.assertEqual(price.quantity, 0.0)


del ModuleTestCase

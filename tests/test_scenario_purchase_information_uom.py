import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import \
    set_fiscalyear_invoice_sequences
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install purchase_information_uom
        config = activate_modules('purchase_information_uom')

        # Create company
        _ = create_company()
        company = get_company()

        # Reload the context
        User = Model.get('res.user')
        Group = Model.get('res.group')
        config._context = User.get_preferences(True, config.context)

        # Create purchase user
        purchase_user = User()
        purchase_user.name = 'Purchase'
        purchase_user.login = 'purchase'
        purchase_group, = Group.find([('name', '=', 'Purchase')])
        purchase_user.groups.append(purchase_group)
        purchase_user.save()

        # Create stock user
        stock_user = User()
        stock_user.name = 'Stock'
        stock_user.login = 'stock'
        stock_group, = Group.find([('name', '=', 'Stock')])
        stock_user.groups.append(stock_group)
        stock_user.save()

        # Create account user
        account_user = User()
        account_user.name = 'Account'
        account_user.login = 'account'
        account_group, = Group.find([('name', '=', 'Accounting')])
        account_user.groups.append(account_group)
        account_user.save()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create parties
        Party = Model.get('party.party')
        supplier = Party(name='Supplier')
        supplier.save()
        customer = Party(name='Customer')
        customer.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        unit2, = ProductUom.find([('name', '=', 'Kilogram')])
        ProductTemplate = Model.get('product.template')
        Product = Model.get('product.product')
        product = Product()
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.use_info_unit = True
        template.info_unit = unit2
        template.info_ratio = Decimal('2')
        template.type = 'service'
        template.purchasable = True
        template.list_price = Decimal('40')
        template.account_category = account_category
        template.save()
        self.assertEqual(template.info_list_price, Decimal('20.0000'))
        product, = template.products
        product.cost_price = Decimal('20')
        product.save()

        # Create payment term
        PaymentTerm = Model.get('account.invoice.payment_term')
        payment_term = PaymentTerm(name='Term')
        line = payment_term.lines.new(type='percent', ratio=Decimal('.5'))
        delta, = line.relativedeltas
        delta.days = 20
        line = payment_term.lines.new(type='remainder')
        delta = line.relativedeltas.new(days=40)
        payment_term.save()

        # Purchase 5 products
        config.user = purchase_user.id
        Purchase = Model.get('purchase.purchase')
        PurchaseLine = Model.get('purchase.line')
        purchase = Purchase()
        purchase.party = supplier
        purchase.payment_term = payment_term
        purchase.invoice_method = 'order'
        purchase_line = PurchaseLine()
        purchase.lines.append(purchase_line)
        purchase_line.product = product
        purchase_line.quantity = 2.0
        purchase_line.unit_price = product.cost_price
        self.assertEqual(purchase_line.show_info_unit, True)
        self.assertEqual(purchase_line.unit_price, Decimal('20'))
        self.assertEqual(purchase_line.info_unit_price, Decimal('10'))
        self.assertEqual(purchase_line.unit, unit)
        self.assertEqual(purchase_line.info_unit, unit2)
        purchase_line.quantity = 5
        self.assertEqual(purchase_line.info_quantity, 10)
        self.assertEqual(purchase_line.amount, Decimal('100.0000'))
        purchase_line.unit_price = Decimal('25')
        self.assertEqual(purchase_line.info_unit_price, Decimal('12.5'))
        self.assertEqual(purchase_line.amount, Decimal('125.00'))
        purchase.save()
        purchase.click('quote')
        purchase.click('confirm')
        self.assertEqual(purchase.state, 'processing')
        purchase.reload()
        self.assertEqual(len(purchase.invoices), 1)
        invoice, = purchase.invoices
        self.assertEqual(invoice.origins, purchase.rec_name)

        # Uom information data is copied to invoice
        config.user = account_user.id
        invoice_line, = purchase.invoices[0].lines
        self.assertEqual(invoice_line.info_quantity, 10)
        self.assertEqual(invoice_line.info_unit_price, Decimal('12.5'))
        self.assertEqual(invoice_line.amount, Decimal('125.00'))

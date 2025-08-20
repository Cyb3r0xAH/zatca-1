from decimal import Decimal, ROUND_HALF_UP

def tax_calc(total, ratio, seller_ratio):
    total = Decimal(str(total))
    ratio = Decimal(str(ratio))
    seller_ratio = Decimal(str(seller_ratio))

    tax = total * ratio
    seller_tax = tax * seller_ratio
    net_total = total - seller_tax - tax

    tax = tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    seller_tax = seller_tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    net_total = net_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return tax, seller_tax, net_total